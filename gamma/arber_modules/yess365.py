import pymysql
import configparser
import requests
import random
from arber_modules.utils import *
import time
from fuzzywuzzy import fuzz
import json
import concurrent.futures

thread_count=2
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

    url="https://yess365.com/services/pregame/Pregame.Service.php"
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
            print("yes outcomes err:",str(msg))

        
        print(outcomes)

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
                print("err in yess365 extra markets loop:",str(msg))#pass#try again

        print ("yess365:",{"id":eid,"book":outcomes,"markets":extra_markets,"start_time":timestamp})
        return {"id":eid,"book":outcomes,"markets":extra_markets,"start_time":timestamp}


def pull_data_yess365(compid,league):

    print("yess365 DATA >>>",compid,league)
    comp_data=[]
    #compid=england/premier_league
    #premier league
    url="https://www.yess365.com/services/pregame/Pregame.Service.php"
    #params={"action":"get-data","type":"matches","sport":"1","champs[]":str(compid),"sort":"date","offset":"0","src":"champ"}
    params={"action": "get-data","type": "matches","sport": "1","champs[]": str(compid),"betype":"","sort": "champ","offset": "0","toFetchLive": "false","src": "champ"}
    res = requests.post(url,data=params,proxies={"https":random.choice(proxies)})
    print(res.reason)
    data = res.json()
    print(len(data['DATA']))
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
            pass#do_odds_history_insert("yess365", cd['id'],cd['book'],cd['markets'])
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


def align_matches(book_data,ref_data,league):
    #here i run through,, so loop over book data,,
    books_left=[]
    matched=0
    total_bookdata=len(book_data)
    total_refdata = len(ref_data)
    
    print("yess365_align:",total_bookdata,total_refdata)


        
    # look for a single team exact match,, and a timestamp match..
    for bd in book_data:
        found=False
        match_data=[]
        if bd['book']==[]:
            continue
        for rd in ref_data:#this is a list not the dict version
            #print(abs(convert_string_timestamp(bd['start_time'])- convert_string_timestamp(rd['start_time'])))
            if abs(convert_string_timestamp(bd['start_time'])- convert_string_timestamp(rd['start_time']))<=20000:#within 30s of each other..

                rd_teams_raw=[rd['matchup'][0],rd['matchup'][1]]
                rd_teams=[rd['matchup'][0].lower(),rd['matchup'][1].lower()]
                
                #print("matchdate aligned..testing..",bd['book'],rd_teams)
                book_names_lower = [bd['book'][0]['name'].lower(),bd['book'][1]['name'].lower(),bd['book'][2]['name'].lower()]
                book_names = [bd['book'][0]['name'],bd['book'][1]['name'],bd['book'][2]['name']]

                if book_names_lower[0]=="x" or book_names_lower[0]=="draw":
                    draw_index=0
                if book_names_lower[1]=="x" or book_names_lower[1]=="draw":
                    draw_index=1
                if book_names_lower[2]=="x" or book_names_lower[2]=="draw":
                    draw_index=2
                
                book_names_lower = remove_draw(book_names_lower)
                book_names = remove_draw(book_names)

                
                
                if len(set(book_names_lower).intersection(set(rd_teams)))>0:# in rd_teams or bd['book'][1]['name'].lower() in rd_teams or bd['book'][2]['name'].lower() in rd_teams:
                    found=True
                    ref_data.remove(rd)
                    if book_names_lower[0]==rd_teams[0]:
                        #straight match..
                        match_data.append([rd_teams_raw[0],bd['book'][0]['price'],0])
                        match_data.append(["X",bd['book'][draw_index]['price'],0])
                        match_data.append([rd_teams_raw[1],bd['book'][2]['price'],0])
                        
                    else:
                        #flipped
                        match_data.append([rd_teams_raw[1],bd['book'][0]['price'],0])
                        match_data.append(["X",bd['book'][draw_index]['price'],0])
                        match_data.append([rd_teams_raw[0],bd['book'][2]['price'],0])
                        
                    #now insert..
                    # this is the T insert part.. do i need to flip the match_data?
                    book_names.sort()
                    rd_teams_raw.sort()
                    
                    #ref
                    tt={"matchup":rd_teams_raw,"matchup_raw":book_names,"book":match_data,"markets":bd['markets'],'event_id':bd['id'],'start_time':bd['start_time']}

                    insert_to_database_yess365(tt,rd,league)
                    
                    #print("inserting..",bd['book'],rd_teams)
                    matched+=1
                    break
        if not found:#
            #add this to the books_left..
            books_left.append(bd)

    unmatched=[]
    
    if len(books_left)>0:
        #print("WOOKIE MODE:")
        for bd in books_left:
            
            found=False
            match_data=[]
            if bd['book'] ==[]:
                continue
            for rd in ref_data:
                if abs(convert_string_timestamp(bd['start_time'])- convert_string_timestamp(rd['start_time']))<=20000:#within 10mins of each other..
                    rd_teams_raw=[rd['matchup'][0],rd['matchup'][1]]
                    rd_teams=[rd['matchup'][0].lower(),rd['matchup'][1].lower()]
                    
                    #print("matchdate aligned..testing..",bd['book'],rd_teams)
                    book_names_lower = [bd['book'][0]['name'].lower(),bd['book'][1]['name'].lower(),bd['book'][2]['name'].lower()]
                    book_names = [bd['book'][0]['name'],bd['book'][1]['name'],bd['book'][2]['name']]

                    if book_names_lower[0]=="x" or book_names_lower[0]=="draw":
                        draw_index=0
                    if book_names_lower[1]=="x" or book_names_lower[1]=="draw":
                        draw_index=1
                    if book_names_lower[2]=="x" or book_names_lower[2]=="draw":
                        draw_index=2
                     
                    book_names_lower = remove_draw(book_names_lower)
                    book_names = remove_draw(book_names)

                    r00 = fuzz.ratio(book_names_lower[0],rd_teams[0])
                    r01 = fuzz.ratio(book_names_lower[0],rd_teams[1])
                    r10 = fuzz.ratio(book_names_lower[1],rd_teams[0])
                    r11 = fuzz.ratio(book_names_lower[1],rd_teams[1])
                    threshold=90
                    if (r00>threshold or book_names_lower[0].find(rd_teams[0])>-1 or rd_teams[0].find(book_names_lower[0])>-1 or  r01>threshold or book_names_lower[0].find(rd_teams[1])>-1 or rd_teams[1].find(book_names_lower[0])>-1 ) or  (r10>threshold or book_names_lower[1].find(rd_teams[0])>-1 or rd_teams[0].find(book_names_lower[1])>-1 or r11>threshold or book_names_lower[1].find(rd_teams[1])>-1  or rd_teams[1].find( book_names_lower[1])>-1):
                        #looks good for fuzz..
                        found=True
                        ref_data.remove(rd)
                        if r00>r01 or book_names_lower[0].find(rd_teams[0])>-1 or rd_teams[0].find(book_names_lower[0])>-1:#straight up match
                            match_data.append([rd_teams_raw[0],bd['book'][0]['price'],0])
                            match_data.append(["X",bd['book'][draw_index]['price'],0])
                            match_data.append([rd_teams_raw[1],bd['book'][2]['price'],0])
                        else:
                            #flipped..
                            match_data.append([rd_teams_raw[1],bd['book'][0]['price'],0])
                            match_data.append(["X",bd['book'][draw_index]['price'],0])
                            match_data.append([rd_teams_raw[0],bd['book'][2]['price'],0])
                        tt={"matchup":rd_teams_raw,"matchup_raw":book_names,"book":match_data,"markets":bd['markets'],'event_id':bd['id'],'start_time':bd['start_time']}
                        insert_to_database_yess365(tt,rd,league)
                    
            if not found:
                unmatched.append(bd)
                    

def do_insert_yess365(unibet_data,betfair_data,league,unibet_teams):
    #global unibet_teams
    #print("doing fuzzy and insert UNIBET")

    
    #pull all bf matches, and subsequent team names.. for fuzzy match
    
    bf_data = betfair_data
    #convert into list of lists
    
    try:        
        if len(unibet_data)>0 and len(betfair_data)>0:
            bf_data=convert_ref_matches(betfair_data)
            align_matches(unibet_data,bf_data,league)
    except Exception as msg:
        print("alignment error:",str(msg))