#betfair API market puller
import time
from operator import le
import betfairlightweight
from betfairlightweight import filters
import pandas as pd
import numpy as np
import os
import datetime
import json
import requests
import pickle
from fuzzywuzzy import fuzz
import pymysql
import concurrent.futures
import random
import unicodedata
#from arber_modules.unibet import *

version="beta"
db_name="arb_db_"+ version
## here do a toto check on comps, on random occasion

def convert_midnight(inny):
	print(inny)
	x,y = inny.split("T")
	yr,mt,dt = x.split("-")
	retval = x
	if y=='00:00:00Z':
		#add a day.
		retval = str(datetime.datetime(int(yr),int(mt),int(dt)) + datetime.timedelta(days=1))[0:10]
	return retval

def strip_accents(s):
   return ''.join(c for c in unicodedata.normalize('NFD', s)
                  if unicodedata.category(c) != 'Mn')

def insert_error(err_str,misc=""):
    conn = pymysql.connect(host='localhost',user='local',passwd='oeijifjwejfio',db=db_name)
    cur  = conn.cursor()
    cur.execute("insert into errors (timestamp,err_msg,misc) values(%s,%s,%s)",(time.time(),err_str,misc))
    conn.commit()
    conn.close()

def do_contra_raw():
    conn = pymysql.connect(host='localhost',user='local',passwd='oeijifjwejfio',db=db_name)
    cur  = conn.cursor()
    cur.execute("select * from raw_comps where site='contra'")
    rows = cur.fetchall()
    ids_done=[]
    for row in rows:
        ids_done.append(row[2])

    comps={}
    # soccer events pull
    for p in range(0,5):
        payload={"Sport":"football","Take":300,"Page":p}
        res=requests.post("https://s.linex11.com/api/front/events",data=payload)
        data = res.json()
        for d in data:
            #comps[d['TournamentId']]={"category":d['Category'],"name":d['Tournament'],"events":d['DateEvents']}
            compid = d['Category'] + "_" + d['Tournament']
            if compid not in ids_done:
                print("adding contra comp:",d['Category'] + " " + d['Tournament'])
                x=cur.execute("insert into raw_comps(comp_name,comp_id,site,timestamp) values(%s,%s,%s,%s)",(d['Category'] + " " + d['Tournament'],compid,"contra",time.time()))

        if len(data)<300:
            break
    conn.commit()
    conn.close()
    #return comps

def do_unibet_raw():
    ##unibet raw comp gatherer
    conn = pymysql.connect(host='localhost',user='local',passwd='oeijifjwejfio',db=db_name)
    cur  = conn.cursor()
    cur.execute("select * from raw_comps where site='unibet'")
    rows = cur.fetchall()
    ids_done=[]
    for row in rows:
        ids_done.append(row[2])

    url="https://www.unibet.com.au/sportsbook-feeds/views/filter/football/all/allGroups?includeParticipants=true&useCombined=true&ncid=1651723345"

    res= requests.get(url)
    comp_data = res.json()
    sections = comp_data['layout']['sections']
    groups = sections[1]['widgets'][0]['allGroups']['groups']

    unibet_leagues={}

    for group in groups:
        ggroups = group['groups']#

        for gg in ggroups:
            unibet_leagues[gg['id']]={"name":gg['name'],"nav_url":gg['navigationUrl'].split("/football/")[-1]}
            compid = gg['navigationUrl'].split("/football/")[-1]
            if compid not in ids_done:
                print("adding unibet comp:",gg['name'])
                x=cur.execute("insert into raw_comps(comp_name,comp_id,site,timestamp) values(%s,%s,%s,%s)",(gg['name'],compid,"unibet",time.time()))

    conn.commit()
    conn.close()


def do_toto_raw():

    conn = pymysql.connect(host='127.0.0.1',user='local',passwd='oeijifjwejfio',db=db_name)
    cur  = conn.cursor()
    cur.execute("select * from raw_comps where site='toto'")
    rows = cur.fetchall()
    ids_done=[]
    for row in rows:
        ids_done.append(int(row[2]))

    url="https://content.toto.nl/content-service/api/v1/q/drilldown-tree?drilldownNodeIds=11&eventState=OPEN_EVENT"
    res = requests.get(url)
    data = res.json()

    countries = data['data']['drilldownNodes'][0]['drilldownNodes'][0]['drilldownNodes']

    all_leagues={}
    for c in countries:
        for ddn in c['drilldownNodes']:
            if int(ddn['id']) not in ids_done:
                #all_leagues[ddn['name']]=ddn['id'] add to table
                print("adding toto comp:",ddn['name'],ddn['id'])
                x=cur.execute("insert into raw_comps(comp_name,comp_id,site,timestamp) values(%s,%s,%s,%s)",(ddn['name'],ddn['id'],"toto",time.time()))
    conn.commit()
    conn.close()

## here do a betfair check on comps..


## CONTRA

def pull_data_contra(compid,league):#country,tourny):
    cat,tourn = compid.split("_")
    payload={"Live":"true","Sport":"football",
             "Categories[]":cat.lower(),
             "DateTo":"",
             "Tournaments[]":tourn.lower()}

    comp_data=[]
    
    res=requests.post("https://s.linex11.com/api/front/events",data=payload)
    data = res.json()
    
    event_dates = data[0]['DateEvents']
    for ed in event_dates:
        events = ed['Events']
        for e in events:
            outcomes=[]
            extra_markets=[]
            home = e['Home']
            away = e['Away']
            timestamp = e['Date'] +"Z"
            markets= json.loads(e['MarketsString'].replace("\\",""))
            
            for m in markets:
                #print(m['Key'])
                if m['Key']=='1x2':
                    #h2h odds..
                    home_odds = m['Lines'][0]['Odds'][0]['Value']
                    draw_odds = m['Lines'][0]['Odds'][1]['Value']
                    away_odds = m['Lines'][0]['Odds'][2]['Value']
                    outcomes.append({"name":home,"price":home_odds})
                    outcomes.append({"name":"X","price":draw_odds})
                    outcomes.append({"name":away,"price":away_odds})
                    
                    
                elif m['Key']=='DNB':## << not in regular odds section, need details per match.. ugh
                    dnb_a_odds = m['Lines'][0]['Odds'][0]['Value']
                    dnb_b_odds = m['Lines'][0]['Odds'][1]['Value']
                    dnb_c_odds = m['Lines'][0]['Odds'][2]['Value']
                    extra_markets.append({"name":m['Lines'][0]['Odds'][0]['Outcome'],"price":dnb_a_odds})
                    extra_markets.append({"name":m['Lines'][0]['Odds'][1]['Outcome'],"price":dnb_b_odds})
                    extra_markets.append({"name":m['Lines'][0]['Odds'][2]['Outcome'],"price":dnb_c_odds})
                    #comp_data.append({"id":e['EventId'],"book":outcomes,"start_time":timestamp})
                elif m['Key']=='OU':
                    for line in m['Lines']:
                        if line['Specifier']=='2.5':
                            ou_a_odds = line['Odds'][0]['Value']
                            ou_b_odds = line['Odds'][1]['Value']
                            extra_markets.append({"name":line['Specifier'] + "_" + line['Odds'][0]['Outcome'],"price":ou_a_odds})
                            extra_markets.append({"name":line['Specifier'] + "_" + line['Odds'][1]['Outcome'],"price":ou_b_odds})
                            
                            

                else:
                    pass # here ill add in the other markets
            comp_data.append({"id":e['EventId'],"book":outcomes,"markets":extra_markets,"start_time":timestamp})#just once? has all outcomes in there..
            print(":::CONTRA--:::",{"id":e['EventId'],"book":outcomes,"markets":extra_markets,"start_time":timestamp})

    with open("raw_contra_data/" + league + "_" + str(compid) + ".json","wb") as f:
        f.write(res.content) 

            
    return comp_data

#toto sectionss
def pull_data_toto(compid,league):

    dates=[]
    for dta in range(0,14):
        dates.append(str(datetime.datetime.now()+datetime.timedelta(days=dta))[0:10])
    #print("toto_dates:",dates)
    #time.sleep(5)
    #this pulls the market for comp raw.. need to swap in ddN, and dates
    #url="https://content.toto.nl/content-service/api/v1/q/time-band-event-list?maxMarkets=10&marketSortsIncluded=--%2CHH%2CHL%2CMR%2CWH&marketGroupTypesIncluded=MONEYLINE%2CROLLING_SPREAD%2CROLLING_TOTAL%2CSTATIC_SPREAD%2CSTATIC_TOTAL&allowedEventSorts=MTCH&includeChildMarkets=true&prioritisePrimaryMarkets=true&includeCommentary=true&includeMedia=true&drilldownTagIds=" + compid + "&maxTotalItems=60&maxEventsPerCompetition=10&maxCompetitionsPerSportPerBand=3&maxEventsForNextToGo=5&startTimeOffsetForNextToGo=600&dates=2022-04-30T22%3A00%3A00Z%2C2022-05-01T22%3A00%3A00Z%2C2022-05-02T22%3A00%3A00Z%2C2022-05-3T22%3A00%3A00Z%2C2022-05-04T22%3A00%3A00Z%2C2022-05-05T22%3A00%3A00Z%2C2022-05-06T22%3A00%3A00Z%2C2022-05-07T22%3A00%3A00Z" 
    url="https://content.toto.nl/content-service/api/v1/q/time-band-event-list?maxMarkets=20&marketSortsIncluded=--%2CHH%2CHL%2CMR%2CWH&marketGroupTypesIncluded=MONEYLINE%2CROLLING_SPREAD%2CROLLING_TOTAL%2CSTATIC_SPREAD%2CSTATIC_TOTAL&allowedEventSorts=MTCH&includeChildMarkets=true&prioritisePrimaryMarkets=true&includeCommentary=true&includeMedia=true&drilldownTagIds=" + compid + "&maxTotalItems=100&maxEventsPerCompetition=20&maxCompetitionsPerSportPerBand=3&maxEventsForNextToGo=5&startTimeOffsetForNextToGo=600&dates=" + dates[0] + "T22%3A00%3A00Z%2C" + dates[1] + "T22%3A00%3A00Z%2C" + dates[2] + "T22%3A00%3A00Z%2C" + dates[3] + "T22%3A00%3A00Z%2C" + dates[4] + "T22%3A00%3A00Z%2C" + dates[5] + "T22%3A00%3A00Z%2C" + dates[6] + "T22%3A00%3A00Z%2C" + dates[7] + "T22%3A00%3A00Z%2C" + dates[8] + "T22%3A00%3A00Z%2C" + dates[9] + "T22%3A00%3A00Z%2C" + dates[10] + "T22%3A00%3A00Z%2C" + dates[11] + "T22%3A00%3A00Z%2C" + dates[12] + "T22%3A00%3A00Z%2C" + dates[13] + "T22%3A00%3A00Z"
    #params="maxMarkets=10&marketSortsIncluded=--%2CHH%2CHL%2CMR%2CWH&marketGroupTypesIncluded=MONEYLINE%2CROLLING_SPREAD%2CROLLING_TOTAL%2CSTATIC_SPREAD%2CSTATIC_TOTAL&allowedEventSorts=MTCH&includeChildMarkets=true&prioritisePrimaryMarkets=true&includeCommentary=true&includeMedia=true&drilldownTagIds=826&maxTotalItems=60&maxEventsPerCompetition=7&maxCompetitionsPerSportPerBand=3&maxEventsForNextToGo=5&startTimeOffsetForNextToGo=600&dates=2022-04-24T22%3A00%3A00Z%2C2022-04-25T22%3A00%3A00Z%2C2022-04-26T22%3A00%3A00Z"
    res = requests.get(url)
    data = res.json()
    events_base = data['data']['timeBandEvents']

    comp_data=[]

    for e in events_base:
        
        for f in e['events']:
            #print(f['id'])
            outcomes=[]
            extra_markets=[]
            markets = f['markets']
            home_outcome= markets[0]['outcomes'][0]['prices'][0]['decimal']
            home = markets[0]['outcomes'][0]['name']
            draw_outcome=markets[0]['outcomes'][1]['prices'][0]['decimal']
            draw =markets[0]['outcomes'][1]['name']
            away_outcome=markets[0]['outcomes'][2]['prices'][0]['decimal']
            away = markets[0]['outcomes'][2]['name']
            outcomes.append({"name":home,"price":home_outcome})
            outcomes.append({"name":draw,"price":draw_outcome})
            outcomes.append({"name":away,"price":away_outcome})
            #here check for other markets.. totals dnb
            for market in markets:
                if market['name']=="Total Goals Over/Under 2.5":
                    odds_a_name = market['outcomes'][0]['prices'][0]['handicapLow'] + "_" + market['outcomes'][0]['name']
                    odds_b_name = market['outcomes'][1]['prices'][0]['handicapLow'] + "_" + market['outcomes'][1]['name']
                    odds_a = market['outcomes'][0]['prices'][0]['decimal']
                    odds_b = market['outcomes'][1]['prices'][0]['decimal']
                    extra_markets.append({"name":odds_a_name,"price":odds_a})
                    extra_markets.append({"name":odds_b_name,"price":odds_b})


            #print(home + " v " + away,home_outcome,draw_outcome,away_outcome,"<>",draw)
            comp_data.append({"id":f['id'],"book":outcomes,"markets":extra_markets,"start_time":f['startTime']})

            #print("~~~~~~~~~~~~" + f['startTime']);


    with open("raw_toto_data/" + league + "_" + str(compid) + ".json","wb") as f:
        f.write(res.content) 
    
    return comp_data


def pull_data_unibet(compid,league):

    
    comp_data=[]
    #compid=england/premier_league
    #premier league
    url="https://o1-api.aws.kambicdn.com/offering/v2018/ubau/listView/football/" + compid + ".json?lang=en_AU&market=UK&client_id=2&channel_id=1&ncid=1651722023500&useCombined=true"
    #url="https://o1-api.aws.kambicdn.com/offering/v2018/ubau/listView/football/bulgaria/pfl_2.json?lang=en_AU&market=UK&client_id=2&channel_id=1&ncid=1651722023500&useCombined=true"

    res = requests.get(url)
    data=res.json()
    events=data['events']
    #offers=data['betoffers']
    for e in range(0,len(events)):
        outcomes=[]
        extra_markets=[]
        eid = events[e]['event']['id']
        timestamp = events[e]['event']['start']
        offers = events[e]['betOffers']
        eventname= events[e]['event']['name']
        home,away = eventname.split(" - ")
        #here i need to find the correct offer
        for f in range(0,len(offers)):
            if offers[f]['eventId']==events[e]['event']['id'] and offers[f]['betOfferType']['id']==2:
                home_odds= offers[f]['outcomes'][0]['odds']
                draw_odds= offers[f]['outcomes'][1]['odds']
                away_odds= offers[f]['outcomes'][2]['odds']   
                outcomes.append({"name":home,"price":home_odds/1000})
                outcomes.append({"name":"X","price":draw_odds/1000})
                outcomes.append({"name":away,"price":away_odds/1000})
            elif offers[f]['eventId']==events[e]['event']['id'] and offers[f]['betOfferType']['id']==6:
                ou_25_odds_a= offers[f]['outcomes'][0]['odds']/1000
                ou_25_odds_b= offers[f]['outcomes'][1]['odds']/1000
               
                extra_markets.append({"name":str(round(offers[f]['outcomes'][0]['line']/1000,1)) + "_" + offers[1]['outcomes'][0]['label'],"price":ou_25_odds_a})
                extra_markets.append({"name":str(round(offers[f]['outcomes'][1]['line']/1000,1)) + "_" + offers[1]['outcomes'][1]['label'],"price":ou_25_odds_b})

        #print ("unibet:",{"id":eid,"book":outcomes,"start_time":timestamp})
        comp_data.append({"id":eid,"book":outcomes,"markets":extra_markets,"start_time":timestamp})
        print("UNIBET MARKETS STUFF::::",{"id":eid,"book":outcomes,"markets":extra_markets,"start_time":timestamp})


    #with open("raw_unibet_data/" + league + "_" + str(compid).replace("/","_") + ".json","wb") as f:
    #    f.write(res.content) 
    
    return comp_data


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

def get_market_books(books):
	price_filter=betfairlightweight.filters.price_projection(price_data=['EX_BEST_OFFERS','EX_TRADED'])
	book =trading.betting.list_market_book(market_ids=books,price_projection=price_filter)
	return book

#betfair section
def pull_betfair_data(compid,league):

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

        comp_data[event_id]['h2h_id']=get_event_matchodds(comp_market,event_id)
        try:
            books = get_market_books([comp_data[event_id]['h2h_id']])
            #print("runnercount:",len(books[0].runners))
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
                
                comp_data[event_id]['odds'].append({"last_back_price":last_back_price,"last_back_vol":last_back_vol,"lowest_back_price":0,"lowest_back_vol":0,"lay_price":lay_price,"lay_vol":runner.ex.available_to_lay[0].size})
               

                
        except Exception as msg:
            insert_error(str(msg),"error in getting betfair book:" + compid + " -- " + event.event.name + " (" + league + ")")
            print(str(msg))
            

####### here do the other markets,, will clean this up later.
        comp_data[event_id]['ou25_id']=get_event_ou25(comp_market,event_id)
        try:
            books = get_market_books([comp_data[event_id]['ou25_id']])
            #print("runnercount:",len(books[0].runners))
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
                
                comp_data[event_id]['markets'].append({"last_back_price_"+which_market:last_back_price_ou25,"last_back_vol_"+which_market:last_back_vol_ou25,"lowest_back_price_"+which_market:0,"lowest_back_vol_"+which_market:0,"lay_price_"+which_market:lay_price_ou25,"lay_vol_"+which_market:runner.ex.available_to_lay[0].size})
               

                
        except Exception as msg:
            insert_error(str(msg),"error in getting betfair book:" + compid + " -- " + event.event.name + " (" + league + ")")
            print(str(msg))
    ## first runner is UNDER, then OVER,, if they swap around, this is where the problem is.. can't locate which odds it refers to.
    ## need to spec which 

    #with open("raw_betfair_data/" + league + "_" + str(compid) + ".json","wb") as f:
    #    f.write(res.content)
    return comp_data

   

##ok,, from here, its matched, and has its fuzzy flag.. now just insert to db
## after consolidating ofc..
def get_team_list_toto():
    #print("<building team list>")
    conn = pymysql.connect(host='localhost',user='local',passwd='oeijifjwejfio',db=db_name)
    cur  = conn.cursor()
    cur.execute("select back_name,betfair_name from toto_teams")
    rows = cur.fetchall()
    teams={}
    for row in rows:
        teams[row[0].upper()]=row[1]
        teams[strip_accents(row[0]).upper()]=row[1]
    conn.close()
    #print("<team list built>")
    return teams

def get_team_list_unibet():
    #print("<building team list>")
    conn = pymysql.connect(host='localhost',user='local',passwd='oeijifjwejfio',db=db_name)
    cur  = conn.cursor()
    cur.execute("select unibet_name,betfair_name from unibet_teams")
    rows = cur.fetchall()
    teams={}
    for row in rows:
        teams[row[0].upper()]=row[1]
        teams[strip_accents(row[0]).upper()]=row[1]
    conn.close()
    #print("<team list built>")
    return teams

def get_team_list_contra():
    #print("<building team list>")
    conn = pymysql.connect(host='localhost',user='local',passwd='oeijifjwejfio',db=db_name)
    cur  = conn.cursor()
    cur.execute("select contra_name,betfair_name from contra_teams")
    rows = cur.fetchall()
    teams={}
    for row in rows:
        teams[row[0].upper()]=row[1]
        teams[strip_accents(row[0]).upper()]=row[1]
    conn.close()
    #print("<team list built>")
    return teams


def insert_to_database_toto(t,b,league):
    conn = pymysql.connect(host='localhost',user='local',passwd='oeijifjwejfio',db=db_name)
    cur  = conn.cursor()
    toto_teamnames = t['matchup_raw']
    t1fuzzy,t2fuzzy=0,0
    print("TOTO YO>>>>>>>>>>",t)
    #toto section
    for runner in t['book']:
        if runner[0]==t['matchup'][0]:
            toto_1_odds=runner[1]
            if runner[2]==1:
                t1fuzzy=1
        elif runner[0]==t['matchup'][1]:
            toto_2_odds=runner[1]
            if runner[2]==1:
                t2fuzzy=1
        else:
            toto_x_odds=runner[1]
    #betfair section
    
    bf_teamnames = b['matchup_raw']
    for runner in b['back_book']:
        if runner[0]==b['matchup'][0]:
            bf_1_last_back_odds=runner[1]
            bf_1_last_back_vol=runner[2]
            bf_1_lowest_back_odds=runner[3]
            bf_1_lowest_back_vol=runner[4]

        elif runner[0]==b['matchup'][1]:
            bf_2_last_back_odds=runner[1]
            bf_2_last_back_vol = runner[2]
            bf_2_lowest_back_odds=runner[3]
            bf_2_lowest_back_vol=runner[4]

        else:
            bf_x_last_back_odds=runner[1]
            bf_x_last_back_vol=runner[2]
            bf_x_lowest_back_odds=runner[3]
            bf_x_lowest_back_vol=runner[4]

    for runner in b['lay_book']:
        if runner[0]==b['matchup'][0]:
            bf_1_lay_odds=runner[1]
            bf_1_lay_vol=runner[2]
        elif runner[0]==b['matchup'][1]:
            bf_2_lay_odds=runner[1]
            bf_2_lay_vol = runner[2]
        else:
            bf_x_lay_odds=runner[1]
            bf_x_lay_vol=runner[2]

    ##here flip back names and odds if flipped..
    if b['flipped']:
        temp = toto_1_odds
        toto_1_odds = toto_2_odds
        toto_2_odds = temp
        temp = toto_teamnames[0]
        toto_teamnames[0] = toto_teamnames[1]
        toto_teamnames[1] = temp
        

        temp = bf_1_last_back_odds
        bf_1_last_back_odds = bf_2_last_back_odds
        bf_2_last_back_odds = temp

        temp = bf_1_last_back_vol
        bf_1_last_back_vol = bf_2_last_back_vol
        bf_2_last_back_vol = temp


        temp = bf_1_lowest_back_odds
        bf_1_lowest_back_odds = bf_2_lowest_back_odds
        bf_2_lowest_back_odds = temp

        temp = bf_1_lowest_back_vol
        bf_1_lowest_back_vol = bf_2_lowest_back_vol
        bf_2_lowest_back_vol = temp

        temp = bf_1_lay_odds
        bf_1_lay_odds = bf_2_lay_odds
        bf_2_lay_odds = temp

        temp = bf_1_lay_vol
        bf_1_lay_vol = bf_2_lay_vol
        bf_2_lay_vol = temp

        temp = bf_teamnames[0]
        bf_teamnames[0] = bf_teamnames[1]
        bf_teamnames[1] = temp

        temp = t1fuzzy
        t1fuzzy = t2fuzzy
        t2fuzzy = temp
    #here add extra markets..
    toto_over_2p5=0
    toto_under_2p5=0
    for outcome in t['markets']:
        if outcome['name']=='2.5_Over':
            toto_over_2p5 = outcome['price']
        elif outcome['name']=='2.5_Under':
            toto_under_2p5 = outcome['price']
    

    #insert section
    print("TOTO###",b)
    odds_json={"toto_1_odds":toto_1_odds,"toto_x_odds":toto_x_odds,"toto_2_odds":toto_2_odds,"toto_under_2.5":toto_under_2p5,"toto_over_2.5":toto_over_2p5,
               "bf_1_odds":{"last_back_price":bf_1_last_back_odds,"last_back_vol":bf_1_last_back_vol,"lowest_back_price":bf_1_lowest_back_odds,"lowest_back_vol":bf_1_lowest_back_vol,"lay_price":bf_1_lay_odds,"lay_vol":bf_1_lay_vol},"bf_x_odds":{"last_back_price":bf_x_last_back_odds,"last_back_vol":bf_x_last_back_vol,"lowest_back_price":bf_x_lowest_back_odds,"lowest_back_vol":bf_x_lowest_back_vol,"lay_price":bf_x_lay_odds,"lay_vol":bf_x_lay_vol},"bf_2_odds":{"last_back_price":bf_2_last_back_odds,"last_back_vol":bf_2_last_back_vol,"lowest_back_price":bf_2_lowest_back_odds,"lowest_back_vol":bf_2_lowest_back_vol,"lay_price":bf_2_lay_odds,"lay_vol":bf_2_lay_vol},"bf_Under_2.5":{"last_back_price":b['back_25'][0][1],"last_back_vol":b['back_25'][0][2],"lowest_back_price":b['back_25'][0][3],"lowest_back_vol":b['back_25'][0][4],"lay_price":b['lay_25'][0][1],"lay_vol":b['lay_25'][0][1]},"bf_Over_2.5":{"last_back_price":b['back_25'][1][1],"last_back_vol":b['back_25'][1][2],"lowest_back_price":b['back_25'][1][3],"lowest_back_vol":b['back_25'][1][4],"lay_price":b['lay_25'][1][1],"lay_vol":b['lay_25'][1][1]}}
    print(">>>odds_json TOTO:",odds_json)
    #here check for existing..
    cur.execute("select * from toto_matches where toto_event_id=%s and betfair_event_id=%s",(t['event_id'],b['event_id']))
    rows = cur.fetchall()
    if len(rows)>0:
        #print("found event,, updating",t['event_id'],b['event_id'])
        cur.execute("update toto_matches set timestamp=%s,odds_data=%s,t1_fuzzy=%s,t2_fuzzy=%s where toto_event_id=%s and betfair_event_id=%s",
                (b['timestamp'],json.dumps(odds_json),t1fuzzy,t2fuzzy,t['event_id'],b['event_id']))
        print("inserted:",t['event_id'],b['event_id'])
    else:
        #print("NO event,, inserting",t['event_id'],b['event_id'])
        #here i do an extra ratio check on toto teams, because somehow are flipping sometimes..
        if fuzz.ratio(toto_teamnames[0],bf_teamnames[0])>fuzz.ratio(toto_teamnames[0],bf_teamnames[1]):
            pass#should be right 
        else:
            #print("flipping:",toto_teamnames[0],toto_teamnames[1])
            temp = toto_teamnames[0]
            toto_teamnames[0] = toto_teamnames[1]
            toto_teamnames[1] = temp

        cur.execute("insert into toto_matches (timestamp,toto_event_id,betfair_event_id,team_1_toto,team_2_toto,team_1_betfair,team_2_betfair,odds_data,t1_fuzzy,t2_fuzzy,ignored,league) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (b['timestamp'],t['event_id'],b['event_id'],toto_teamnames[0],toto_teamnames[1],bf_teamnames[0],bf_teamnames[1],json.dumps(odds_json),t1fuzzy,t2fuzzy,0,league))
    conn.commit()
    conn.close()
    

def insert_to_database_unibet(t,b,league):
    conn = pymysql.connect(host='localhost',user='local',passwd='oeijifjwejfio',db=db_name)
    cur  = conn.cursor()
    unibet_teamnames = t['matchup_raw']
    t1fuzzy,t2fuzzy=0,0
    
    #toto section
    for runner in t['book']:
        if runner[0]==t['matchup'][0]:
            toto_1_odds=runner[1]
            if runner[2]==1:
                t1fuzzy=1
        elif runner[0]==t['matchup'][1]:
            toto_2_odds=runner[1]
            if runner[2]==1:
                t2fuzzy=1
        else:
            toto_x_odds=runner[1]
    #betfair section
    
    bf_teamnames = b['matchup_raw']
    for runner in b['back_book']:
        if runner[0]==b['matchup'][0]:
            bf_1_last_back_odds=runner[1]
            bf_1_last_back_vol=runner[2]
            bf_1_lowest_back_odds=runner[3]
            bf_1_lowest_back_vol=runner[4]

        elif runner[0]==b['matchup'][1]:
            bf_2_last_back_odds=runner[1]
            bf_2_last_back_vol = runner[2]
            bf_2_lowest_back_odds=runner[3]
            bf_2_lowest_back_vol=runner[4]

        else:
            bf_x_last_back_odds=runner[1]
            bf_x_last_back_vol=runner[2]
            bf_x_lowest_back_odds=runner[3]
            bf_x_lowest_back_vol=runner[4]

    for runner in b['lay_book']:
        if runner[0]==b['matchup'][0]:
            bf_1_lay_odds=runner[1]
            bf_1_lay_vol=runner[2]
        elif runner[0]==b['matchup'][1]:
            bf_2_lay_odds=runner[1]
            bf_2_lay_vol = runner[2]
        else:
            bf_x_lay_odds=runner[1]
            bf_x_lay_vol=runner[2]

    ##here flip back names and odds if flipped..
    if b['flipped']:
        temp = toto_1_odds
        toto_1_odds = toto_2_odds
        toto_2_odds = temp
        temp = unibet_teamnames[0]
        unibet_teamnames[0] = unibet_teamnames[1]
        unibet_teamnames[1] = temp
        

        temp = bf_1_last_back_odds
        bf_1_last_back_odds = bf_2_last_back_odds
        bf_2_last_back_odds = temp

        temp = bf_1_last_back_vol
        bf_1_last_back_vol = bf_2_last_back_vol
        bf_2_last_back_vol = temp


        temp = bf_1_lowest_back_odds
        bf_1_lowest_back_odds = bf_2_lowest_back_odds
        bf_2_lowest_back_odds = temp

        temp = bf_1_lowest_back_vol
        bf_1_lowest_back_vol = bf_2_lowest_back_vol
        bf_2_lowest_back_vol = temp


        temp = bf_1_lay_odds
        bf_1_lay_odds = bf_2_lay_odds
        bf_2_lay_odds = temp

        temp = bf_1_lay_vol
        bf_1_lay_vol = bf_2_lay_vol
        bf_2_lay_vol = temp
        temp = bf_teamnames[0]
        bf_teamnames[0] = bf_teamnames[1]
        bf_teamnames[1] = temp

        temp = t1fuzzy
        t1fuzzy = t2fuzzy
        t2fuzzy = temp
       
    #add extra odds stuff..
    unibet_over_2p5=0
    unibet_under_2p5=0
    for outcome in t['markets']:
        if outcome['name']=='2.5_Over':
            unibet_over_2p5 = outcome['price']
        elif outcome['name']=='2.5_Under':
            unibet_under_2p5 = outcome['price']
    
    #insert section
    odds_json={"unibet_1_odds":toto_1_odds,"unibet_x_odds":toto_x_odds,"unibet_2_odds":toto_2_odds,"unibet_over_2.5":unibet_over_2p5,"unibet_under_2.5":unibet_under_2p5,
               "bf_1_odds":{"last_back_price":bf_1_last_back_odds,"last_back_vol":bf_1_last_back_vol,"lowest_back_price":bf_1_lowest_back_odds,"lowest_back_vol":bf_1_lowest_back_vol,"lay_price":bf_1_lay_odds,"lay_vol":bf_1_lay_vol},"bf_x_odds":{"last_back_price":bf_x_last_back_odds,"last_back_vol":bf_x_last_back_vol,"lowest_back_price":bf_x_lowest_back_odds,"lowest_back_vol":bf_x_lowest_back_vol,"lay_price":bf_x_lay_odds,"lay_vol":bf_x_lay_vol},"bf_2_odds":{"last_back_price":bf_2_last_back_odds,"last_back_vol":bf_2_last_back_vol,"lowest_back_price":bf_2_lowest_back_odds,"lowest_back_vol":bf_2_lowest_back_vol,"lay_price":bf_2_lay_odds,"lay_vol":bf_2_lay_vol},"bf_Under_2.5":{"last_back_price":b['back_25'][0][1],"last_back_vol":b['back_25'][0][2],"lowest_back_price":b['back_25'][0][3],"lowest_back_vol":b['back_25'][0][4],"lay_price":b['lay_25'][0][1],"lay_vol":b['lay_25'][0][1]},"bf_Over_2.5":{"last_back_price":b['back_25'][1][1],"last_back_vol":b['back_25'][1][2],"lowest_back_price":b['back_25'][1][3],"lowest_back_vol":b['back_25'][1][4],"lay_price":b['lay_25'][1][1],"lay_vol":b['lay_25'][1][1]}}
    #here check for existing..
    cur.execute("select * from unibet_matches where unibet_event_id=%s and betfair_event_id=%s",(t['event_id'],b['event_id']))
    rows = cur.fetchall()
    if len(rows)>0:
        #print("found event,, updating",t['event_id'],b['event_id'])
        cur.execute("update unibet_matches set timestamp=%s,unibet_data=%s,t1_unibet_fuzzy=%s,t2_unibet_fuzzy=%s where unibet_event_id=%s and betfair_event_id=%s",
                (b['timestamp'],json.dumps(odds_json),t1fuzzy,t2fuzzy,t['event_id'],b['event_id']))
        #print("inserted:",t['event_id'],b['event_id'])
    else:
        #print("NO event,, inserting",t['event_id'],b['event_id'])
        ##here i do an extra ratio check on toto teams, because somehow are flipping sometimes..
        if fuzz.ratio(unibet_teamnames[0],bf_teamnames[0])>fuzz.ratio(unibet_teamnames[0],bf_teamnames[1]):
            pass#should be right 
        else:
            #print("flipping:",unibet_teamnames[0],unibet_teamnames[1])
            temp = unibet_teamnames[0]
            unibet_teamnames[0] = unibet_teamnames[1]
            unibet_teamnames[1] = temp

        cur.execute("insert into unibet_matches (timestamp,unibet_event_id,betfair_event_id,team_1_unibet,team_2_unibet,team_1_betfair,team_2_betfair,unibet_data,t1_unibet_fuzzy,t2_unibet_fuzzy,ignored,league) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (b['timestamp'],t['event_id'],b['event_id'],unibet_teamnames[0],unibet_teamnames[1],bf_teamnames[0],bf_teamnames[1],json.dumps(odds_json),t1fuzzy,t2fuzzy,0,league))
    conn.commit()
    conn.close()

def insert_to_database_contra(t,b,league):
    conn = pymysql.connect(host='localhost',user='local',passwd='oeijifjwejfio',db=db_name)
    cur  = conn.cursor()
    contra_teamnames = t['matchup_raw']
    #print("CONTRA INSERT AREA:::",t,b)
    t1fuzzy,t2fuzzy=0,0
    
    #toto section
    for runner in t['book']:
        if runner[0]==t['matchup'][0]:
            toto_1_odds=runner[1]
            if runner[2]==1:
                t1fuzzy=1
        elif runner[0]==t['matchup'][1]:
            toto_2_odds=runner[1]
            if runner[2]==1:
                t2fuzzy=1
        else:
            toto_x_odds=runner[1]
    #betfair section
    
    bf_teamnames = b['matchup_raw']
    for runner in b['back_book']:
        if runner[0]==b['matchup'][0]:
            bf_1_last_back_odds=runner[1]
            bf_1_last_back_vol=runner[2]
            bf_1_lowest_back_odds=runner[3]
            bf_1_lowest_back_vol=runner[4]

        elif runner[0]==b['matchup'][1]:
            bf_2_last_back_odds=runner[1]
            bf_2_last_back_vol = runner[2]
            bf_2_lowest_back_odds=runner[3]
            bf_2_lowest_back_vol=runner[4]

        else:
            bf_x_last_back_odds=runner[1]
            bf_x_last_back_vol=runner[2]
            bf_x_lowest_back_odds=runner[3]
            bf_x_lowest_back_vol=runner[4]

    for runner in b['lay_book']:
        if runner[0]==b['matchup'][0]:
            bf_1_lay_odds=runner[1]
            bf_1_lay_vol=runner[2]
        elif runner[0]==b['matchup'][1]:
            bf_2_lay_odds=runner[1]
            bf_2_lay_vol = runner[2]
        else:
            bf_x_lay_odds=runner[1]
            bf_x_lay_vol=runner[2]

    ##here flip back names and odds if flipped..
    if b['flipped']:
        temp = toto_1_odds
        toto_1_odds = toto_2_odds
        toto_2_odds = temp
        temp = contra_teamnames[0]
        contra_teamnames[0] = contra_teamnames[1]
        contra_teamnames[1] = temp
        

        temp = bf_1_last_back_odds
        bf_1_last_back_odds = bf_2_last_back_odds
        bf_2_last_back_odds = temp

        temp = bf_1_last_back_vol
        bf_1_last_back_vol = bf_2_last_back_vol
        bf_2_last_back_vol = temp


        temp = bf_1_lowest_back_odds
        bf_1_lowest_back_odds = bf_2_lowest_back_odds
        bf_2_lowest_back_odds = temp

        temp = bf_1_lowest_back_vol
        bf_1_lowest_back_vol = bf_2_lowest_back_vol
        bf_2_lowest_back_vol = temp


        temp = bf_1_lay_odds
        bf_1_lay_odds = bf_2_lay_odds
        bf_2_lay_odds = temp

        temp = bf_1_lay_vol
        bf_1_lay_vol = bf_2_lay_vol
        bf_2_lay_vol = temp
        temp = bf_teamnames[0]
        bf_teamnames[0] = bf_teamnames[1]
        bf_teamnames[1] = temp

        temp = t1fuzzy
        t1fuzzy = t2fuzzy
        t2fuzzy = temp
        
    #here define extra market data
    contra_over_2p5=0
    contra_under_2p5=0
    for outcome in t['markets']:
        if outcome['name']=='2.5_Over':
            contra_over_2p5 = outcome['price']
        elif outcome['name']=='2.5_Under':
            contra_under_2p5 = outcome['price']
    print("###",b)
    #insert section  here need to add the extra market odds..
    odds_json={"contra_1_odds":toto_1_odds,"contra_x_odds":toto_x_odds,"contra_2_odds":toto_2_odds,"contra_over_2.5":contra_over_2p5,"contra_under_2.5":contra_under_2p5,
               "bf_1_odds":{"last_back_price":bf_1_last_back_odds,"last_back_vol":bf_1_last_back_vol,"lowest_back_price":bf_1_lowest_back_odds,"lowest_back_vol":bf_1_lowest_back_vol,"lay_price":bf_1_lay_odds,"lay_vol":bf_1_lay_vol},"bf_x_odds":{"last_back_price":bf_x_last_back_odds,"last_back_vol":bf_x_last_back_vol,"lowest_back_price":bf_x_lowest_back_odds,"lowest_back_vol":bf_x_lowest_back_vol,"lay_price":bf_x_lay_odds,"lay_vol":bf_x_lay_vol},"bf_2_odds":{"last_back_price":bf_2_last_back_odds,"last_back_vol":bf_2_last_back_vol,"lowest_back_price":bf_2_lowest_back_odds,"lowest_back_vol":bf_2_lowest_back_vol,"lay_price":bf_2_lay_odds,"lay_vol":bf_2_lay_vol},"bf_Under_2.5":{"last_back_price":b['back_25'][0][1],"last_back_vol":b['back_25'][0][2],"lowest_back_price":b['back_25'][0][3],"lowest_back_vol":b['back_25'][0][4],"lay_price":b['lay_25'][0][1],"lay_vol":b['lay_25'][0][1]},"bf_Over_2.5":{"last_back_price":b['back_25'][1][1],"last_back_vol":b['back_25'][1][2],"lowest_back_price":b['back_25'][1][3],"lowest_back_vol":b['back_25'][1][4],"lay_price":b['lay_25'][1][1],"lay_vol":b['lay_25'][1][1]}}
    print("<><><>",odds_json)



    #here check for existing..
    cur.execute("select * from contra_matches where contra_event_id=%s and betfair_event_id=%s",(t['event_id'],b['event_id']))
    rows = cur.fetchall()
    if len(rows)>0:
        #print("found CONTRA event,, updating",t['event_id'],b['event_id'])
        cur.execute("update contra_matches set timestamp=%s,contra_data=%s,t1_contra_fuzzy=%s,t2_contra_fuzzy=%s where contra_event_id=%s and betfair_event_id=%s",
                (b['timestamp'],json.dumps(odds_json),t1fuzzy,t2fuzzy,t['event_id'],b['event_id']))
        #print("updated:",t['event_id'],b['event_id'])
    else:
        #print("NO event,, inserting",t['event_id'],b['event_id'])
        #here i do an extra ratio check on toto teams, because somehow are flipping sometimes..
        if fuzz.ratio(contra_teamnames[0],bf_teamnames[0])>fuzz.ratio(contra_teamnames[0],bf_teamnames[1]):
            pass#should be right 
        else:
            #print("flipping:",contra_teamnames[0],contra_teamnames[1])
            temp = contra_teamnames[0]
            contra_teamnames[0] = contra_teamnames[1]
            contra_teamnames[1] = temp

        cur.execute("insert into contra_matches (timestamp,contra_event_id,betfair_event_id,team_1_contra,team_2_contra,team_1_betfair,team_2_betfair,contra_data,t1_contra_fuzzy,t2_contra_fuzzy,ignored,league) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (b['timestamp'],t['event_id'],b['event_id'],contra_teamnames[0],contra_teamnames[1],bf_teamnames[0],bf_teamnames[1],json.dumps(odds_json),t1fuzzy,t2fuzzy,0,league))
    conn.commit()
    conn.close()



def do_insert_toto(toto_data,betfair_data,league):
    print("doing fuzzy and insert TOTO")

    
    #pull all bf matches, and subsequent team names.. for fuzzy match
    
    bf_data = betfair_data
    #convert into list of lists
    print("toto:",len(toto_data),"bf:",len(betfair_data),league)
    bf_matches=[]
    for b in bf_data:
        try:
            if len(bf_data[b]['odds'])>0:
                back_25=[]
                lay_25=[]

                back_matchlist=[]
                lay_matchlist=[]
                teama,teamb  = bf_data[b]['name'].split(" v ")
                #print("bfmatches:",teama,teamb)
                #print(bf_data[b]['odds'])
                #print("---")
                matchteams=[teama,teamb]
                matchteams.sort()
                if matchteams!=[teama,teamb]:
                        flipped=1
                else:
                        flipped=0
                        
                back_matchlist.append([teama,bf_data[b]['odds'][0]['last_back_price'],bf_data[b]['odds'][0]['last_back_vol'],bf_data[b]['odds'][0]['lowest_back_price'],bf_data[b]['odds'][0]['lowest_back_vol']])
                back_matchlist.append([teamb,bf_data[b]['odds'][1]['last_back_price'],bf_data[b]['odds'][1]['last_back_vol'],bf_data[b]['odds'][1]['lowest_back_price'],bf_data[b]['odds'][1]['lowest_back_vol']])
                back_matchlist.append(["X",bf_data[b]['odds'][2]['last_back_price'],bf_data[b]['odds'][2]['last_back_vol'],bf_data[b]['odds'][2]['lowest_back_price'],bf_data[b]['odds'][2]['lowest_back_vol']])
                lay_matchlist.append([teama,bf_data[b]['odds'][0]['lay_price'],bf_data[b]['odds'][0]['lay_vol']])
                lay_matchlist.append([teamb,bf_data[b]['odds'][1]['lay_price'],bf_data[b]['odds'][1]['lay_vol']])
                lay_matchlist.append(["X",bf_data[b]['odds'][2]['lay_price'],bf_data[b]['odds'][2]['lay_vol']])

 #add extra markets here
                back_25.append(["Under_2.5",bf_data[b]['markets'][0]['last_back_price_Under_2.5'],bf_data[b]['markets'][0]['last_back_vol_Under_2.5'],bf_data[b]['markets'][0]['lowest_back_price_Under_2.5'],bf_data[b]['markets'][0]['lowest_back_vol_Under_2.5']])
                back_25.append(["Over_2.5",bf_data[b]['markets'][1]['last_back_price_Over_2.5'],bf_data[b]['markets'][1]['last_back_vol_Over_2.5'],bf_data[b]['markets'][1]['lowest_back_price_Over_2.5'],bf_data[b]['markets'][1]['lowest_back_vol_Over_2.5']])

                lay_25.append(["Under_2.5",bf_data[b]['markets'][0]['lay_price_Under_2.5'],bf_data[b]['markets'][0]['lay_vol_Under_2.5']])
                lay_25.append(["Over_2.5",bf_data[b]['markets'][1]['lay_price_Over_2.5'],bf_data[b]['markets'][1]['lay_vol_Over_2.5']])
                bf_matches.append({"matchup":matchteams,"flipped":flipped,"matchup_raw":matchteams,"lay_book":lay_matchlist,"back_book":back_matchlist,"back_25":back_25,"lay_25":lay_25,'event_id':b,"timestamp":bf_data[b]['timestamp']})
#print("BF>>",{"matchup":matchteams,"flipped":flipped,"matchup_raw":matchteams,"lay_book":lay_matchlist,"back_book":back_matchlist,'event_id':b,"timestamp":bf_data[b]['timestamp']})
        except Exception as msg:
            print("err on betfair match check:",teama,teamb,str(msg))
            try:
                insert_error(str(msg),"err on betfair (toto) match check:",teama,teamb,str(msg))
            except Exception as msg:
                print(">>> insert err error..",str(msg))
            

    #for b in bf_matches:
    #    print(b)

    #print("------------------------>")
    
    tt_data = toto_data#pickle.load(f)

    #here pull from db, and whittle down to unique,, then create the list..
    toto_teams = get_team_list_toto()
    #unibet_teams = get_team_list_unibet()

    print("there are:",len(toto_teams),"teams")   

    bf_teams=[]
    for b in bf_data:
        for name in bf_data[b]['name'].split(" v "):
            bf_teams.append(name)
    bf_teams=list(set(bf_teams))

    tt_matches=[]

    for t in  tt_data:
        match_data=[]
        matchteams=[]
        matchteams_raw=[]
        for runner in t['book']:
            if runner['name']!='Draw':
                matchteams_raw.append(runner['name'])
                #try to match it,, if not,, fuzzy?
                if runner['name'].upper() in toto_teams and toto_teams[runner['name'].upper()]!="":
                    match_data.append([toto_teams[runner['name'].upper()],runner['price'],0])
                    matchteams.append(toto_teams[runner['name'].upper()])
                else:
                    #fuzzy..
                    maxfuzz=0
                    likely_team=""
                    for b in bf_teams:
                        r=fuzz.ratio(b,runner['name'])
                        if r>maxfuzz:
                            maxfuzz=r
                            likely_team=b
                    match_data.append([likely_team,runner['price'],1])
                    matchteams.append(likely_team)
            else:
                match_data.append(["X",runner['price'],0])
        matchteams.sort()
        matchteams_raw.sort()
        tt_matches.append({"matchup":matchteams,"matchup_raw":matchteams_raw,"book":match_data,"markets":t['markets'],'event_id':t['id'],'start_time':t['start_time']})

    #for t in tt_matches:
    #    print("toto",t)
    found=0
    for t in tt_matches:
        found=0
        for b in bf_matches:
            #print("date match:",t['start_time'][0:10],str(datetime.datetime.utcfromtimestamp(int(b['timestamp'])).strftime('%Y-%m-%d %H:%M:%S'))[0:10])
            #print("<><><>",t['matchup'],b['matchup'],t['start_time'][0:10],int(b['timestamp']),str(datetime.datetime.utcfromtimestamp(int(b['timestamp'])).strftime('%Y-%m-%d %H:%M:%S'))[0:10])
            if t['matchup']==b['matchup'] and convert_midnight(t['start_time'])==str(datetime.datetime.utcfromtimestamp(int(b['timestamp'])).strftime('%Y-%m-%d %H:%M:%S'))[0:10]:
                #print("MATCHED>>>>",t['matchup'],b['matchup'],t['start_time'][0:10],int(b['timestamp']),str(datetime.datetime.utcfromtimestamp(int(b['timestamp'])).strftime('%Y-%m-%d %H:%M:%S'))[0:10])
                insert_to_database_toto(t,b,league)
                found=1
                break
            else:
                pass#print("<<<<UNMATCHED",t['matchup'],b['matchup'],t['start_time'][0:10],int(b['timestamp']),str(datetime.datetime.utcfromtimestamp(int(b['timestamp'])).strftime('%Y-%m-%d %H:%M:%S'))[0:10])
    if not found:
        #print("NOT MATCHED:",t['matchup'],b['matchup'])
        conn = pymysql.connect(host='localhost',user='local',passwd='oeijifjwejfio',db=db_name)
        cur  = conn.cursor()
        #print("select * from unmatched where start_time=%s and team1=%s and team2=%s",(t['start_time'],t['matchup_raw'][0],t['matchup_raw'][1]))

        cur.execute("select * from toto_unmatched where start_time=%s and team1=%s and team2=%s",(t['start_time'],t['matchup_raw'][0],t['matchup_raw'][1]))
        rows =cur.fetchall()
        if len(rows)==0:
            cur.execute("insert into toto_unmatched (team1,team2,league,start_time,timestamp) values(%s,%s,%s,%s,%s)",(t['matchup_raw'][0],t['matchup_raw'][1],league,t['start_time'],time.time()))
            conn.commit()
        conn.close()        


def do_insert_unibet(unibet_data,betfair_data,league):
    #print("doing fuzzy and insert UNIBET")

    
    #pull all bf matches, and subsequent team names.. for fuzzy match
    
    bf_data = betfair_data
    #convert into list of lists
    #print("unibet:",len(unibet_data),"bf:",len(betfair_data),league)
    bf_matches=[]
    for b in bf_data:
        try:
            if len(bf_data[b]['odds'])>0:
                back_25=[]
                lay_25=[]

                back_matchlist=[]
                lay_matchlist=[]
                teama,teamb  = bf_data[b]['name'].split(" v ")
                #print("bfmatches:",teama,teamb)
                #print(bf_data[b]['odds'])
                #print("---")
                matchteams=[teama,teamb]
                matchteams.sort()
                if matchteams!=[teama,teamb]:
                        flipped=1
                else:
                        flipped=0
                #print("bf_data check:",bf_data)
                back_matchlist.append([teama,bf_data[b]['odds'][0]['last_back_price'],bf_data[b]['odds'][0]['last_back_vol'],bf_data[b]['odds'][0]['lowest_back_price'],bf_data[b]['odds'][0]['lowest_back_vol']])
                back_matchlist.append([teamb,bf_data[b]['odds'][1]['last_back_price'],bf_data[b]['odds'][1]['last_back_vol'],bf_data[b]['odds'][1]['lowest_back_price'],bf_data[b]['odds'][1]['lowest_back_vol']])
                back_matchlist.append(["X",bf_data[b]['odds'][2]['last_back_price'],bf_data[b]['odds'][2]['last_back_vol'],bf_data[b]['odds'][2]['lowest_back_price'],bf_data[b]['odds'][2]['lowest_back_vol']])
                lay_matchlist.append([teama,bf_data[b]['odds'][0]['lay_price'],bf_data[b]['odds'][0]['lay_vol']])
                lay_matchlist.append([teamb,bf_data[b]['odds'][1]['lay_price'],bf_data[b]['odds'][1]['lay_vol']])
                lay_matchlist.append(["X",bf_data[b]['odds'][2]['lay_price'],bf_data[b]['odds'][2]['lay_vol']])
 #add extra markets here
                back_25.append(["Under_2.5",bf_data[b]['markets'][0]['last_back_price_Under_2.5'],bf_data[b]['markets'][0]['last_back_vol_Under_2.5'],bf_data[b]['markets'][0]['lowest_back_price_Under_2.5'],bf_data[b]['markets'][0]['lowest_back_vol_Under_2.5']])
                back_25.append(["Over_2.5",bf_data[b]['markets'][1]['last_back_price_Over_2.5'],bf_data[b]['markets'][1]['last_back_vol_Over_2.5'],bf_data[b]['markets'][1]['lowest_back_price_Over_2.5'],bf_data[b]['markets'][1]['lowest_back_vol_Over_2.5']])

                lay_25.append(["Under_2.5",bf_data[b]['markets'][0]['lay_price_Under_2.5'],bf_data[b]['markets'][0]['lay_vol_Under_2.5']])
                lay_25.append(["Over_2.5",bf_data[b]['markets'][1]['lay_price_Over_2.5'],bf_data[b]['markets'][1]['lay_vol_Over_2.5']])
                bf_matches.append({"matchup":matchteams,"flipped":flipped,"matchup_raw":matchteams,"lay_book":lay_matchlist,"back_book":back_matchlist,"back_25":back_25,"lay_25":lay_25,'event_id':b,"timestamp":bf_data[b]['timestamp']})
        except Exception as msg:
            print("err on betfair match check:",teama,teamb,str(msg))
            try:
                insert_error(str(msg),"err on betfair (ub) match check:",teama,teamb,str(msg))
            except Exception as msg:
                print(">>> insert err error..",str(msg))

            

    #for b in bf_matches:
    #    print(b)

    #print("------------------------>")
    
    tt_data = unibet_data#pickle.load(f)

    #here pull from db, and whittle down to unique,, then create the list..
    #toto_teams = get_team_list_toto()
    unibet_teams = get_team_list_unibet()

    print("there are:",len(unibet_teams),"teams")   

    bf_teams=[]
    for b in bf_data:
        for name in bf_data[b]['name'].split(" v "):
            bf_teams.append(name)
    bf_teams=list(set(bf_teams))

    tt_matches=[]

    for t in  tt_data:
        match_data=[]
        matchteams=[]
        matchteams_raw=[]
        for runner in t['book']:
            #print(">>",runner['name'],"<<")
            if runner['name']!='Draw' and runner['name']!='' and   runner['name']!='X':
                matchteams_raw.append(runner['name'])
                #try to match it,, if not,, fuzzy?
                if runner['name'].upper() in unibet_teams and unibet_teams[runner['name'].upper()]!="":
                    match_data.append([unibet_teams[runner['name'].upper()],runner['price'],0])
                    matchteams.append(unibet_teams[runner['name'].upper()])
                else:
                    #fuzzy..
                    maxfuzz=0
                    likely_team=""
                    for b in bf_teams:
                        r=fuzz.ratio(b,runner['name'])
                        if r>maxfuzz:
                            maxfuzz=r
                            likely_team=b
                    match_data.append([likely_team,runner['price'],1])
                    #print("fuzzy",likely_team,t)
                    matchteams.append(likely_team)
            else:
                match_data.append(["X",runner['price'],0])
        try:
            matchteams.remove('')
        except:
            pass
        matchteams.sort()
        matchteams_raw.sort()
        tt_matches.append({"matchup":matchteams,"matchup_raw":matchteams_raw,"book":match_data,"markets":t['markets'],'event_id':t['id'],'start_time':t['start_time']})

    #for t in tt_matches:
    #    print("unibet",t)
    found=0
    for t in tt_matches:
        found=0
        for b in bf_matches:
            #print("<><><>",t['matchup'],b['matchup'],t['start_time'][0:10],int(b['timestamp']),str(datetime.datetime.utcfromtimestamp(int(b['timestamp'])).strftime('%Y-%m-%d %H:%M:%S'))[0:10])
            #print("date match:",t['start_time'][0:10],str(datetime.datetime.utcfromtimestamp(int(b['timestamp'])).strftime('%Y-%m-%d %H:%M:%S'))[0:10])
            
            if t['matchup']==b['matchup'] and convert_midnight(t['start_time'])==str(datetime.datetime.utcfromtimestamp(int(b['timestamp'])).strftime('%Y-%m-%d %H:%M:%S'))[0:10]:
                
                insert_to_database_unibet(t,b,league)
                found=1
                break
            else:
                pass#print("UNMATCHED<<<<<",t['matchup'],b['matchup'],t['start_time'][0:10],int(b['timestamp']),str(datetime.datetime.utcfromtimestamp(int(b['timestamp'])).strftime('%Y-%m-%d %H:%M:%S'))[0:10])
            
                
    if not found:
        #print("NOT MATCHED:",t['matchup'],b['matchup'])
        conn = pymysql.connect(host='localhost',user='local',passwd='oeijifjwejfio',db=db_name)
        cur  = conn.cursor()
        #print("select * from unmatched where start_time=%s and team1=%s and team2=%s",(t['start_time'],t['matchup_raw'][0],t['matchup_raw'][1]))

        cur.execute("select * from unibet_unmatched where start_time=%s and team1=%s and team2=%s",(t['start_time'],t['matchup_raw'][0],t['matchup_raw'][1]))
        rows =cur.fetchall()
        if len(rows)==0:
            cur.execute("insert into unibet_unmatched (team1,team2,league,start_time,timestamp) values(%s,%s,%s,%s,%s)",(t['matchup_raw'][0],t['matchup_raw'][1],league,t['start_time'],time.time()))
            conn.commit()
        conn.close()    

def do_insert_contra(contra_data,betfair_data,league):
    #print("doing fuzzy and insert contra")

    
    #pull all bf matches, and subsequent team names.. for fuzzy match
    
    bf_data = betfair_data
    #convert into list of lists
    print("contra:",len(contra_data),"bf:",len(betfair_data),league)
    bf_matches=[]
    for b in bf_data:
        try:
            if len(bf_data[b]['odds'])>0:

                back_matchlist=[]
                lay_matchlist=[]
                back_25=[]
                lay_25=[]

                teama,teamb  = bf_data[b]['name'].split(" v ")
                #print("bfmatches:",teama,teamb)
                #print(bf_data[b]['odds'])
                #print("---")
                matchteams=[teama,teamb]
                matchteams.sort()
                if matchteams!=[teama,teamb]:
                        flipped=1
                else:
                        flipped=0
                #print("bf_data check:",bf_data)
                back_matchlist.append([teama,bf_data[b]['odds'][0]['last_back_price'],bf_data[b]['odds'][0]['last_back_vol'],bf_data[b]['odds'][0]['lowest_back_price'],bf_data[b]['odds'][0]['lowest_back_vol']])
                back_matchlist.append([teamb,bf_data[b]['odds'][1]['last_back_price'],bf_data[b]['odds'][1]['last_back_vol'],bf_data[b]['odds'][1]['lowest_back_price'],bf_data[b]['odds'][1]['lowest_back_vol']])
                back_matchlist.append(["X",bf_data[b]['odds'][2]['last_back_price'],bf_data[b]['odds'][2]['last_back_vol'],bf_data[b]['odds'][2]['lowest_back_price'],bf_data[b]['odds'][2]['lowest_back_vol']])
                lay_matchlist.append([teama,bf_data[b]['odds'][0]['lay_price'],bf_data[b]['odds'][0]['lay_vol']])
                lay_matchlist.append([teamb,bf_data[b]['odds'][1]['lay_price'],bf_data[b]['odds'][1]['lay_vol']])
                lay_matchlist.append(["X",bf_data[b]['odds'][2]['lay_price'],bf_data[b]['odds'][2]['lay_vol']])

 #add extra markets here
                back_25.append(["Under_2.5",bf_data[b]['markets'][0]['last_back_price_Under_2.5'],bf_data[b]['markets'][0]['last_back_vol_Under_2.5'],bf_data[b]['markets'][0]['lowest_back_price_Under_2.5'],bf_data[b]['markets'][0]['lowest_back_vol_Under_2.5']])
                back_25.append(["Over_2.5",bf_data[b]['markets'][1]['last_back_price_Over_2.5'],bf_data[b]['markets'][1]['last_back_vol_Over_2.5'],bf_data[b]['markets'][1]['lowest_back_price_Over_2.5'],bf_data[b]['markets'][1]['lowest_back_vol_Over_2.5']])

                lay_25.append(["Under_2.5",bf_data[b]['markets'][0]['lay_price_Under_2.5'],bf_data[b]['markets'][0]['lay_vol_Under_2.5']])
                lay_25.append(["Over_2.5",bf_data[b]['markets'][1]['lay_price_Over_2.5'],bf_data[b]['markets'][1]['lay_vol_Over_2.5']])
                bf_matches.append({"matchup":matchteams,"flipped":flipped,"matchup_raw":matchteams,"lay_book":lay_matchlist,"back_book":back_matchlist,"back_25":back_25,"lay_25":lay_25,'event_id':b,"timestamp":bf_data[b]['timestamp']})
        except Exception as msg:
            print("err on betfair match check:",teama,teamb,str(msg))
            try:
                insert_error(str(msg),"err on betfair (ub) match check:",teama,teamb,str(msg))
            except Exception as msg:
                print(">>> insert err error..",str(msg))

            
    print("bf data check")
    #for b in bf_matches:
    #    print(b)

    print("------------------------>")
    
    tt_data = contra_data#pickle.load(f)
    #print("CONTRA>>>>>>>")
    #print(tt_data[0])
    #print("<<<<<<<<")
    #here pull from db, and whittle down to unique,, then create the list..
    #toto_teams = get_team_list_toto()
    contra_teams = get_team_list_contra()

    print("there are:",len(contra_teams),"teams")   

    bf_teams=[]
    for b in bf_data:
        for name in bf_data[b]['name'].split(" v "):
            bf_teams.append(name)
    bf_teams=list(set(bf_teams))

    tt_matches=[]

    for t in  tt_data:
        match_data=[]
        matchteams=[]
        matchteams_raw=[]
        for runner in t['book']:
            print(">>",runner['name'],"<<")
            if runner['name']!='Draw' and runner['name']!='' and   runner['name']!='X':
                matchteams_raw.append(runner['name'])
                #try to match it,, if not,, fuzzy?
                if runner['name'].upper() in contra_teams and contra_teams[runner['name'].upper()]!="":
                    match_data.append([contra_teams[runner['name'].upper()],runner['price'],0])
                    matchteams.append(contra_teams[runner['name'].upper()])
                else:
                    #fuzzy..
                    maxfuzz=0
                    likely_team=""
                    for b in bf_teams:
                        r=fuzz.ratio(b,runner['name'])
                        if r>maxfuzz:
                            maxfuzz=r
                            likely_team=b
                    match_data.append([likely_team,runner['price'],1])
                    print("fuzzy",likely_team,t)
                    matchteams.append(likely_team)
            else:
                match_data.append(["X",runner['price'],0])
        try:
            matchteams.remove('')
        except:
            pass
        matchteams.sort()
        matchteams_raw.sort()
        tt_matches.append({"matchup":matchteams,"matchup_raw":matchteams_raw,"book":match_data,"markets":t['markets'],'event_id':t['id'],'start_time':t['start_time']})

    for t in tt_matches:
        print("contra",t)
    found=0
    for t in tt_matches:
        found=0
        for b in bf_matches:
            #print("<><><>",t['matchup'],b['matchup'],t['start_time'][0:10],int(b['timestamp']),str(datetime.datetime.utcfromtimestamp(int(b['timestamp'])).strftime('%Y-%m-%d %H:%M:%S'))[0:10])
            #print("date match:",t['start_time'][0:10],str(datetime.datetime.utcfromtimestamp(int(b['timestamp'])).strftime('%Y-%m-%d %H:%M:%S'))[0:10])
            
            if t['matchup']==b['matchup'] and convert_midnight(t['start_time'])==str(datetime.datetime.utcfromtimestamp(int(b['timestamp'])).strftime('%Y-%m-%d %H:%M:%S'))[0:10]:
                
                insert_to_database_contra(t,b,league)
                found=1
                break
            else:
                pass#print("UNMATCHED<<<<<",t['matchup'],b['matchup'],t['start_time'][0:10],int(b['timestamp']),str(datetime.datetime.utcfromtimestamp(int(b['timestamp'])).strftime('%Y-%m-%d %H:%M:%S'))[0:10])
            
                
    if not found:
        #print("NOT MATCHED:",t['matchup'],b['matchup'])
        conn = pymysql.connect(host='localhost',user='local',passwd='oeijifjwejfio',db=db_name)
        cur  = conn.cursor()
        #print("select * from unmatched where start_time=%s and team1=%s and team2=%s",(t['start_time'],t['matchup_raw'][0],t['matchup_raw'][1]))

        cur.execute("select * from contra_unmatched where start_time=%s and team1=%s and team2=%s",(t['start_time'],t['matchup_raw'][0],t['matchup_raw'][1]))
        rows =cur.fetchall()
        if len(rows)==0:
            cur.execute("insert into contra_unmatched (team1,team2,league,start_time,timestamp) values(%s,%s,%s,%s,%s)",(t['matchup_raw'][0],t['matchup_raw'][1],league,t['start_time'],time.time()))
            conn.commit()
        conn.close()    



def process_comp(comp_meta):#toto_id,bf_id,league):
    try:
        toto_data = pull_data_toto(comp_meta['toto'],comp_meta['league'])
    except Exception as msg:
        print("process err (toto):",str(msg))

    try:
        betfair_data = pull_betfair_data(comp_meta['betfair'],comp_meta['league'])
    except Exception as msg:
        print("process err (bf):",str(msg))

    try:
        if comp_meta['unibet']=="":
            print("skipping unibet for " + comp_meta['league'] + " >>  no compurl yet")
        else:
            unibet_data = pull_data_unibet(comp_meta['unibet'],comp_meta['league'])
    except Exception as msg:
        print("err on unibet pull:",str(msg))

    try:
        if comp_meta['contra']=="":
            print("skipping contra for " + comp_meta['league'] + " >>  no compurl yet")
        else:
            contra_data = pull_data_contra(comp_meta['contra'],comp_meta['league'])
    except Exception as msg:
        print("err on contra pull:",str(msg))

    ##toto check
    try:
        do_insert_toto(toto_data,betfair_data,comp_meta['league'])
    except:
        print("err on toto insert")

    try:
        do_insert_unibet(unibet_data,betfair_data,comp_meta['league'])
    except Exception as msg:
        print("err on unibet insert:",str(msg))

    try:
        do_insert_contra(contra_data,betfair_data,comp_meta['league'])
    except Exception as msg:
        print("err on contra insert:",str(msg))


    ##unibet check
    print("finished processing :",comp_meta['league'],"<<<<<<<<<<>>>>>>>>>>>")

"""comps=[{"toto":"591","betfair":"129","league":"sweall"},
{"toto":"826","betfair":"12117172","league":"aleague"},
{"toto":"567","betfair":"10932509","league":"epl"},
{"toto":"1001","betfair":"12206014","league":"bahpre"},
{"toto":"4319","betfair":"12231751","league":"canpre"}]
"""

#comps=[{"toto":"567","betfair":"10932509","league":"epl"}]
def get_comp_list():
    comps=[]
    conn = pymysql.connect(host='127.0.0.1',user='local',passwd='oeijifjwejfio',db=db_name)
    cur  = conn.cursor()
    cur.execute("select * from comps where id=138")# where id=6")
    rows = cur.fetchall()
    conn.close()
    for row in rows:
        if row[6] is None:
            if row[8] is None:
                comps.append({"toto":str(row[4]),"betfair":str(row[2]),"unibet":str(""),"contra":"","league":row[1]}) # << here just need to splice in something benign for ub if null
            else:
                comps.append({"toto":str(row[4]),"betfair":str(row[2]),"unibet":str(""),"contra":row[8],"league":row[1]}) # << here just need to splice in something benign for ub if null
        else:
            if row[8] is None:
                comps.append({"toto":str(row[4]),"betfair":str(row[2]),"unibet":str(row[6]),"contra":"","league":row[1]}) # << here just need to splice in something benign for ub if null
 
            else:
                comps.append({"toto":str(row[4]),"betfair":str(row[2]),"unibet":str(row[6]),"contra":row[8],"league":row[1]}) # << here just need to splice in something benign for ub if null
    print("complen:",len(comps))
    #time.sleep(2)
    return comps



def go(comps):
    threads = min(len(comps),20)

    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        executor.map(process_comp, comps )



while 1:
    trading.login()
    print("logged in!")

    stime=time.time()
    try:
        do_toto_raw()
    except Exception as msg:
        print("err on toto_raw",str(msg))

    try:
        do_betfair_raw()
    except Exception as msg:
        print("err on betfair_raw",str(msg))

    try:
        do_unibet_raw()
    except Exception as msg:
        print("err on unibet_raw",str(msg))

    try:
        if random.randint(1,180)==1:#change this to happen once every few hours,, so 1,180 would be 1hr,, (assuming 20s scan time)
            do_contra_raw() # >> when i decide on course of action
    except Exception as msg:
        print("err on contra_raw",str(msg))
    
    #time.sleep(10)#lets look at contras raws..

    if 1:#try:
        comps = get_comp_list()
        print("got comps..")
        go(comps)
    
    else:#except Exception as msg:
        print("err on scan",str(msg))

    ## insert into last scan
    conn = pymysql.connect(host='127.0.0.1',user='local',passwd='oeijifjwejfio',db=db_name)
    cur  = conn.cursor()
    cur.execute("update log_table set timestamp=%s where log_type='last_scan'",(time.time()))# where toto_id=587")
    conn.commit()
    conn.close()

    print("scan took(" + str(int(time.time()-stime)) + " seconds (20 threads)..NOSleep..0 (" +version.upper() + "):" + str(datetime.datetime.now())[0:19])#
    trading.logout()
    print("logged out!")

    time.sleep(10)#sleep 20secs before redownload
#process_comp(comps[0])

