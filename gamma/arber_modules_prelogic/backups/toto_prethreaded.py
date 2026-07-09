import pymysql
import configparser
import requests
import random
import datetime
from arber_modules.utils import *
import time
from fuzzywuzzy import fuzz
import json
import concurrent.futures

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


def do_toto_raw():

    conn = pymysql.connect(host='127.0.0.1',user='local',passwd='oeijifjwejfio',db=db_name)
    cur  = conn.cursor()
    cur.execute("select * from raw_comps where site='toto'")
    rows = cur.fetchall()
    ids_done=[]
    for row in rows:
        ids_done.append(int(row[2]))

    url="https://content.toto.nl/content-service/api/v1/q/drilldown-tree?drilldownNodeIds=11&eventState=OPEN_EVENT"
    res = requests.get(url)#,proxies = {"https":random.choice(proxies)})
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



def get_extra_markets_toto(ld):
    #print("--",ld,"--")
    retdata={"2.5":[],"3.5":[],"DNB":[]}
    
    url="https://content.toto.nl/content-service/api/v1/q/events-by-ids?eventIds="+ str(ld) + "&includeChildMarkets=false&includeCollections=true&includePriceHistory=false&includeCommentary=false&includeIncidents=false&includeRace=false&includeMedia=false&includePools=false"
    res = requests.get(url)#,proxies = {"https":random.choice(proxies)})
    colls = res.json()['data']['events'][0]['collections']
    market_ids=[]
    for c in colls:
        if c['name']=='Wedstrijd' or c['name']=='Doelpunten':#dnb/3.5
            for m in c['marketIds']:
                market_ids.append(m)
    #now pull these marketids for this event, and extract the POIs
    url="https://content.toto.nl/content-service/api/v1/q/events-by-ids?marketIds=" + "%2C".join(market_ids) + "&includeChildMarkets=true&includePriceHistory=false&includeCommentary=false&includeMedia=false"
    res = requests.get(url)#,proxies = {"https":random.choice(proxies)})
    data = res.json()
    event = data['data']['events'][0]
    markets = event['markets']
    for market in markets:
        if market['name']=="Total Goals Over/Under 2.5":
            print("uo2.5")
            for o in market['outcomes']:
                retdata['2.5'].append(o['prices'][0]['decimal'])
        elif market['name']=="Total Goals Over/Under 3.5":
            print("uo3.5")
            for o in market['outcomes']:
                retdata['3.5'].append(o['prices'][0]['decimal'])
        elif market['name']=="Draw No Bet":
            print("DNB")
            for o in market['outcomes']:
                retdata['DNB'].append(o['prices'][0]['decimal'])
    if len(retdata['2.5'])<2:
        retdata['2.5']=[0,0]
    if len(retdata['3.5'])<2:
        retdata['3.5']=[0,0]
    if len(retdata['DNB'])<2:
        retdata['DNB']=[0,0]

    return retdata

def toto_data_thread(e):
    pass

def pull_data_toto(compid,league):#add comp_data as mutable param
    print("TOTO DATA >>>")
    dates=[]
    for dta in range(0,14):
        dates.append(str(datetime.datetime.now()+datetime.timedelta(days=dta))[0:10])
    #print("toto_dates:",dates)
    #time.sleep(5)
    #this pulls the market for comp raw.. need to swap in ddN, and dates
    #url="https://content.toto.nl/content-service/api/v1/q/time-band-event-list?maxMarkets=10&marketSortsIncluded=--%2CHH%2CHL%2CMR%2CWH&marketGroupTypesIncluded=MONEYLINE%2CROLLING_SPREAD%2CROLLING_TOTAL%2CSTATIC_SPREAD%2CSTATIC_TOTAL&allowedEventSorts=MTCH&includeChildMarkets=true&prioritisePrimaryMarkets=true&includeCommentary=true&includeMedia=true&drilldownTagIds=" + compid + "&maxTotalItems=60&maxEventsPerCompetition=10&maxCompetitionsPerSportPerBand=3&maxEventsForNextToGo=5&startTimeOffsetForNextToGo=600&dates=2022-04-30T22%3A00%3A00Z%2C2022-05-01T22%3A00%3A00Z%2C2022-05-02T22%3A00%3A00Z%2C2022-05-3T22%3A00%3A00Z%2C2022-05-04T22%3A00%3A00Z%2C2022-05-05T22%3A00%3A00Z%2C2022-05-06T22%3A00%3A00Z%2C2022-05-07T22%3A00%3A00Z" 
    url="https://content.toto.nl/content-service/api/v1/q/time-band-event-list?maxMarkets=20&marketSortsIncluded=--%2CHH%2CHL%2CMR%2CWH&marketGroupTypesIncluded=MONEYLINE%2CROLLING_SPREAD%2CROLLING_TOTAL%2CSTATIC_SPREAD%2CSTATIC_TOTAL&allowedEventSorts=MTCH&includeChildMarkets=true&prioritisePrimaryMarkets=true&includeCommentary=true&includeMedia=true&drilldownTagIds=" + compid + "&maxTotalItems=100&maxEventsPerCompetition=20&maxCompetitionsPerSportPerBand=3&maxEventsForNextToGo=5&startTimeOffsetForNextToGo=600&dates=" + dates[0] + "T22%3A00%3A00Z%2C" + dates[1] + "T22%3A00%3A00Z%2C" + dates[2] + "T22%3A00%3A00Z%2C" + dates[3] + "T22%3A00%3A00Z%2C" + dates[4] + "T22%3A00%3A00Z%2C" + dates[5] + "T22%3A00%3A00Z%2C" + dates[6] + "T22%3A00%3A00Z%2C" + dates[7] + "T22%3A00%3A00Z%2C" + dates[8] + "T22%3A00%3A00Z%2C" + dates[9] + "T22%3A00%3A00Z%2C" + dates[10] + "T22%3A00%3A00Z%2C" + dates[11] + "T22%3A00%3A00Z%2C" + dates[12] + "T22%3A00%3A00Z%2C" + dates[13] + "T22%3A00%3A00Z"
    #params="maxMarkets=10&marketSortsIncluded=--%2CHH%2CHL%2CMR%2CWH&marketGroupTypesIncluded=MONEYLINE%2CROLLING_SPREAD%2CROLLING_TOTAL%2CSTATIC_SPREAD%2CSTATIC_TOTAL&allowedEventSorts=MTCH&includeChildMarkets=true&prioritisePrimaryMarkets=true&includeCommentary=true&includeMedia=true&drilldownTagIds=826&maxTotalItems=60&maxEventsPerCompetition=7&maxCompetitionsPerSportPerBand=3&maxEventsForNextToGo=5&startTimeOffsetForNextToGo=600&dates=2022-04-24T22%3A00%3A00Z%2C2022-04-25T22%3A00%3A00Z%2C2022-04-26T22%3A00%3A00Z"
    for counter in range(3):
        try:
            res = requests.get(url)#,proxies = {"https":random.choice(proxies)})
            break
        except:
            print("toto comp err.. retrying")

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
            #here you call in the other markets for this eventId=
            other_markets = get_extra_markets_toto(f['id'])
            extra_markets.append({"name":"2.5_Under","price":other_markets['2.5'][0]})
            extra_markets.append({"name":"2.5_Over","price":other_markets['2.5'][1]})
            extra_markets.append({"name":"3.5_Under","price":other_markets['3.5'][0]})
            extra_markets.append({"name":"3.5_Over","price":other_markets['3.5'][1]})
            extra_markets.append({"name":"DNB_Home","price":other_markets['DNB'][0]})
            extra_markets.append({"name":"DNB_Away","price":other_markets['DNB'][1]})

            #for market in markets:
            #    if market['name']=="Total Goals Over/Under 2.5":
            #        odds_a_name = market['outcomes'][0]['prices'][0]['handicapLow'] + "_" + market['outcomes'][0]['name']
            #        odds_b_name = market['outcomes'][1]['prices'][0]['handicapLow'] + "_" + market['outcomes'][1]['name']
            #        odds_a = market['outcomes'][0]['prices'][0]['decimal']
            #        odds_b = market['outcomes'][1]['prices'][0]['decimal']
            #        extra_markets.append({"name":odds_a_name,"price":odds_a})
            #        extra_markets.append({"name":odds_b_name,"price":odds_b})


            print(home + " v " + away,extra_markets)
            comp_data.append({"id":f['id'],"book":outcomes,"markets":extra_markets,"start_time":f['startTime']})

            #print("~~~~~~~~~~~~" + f['startTime']);



    
    return comp_data



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
    toto_over_3p5=0
    toto_under_3p5=0
    toto_dnb_home=0
    toto_dnb_away=0

    for outcome in t['markets']:
        if outcome['name']=='2.5_Over':
            toto_over_2p5 = outcome['price']
        elif outcome['name']=='2.5_Under':
            toto_under_2p5 = outcome['price']
        if outcome['name']=='3.5_Over':
            toto_over_3p5 = outcome['price']
        elif outcome['name']=='3.5_Under':
            toto_under_3p5 = outcome['price']
        elif outcome['name']=='DNB_Home':
            toto_dnb_home = outcome['price']
        elif outcome['name']=='DNB_Away':
            toto_dnb_away = outcome['price']


    #insert section
    print("TOTO###",b)
    odds_json={"toto_1_odds":toto_1_odds,"toto_x_odds":toto_x_odds,"toto_2_odds":toto_2_odds,"toto_under_2.5":toto_under_2p5,"toto_over_2.5":toto_over_2p5,"toto_under_3.5":toto_under_3p5,"toto_over_3.5":toto_over_3p5,"toto_dnb_home":toto_dnb_home,"toto_dnb_away":toto_dnb_away,
               "bf_1_odds":{"last_back_price":bf_1_last_back_odds,"last_back_vol":bf_1_last_back_vol,"lowest_back_price":bf_1_lowest_back_odds,"lowest_back_vol":bf_1_lowest_back_vol,"lay_price":bf_1_lay_odds,"lay_vol":bf_1_lay_vol},"bf_x_odds":{"last_back_price":bf_x_last_back_odds,"last_back_vol":bf_x_last_back_vol,"lowest_back_price":bf_x_lowest_back_odds,"lowest_back_vol":bf_x_lowest_back_vol,"lay_price":bf_x_lay_odds,"lay_vol":bf_x_lay_vol},"bf_2_odds":{"last_back_price":bf_2_last_back_odds,"last_back_vol":bf_2_last_back_vol,"lowest_back_price":bf_2_lowest_back_odds,"lowest_back_vol":bf_2_lowest_back_vol,"lay_price":bf_2_lay_odds,"lay_vol":bf_2_lay_vol},"bf_Under_2.5":{"last_back_price":b['back_25'][0][1],"last_back_vol":b['back_25'][0][2],"lowest_back_price":b['back_25'][0][3],"lowest_back_vol":b['back_25'][0][4],"lay_price":b['lay_25'][0][1],"lay_vol":b['lay_25'][0][1]},"bf_Over_2.5":{"last_back_price":b['back_25'][1][1],"last_back_vol":b['back_25'][1][2],"lowest_back_price":b['back_25'][1][3],"lowest_back_vol":b['back_25'][1][4],"lay_price":b['lay_25'][1][1],"lay_vol":b['lay_25'][1][1]},"bf_Under_3.5":{"last_back_price":b['back_35'][0][1],"last_back_vol":b['back_35'][0][2],"lowest_back_price":b['back_35'][0][3],"lowest_back_vol":b['back_35'][0][4],"lay_price":b['lay_35'][0][1],"lay_vol":b['lay_35'][0][1]},"bf_Over_3.5":{"last_back_price":b['back_35'][1][1],"last_back_vol":b['back_35'][1][2],"lowest_back_price":b['back_35'][1][3],"lowest_back_vol":b['back_35'][1][4],"lay_price":b['lay_35'][1][1],"lay_vol":b['lay_35'][1][1]},"bf_dnb_home":{"last_back_price":b['back_dnb'][0][1],"last_back_vol":b['back_dnb'][0][2],"lowest_back_price":b['back_dnb'][0][3],"lowest_back_vol":b['back_dnb'][0][4],"lay_price":b['lay_dnb'][0][1],"lay_vol":b['lay_dnb'][0][1]},"bf_dnb_away":{"last_back_price":b['back_dnb'][1][1],"last_back_vol":b['back_dnb'][1][2],"lowest_back_price":b['back_dnb'][1][3],"lowest_back_vol":b['back_dnb'][1][4],"lay_price":b['lay_dnb'][1][1],"lay_vol":b['lay_dnb'][1][1]}}
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
    

def do_insert_toto(toto_data,betfair_data,league):
    print("doing fuzzy and insert TOTO")

    
    #pull all bf matches, and subsequent team names.. for fuzzy match
    
    bf_data = betfair_data
    #convert into list of lists
    print("toto:",len(toto_data),"bf:",len(betfair_data),league)
    bf_matches=[]
    for b in bf_data:
        print("CHECK:",bf_data[b])
        try:
            if len(bf_data[b]['odds'])>0:
                back_25=[]
                lay_25=[]
                back_35=[]
                lay_35=[]
                back_dnb=[]
                lay_dnb=[]

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
                try:
                    back_35.append(["Under_3.5",bf_data[b]['markets'][2]['last_back_price_Under_3.5'],bf_data[b]['markets'][2]['last_back_vol_Under_3.5'],bf_data[b]['markets'][2]['lowest_back_price_Under_3.5'],bf_data[b]['markets'][2]['lowest_back_vol_Under_3.5']])
                    back_35.append(["Over_3.5",bf_data[b]['markets'][3]['last_back_price_Over_3.5'],bf_data[b]['markets'][3]['last_back_vol_Over_3.5'],bf_data[b]['markets'][3]['lowest_back_price_Over_3.5'],bf_data[b]['markets'][3]['lowest_back_vol_Over_3.5']])
                except:
                    pass
                try:
                    lay_35.append(["Under_3.5",bf_data[b]['markets'][2]['lay_price_Under_3.5'],bf_data[b]['markets'][2]['lay_vol_Under_3.5']])
                    lay_35.append(["Over_3.5",bf_data[b]['markets'][3]['lay_price_Over_3.5'],bf_data[b]['markets'][3]['lay_vol_Over_3.5']])
                except:
                    pass

                try:
                    back_dnb.append(["DNB_Home",bf_data[b]['markets'][4]['last_back_price_DNB_Home'],bf_data[b]['markets'][4]['last_back_vol_DNB_Home'],bf_data[b]['markets'][4]['lowest_back_price_DNB_Home'],bf_data[b]['markets'][4]['lowest_back_vol_DNB_Home']])
                    back_dnb.append(["DNB_Away",bf_data[b]['markets'][5]['last_back_price_DNB_Away'],bf_data[b]['markets'][5]['last_back_vol_DNB_Away'],bf_data[b]['markets'][5]['lowest_back_price_DNB_Away'],bf_data[b]['markets'][5]['lowest_back_vol_DNB_Away']])
                except:
                    print("err on dnb_home",bf_data[b]['markets'][4])
                    pass
                
                try:
                    lay_dnb.append(["DNB_Home",bf_data[b]['markets'][4]['lay_price_DNB_Home'],bf_data[b]['markets'][4]['lay_vol_DNB_Home']])
                    lay_dnb.append(["DNB_Away",bf_data[b]['markets'][5]['lay_price_DNB_Away'],bf_data[b]['markets'][5]['lay_vol_DNB_Away']])
                except:
                    pass

                bf_matches.append({"matchup":matchteams,"flipped":flipped,"matchup_raw":matchteams,"lay_book":lay_matchlist,"back_book":back_matchlist,"back_25":back_25,"lay_25":lay_25,"back_35":back_35,"lay_35":lay_35,"back_dnb":back_dnb,"lay_dnb":lay_dnb,'event_id':b,"timestamp":bf_data[b]['timestamp']})
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
                try:
                    insert_to_database_toto(t,b,league)
                except Exception as msg:
                    print("INSERT NOPE! TOTO..check the extra markets likely",str(msg))
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
