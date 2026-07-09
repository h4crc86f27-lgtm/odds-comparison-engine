import pymysql
import configparser
import requests
import random
import betfairlightweight
from betfairlightweight import filters
import pandas as pd
import numpy as np
import datetime
from arber_modules.utils import *
import time
from fuzzywuzzy import fuzz
import json
import concurrent.futures

thread_count=20

config = configparser.ConfigParser()
config.read('config.ini')
#print(config.sections())
db_name="arb_db_beta"#db_name = config['DEFAULT']['db_name']

with open("/home/arb_bot/proxies") as f:
    proxies = f.read().split("\n")

try:
    proxies.remove('')
except:
    pass


my_username ="hippienew@outlook.com"# cred['username']
my_password = "Saphires_43"#cred['password']
my_app_key ="o4DESE5fzU4r1fkv"# cred['app_key']

trading = betfairlightweight.APIClient(username=my_username,
                                       password=my_password,
                                       app_key=my_app_key,
                                       certs="/home/arb_bot/certs")
#print("logged in!")

# Get a datetime object in a week and convert to string
datetime_in_a_week = (datetime.datetime.utcnow() + datetime.timedelta(weeks=4)).strftime("%Y-%m-%dT%TZ")


def do_betfair_raw():
    conn = pymysql.connect(host='127.0.0.1',user='local',passwd='oeijifjwejfio',db=db_name)
    cur  = conn.cursor()
    cur.execute("select * from raw_comps where site='betfair'")
    rows = cur.fetchall()
    ids_done=[]
    for row in rows:
        ids_done.append(int(row[2]))

    # Create a competition filter
    competition_filter = betfairlightweight.filters.market_filter(
        event_type_ids=[1], # Soccer's event type id is 1
        market_start_time={
            'to': datetime_in_a_week
        })

    # Get a list of competitions for soccer
    competitions = trading.betting.list_competitions(
        filter=competition_filter
    )
    
    for comp in competitions:
        if int(comp.competition.id) not in ids_done:
            print("adding bf comp:",comp.competition.name,comp.competition.id)
            x=cur.execute("insert into raw_comps (comp_name,comp_id,site,timestamp) values(%s,%s,%s,%s)",(comp.competition.name,comp.competition.id,"betfair",time.time()))
    conn.commit()
    conn.close()

def pull_markets(eventids):
	market_catalogue_filter={"eventIds":eventids}

	market_catalogues = trading.betting.list_market_catalogue(
    		filter=market_catalogue_filter,
    		max_results='100',
    		sort='FIRST_TO_START'
	)
	return market_catalogues

def pull_events(compid):
	filter={"competitionIds":[str(compid)]}

	events = trading.betting.list_events(
    		filter=filter
	)
	return events

def get_event_matchodds(markets,eventid): 

	for m in markets:
		if m.market_name=='Match Odds':
			return m.market_id
	return 0

def get_event_ou25(markets,eventid):

	for m in markets:
		if m.market_name=='Over/Under 2.5 Goals':
			return m.market_id
	return 0

def get_event_ou35(markets,eventid):

	for m in markets:
		if m.market_name=='Over/Under 3.5 Goals':
			return m.market_id
	return 0

def get_event_dnb(markets,eventid):
	for m in markets:
		if m.market_name=='Draw no Bet':
			return m.market_id
	return 0

def get_event_dc(markets,eventid):
	for m in markets:
		if m.market_name=='Double Chance':
			return m.market_id
	return 0

def get_event_1x2_ht(markets,eventid):
	for m in markets:
		if m.market_name=='Half Time':
			return m.market_id
	return 0

def get_market_books(books):
	price_filter=betfairlightweight.filters.price_projection(price_data=['EX_BEST_OFFERS','EX_TRADED'])
	book =trading.betting.list_market_book(market_ids=books,price_projection=price_filter)
	return book


def betfair_data_thread(event_id,event):
        retval={"odds":[],"markets":[]}
        #comp_markets = pull_markets(eventids)
        #print("----",event_id,"Getting 1x2----")
        comp_market = pull_markets([event_id])
        #print("comp_market",comp_market)
	    #h2h odds
        #for cm in comp_market:
        #    print(cm.market_name)
        h2h_id=get_event_matchodds(comp_market,event_id)
        try:
            #print("getting books")
            books = get_market_books([h2h_id])
            #print("runnercount:(h2h)",len(books[0].runners))
            for runner in books[0].runners:
                #traded_table={}
                last_back_vol = 0
                #print("---")#,runner.name)
                #last_back_price = runner.last_price_traded
                for tv in runner.ex.traded_volume:
                    #if last_back_price == tv.price:
                    last_back_vol += tv.size
                    #print(tv.price,tv.size)
                    #break
                #print("<<<")
                try:
                    last_back_price = runner.ex.available_to_back[0].price
                except:
                    last_back_price =0 

                try:
                    lay_price = runner.ex.available_to_lay[0].price
                except:
                    lay_price = 0

                try:
                    lay_volume = runner.ex.available_to_lay[0].size
                except:
                    lay_volume = 0
                
                retval['odds'].append({"last_back_price":last_back_price,"last_back_vol":last_back_vol,"lowest_back_price":0,"lowest_back_vol":0,"lay_price":lay_price,"lay_vol":lay_volume})
               

                
        except Exception as msg:
            #insert_error(str(msg),"error in getting betfair book:" + event_id + " -- " + event.event.name + " ("  + ")")
            retval['odds'].append({"last_back_price":0,"last_back_vol":0,"lowest_back_price":0,"lowest_back_vol":0,"lay_price":lay_price,"lay_vol":0})
            #print(str(msg),"H2H",event_id)
            

####### here do the other markets,, will clean this up later.
	#uo 2.5
        #print("----",event_id,"Getting uo2.5----")
        ou25_id =get_event_ou25(comp_market,event_id)
        try:
            books = get_market_books([ou25_id])
            #print("runnercount:(2.5)",len(books[0].runners))
            which_side=0
            for runner in books[0].runners:
                which_side+=1
                if which_side==1:
                    which_market="Under_2.5"
                else:
                    which_market="Over_2.5"
                #traded_table={}
                last_back_vol_ou25 = 0
                
                for tv in runner.ex.traded_volume:
                    #if last_back_price == tv.price:
                    last_back_vol_ou25 += tv.size
                    
                try:
                    last_back_price_ou25 = runner.ex.available_to_back[0].price
                except:
                    last_back_price_ou25 =0 

                try:
                    lay_price_ou25 = runner.ex.available_to_lay[0].price
                except:
                    lay_price_ou25 = 0

                try:
                    lay_volume_ou25 = runner.ex.available_to_lay[0].size
                except:
                    lay_volume_ou25 = 0
                
                retval['markets'].append({"last_back_price_"+which_market:last_back_price_ou25,"last_back_vol_"+which_market:last_back_vol_ou25,"lowest_back_price_"+which_market:0,"lowest_back_vol_"+which_market:0,"lay_price_"+which_market:lay_price_ou25,"lay_vol_"+which_market:lay_volume_ou25})
        except Exception as msg:
            which_market="Under_2.5"
            retval['markets'].append({"last_back_price_"+which_market:0,"last_back_vol_"+which_market:0,"lowest_back_price_"+which_market:0,"lowest_back_vol_"+which_market:0,"lay_price_"+which_market:0,"lay_vol_"+which_market:0})
            which_market="Over_2.5"
            retval['markets'].append({"last_back_price_"+which_market:0,"last_back_vol_"+which_market:0,"lowest_back_price_"+which_market:0,"lowest_back_vol_"+which_market:0,"lay_price_"+which_market:0,"lay_vol_"+which_market:0})
            
            #insert_error(str(msg),"error in getting betfair book:" + compid + " -- " + event.event.name + " (" + league + ")")
            #print(str(msg),"2.5",event_id) 
            #print("added faux 2.5 data..")

	#uo 3.5
        #print("----",event_id,"Getting uo3.5----")
        ou35_id=get_event_ou35(comp_market,event_id)
        try:
            books = get_market_books([ou35_id])
            if 1:#len(books)>0:
                #print("runnercount(3.5):",len(books[0].runners))
                which_side=0
                for runner in books[0].runners:
                    which_side+=1
                    if which_side==1:
                        which_market="Under_3.5"
                    else:
                        which_market="Over_3.5"
                    #traded_table={}
                    last_back_vol_ou35 = 0
                    
                    for tv in runner.ex.traded_volume:
                        #if last_back_price == tv.price:
                        try:
                            last_back_vol_ou35 += tv.size
                        except:
                            pass
                    try:
                        last_back_price_ou35 = runner.ex.available_to_back[0].price
                    except:
                        last_back_price_ou35 =0 

                    try:
                        lay_price_ou35 = runner.ex.available_to_lay[0].price
                    except:
                        lay_price_ou35 = 0

                    try:
                        lay_volume_ou35 = runner.ex.available_to_lay[0].size
                    except:
                        lay_volume_ou35 = 0
                    
                    retval['markets'].append({"last_back_price_"+which_market:last_back_price_ou35,"last_back_vol_"+which_market:last_back_vol_ou35,"lowest_back_price_"+which_market:0,"lowest_back_vol_"+which_market:0,"lay_price_"+which_market:lay_price_ou35,"lay_vol_"+which_market:lay_volume_ou35})
        except Exception as msg:
            which_market="Under_3.5"
            retval['markets'].append({"last_back_price_"+which_market:0,"last_back_vol_"+which_market:0,"lowest_back_price_"+which_market:0,"lowest_back_vol_"+which_market:0,"lay_price_"+which_market:0,"lay_vol_"+which_market:0})
            which_market="Over_3.5"
            retval['markets'].append({"last_back_price_"+which_market:0,"last_back_vol_"+which_market:0,"lowest_back_price_"+which_market:0,"lowest_back_vol_"+which_market:0,"lay_price_"+which_market:0,"lay_vol_"+which_market:0})
            #insert_error(str(msg),"error in getting betfair book:" + compid + " -- " + event.event.name + " (" + league + ")")
            #print(str(msg),"3.5",event_id)
            #print("added faux 3.5 data")

	#DNB
        #print("----",event_id,"Getting DNB----")
        dnb_id=get_event_dnb(comp_market,event_id)
        try:
            books = get_market_books([dnb_id])
            if 1:#len(books)>0:
                #print("runnercount(DNB):",len(books[0].runners))
                which_side=0
                for runner in books[0].runners:
                    which_side+=1
                    if which_side==1:
                        which_market="DNB_Home"
                    else:
                        which_market="DNB_Away"
                    #traded_table={}
                    last_back_vol_dnb = 0
                    
                    for tv in runner.ex.traded_volume:
                        #if last_back_price == tv.price:
                        try:
                            last_back_vol_dnb += tv.size
                        except:
                            pass
                    try:
                        last_back_price_dnb= runner.ex.available_to_back[0].price
                    except:
                        last_back_price_dnb=0 

                    try:
                        lay_price_dnb= runner.ex.available_to_lay[0].price
                    except:
                        lay_price_dnb= 0

                    try:
                        lay_volume_dnb= runner.ex.available_to_lay[0].size
                    except:
                        lay_volume_dnb= 0
                    
                    retval['markets'].append({"last_back_price_"+which_market:last_back_price_dnb,"last_back_vol_"+which_market:last_back_vol_dnb,"lowest_back_price_"+which_market:0,"lowest_back_vol_"+which_market:0,"lay_price_"+which_market:lay_price_dnb,"lay_vol_"+which_market:lay_volume_dnb})
                


        except Exception as msg:
            which_market="DNB_Home"
            
            retval['markets'].append({"last_back_price_"+which_market:0,"last_back_vol_"+which_market:0,"lowest_back_price_"+which_market:0,"lowest_back_vol_"+which_market:0,"lay_price_"+which_market:0,"lay_vol_"+which_market:0})
            which_market="DNB_Away"
            
            retval['markets'].append({"last_back_price_"+which_market:0,"last_back_vol_"+which_market:0,"lowest_back_price_"+which_market:0,"lowest_back_vol_"+which_market:0,"lay_price_"+which_market:0,"lay_vol_"+which_market:0})



	#DC
        #print("----",event_id,"Getting DNB----")
        dc_id=get_event_dc(comp_market,event_id)
        #print("DC ID:",event_id,dc_id)
        try:
            books = get_market_books([dc_id])
            if len(books)>0:
                #print("runnercount(DC):",len(books[0].runners))
                which_side=0
                for runner in books[0].runners:
                    which_side+=1
                    if which_side==1:
                        which_market="DC_1X"
                    elif which_side==2:
                        which_market="DC_X2"
                    else:
                        which_market="DC_12"
                    #traded_table={}
                    last_back_vol_dc = 0
                    
                    for tv in runner.ex.traded_volume:
                        #if last_back_price == tv.price:
                        try:
                            last_back_vol_dc += tv.size
                        except:
                            pass
                    try:
                        last_back_price_dc= runner.ex.available_to_back[0].price
                    except:
                        last_back_price_dc=0 

                    try:
                        lay_price_dc= runner.ex.available_to_lay[0].price
                    except:
                        lay_price_dc= 0

                    try:
                        lay_volume_dc= runner.ex.available_to_lay[0].size
                    except:
                        lay_volume_dc= 0
                    #print(event_id,"dcdata:",{"last_back_price_"+which_market:last_back_price_dc,"last_back_vol_"+which_market:last_back_vol_dc,"lowest_back_price_"+which_market:0,"lowest_back_vol_"+which_market:0,"lay_price_"+which_market:lay_price_dc,"lay_vol_"+which_market:lay_volume_dc})
                    retval['markets'].append({"last_back_price_"+which_market:last_back_price_dc,"last_back_vol_"+which_market:last_back_vol_dc,"lowest_back_price_"+which_market:0,"lowest_back_vol_"+which_market:0,"lay_price_"+which_market:lay_price_dc,"lay_vol_"+which_market:lay_volume_dc})
                


        except Exception as msg:
            #print("error with dc data",str(msg))
            which_market="DC_1X"
            
            retval['markets'].append({"last_back_price_"+which_market:0,"last_back_vol_"+which_market:0,"lowest_back_price_"+which_market:0,"lowest_back_vol_"+which_market:0,"lay_price_"+which_market:0,"lay_vol_"+which_market:0})
            which_market="DC_X2"
            
            retval['markets'].append({"last_back_price_"+which_market:0,"last_back_vol_"+which_market:0,"lowest_back_price_"+which_market:0,"lowest_back_vol_"+which_market:0,"lay_price_"+which_market:0,"lay_vol_"+which_market:0})

            which_market="DC_12"
            
            retval['markets'].append({"last_back_price_"+which_market:0,"last_back_vol_"+which_market:0,"lowest_back_price_"+which_market:0,"lowest_back_vol_"+which_market:0,"lay_price_"+which_market:0,"lay_vol_"+which_market:0})
            

	#1x2_HT
        #print("----",event_id,"Getting DNB----")
        ht_1x2_id=get_event_1x2_ht(comp_market,event_id)
        #print("HT ID:",event_id,ht_1x2_id)

        try:
            books = get_market_books([ht_1x2_id])
            if 1:#len(books)>0:
                #print("runnercount(DNB):",len(books[0].runners))
                which_side=0
                for runner in books[0].runners:
                    which_side+=1
                    if which_side==1:
                        which_market="1_HT"
                    elif which_side==2:
                        which_market="2_HT"
                    else:
                        which_market="X_HT"
                    #traded_table={}
                    last_back_vol_1x2_ht= 0
                    
                    for tv in runner.ex.traded_volume:
                        #if last_back_price == tv.price:
                        try:
                            last_back_vol_1x2_ht += tv.size
                        except:
                            pass
                    try:
                        last_back_price_1x2_ht= runner.ex.available_to_back[0].price
                    except:
                        last_back_price_1x2_ht=0 

                    try:
                        lay_price_1x2_ht= runner.ex.available_to_lay[0].price
                    except:
                        lay_price_1x2_ht= 0

                    try:
                        lay_volume_1x2_ht= runner.ex.available_to_lay[0].size
                    except:
                        lay_volume_1x2_ht= 0
                    #print(event_id,"ht data:",{"last_back_price_"+which_market:last_back_price_1x2_ht,"last_back_vol_"+which_market:last_back_vol_1x2_ht,"lowest_back_price_"+which_market:0,"lowest_back_vol_"+which_market:0,"lay_price_"+which_market:lay_price_1x2_ht,"lay_vol_"+which_market:lay_volume_1x2_ht})
                    retval['markets'].append({"last_back_price_"+which_market:last_back_price_1x2_ht,"last_back_vol_"+which_market:last_back_vol_1x2_ht,"lowest_back_price_"+which_market:0,"lowest_back_vol_"+which_market:0,"lay_price_"+which_market:lay_price_1x2_ht,"lay_vol_"+which_market:lay_volume_1x2_ht})
                


        except Exception as msg:
            #print("error with HT data",str(msg))
            which_market="1_HT"
            
            retval['markets'].append({"last_back_price_"+which_market:0,"last_back_vol_"+which_market:0,"lowest_back_price_"+which_market:0,"lowest_back_vol_"+which_market:0,"lay_price_"+which_market:0,"lay_vol_"+which_market:0})
            which_market="2_HT"
            
            retval['markets'].append({"last_back_price_"+which_market:0,"last_back_vol_"+which_market:0,"lowest_back_price_"+which_market:0,"lowest_back_vol_"+which_market:0,"lay_price_"+which_market:0,"lay_vol_"+which_market:0})
            which_market="X_HT"
            
            retval['markets'].append({"last_back_price_"+which_market:0,"last_back_vol_"+which_market:0,"lowest_back_price_"+which_market:0,"lowest_back_vol_"+which_market:0,"lay_price_"+which_market:0,"lay_vol_"+which_market:0})
            

                 
            #insert_error(str(msg),"error in getting betfair book:" + compid + " -- " + event.event.name + " (" + league + ")")
            #print("err in betfair book..",str(msg),"dnb",event_id)
            #print("added faux dnb data")
        #print("@@@@@@@@@",event_id,retval)
        #print("")
        return retval,event_id




def pull_betfair_data(compid,league):
    #print("BETFAIR DATA >>>")

    events = pull_events(compid)
    comp_data={}
    eventids=[]
    h2h_ids = []
    e_list=[]

    for event in events:
        event_id =event.event.id
        comp_data[event_id]={"name":event.event.name,"odds":[],'markets':[],"timestamp":event.event.open_date.timestamp()}
        eventids.append(event_id)
        #print("--",event.event.name,"--")
        e_list.append([event_id,event])

    #print(">> BF thread pull")
    #print("e_list_len:",len(e_list))    

    with concurrent.futures.ThreadPoolExecutor(max_workers=thread_count) as executor:
        future_to_url = {executor.submit(betfair_data_thread, e[0],e[1]): e for e in e_list}
        for future in concurrent.futures.as_completed(future_to_url):
            #url = future_to_url[future]
            try:
                data,event_id = future.result()
                for d in data['odds']:
                    comp_data[event_id]['odds'].append(d)
                for d in data['markets']:
                    comp_data[event_id]['markets'].append(d)
                try:
                    do_odds_history_insert("betfair",event_id,data['odds'],data['markets'])
                except Exception as msg:
                    pass#print("err on odds history insert..",str(msg))

            except Exception as exc:
                pass#print("betfair section", '%r generated an exception: %s' % ("brr", exc))

    #print("betfair data")
    #for cd in comp_data:
    #    print(">>",cd,comp_data[cd])
    #print("--END BF--")



    ## first runner is UNDER, then OVER,, if they swap around, this is where the problem is.. can't locate which odds it refers to.
    ## need to spec which 

    #with open("raw_betfair_data/" + league + "_" + str(compid) + ".json","wb") as f:
    #    f.write(res.content)
    #print(comp_data)
    #print("^^^ BETFAIR COMPDATA")
    return comp_data

