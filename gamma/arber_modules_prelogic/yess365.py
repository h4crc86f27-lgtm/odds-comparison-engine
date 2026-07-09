import pymysql
import configparser
import requests
import random
from arber_modules.utils import *
import time
from fuzzywuzzy import fuzz
import json
import concurrent.futures

thread_count=10
timeout_count=4


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


def pull_extra_markets_yess365(eventid):
    retval={"2.5":{"Over":0,"Under":0},
            "3.5":{"Over":0,"Under":0},
            "DNB":{"Home":0,"Away":0},
            "1x2_HT":{"1":0,"X":0,"2":0},
            "DC":{"1X":0,"12":0,"X2":0}
            }

    url="http://yess365.com/services/pregame/Pregame.Service.php"
    params = {"action":"get-data","type":"match-details","sport":"1","gamecode":str(eventid)}
    res = requests.post(url,data =params,proxies={"https":random.choice(proxies)})
    #print("yess_extra:",res.reason)

    markets = res.json()['DATA']['DATASET']['markets']
    #print("markets:",len(markets))
    try:
        #print("main:",markets.keys())
        #print("dnb:",markets['Draw No Bet']['odds'].keys())
        #print("uo25:",markets['Goal Line']['odds'].keys())
        retval['DNB']['Home']= round(float(markets['Draw No Bet']['odds']["1"]['valueDec'])/0.99,2)
        retval['DNB']['Away'] = round(float(markets['Draw No Bet']['odds']["2"]['valueDec'])/0.99,2)
        retval['2.5']['Over'] = round(float(markets['Goal Line']['odds']['Over 2.5']['valueDec'])/0.99,2)
        retval['2.5']['Under'] = round(float(markets['Goal Line']['odds']['Under 2.5']['valueDec'])/0.99,2)
    except Exception as msg:
        pass#print("yes extra err:",str(msg))

    return retval

def do_yess365_raw():
    ##unibet raw comp gatherer
    conn = pymysql.connect(host='localhost',user='local',passwd='oeijifjwejfio',db=db_name)
    cur  = conn.cursor()
    cur.execute("select * from raw_comps where site='yess365'")
    rows = cur.fetchall()
    ids_done=[]
    for row in rows:
        ids_done.append(row[2])

    url="http://yess365.com/services/pregame/Pregame.Service.php"
    params = {"action":"get-filters","type":"champs-by-sport","sport":"1","onlytoday":"false"}

    res = requests.post(url,data =params,proxies={"https":random.choice(proxies)})
    data = res.json()
    data = data['DATA']['DATASET']
    comps = []
    for nation in data:
        for comp in data[nation]:
            #comps.append([nation,comp['id'],comp['label']])
            if comp['id'] not in ids_done:
                x=cur.execute("insert into raw_comps(comp_name,comp_id,site,timestamp) values(%s,%s,%s,%s)",(comp['label'],comp['id'],"yess365",time.time()))

    conn.commit()
    conn.close()

def yess365_data_thread(e,events):
        #print("yes_thread:",events[e])
        outcomes=[]
        extra_markets=[]
        try:
            eid = events[e]['gamecode']
            timestamp = convert_yess_time(events[e]['gamedate'] + " " + events[e]['gametime']  + ":00")
            eventname= events[e]['teams']
            #print(eventname)
            home,away = events[e]['teams'].split("-")
            #print("Splat:",home,away)
            #away = events[e]['team2']
            
            markets  = events[e]['markets']
            outcomes.append({"name":home,"price":round(float(markets['point1']['valueDec'])/0.99,2)})
            outcomes.append({"name":"X","price":round(float(markets['pointX']['valueDec'])/0.99,2)})
            outcomes.append({"name":away,"price":round(float(markets['point2']['valueDec'])/0.99,2)})
        except Exception as msg:
            pass#print("yes outcomes err:",str(msg))

        
        #print(outcomes)

        for counter in range(3):
            try:
                other_markets = pull_extra_markets_yess365(eid)
        
                extra_markets.append({"name":"2.5_Under","price":other_markets['2.5']['Under']})
                extra_markets.append({"name":"2.5_Over","price":other_markets['2.5']['Over']})
                extra_markets.append({"name":"3.5_Under","price":other_markets['3.5']['Under']})
                extra_markets.append({"name":"3.5_Over","price":other_markets['3.5']['Over']})
                extra_markets.append({"name":"DNB_Home","price":other_markets['DNB']['Home']})
                extra_markets.append({"name":"DNB_Away","price":other_markets['DNB']['Away']})
                extra_markets.append({"name":"DC_1X","price":other_markets['DC']['1X']})
                extra_markets.append({"name":"DC_X2","price":other_markets['DC']['X2']})
                extra_markets.append({"name":"DC_12","price":other_markets['DC']['12']})
                extra_markets.append({"name":"1_HT","price":other_markets['1x2_HT']['1']})
                extra_markets.append({"name":"X_HT","price":other_markets['1x2_HT']['X']})
                extra_markets.append({"name":"2_HT","price":other_markets['1x2_HT']['2']})
                break
            except Exception as msg:
                pass#print("err in yess365 extra markets loop:",str(msg))#pass#try again

        #print ("yess365:",{"id":eid,"book":outcomes,"markets":extra_markets,"start_time":timestamp})
        return {"id":eid,"book":outcomes,"markets":extra_markets,"start_time":timestamp}


def pull_data_yess365(compid,league):

    #print("yess365 DATA >>>")
    comp_data=[]
    #compid=england/premier_league
    #premier league
    url="http://yess365.com/services/pregame/Pregame.Service.php"
    params={"action":"get-data","type":"matches","sport":"1","champs[]":str(compid),"sort":"date","offset":"0","src":"champ"}
    res = requests.post(url,data=params,proxies={"https":random.choice(proxies)})
    #print(res.reason)
    data = res.json()
    events = data['DATA']['DATASET']
    
    e_list=[]

    for e in range(0,len(events)):
        e_list.append([e,events])

    print("yess365 event_list_len:",len(e_list))

    with concurrent.futures.ThreadPoolExecutor(max_workers=thread_count) as executor:
        future_to_url = {executor.submit(yess365_data_thread, e[0],e[1]): e for e in e_list}
        for future in concurrent.futures.as_completed(future_to_url):
            #url = future_to_url[future]
            try:
                data = future.result()
                comp_data.append(data)
            except Exception as exc:
                pass#print('%r generated an exception: %s' % ("brr", exc))


   
    for cd in comp_data:
        try:
            do_odds_history_insert("yess365", cd['id'],cd['book'],cd['markets'])
        except Exception as msg:
            pass#print("err on odds history insert..",str(msg))  
    
    #with open("/home/arb_bot/beta_bingoal_fastbf/yess365_dumps/" +  league  + ".json","w") as f:
    #    f.write(json.dumps(comp_data))

    return comp_data

def get_team_list_yess365():
    #print("<building team list>")
    conn = pymysql.connect(host='localhost',user='local',passwd='oeijifjwejfio',db=db_name)
    cur  = conn.cursor()
    cur.execute("select yess365_name,betfair_name from yess365_teams")
    rows = cur.fetchall()
    teams={}
    for row in rows:
        teams[row[0].upper()]=row[1]
        teams[strip_accents(row[0]).upper()]=row[1]
    conn.close()
    #print("<team list built>")
    return teams

def insert_to_database_yess365(t,b,league):
    conn = pymysql.connect(host='localhost',user='local',passwd='oeijifjwejfio',db=db_name)
    cur  = conn.cursor()
    unibet_teamnames = t['matchup_raw']
    t1fuzzy,t2fuzzy=0,0
    
    #unibet section
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
    unibet_over_3p5=0
    unibet_under_3p5=0
    unibet_dnb_home=0
    unibet_dnb_away=0
    unibet_dc_1x=0
    unibet_dc_12=0
    unibet_dc_x2=0
    unibet_1_ht =0
    unibet_x_ht =0
    unibet_2_ht =0
    for outcome in t['markets']:
        if outcome['name']=='2.5_Over':
            unibet_over_2p5 = outcome['price']
        elif outcome['name']=='2.5_Under':
            unibet_under_2p5 = outcome['price']
        elif outcome['name']=='3.5_Over':
            unibet_over_3p5 = outcome['price']
        elif outcome['name']=='3.5_Under':
            unibet_under_3p5 = outcome['price']
        elif outcome['name']=='DNB_Home':
            if 0:#b['flipped']:#guess the dnb too
                unibet_dnb_away= outcome['price']
            else:
                unibet_dnb_home= outcome['price']
        elif outcome['name']=='DNB_Away':
            if 0:#b['flipped']:#guess the dnb too
                unibet_dnb_home = outcome['price']
            else:
                unibet_dnb_away= outcome['price']
        elif outcome['name']=='DC_1X':
            if 0:#b['flipped']:
                unibet_dc_x2 = outcome['price']
            else:
                unibet_dc_1x = outcome['price']
        elif outcome['name']=='DC_12':
            unibet_dc_12 = outcome['price']
        elif outcome['name']=='DC_X2':
            if 0:#b['flipped']:
                unibet_dc_1x = outcome['price']
            else:
                unibet_dc_x2 = outcome['price']
        elif outcome['name']=='1_HT':
            if 0:#b['flipped']:
                unibet_2_ht = outcome['price']
            else:
                unibet_1_ht = outcome['price']
        elif outcome['name']=='X_HT':
            unibet_x_ht = outcome['price']
        elif outcome['name']=='2_HT':
            if 0:#b['flipped']:
                unibet_1_ht = outcome['price']
            else:
                unibet_2_ht = outcome['price']
    #insert section
    odds_json={"yess365_1_odds":toto_1_odds,"yess365_x_odds":toto_x_odds,"yess365_2_odds":toto_2_odds,"yess365_over_2.5":unibet_over_2p5,"yess365_under_2.5":unibet_under_2p5,"yess365_over_3.5":unibet_over_3p5,"yess365_under_3.5":unibet_under_3p5,"yess365_dnb_home":unibet_dnb_home,"yess365_dnb_away":unibet_dnb_away,
            "yess365_dc_1x":unibet_dc_1x,"yess365_dc_12":unibet_dc_12,"yess365_dc_x2":unibet_dc_x2,
           "yess365_1_ht":unibet_1_ht,"yess365_x_ht":unibet_x_ht,"yess365_2_ht":unibet_2_ht,
           "bf_1_odds":{"vwap":b['vwaps']['1'],"last_back_price":bf_1_last_back_odds,"last_back_vol":bf_1_last_back_vol,"lowest_back_price":bf_1_lowest_back_odds,"lowest_back_vol":bf_1_lowest_back_vol,"lay_price":bf_1_lay_odds,"lay_vol":bf_1_lay_vol},
           "bf_x_odds":{"vwap":b['vwaps']['X'],"last_back_price":bf_x_last_back_odds,"last_back_vol":bf_x_last_back_vol,"lowest_back_price":bf_x_lowest_back_odds,"lowest_back_vol":bf_x_lowest_back_vol,"lay_price":bf_x_lay_odds,"lay_vol":bf_x_lay_vol},
           "bf_2_odds":{"vwap":b['vwaps']['2'],"last_back_price":bf_2_last_back_odds,"last_back_vol":bf_2_last_back_vol,"lowest_back_price":bf_2_lowest_back_odds,"lowest_back_vol":bf_2_lowest_back_vol,"lay_price":bf_2_lay_odds,"lay_vol":bf_2_lay_vol},
           "bf_Under_2.5":{"vwap":b['vwaps']['Under_2.5'],"last_back_price":b['back_25'][0][1],"last_back_vol":b['back_25'][0][2],"lowest_back_price":b['back_25'][0][3],"lowest_back_vol":b['back_25'][0][4],"lay_price":b['lay_25'][0][1],"lay_vol":b['lay_25'][0][2]},
           "bf_Over_2.5":{"vwap":b['vwaps']['Over_2.5'],"last_back_price":b['back_25'][1][1],"last_back_vol":b['back_25'][1][2],"lowest_back_price":b['back_25'][1][3],"lowest_back_vol":b['back_25'][1][4],"lay_price":b['lay_25'][1][1],"lay_vol":b['lay_25'][1][2]},
           "bf_Under_3.5":{"vwap":b['vwaps']['Under_3.5'],"last_back_price":b['back_35'][0][1],"last_back_vol":b['back_35'][0][2],"lowest_back_price":b['back_35'][0][3],"lowest_back_vol":b['back_35'][0][4],"lay_price":b['lay_35'][0][1],"lay_vol":b['lay_35'][0][2]},
           "bf_Over_3.5":{"vwap":b['vwaps']['Over_3.5'],"last_back_price":b['back_35'][1][1],"last_back_vol":b['back_35'][1][2],"lowest_back_price":b['back_35'][1][3],"lowest_back_vol":b['back_35'][1][4],"lay_price":b['lay_35'][1][1],"lay_vol":b['lay_35'][1][2]},
           "bf_dnb_home":{"vwap":b['vwaps']['DNB_Home'],"last_back_price":b['back_dnb'][0][1],"last_back_vol":b['back_dnb'][0][2],"lowest_back_price":b['back_dnb'][0][3],"lowest_back_vol":b['back_dnb'][0][4],"lay_price":b['lay_dnb'][0][1],"lay_vol":b['lay_dnb'][0][2]},
           "bf_dnb_away":{"vwap":b['vwaps']['DNB_Away'],"last_back_price":b['back_dnb'][1][1],"last_back_vol":b['back_dnb'][1][2],"lowest_back_price":b['back_dnb'][1][3],"lowest_back_vol":b['back_dnb'][1][4],"lay_price":b['lay_dnb'][1][1],"lay_vol":b['lay_dnb'][1][2]},
           "bf_1_ht":{"vwap":b['vwaps']['1_HT'],"last_back_price":b['back_ht'][0][1],"last_back_vol":b['back_ht'][0][2],"lowest_back_price":b['back_ht'][0][3],"lowest_back_vol":b['back_ht'][0][4],"lay_price":b['lay_ht'][0][1],"lay_vol":b['lay_ht'][0][2]},
           "bf_2_ht":{"vwap":b['vwaps']['2_HT'],"last_back_price":b['back_ht'][1][1],"last_back_vol":b['back_ht'][1][2],"lowest_back_price":b['back_ht'][1][3],"lowest_back_vol":b['back_ht'][1][4],"lay_price":b['lay_ht'][1][1],"lay_vol":b['lay_ht'][1][2]},
           "bf_x_ht":{"vwap":b['vwaps']['X_HT'],"last_back_price":b['back_ht'][2][1],"last_back_vol":b['back_ht'][2][2],"lowest_back_price":b['back_ht'][2][3],"lowest_back_vol":b['back_ht'][2][4],"lay_price":b['lay_ht'][2][1],"lay_vol":b['lay_ht'][2][2]},
           "bf_dc_1x":{"vwap":b['vwaps']['DC_1X'],"last_back_price":b['back_dc'][0][1],"last_back_vol":b['back_dc'][0][2],"lowest_back_price":b['back_dc'][0][3],"lowest_back_vol":b['back_dc'][0][4],"lay_price":b['lay_dc'][0][1],"lay_vol":b['lay_dc'][0][2]},
           "bf_dc_x2":{"vwap":b['vwaps']['DC_X2'],"last_back_price":b['back_dc'][1][1],"last_back_vol":b['back_dc'][1][2],"lowest_back_price":b['back_dc'][1][3],"lowest_back_vol":b['back_dc'][1][4],"lay_price":b['lay_dc'][1][1],"lay_vol":b['lay_dc'][1][2]},
           "bf_dc_12":{"vwap":b['vwaps']['DC_12'],"last_back_price":b['back_dc'][2][1],"last_back_vol":b['back_dc'][2][2],"lowest_back_price":b['back_dc'][2][3],"lowest_back_vol":b['back_dc'][2][4],"lay_price":b['lay_dc'][2][1],"lay_vol":b['lay_dc'][2][2]}}
    
    #here check for existing..
    cur.execute("select * from yess365_matches where yess365_event_id=%s and betfair_event_id=%s",(t['event_id'],b['event_id']))
    rows = cur.fetchall()
    if len(rows)>0:
        #print("found event,, updating",t['event_id'],b['event_id'])
        cur.execute("update yess365_matches set timestamp=%s,yess365_data=%s,t1_yess365_fuzzy=%s,t2_yess365_fuzzy=%s where yess365_event_id=%s and betfair_event_id=%s",
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

        cur.execute("insert into yess365_matches (timestamp,yess365_event_id,betfair_event_id,team_1_yess365,team_2_yess365,team_1_betfair,team_2_betfair,yess365_data,t1_yess365_fuzzy,t2_yess365_fuzzy,ignored,league) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (b['timestamp'],t['event_id'],b['event_id'],unibet_teamnames[0],unibet_teamnames[1],bf_teamnames[0],bf_teamnames[1],json.dumps(odds_json),t1fuzzy,t2fuzzy,0,league))
    conn.commit()
    conn.close()


def do_insert_yess365(unibet_data,betfair_data,league,unibet_teams):
    #global unibet_teams
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
                back_35=[]
                lay_35=[]
                back_dnb=[]
                lay_dnb=[]

                back_dc=[]
                lay_dc=[]

                back_ht=[]
                lay_ht=[]

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
                
                try:
                    back_35.append(["Under_3.5",bf_data[b]['markets'][2]['last_back_price_Under_3.5'],bf_data[b]['markets'][2]['last_back_vol_Under_3.5'],bf_data[b]['markets'][2]['lowest_back_price_Under_3.5'],bf_data[b]['markets'][2]['lowest_back_vol_Under_3.5']])
                    back_35.append(["Over_3.5",bf_data[b]['markets'][3]['last_back_price_Over_3.5'],bf_data[b]['markets'][3]['last_back_vol_Over_3.5'],bf_data[b]['markets'][3]['lowest_back_price_Over_3.5'],bf_data[b]['markets'][3]['lowest_back_vol_Over_3.5']])
                except:
                    back_35.append(["Under_3.5",0,0,0,0])
                    back_35.append(["Over_3.5",0,0,0,0])
                
                try:
                    lay_35.append(["Under_3.5",bf_data[b]['markets'][2]['lay_price_Under_3.5'],bf_data[b]['markets'][2]['lay_vol_Under_3.5']])
                    lay_35.append(["Over_3.5",bf_data[b]['markets'][3]['lay_price_Over_3.5'],bf_data[b]['markets'][3]['lay_vol_Over_3.5']])
                except:
                    lay_35.append(["Under_3.5",0,0])
                    lay_35.append(["Over_3.5",0,0])

                try:
                    back_dnb.append(["DNB_Home",bf_data[b]['markets'][4]['last_back_price_DNB_Home'],bf_data[b]['markets'][4]['last_back_vol_DNB_Home'],bf_data[b]['markets'][4]['lowest_back_price_DNB_Home'],bf_data[b]['markets'][4]['lowest_back_vol_DNB_Home']])
                    back_dnb.append(["DNB_Away",bf_data[b]['markets'][5]['last_back_price_DNB_Away'],bf_data[b]['markets'][5]['last_back_vol_DNB_Away'],bf_data[b]['markets'][5]['lowest_back_price_DNB_Away'],bf_data[b]['markets'][5]['lowest_back_vol_DNB_Away']])
                except:
                    #print("err on dnb_home",bf_data[b]['markets'][4])
                    back_dnb.append(["DNB_Home",0,0,0,0])
                    back_dnb.append(["DNB_Away",0,0,0,0])
 
                try:
                    lay_dnb.append(["DNB_Home",bf_data[b]['markets'][4]['lay_price_DNB_Home'],bf_data[b]['markets'][4]['lay_vol_DNB_Home']])
                    lay_dnb.append(["DNB_Away",bf_data[b]['markets'][5]['lay_price_DNB_Away'],bf_data[b]['markets'][5]['lay_vol_DNB_Away']])
                except:
                    lay_dnb.append(["DNB_Home",0,0])
                    lay_dnb.append(["DNB_Away",0,0])


                #DC
                try:
                    back_dc.append(["DC_1X",bf_data[b]['markets'][6]['last_back_price_DC_1X'],bf_data[b]['markets'][6]['last_back_vol_DC_1X'],bf_data[b]['markets'][6]['lowest_back_price_DC_1X'],bf_data[b]['markets'][6]['lowest_back_vol_DC_1X']])
                    back_dc.append(["DC_X2",bf_data[b]['markets'][7]['last_back_price_DC_X2'],bf_data[b]['markets'][7]['last_back_vol_DC_X2'],bf_data[b]['markets'][7]['lowest_back_price_DC_X2'],bf_data[b]['markets'][7]['lowest_back_vol_DC_X2']])
                    back_dc.append(["DC_12",bf_data[b]['markets'][8]['last_back_price_DC_12'],bf_data[b]['markets'][8]['last_back_vol_DC_12'],bf_data[b]['markets'][8]['lowest_back_price_DC_12'],bf_data[b]['markets'][8]['lowest_back_vol_DC_12']])
                
                except:
                    #print("err on dnb_home",bf_data[b]['markets'][4])
                    back_dc.append(["DC_1X",0,0,0,0])
                    back_dc.append(["DC_X2",0,0,0,0])
                    back_dc.append(["DC_12",0,0,0,0])
                    
 
                try:
                    lay_dc.append(["DC_1X",bf_data[b]['markets'][6]['lay_price_DC_1X'],bf_data[b]['markets'][6]['lay_vol_DC_1X']])
                    lay_dc.append(["DC_X2",bf_data[b]['markets'][7]['lay_price_DC_X2'],bf_data[b]['markets'][7]['lay_vol_DC_X2']])
                    lay_dc.append(["DC_12",bf_data[b]['markets'][8]['lay_price_DC_12'],bf_data[b]['markets'][8]['lay_vol_DC_12']])
                except:
                    lay_dc.append(["DC_1X",0,0])
                    lay_dc.append(["DC_X2",0,0])
                    lay_dc.append(["DC_12",0,0])

                #HT
                try:
                    #back_dc.append(["DC_1X",bf_data[b]['markets'][4]['last_back_price_DC_1X'],bf_data[b]['markets'][4]['last_back_price_DC_1X'],bf_data[b]['markets'][4]['last_back_price_DC_1X'],bf_data[b]['markets'][4]['last_back_price_DC_1X']])
                    back_ht.append(["1_HT",bf_data[b]['markets'][9]['last_back_price_1_HT'],bf_data[b]['markets'][9]['last_back_vol_1_HT'],bf_data[b]['markets'][9]['lowest_back_price_1_HT'],bf_data[b]['markets'][9]['lowest_back_vol_1_HT']])
                    back_ht.append(["2_HT",bf_data[b]['markets'][10]['last_back_price_2_HT'],bf_data[b]['markets'][10]['last_back_vol_2_HT'],bf_data[b]['markets'][10]['lowest_back_price_2_HT'],bf_data[b]['markets'][10]['lowest_back_vol_2_HT']])
                    back_ht.append(["X_HT",bf_data[b]['markets'][11]['last_back_price_X_HT'],bf_data[b]['markets'][11]['last_back_vol_X_HT'],bf_data[b]['markets'][11]['lowest_back_price_X_HT'],bf_data[b]['markets'][11]['lowest_back_vol_X_HT']])
                    
                except:
                    #print("err on dnb_home",bf_data[b]['markets'][4])
                    back_ht.append(["1_HT",0,0,0,0])
                    back_ht.append(["2_HT",0,0,0,0])
                    back_ht.append(["X_HT",0,0,0,0])
                    
 
                try:
                    lay_ht.append(["1_HT",bf_data[b]['markets'][9]['lay_price_1_HT'],bf_data[b]['markets'][9]['lay_vol_1_HT']])
                    lay_ht.append(["2_HT",bf_data[b]['markets'][10]['lay_price_2_HT'],bf_data[b]['markets'][10]['lay_vol_2_HT']])
                    lay_ht.append(["X_HT",bf_data[b]['markets'][11]['lay_price_X_HT'],bf_data[b]['markets'][11]['lay_vol_X_HT']])
                except:
                    lay_ht.append(["1_HT",0,0])
                    lay_ht.append(["2_HT",0,0])
                    lay_ht.append(["X_HT",0,0])
                try:
                    vwaps={"1":bf_data[b]['vwaps']['1'],"X":bf_data[b]['vwaps']['X'],"2":bf_data[b]['vwaps']['2'],
                    "Under_2.5":bf_data[b]['vwaps']['Under_2.5'],"Over_2.5":bf_data[b]['vwaps']['Over_2.5'],
                    "Under_3.5":bf_data[b]['vwaps']['Under_3.5'],"Over_3.5":bf_data[b]['vwaps']['Over_3.5'],
                    "DNB_Home":bf_data[b]['vwaps']['DNB_Home'],"DNB_Away":bf_data[b]['vwaps']['DNB_Away'],
                    "DC_1X":bf_data[b]['vwaps']['DC_1X'],"DC_X2":bf_data[b]['vwaps']['DC_X2'],"DC_12":bf_data[b]['vwaps']['DC_12'],
                    "1_HT":bf_data[b]['vwaps']['1_HT'],"X_HT":bf_data[b]['vwaps']['X_HT'],"2_HT":bf_data[b]['vwaps']['2_HT']}
                    #print("VWAP DICT:",vwaps)
                except Exception as msg:
                    pass#print("VWAP ERROR:",str(msg))

                bf_matches.append({"matchup":matchteams,"flipped":flipped,"matchup_raw":matchteams,"lay_book":lay_matchlist,"back_book":back_matchlist,"back_25":back_25,"lay_25":lay_25,"back_35":back_35,"lay_35":lay_35,"back_dnb":back_dnb,"lay_dnb":lay_dnb,"back_dc":back_dc,"lay_dc":lay_dc,"back_ht":back_ht,"lay_ht":lay_ht,"vwaps":vwaps,'event_id':b,"timestamp":bf_data[b]['timestamp']})
 #print("BF>>",{"matchup":matchteams,"flipped":flipped,"matchup_raw":matchteams,"lay_book":lay_matchlist,"back_book":back_matchlist,'event_id':b,"timestamp":bf_data[b]['timestamp']})
        except Exception as msg:
            #print("err on betfair match check:",teama,teamb,str(msg))
            try:
                #print(str(msg),"err on betfair (ub) match check:",teama,teamb)
                insert_error(str(msg),"err on betfair (yess365) match check:",teama,teamb,str(msg))
            except Exception as msg:
                pass#print(">>> unibet insert err error..",str(msg))

            

    #for b in bf_matches:
    #    print(b)

    #print("------------------------>")
    
    tt_data = unibet_data#pickle.load(f)

    #here pull from db, and whittle down to unique,, then create the list..
    #toto_teams = get_team_list_toto()
    #unibet_teams = get_team_list_unibet()

    #print("there are:",len(unibet_teams),"teams")   

    bf_teams=[]
    for b in bf_data:
        for name in bf_data[b]['name'].split(" v "):
            bf_teams.append(name)
    bf_teams=list(set(bf_teams))

    tt_matches=[]
    #conn = pymysql.connect(host='localhost',user='local',passwd='oeijifjwejfio',db=db_name)
    #cur = conn.cursor()
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
                        if r>maxfuzz and r>=40:
                            maxfuzz=r
                            likely_team=b
                            if r>85:
                                break
                    #try:
                    #    cur.execute("insert into unibet_teams (unibet_name,betfair_name) values(%s,%s)",(runner['name'],likely_team))
                    #    conn.commit()
                    #except:
                    #    pass
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
    #conn.close()

    #for t in tt_matches:
    #    print("unibet",t)
    found=0
    for t in tt_matches:
        found=0
        for b in bf_matches:
            #print("<><><>",t['matchup'],b['matchup'],t['start_time'][0:10],int(b['timestamp']),str(datetime.datetime.utcfromtimestamp(int(b['timestamp'])).strftime('%Y-%m-%d %H:%M:%S'))[0:10])
            #print("date match:",t['start_time'][0:10],str(datetime.datetime.utcfromtimestamp(int(b['timestamp'])).strftime('%Y-%m-%d %H:%M:%S'))[0:10])
            
            if t['matchup']==b['matchup'] and convert_midnight(t['start_time'])==str(datetime.datetime.utcfromtimestamp(int(b['timestamp'])).strftime('%Y-%m-%d %H:%M:%S'))[0:10]:
                
                insert_to_database_yess365(t,b,league)
                found=1
                break
            else:
                pass#print("UNMATCHED<<<<<",t['matchup'],b['matchup'],t['start_time'][0:10],int(b['timestamp']),str(datetime.datetime.utcfromtimestamp(int(b['timestamp'])).strftime('%Y-%m-%d %H:%M:%S'))[0:10])
            
                
    if not found:
        #print("NOT MATCHED:",t['matchup'],b['matchup'])
        conn = pymysql.connect(host='localhost',user='local',passwd='oeijifjwejfio',db=db_name)
        cur  = conn.cursor()
        #print("select * from unmatched where start_time=%s and team1=%s and team2=%s",(t['start_time'],t['matchup_raw'][0],t['matchup_raw'][1]))

        cur.execute("select * from yess365_unmatched where start_time=%s and team1=%s and team2=%s",(t['start_time'],t['matchup_raw'][0],t['matchup_raw'][1]))
        rows =cur.fetchall()
        if len(rows)==0:
            cur.execute("insert into yess365_unmatched (team1,team2,league,start_time,timestamp) values(%s,%s,%s,%s,%s)",(t['matchup_raw'][0],t['matchup_raw'][1],league,t['start_time'],time.time()))
            conn.commit()
        conn.close()  