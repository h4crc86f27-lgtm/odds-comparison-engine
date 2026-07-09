import pymysql
import configparser
import requests
import random
import json
from arber_modules.utils import *
import time
from fuzzywuzzy import fuzz
import json
import concurrent.futures

thread_count=20

config = configparser.ConfigParser()
config.read('config.ini')
print(config.sections())
db_name="arb_db_beta"#db_name = config['DEFAULT']['db_name']

with open("/home/arb_bot/proxies") as f:
    proxies = f.read().split("\n")

try:
    proxies.remove('')
except:
    pass




def do_qrbet_raw():
    conn = pymysql.connect(host='localhost',user='local',passwd='oeijifjwejfio',db=db_name)
    cur  = conn.cursor()
    cur.execute("select * from raw_comps where site='qrbet'")
    rows = cur.fetchall()
    ids_done=[]
    for row in rows:
        ids_done.append(row[1])

    comps={}
    url="https://qrbet.eu/Home/GetAllMatches"
    for counter in range(5):
        try:
            res = requests.get(url,proxies = {"https":random.choice(proxies)},timeout=3)
            data = res.json()
            break  
        except:
            pass
    main_leagues = data['leagues']
    for ml in main_leagues:
        cat_id = ml['betradarCategoryId']
        country = ml['name']
        for sl in ml['leagueList']:
            compid = sl['tournamentId']
            compname =sl['name']
            if compname not in ids_done:
                print("adding qrbet comp:",str(cat_id) + " " + compname)
                x=cur.execute("insert into raw_comps(comp_name,comp_id,site,timestamp,country) values(%s,%s,%s,%s,%s)",(compname,cat_id,"qrbet",time.time(),country))

        #if len(data)<300:
        #    break
    conn.commit()
    conn.close()
    #return comps



## QRBET


def pull_data_qrbet(compid,league):#country,tourny):
    #url = "https://qrbet.eu/Home/GetMatches?sportTypeId=1&betradarCategoryId=1&leagueName=" + comp_name + "&matchState=home&startIndex=0&orderByLeague=false"
    #url="https://qrbet.eu/Home/GetMatches?sportTypeId=1&betradarCategoryId=1&leagueName=Premier%20League&matchState=home&startIndex=0&orderByLeague=false"
    url="https://qrbet.eu/Home/GetMatches?sportTypeId=1&betradarCategoryId=" + str(compid) + "&leagueName=" + league + "&matchState=home&startIndex=0&orderByLeague=false"

    res = requests.get(url,proxies = {"https":random.choice(proxies)},timeout=3)
    #now i have all the matches for this comp..
    retval = []
    data = res.json()
    matches = data['matches']
    for match in matches:
        euro_start_time = convert_euro_time(match['europeanStartTime'])#GMT+2,, need it back two hours
        home = match['match']['homeTeam']
        away = match['match']['awayTeam']
        odds = match['betState']
        #1x2 odds.. 0 is draw.
        homeOdds = int(odds['matchOdds102']['o1'])/100
        drawOdds = int(odds['matchOdds102']['o0'])/100
        awayOdds = int(odds['matchOdds102']['o2'])/100
        #dnb
        dnbHome=int(odds['drawNoBet12']['o1'])/100
        dnbAway=int(odds['drawNoBet12']['o2'])/100
        
        #uo2.5
        uo25_under=int(odds['matchOddsOU']['under'])/100
        uo25_over=int(odds['matchOddsOU']['over'])/100
        uo25_threshold = odds['matchOddsOU']['threshold']/10
        if uo25_threshold!=2.5:
            #print("@#(573258#@)%*@#%*#@)%&#@)%&#@)%#@)%&",uo25_threshold,"not correct uo2.5 !!!!!!!!!!!!! setting to zero for now")
            uo25_under=0
            uo25_over=0

        #uo3.5 - this might need tweaking,, depending on the name of this market json
        uo35_under=int(odds['matchOdds3rdOU']['under'])/100
        uo35_over=int(odds['matchOdds3rdOU']['over'])/100
        uo35_threshold = odds['matchOdds3rdOU']['threshold']/10
        if uo35_threshold!=3.5:
            #print("@#(573258#@)%*@#%*#@)%&#@)%&#@)%#@)%&",uo35_threshold,"not correct uo3.5 !!!!!!!!!!!!! setting to zero for now")
            uo35_under=0
            uo35_over=0
        #DC
        dc_12=int(odds['doubleChanceOdds102']['o0'])/100
        dc_1x=int(odds['doubleChanceOdds102']['o1'])/100
        dc_x2=int(odds['doubleChanceOdds102']['o2'])/100

        #HT
        ht_x=int(odds['firstHalftimeOdds102']['o0'])/100
        ht_1=int(odds['firstHalftimeOdds102']['o1'])/100
        ht_2=int(odds['firstHalftimeOdds102']['o2'])/100


        outcomes=[]
        outcomes.append({"name":home,"price":homeOdds})
        outcomes.append({"name":"X","price":drawOdds})
        outcomes.append({"name":away,"price":awayOdds})

        extra_markets=[]
        extra_markets.append({"name":"2.5_Under","price":uo25_under})
        extra_markets.append({"name":"2.5_Over","price":uo25_over})
        extra_markets.append({"name":"3.5_Under","price":uo35_under})
        extra_markets.append({"name":"3.5_Over","price":uo35_over})
        extra_markets.append({"name":"DNB_Home","price":dnbHome})
        extra_markets.append({"name":"DNB_Away","price":dnbAway})
        extra_markets.append({"name":"DC_1X","price":dc_1x})
        extra_markets.append({"name":"DC_12","price":dc_12})
        extra_markets.append({"name":"DC_X2","price":dc_x2})
        extra_markets.append({"name":"1_HT","price":ht_1})
        extra_markets.append({"name":"X_HT","price":ht_x})
        extra_markets.append({"name":"2_HT","price":ht_2})

        match_data = {"id":match['id'],"book":outcomes,"markets":extra_markets,"start_time":euro_start_time}    
        retval.append(match_data)
        
        try:
            do_odds_history_insert("qrbet", match['id'],outcomes,extra_markets)
        except Exception as msg:
            pass#print("err on odds history insert..",str(msg))   
    return retval
    #return comp_data


def get_team_list_qrbet():
    #print("<building team list>")
    conn = pymysql.connect(host='localhost',user='local',passwd='oeijifjwejfio',db=db_name)
    cur  = conn.cursor()
    cur.execute("select qrbet_name,betfair_name from qrbet_teams")
    rows = cur.fetchall()
    teams={}
    for row in rows:
        teams[row[0].upper()]=row[1]
        teams[strip_accents(row[0]).upper()]=row[1]
    conn.close()
    #print("<team list built>")
    return teams


def insert_to_database_qrbet(t,b,league):
    conn = pymysql.connect(host='localhost',user='local',passwd='oeijifjwejfio',db=db_name)
    cur  = conn.cursor()
    qrbet_teamnames = t['matchup_raw']
    #print("QRBET INSERT AREA:::",t,b)
    t1fuzzy,t2fuzzy=0,0
    
    #book section
    for runner in t['book']:
        if runner[0]==t['matchup'][0]:
            qrbet_1_odds=runner[1]
            if runner[2]==1:
                t1fuzzy=1
        elif runner[0]==t['matchup'][1]:
            qrbet_2_odds=runner[1]
            if runner[2]==1:
                t2fuzzy=1
        else:
            qrbet_x_odds=runner[1]
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
        temp = qrbet_1_odds
        qrbet_1_odds = qrbet_2_odds
        qrbet_2_odds = temp
        temp = qrbet_teamnames[0]
        qrbet_teamnames[0] = qrbet_teamnames[1]
        qrbet_teamnames[1] = temp
        

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
    qrbet_over_2p5=0
    qrbet_under_2p5=0
    qrbet_over_3p5=0
    qrbet_under_3p5=0

    for outcome in t['markets']:
        if outcome['name']=='2.5_Over':
            qrbet_over_2p5 = outcome['price']
        elif outcome['name']=='2.5_Under':
            qrbet_under_2p5 = outcome['price']
        elif outcome['name']=='3.5_Under':
            qrbet_under_3p5 = outcome['price']
        elif outcome['name']=='3.5_Over':
            qrbet_over_3p5 = outcome['price']
        elif outcome['name']=='DNB_Home':
            qrbet_dnb_home = outcome['price']
        elif outcome['name']=='DNB_Away':
            qrbet_dnb_away = outcome['price']
        elif outcome['name']=='DC_1X':
            if 0:#b['flipped']:
                qrbet_dc_x2 = outcome['price']
            else:
                qrbet_dc_1x = outcome['price']
        elif outcome['name']=='DC_12':
            qrbet_dc_12 = outcome['price']
        elif outcome['name']=='DC_X2':
            if 0:#b['flipped']:
                qrbet_dc_1x = outcome['price']
            else:
                qrbet_dc_x2 = outcome['price']
        elif outcome['name']=='1_HT':
            if 0:#b['flipped']:
                qrbet_2_ht = outcome['price']
            else:
                qrbet_1_ht = outcome['price']
        elif outcome['name']=='X_HT':
            qrbet_x_ht = outcome['price']
        elif outcome['name']=='2_HT':
            if 0:#b['flipped']:
                qrbet_1_ht = outcome['price']
            else:
                qrbet_2_ht = outcome['price']
    #print("###",b)
    #insert section  here need to add the extra market odds..
    odds_json={"qrbet_1_odds":qrbet_1_odds,"qrbet_x_odds":qrbet_x_odds,"qrbet_2_odds":qrbet_2_odds,"qrbet_over_2.5":qrbet_over_2p5,"qrbet_under_2.5":qrbet_under_2p5,"qrbet_over_3.5":qrbet_over_3p5,"qrbet_under_3.5":qrbet_under_3p5,"qrbet_dnb_home":qrbet_dnb_home,"qrbet_dnb_away":qrbet_dnb_away,
               "qrbet_dc_1x":qrbet_dc_1x,"qrbet_dc_12":qrbet_dc_12,"qrbet_dc_x2":qrbet_dc_x2,
           "qrbet_1_ht":qrbet_1_ht,"qrbet_x_ht":qrbet_x_ht,"qrbet_2_ht":qrbet_2_ht,
               "bf_1_odds":{"last_back_price":bf_1_last_back_odds,"last_back_vol":bf_1_last_back_vol,"lowest_back_price":bf_1_lowest_back_odds,"lowest_back_vol":bf_1_lowest_back_vol,"lay_price":bf_1_lay_odds,"lay_vol":bf_1_lay_vol},
           "bf_x_odds":{"last_back_price":bf_x_last_back_odds,"last_back_vol":bf_x_last_back_vol,"lowest_back_price":bf_x_lowest_back_odds,"lowest_back_vol":bf_x_lowest_back_vol,"lay_price":bf_x_lay_odds,"lay_vol":bf_x_lay_vol},
           "bf_2_odds":{"last_back_price":bf_2_last_back_odds,"last_back_vol":bf_2_last_back_vol,"lowest_back_price":bf_2_lowest_back_odds,"lowest_back_vol":bf_2_lowest_back_vol,"lay_price":bf_2_lay_odds,"lay_vol":bf_2_lay_vol},
           "bf_Under_2.5":{"last_back_price":b['back_25'][0][1],"last_back_vol":b['back_25'][0][2],"lowest_back_price":b['back_25'][0][3],"lowest_back_vol":b['back_25'][0][4],"lay_price":b['lay_25'][0][1],"lay_vol":b['lay_25'][0][2]},
           "bf_Over_2.5":{"last_back_price":b['back_25'][1][1],"last_back_vol":b['back_25'][1][2],"lowest_back_price":b['back_25'][1][3],"lowest_back_vol":b['back_25'][1][4],"lay_price":b['lay_25'][1][1],"lay_vol":b['lay_25'][1][2]},
           "bf_Under_3.5":{"last_back_price":b['back_35'][0][1],"last_back_vol":b['back_35'][0][2],"lowest_back_price":b['back_35'][0][3],"lowest_back_vol":b['back_35'][0][4],"lay_price":b['lay_35'][0][1],"lay_vol":b['lay_35'][0][2]},
           "bf_Over_3.5":{"last_back_price":b['back_35'][1][1],"last_back_vol":b['back_35'][1][2],"lowest_back_price":b['back_35'][1][3],"lowest_back_vol":b['back_35'][1][4],"lay_price":b['lay_35'][1][1],"lay_vol":b['lay_35'][1][2]},
           "bf_dnb_home":{"last_back_price":b['back_dnb'][0][1],"last_back_vol":b['back_dnb'][0][2],"lowest_back_price":b['back_dnb'][0][3],"lowest_back_vol":b['back_dnb'][0][4],"lay_price":b['lay_dnb'][0][1],"lay_vol":b['lay_dnb'][0][2]},
           "bf_dnb_away":{"last_back_price":b['back_dnb'][1][1],"last_back_vol":b['back_dnb'][1][2],"lowest_back_price":b['back_dnb'][1][3],"lowest_back_vol":b['back_dnb'][1][4],"lay_price":b['lay_dnb'][1][1],"lay_vol":b['lay_dnb'][1][2]},
           "bf_1_ht":{"last_back_price":b['back_ht'][0][1],"last_back_vol":b['back_ht'][0][2],"lowest_back_price":b['back_ht'][0][3],"lowest_back_vol":b['back_ht'][0][4],"lay_price":b['lay_ht'][0][1],"lay_vol":b['lay_ht'][0][2]},
           "bf_2_ht":{"last_back_price":b['back_ht'][1][1],"last_back_vol":b['back_ht'][1][2],"lowest_back_price":b['back_ht'][1][3],"lowest_back_vol":b['back_ht'][1][4],"lay_price":b['lay_ht'][1][1],"lay_vol":b['lay_ht'][1][2]},
           "bf_x_ht":{"last_back_price":b['back_ht'][2][1],"last_back_vol":b['back_ht'][2][2],"lowest_back_price":b['back_ht'][2][3],"lowest_back_vol":b['back_ht'][2][4],"lay_price":b['lay_ht'][2][1],"lay_vol":b['lay_ht'][2][2]},
           "bf_dc_1x":{"last_back_price":b['back_dc'][0][1],"last_back_vol":b['back_dc'][0][2],"lowest_back_price":b['back_dc'][0][3],"lowest_back_vol":b['back_dc'][0][4],"lay_price":b['lay_dc'][0][1],"lay_vol":b['lay_dc'][0][2]},
           "bf_dc_x2":{"last_back_price":b['back_dc'][1][1],"last_back_vol":b['back_dc'][1][2],"lowest_back_price":b['back_dc'][1][3],"lowest_back_vol":b['back_dc'][1][4],"lay_price":b['lay_dc'][1][1],"lay_vol":b['lay_dc'][1][2]},
           "bf_dc_12":{"last_back_price":b['back_dc'][2][1],"last_back_vol":b['back_dc'][2][2],"lowest_back_price":b['back_dc'][2][3],"lowest_back_vol":b['back_dc'][2][4],"lay_price":b['lay_dc'][2][1],"lay_vol":b['lay_dc'][2][2]}}
      #print("<><><>",odds_json)



    #here check for existing..
    cur.execute("select * from qrbet_matches where qrbet_event_id=%s and betfair_event_id=%s",(t['event_id'],b['event_id']))
    rows = cur.fetchall()
    if len(rows)>0:
        #print("found qrbet event,, updating",t['event_id'],b['event_id'])
        cur.execute("update qrbet_matches set timestamp=%s,qrbet_data=%s,t1_qrbet_fuzzy=%s,t2_qrbet_fuzzy=%s where qrbet_event_id=%s and betfair_event_id=%s",
                (b['timestamp'],json.dumps(odds_json),t1fuzzy,t2fuzzy,t['event_id'],b['event_id']))
        #print("updated:",t['event_id'],b['event_id'])
    else:
        #print("NO event,, inserting",t['event_id'],b['event_id'])
        #here i do an extra ratio check on toto teams, because somehow are flipping sometimes..
        if fuzz.ratio(qrbet_teamnames[0],bf_teamnames[0])>fuzz.ratio(qrbet_teamnames[0],bf_teamnames[1]):
            pass#should be right 
        else:
            #print("flipping:",contra_teamnames[0],contra_teamnames[1])
            temp = qrbet_teamnames[0]
            qrbet_teamnames[0] = qrbet_teamnames[1]
            qrbet_teamnames[1] = temp

        cur.execute("insert into qrbet_matches (timestamp,qrbet_event_id,betfair_event_id,team_1_qrbet,team_2_qrbet,team_1_betfair,team_2_betfair,qrbet_data,t1_qrbet_fuzzy,t2_qrbet_fuzzy,ignored,league) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (b['timestamp'],t['event_id'],b['event_id'],qrbet_teamnames[0],qrbet_teamnames[1],bf_teamnames[0],bf_teamnames[1],json.dumps(odds_json),t1fuzzy,t2fuzzy,0,league))
    conn.commit()
    conn.close()


def do_insert_qrbet(qrbet_data,betfair_data,league,qrbet_teams):
    #global qrbet_teams
    #print("doing fuzzy and insert contra")

    
    #pull all bf matches, and subsequent team names.. for fuzzy match
    
    bf_data = betfair_data
    #convert into list of lists
    #print("contra:",len(contra_data),"bf:",len(betfair_data),league)
    bf_matches=[]
    for b in bf_data:
        try:
            if len(bf_data[b]['odds'])>0:

                back_matchlist=[]
                lay_matchlist=[]
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

                bf_matches.append({"matchup":matchteams,"flipped":flipped,"matchup_raw":matchteams,"lay_book":lay_matchlist,"back_book":back_matchlist,"back_25":back_25,"lay_25":lay_25,"back_35":back_35,"lay_35":lay_35,"back_dnb":back_dnb,"lay_dnb":lay_dnb,"back_dc":back_dc,"lay_dc":lay_dc,"back_ht":back_ht,"lay_ht":lay_ht,'event_id':b,"timestamp":bf_data[b]['timestamp']})
#print("BF>>",{"matchup":matchteams,"flipped":flipped,"matchup_raw":matchteams,"lay_book":lay_matchlist,"back_book":back_matchlist,'event_id':b,"timestamp":bf_data[b]['timestamp']})

        except Exception as msg:
            #print("err on betfair match check:",teama,teamb,str(msg))
            try:
                insert_error(str(msg),"err on betfair (qrbet) match check:",teama,teamb,str(msg))
            except Exception as msg:
                pass#print(">>> insert err error..",str(msg))

            
    #print("bf data check")
    #for b in bf_matches:
    #    print(b)

    #print("------------------------>")
    
    tt_data = qrbet_data#pickle.load(f)
    #print("CONTRA>>>>>>>")
    #print(tt_data[0])
    #print("<<<<<<<<")
    #here pull from db, and whittle down to unique,, then create the list..
    #toto_teams = get_team_list_toto()
    #contra_teams = get_team_list_contra()

    #print("there are:",len(contra_teams),"teams")   

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
                if runner['name'].upper() in qrbet_teams and qrbet_teams[runner['name'].upper()]!="":
                    match_data.append([qrbet_teams[runner['name'].upper()],runner['price'],0])
                    matchteams.append(qrbet_teams[runner['name'].upper()])
                else:
                    #fuzzy..
                    maxfuzz=0
                    likely_team=""
                    for b in bf_teams:
                        r=fuzz.ratio(b,runner['name'])
                        if r>maxfuzz and r>=40:
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
    #    print("contra",t)
    found=0
    for t in tt_matches:
        found=0
        for b in bf_matches:
            #print("<><><>",t['matchup'],b['matchup'],t['start_time'][0:10],int(b['timestamp']),str(datetime.datetime.utcfromtimestamp(int(b['timestamp'])).strftime('%Y-%m-%d %H:%M:%S'))[0:10])
            #print("date match:",t['start_time'][0:10],str(datetime.datetime.utcfromtimestamp(int(b['timestamp'])).strftime('%Y-%m-%d %H:%M:%S'))[0:10])
            
            if t['matchup']==b['matchup'] and convert_midnight(t['start_time'])==str(datetime.datetime.utcfromtimestamp(int(b['timestamp'])).strftime('%Y-%m-%d %H:%M:%S'))[0:10]:
                
                insert_to_database_qrbet(t,b,league)
                found=1
                break
            else:
                pass#print("UNMATCHED<<<<<",t['matchup'],b['matchup'],t['start_time'][0:10],int(b['timestamp']),str(datetime.datetime.utcfromtimestamp(int(b['timestamp'])).strftime('%Y-%m-%d %H:%M:%S'))[0:10])
            
                
    if not found:
        #print("NOT MATCHED:",t['matchup'],b['matchup'])
        conn = pymysql.connect(host='localhost',user='local',passwd='oeijifjwejfio',db=db_name)
        cur  = conn.cursor()
        #print("select * from unmatched where start_time=%s and team1=%s and team2=%s",(t['start_time'],t['matchup_raw'][0],t['matchup_raw'][1]))

        cur.execute("select * from qrbet_unmatched where start_time=%s and team1=%s and team2=%s",(t['start_time'],t['matchup_raw'][0],t['matchup_raw'][1]))
        rows =cur.fetchall()
        if len(rows)==0:
            cur.execute("insert into qrbet_unmatched (team1,team2,league,start_time,timestamp) values(%s,%s,%s,%s,%s)",(t['matchup_raw'][0],t['matchup_raw'][1],league,t['start_time'],time.time()))
            conn.commit()
        conn.close()    

