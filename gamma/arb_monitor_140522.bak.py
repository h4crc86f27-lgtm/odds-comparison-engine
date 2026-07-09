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

db_name="arb_db_main"
## here do a toto check on comps, on random occasion

def strip_accents(s):
   return ''.join(c for c in unicodedata.normalize('NFD', s)
                  if unicodedata.category(c) != 'Mn')

def insert_error(err_str,misc=""):
    conn = pymysql.connect(host='localhost',user='local',passwd='oeijifjwejfio',db=db_name)
    cur  = conn.cursor()
    cur.execute("insert into errors (timestamp,err_msg,misc) values(%s,%s,%s)",(time.time(),err_str,misc))
    conn.commit()
    conn.close()

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
                x=cur.execute("insert into raw_comps(comp_name,comp_id,site) values(%s,%s,%s)",(gg['name'],compid,"unibet"))

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
                x=cur.execute("insert into raw_comps(comp_name,comp_id,site) values(%s,%s,%s)",(ddn['name'],ddn['id'],"toto"))
    conn.commit()
    conn.close()

## here do a betfair check on comps..
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
            #print(home + " v " + away,home_outcome,draw_outcome,away_outcome,"<>",draw)
            comp_data.append({"id":f['id'],"book":outcomes,"start_time":f['startTime']})
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
        #print ("unibet:",{"id":eid,"book":outcomes,"start_time":timestamp})
        comp_data.append({"id":eid,"book":outcomes,"start_time":timestamp})
        


    #with open("raw_unibet_data/" + league + "_" + str(compid) + ".json","wb") as f:
    #    f.write(res.content) 
    
    return comp_data


my_username ="hippienew@outlook.com"# cred['username']
my_password = "Saphires_43"#cred['password']
my_app_key ="o4DESE5fzU4r1fkv"# cred['app_key']

trading = betfairlightweight.APIClient(username=my_username,
                                       password=my_password,
                                       app_key=my_app_key,
                                       certs="/home/arb_bot/certs")

trading.login()
print("logged in!")

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
            x=cur.execute("insert into raw_comps (comp_name,comp_id,site) values(%s,%s,%s)",(comp.competition.name,comp.competition.id,"betfair"))
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

def get_market_books(books):
	price_filter=betfairlightweight.filters.price_projection(price_data=['EX_BEST_OFFERS'])
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
        comp_data[event_id]={"name":event.event.name,"odds":[],"timestamp":event.event.open_date.timestamp()}
        eventids.append(event_id)
        #comp_markets = pull_markets(eventids)
        comp_market = pull_markets([event_id])
        comp_data[event_id]['h2h_id']=get_event_matchodds(comp_market,event_id)
        try:
            books = get_market_books([comp_data[event_id]['h2h_id']])
            for runner in books[0].runners:
                comp_data[event_id]['odds'].append({"price":runner.ex.available_to_lay[0].price,"vol":runner.ex.available_to_lay[0].size})
        except Exception as msg:
            insert_error(str(msg),"error in getting betfair book:" + compid + " -- " + event.event.name + " (" + league + ")")
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

def insert_to_database_toto(t,b):
    conn = pymysql.connect(host='localhost',user='local',passwd='oeijifjwejfio',db=db_name)
    cur  = conn.cursor()
    toto_teamnames = t['matchup_raw']
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
    for runner in b['book']:
        if runner[0]==b['matchup'][0]:
            bf_1_odds=runner[1]
            bf_1_vol=runner[2]
        elif runner[0]==b['matchup'][1]:
            bf_2_odds=runner[1]
            bf_2_vol = runner[2]
        else:
            bf_x_odds=runner[1]
            bf_x_vol=runner[2]
    ##here flip back names and odds if flipped..
    if b['flipped']:
        temp = toto_1_odds
        toto_1_odds = toto_2_odds
        toto_2_odds = temp
        temp = toto_teamnames[0]
        toto_teamnames[0] = toto_teamnames[1]
        toto_teamnames[1] = temp
        

        temp = bf_1_odds
        bf_1_odds = bf_2_odds
        bf_2_odds = temp

        temp = bf_1_vol
        bf_1_vol = bf_2_vol
        bf_2_vol = temp

        temp = bf_teamnames[0]
        bf_teamnames[0] = bf_teamnames[1]
        bf_teamnames[1] = temp

        temp = t1fuzzy
        t1fuzzy = t2fuzzy
        t2fuzzy = temp
        
    #insert section
    odds_json={"toto_1_odds":toto_1_odds,"toto_x_odds":toto_x_odds,"toto_2_odds":toto_2_odds,
               "bf_1_odds":{"price":bf_1_odds,"vol":bf_1_vol},"bf_x_odds":{"price":bf_x_odds,"vol":bf_x_vol},"bf_2_odds":{"price":bf_2_odds,"vol":bf_2_vol}}
    #here check for existing..
    cur.execute("select * from toto_matches where toto_event_id=%s and betfair_event_id=%s",(t['event_id'],b['event_id']))
    rows = cur.fetchall()
    if len(rows)>0:
        print("found event,, updating",t['event_id'],b['event_id'])
        cur.execute("update toto_matches set timestamp=%s,odds_data=%s,t1_fuzzy=%s,t2_fuzzy=%s where toto_event_id=%s and betfair_event_id=%s",
                (b['timestamp'],json.dumps(odds_json),t1fuzzy,t2fuzzy,t['event_id'],b['event_id']))
        print("inserted:",t['event_id'],b['event_id'])
    else:
        print("NO event,, inserting",t['event_id'],b['event_id'])
        #here i do an extra ratio check on toto teams, because somehow are flipping sometimes..
        if fuzz.ratio(toto_teamnames[0],bf_teamnames[0])>fuzz.ratio(toto_teamnames[0],bf_teamnames[1]):
            pass#should be right 
        else:
            print("flipping:",toto_teamnames[0],toto_teamnames[1])
            temp = toto_teamnames[0]
            toto_teamnames[0] = toto_teamnames[1]
            toto_teamnames[1] = temp

        cur.execute("insert into toto_matches (timestamp,toto_event_id,betfair_event_id,team_1_toto,team_2_toto,team_1_betfair,team_2_betfair,odds_data,t1_fuzzy,t2_fuzzy,ignored) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (b['timestamp'],t['event_id'],b['event_id'],toto_teamnames[0],toto_teamnames[1],bf_teamnames[0],bf_teamnames[1],json.dumps(odds_json),t1fuzzy,t2fuzzy,0))
    conn.commit()
    conn.close()
    

def insert_to_database_unibet(t,b):
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
    for runner in b['book']:
        if runner[0]==b['matchup'][0]:
            bf_1_odds=runner[1]
            bf_1_vol=runner[2]
        elif runner[0]==b['matchup'][1]:
            bf_2_odds=runner[1]
            bf_2_vol = runner[2]
        else:
            bf_x_odds=runner[1]
            bf_x_vol=runner[2]
    ##here flip back names and odds if flipped..
    if b['flipped']:
        temp = toto_1_odds
        toto_1_odds = toto_2_odds
        toto_2_odds = temp
        temp = unibet_teamnames[0]
        unibet_teamnames[0] = unibet_teamnames[1]
        unibet_teamnames[1] = temp
        

        temp = bf_1_odds
        bf_1_odds = bf_2_odds
        bf_2_odds = temp

        temp = bf_1_vol
        bf_1_vol = bf_2_vol
        bf_2_vol = temp

        temp = bf_teamnames[0]
        bf_teamnames[0] = bf_teamnames[1]
        bf_teamnames[1] = temp

        temp = t1fuzzy
        t1fuzzy = t2fuzzy
        t2fuzzy = temp
        
    #insert section
    odds_json={"unibet_1_odds":toto_1_odds,"unibet_x_odds":toto_x_odds,"unibet_2_odds":toto_2_odds,
               "bf_1_odds":{"price":bf_1_odds,"vol":bf_1_vol},"bf_x_odds":{"price":bf_x_odds,"vol":bf_x_vol},"bf_2_odds":{"price":bf_2_odds,"vol":bf_2_vol}}
    #here check for existing..
    cur.execute("select * from unibet_matches where unibet_event_id=%s and betfair_event_id=%s",(t['event_id'],b['event_id']))
    rows = cur.fetchall()
    if len(rows)>0:
        print("found event,, updating",t['event_id'],b['event_id'])
        cur.execute("update unibet_matches set timestamp=%s,unibet_data=%s,t1_unibet_fuzzy=%s,t2_unibet_fuzzy=%s where unibet_event_id=%s and betfair_event_id=%s",
                (b['timestamp'],json.dumps(odds_json),t1fuzzy,t2fuzzy,t['event_id'],b['event_id']))
        print("inserted:",t['event_id'],b['event_id'])
    else:
        print("NO event,, inserting",t['event_id'],b['event_id'])
        #here i do an extra ratio check on toto teams, because somehow are flipping sometimes..
        if fuzz.ratio(unibet_teamnames[0],bf_teamnames[0])>fuzz.ratio(unibet_teamnames[0],bf_teamnames[1]):
            pass#should be right 
        else:
            print("flipping:",unibet_teamnames[0],unibet_teamnames[1])
            temp = unibet_teamnames[0]
            unibet_teamnames[0] = unibet_teamnames[1]
            unibet_teamnames[1] = temp

        cur.execute("insert into unibet_matches (timestamp,unibet_event_id,betfair_event_id,team_1_unibet,team_2_unibet,team_1_betfair,team_2_betfair,unibet_data,t1_unibet_fuzzy,t2_unibet_fuzzy,ignored) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (b['timestamp'],t['event_id'],b['event_id'],unibet_teamnames[0],unibet_teamnames[1],bf_teamnames[0],bf_teamnames[1],json.dumps(odds_json),t1fuzzy,t2fuzzy,0))
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

                matchlist=[]
                teama,teamb  = bf_data[b]['name'].split(" v ")
                print("bfmatches:",teama,teamb)
                print(bf_data[b]['odds'])
                print("---")
                matchteams=[teama,teamb]
                matchteams.sort()
                if matchteams!=[teama,teamb]:
                        flipped=1
                else:
                        flipped=0
                        
                matchlist.append([teama,bf_data[b]['odds'][0]['price'],bf_data[b]['odds'][0]['vol']])
                matchlist.append([teamb,bf_data[b]['odds'][1]['price'],bf_data[b]['odds'][1]['vol']])
                matchlist.append(["X",bf_data[b]['odds'][2]['price'],bf_data[b]['odds'][2]['vol']])
                bf_matches.append({"matchup":matchteams,"flipped":flipped,"matchup_raw":matchteams,"book":matchlist,'event_id':b,"timestamp":bf_data[b]['timestamp']})
        except Exception as msg:
            print("err on betfair match check:",teama,teamb,str(msg))
            try:
                insert_error(str(msg),"err on betfair (toto) match check:",teama,teamb,str(msg))
            except Exception as msg:
                print(">>> insert err error..",str(msg))
            

    for b in bf_matches:
        print(b)

    print("------------------------>")
    
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
        tt_matches.append({"matchup":matchteams,"matchup_raw":matchteams_raw,"book":match_data,'event_id':t['id'],'start_time':t['start_time']})

    for t in tt_matches:
        print("toto",t)
    found=0
    for t in tt_matches:
        found=0
        for b in bf_matches:
            #print("date match:",t['start_time'][0:10],str(datetime.datetime.utcfromtimestamp(int(b['timestamp'])).strftime('%Y-%m-%d %H:%M:%S'))[0:10])
            if t['matchup']==b['matchup'] and t['start_time'][0:10]==str(datetime.datetime.utcfromtimestamp(int(b['timestamp'])).strftime('%Y-%m-%d %H:%M:%S'))[0:10]:
                insert_to_database_toto(t,b)
                found=1
                break
    if not found:
        print("NOT MATCHED:",t['matchup'],b['matchup'])
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
    print("doing fuzzy and insert UNIBET")

    
    #pull all bf matches, and subsequent team names.. for fuzzy match
    
    bf_data = betfair_data
    #convert into list of lists
    print("unibet:",len(unibet_data),"bf:",len(betfair_data),league)
    bf_matches=[]
    for b in bf_data:
        try:
            if len(bf_data[b]['odds'])>0:

                matchlist=[]
                teama,teamb  = bf_data[b]['name'].split(" v ")
                print("bfmatches:",teama,teamb)
                print(bf_data[b]['odds'])
                print("---")
                matchteams=[teama,teamb]
                matchteams.sort()
                if matchteams!=[teama,teamb]:
                        flipped=1
                else:
                        flipped=0
                        
                matchlist.append([teama,bf_data[b]['odds'][0]['price'],bf_data[b]['odds'][0]['vol']])
                matchlist.append([teamb,bf_data[b]['odds'][1]['price'],bf_data[b]['odds'][1]['vol']])
                matchlist.append(["X",bf_data[b]['odds'][2]['price'],bf_data[b]['odds'][2]['vol']])
                bf_matches.append({"matchup":matchteams,"flipped":flipped,"matchup_raw":matchteams,"book":matchlist,'event_id':b,"timestamp":bf_data[b]['timestamp']})
        except Exception as msg:
            print("err on betfair match check:",teama,teamb,str(msg))
            try:
                insert_error(str(msg),"err on betfair (ub) match check:",teama,teamb,str(msg))
            except Exception as msg:
                print(">>> insert err error..",str(msg))

            

    #for b in bf_matches:
    #    print(b)

    print("------------------------>")
    
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
            print(">>",runner['name'],"<<")
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
        tt_matches.append({"matchup":matchteams,"matchup_raw":matchteams_raw,"book":match_data,'event_id':t['id'],'start_time':t['start_time']})

    for t in tt_matches:
        print("unibet",t)
    found=0
    for t in tt_matches:
        found=0
        for b in bf_matches:
            #print("date match:",t['start_time'][0:10],str(datetime.datetime.utcfromtimestamp(int(b['timestamp'])).strftime('%Y-%m-%d %H:%M:%S'))[0:10])
            if t['matchup']==b['matchup'] and t['start_time'][0:10]==str(datetime.datetime.utcfromtimestamp(int(b['timestamp'])).strftime('%Y-%m-%d %H:%M:%S'))[0:10]:
                insert_to_database_unibet(t,b)
                found=1
                break
    if not found:
        print("NOT MATCHED:",t['matchup'],b['matchup'])
        conn = pymysql.connect(host='localhost',user='local',passwd='oeijifjwejfio',db=db_name)
        cur  = conn.cursor()
        #print("select * from unmatched where start_time=%s and team1=%s and team2=%s",(t['start_time'],t['matchup_raw'][0],t['matchup_raw'][1]))

        cur.execute("select * from unibet_unmatched where start_time=%s and team1=%s and team2=%s",(t['start_time'],t['matchup_raw'][0],t['matchup_raw'][1]))
        rows =cur.fetchall()
        if len(rows)==0:
            cur.execute("insert into unibet_unmatched (team1,team2,league,start_time,timestamp) values(%s,%s,%s,%s,%s)",(t['matchup_raw'][0],t['matchup_raw'][1],league,t['start_time'],time.time()))
            conn.commit()
        conn.close()    

def process_comp(comp_meta):#toto_id,bf_id,league):
    toto_data = pull_data_toto(comp_meta['toto'],comp_meta['league'])
    betfair_data = pull_betfair_data(comp_meta['betfair'],comp_meta['league'])
    try:
        if comp_meta['unibet']=="":
            print("skipping unibet for " + comp_meta['league'] + " >>  no compurl yet")
        else:
            unibet_data = pull_data_unibet(comp_meta['unibet'],comp_meta['league'])
    except Exception as msg:
        print("err on unibet pull:",str(msg))

    ##toto check
    try:
        do_insert_toto(toto_data,betfair_data,comp_meta['league'])
    except:
        print("err on toto insert")

    try:
        do_insert_unibet(unibet_data,betfair_data,comp_meta['league'])
    except Exception as msg:
        print("err on unibet insert:",str(msg))

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
    cur.execute("select * from comps")# where toto_id=664")
    rows = cur.fetchall()
    conn.close()
    for row in rows:
        if row[6] is None:
            comps.append({"toto":str(row[4]),"betfair":str(row[2]),"unibet":str(""),"league":row[1]}) # << here just need to splice in something benign for ub if null
        else:
            comps.append({"toto":str(row[4]),"betfair":str(row[2]),"unibet":str(row[6]),"league":row[1]}) # << here just need to splice in something benign for ub if null
    print("complen:",len(comps))
    time.sleep(2)
    return comps



def go(comps):
    threads = min(len(comps),10)

    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        executor.map(process_comp, comps )

while 1:
    try:
        do_toto_raw()
    except Exception as msg:
        print("err on toto_raw",str(msg))

    try:
        do_betfair_raw()
    except Exception as msg:
        print("err on betfair_raw",str(msg))
    if 1:#try:
       
        comps = get_comp_list()
        go(comps)
    
    else:#except Exception as msg:
        print("err on scan",str(msg))

    ## insert into last scan
    conn = pymysql.connect(host='127.0.0.1',user='local',passwd='oeijifjwejfio',db=db_name)
    cur  = conn.cursor()
    cur.execute("update log_table set timestamp=%s where log_type='last_scan'",(time.time()))# where toto_id=587")
    conn.commit()
    conn.close()

    print("..Sleep..60 (BETA):" + str(datetime.datetime.now())[0:19])#
    time.sleep(60)#sleep 30secs before redownload
#process_comp(comps[0])

