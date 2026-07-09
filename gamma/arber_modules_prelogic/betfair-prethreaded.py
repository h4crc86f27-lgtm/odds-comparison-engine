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

config = configparser.ConfigParser()
config.read('config.ini')
print(config.sections())
db_name = config['DEFAULT']['db_name']

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


def get_market_books(books):
	price_filter=betfairlightweight.filters.price_projection(price_data=['EX_BEST_OFFERS','EX_TRADED'])
	book =trading.betting.list_market_book(market_ids=books,price_projection=price_filter)
	return book


def pull_betfair_data(compid,league):
    print("BETFAIR DATA >>>")

    events = pull_events(compid)
    comp_data={}
    eventids=[]
    h2h_ids = []
    for event in events:
        event_id =event.event.id
        comp_data[event_id]={"name":event.event.name,"odds":[],'markets':[],"timestamp":event.event.open_date.timestamp()}
        eventids.append(event_id)
        print("--",event.event.name,"--")
        #comp_markets = pull_markets(eventids)
        comp_market = pull_markets([event_id])
        #print("comp_market",comp_market)
	#h2h odds
        comp_data[event_id]['h2h_id']=get_event_matchodds(comp_market,event_id)
        try:
            print("getting books")
            books = get_market_books([comp_data[event_id]['h2h_id']])
            print("runnercount:(h2h)",len(books[0].runners))
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
                
                comp_data[event_id]['odds'].append({"last_back_price":last_back_price,"last_back_vol":last_back_vol,"lowest_back_price":0,"lowest_back_vol":0,"lay_price":lay_price,"lay_vol":lay_volume})
               

                
        except Exception as msg:
            insert_error(str(msg),"error in getting betfair book:" + compid + " -- " + event.event.name + " (" + league + ")")
            print(str(msg),"H2H")
            

####### here do the other markets,, will clean this up later.
	#uo 2.5
        comp_data[event_id]['ou25_id']=get_event_ou25(comp_market,event_id)
        try:
            books = get_market_books([comp_data[event_id]['ou25_id']])
            print("runnercount:(2.5)",len(books[0].runners))
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
                
                comp_data[event_id]['markets'].append({"last_back_price_"+which_market:last_back_price_ou25,"last_back_vol_"+which_market:last_back_vol_ou25,"lowest_back_price_"+which_market:0,"lowest_back_vol_"+which_market:0,"lay_price_"+which_market:lay_price_ou25,"lay_vol_"+which_market:lay_volume_ou25})
        except Exception as msg:
            insert_error(str(msg),"error in getting betfair book:" + compid + " -- " + event.event.name + " (" + league + ")")
            print(str(msg),"2.5")               
	#uo 3.5
        comp_data[event_id]['ou35_id']=get_event_ou35(comp_market,event_id)
        try:
            books = get_market_books([comp_data[event_id]['ou35_id']])
            if len(books)>0:
                print("runnercount(3.5):",len(books[0].runners))
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
                    
                    comp_data[event_id]['markets'].append({"last_back_price_"+which_market:last_back_price_ou35,"last_back_vol_"+which_market:last_back_vol_ou35,"lowest_back_price_"+which_market:0,"lowest_back_vol_"+which_market:0,"lay_price_"+which_market:lay_price_ou35,"lay_vol_"+which_market:lay_volume_ou35})
        except Exception as msg:
            insert_error(str(msg),"error in getting betfair book:" + compid + " -- " + event.event.name + " (" + league + ")")
            print(str(msg),"3.5")

	#DNB
        comp_data[event_id]['dnb_id']=get_event_dnb(comp_market,event_id)
        try:
            books = get_market_books([comp_data[event_id]['dnb_id']])
            if len(books)>0:
                print("runnercount(DNB):",len(books[0].runners))
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
                    
                    comp_data[event_id]['markets'].append({"last_back_price_"+which_market:last_back_price_dnb,"last_back_vol_"+which_market:last_back_vol_dnb,"lowest_back_price_"+which_market:0,"lowest_back_vol_"+which_market:0,"lay_price_"+which_market:lay_price_dnb,"lay_vol_"+which_market:lay_volume_dnb})
                


        except Exception as msg:
            insert_error(str(msg),"error in getting betfair book:" + compid + " -- " + event.event.name + " (" + league + ")")
            print(str(msg),"dnb")
    ## first runner is UNDER, then OVER,, if they swap around, this is where the problem is.. can't locate which odds it refers to.
    ## need to spec which 

    #with open("raw_betfair_data/" + league + "_" + str(compid) + ".json","wb") as f:
    #    f.write(res.content)
    return comp_data
