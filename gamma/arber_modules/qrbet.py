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


thread_count=10
timeout_count=4

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
            res = requests.get(url,proxies = {"https":random.choice(proxies)},timeout=timeout_count)
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
                #print("adding qrbet comp:",str(cat_id) + " " + compname)
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
    #print(compid)

    url="https://qrbet.eu/Home/GetMatches?sportTypeId=1&betradarCategoryId=" + str(compid['id']) + "&leagueName=" + compid['name'] + "&matchState=home&startIndex=0&orderByLeague=false"
    
    res = requests.get(url,proxies = {"https":random.choice(proxies)},timeout=timeout_count)
    #now i have all the matches for this comp..
    retval = []
    data = res.json()
    matches = data['matches']
    #print("qrbet match count:",league,len(matches))
    if len(matches)==0:
        #print("QRBET .. bailing on zero matches..",league)

        return {}
    for match in matches:
        #print("in match..")
        euro_start_time = convert_euro_time(match['europeanStartTime'])#GMT+2,, need it back two hours
        home = match['match']['homeTeam']
        away = match['match']['awayTeam']
        #print("teams")
        odds = match['betState']
        #print("odds")
        #1x2 odds.. 0 is draw.
        homeOdds = int(odds['matchOdds102']['o1'])/100
        drawOdds = int(odds['matchOdds102']['o0'])/100
        awayOdds = int(odds['matchOdds102']['o2'])/100
        #print("matchods..")
        #dnb
        try:
            dnbHome=int(odds['drawNoBet12']['o1'])/100
            dnbAway=int(odds['drawNoBet12']['o2'])/100
        except:
            dnbHome=0
            dnbAway=0

        #uo2.5
        try:
            uo25_under=int(odds['matchOddsOU']['under'])/100
            uo25_over=int(odds['matchOddsOU']['over'])/100
            uo25_threshold = odds['matchOddsOU']['threshold']/10
            if uo25_threshold!=2.5:
                #print("@#(573258#@)%*@#%*#@)%&#@)%&#@)%#@)%&",uo25_threshold,"not correct uo2.5 !!!!!!!!!!!!! setting to zero for now")
                uo25_under=0
                uo25_over=0
        except:
            uo25_under=0
            uo25_over=0

        #uo3.5 - this might need tweaking,, depending on the name of this market json
        try:
            uo35_under=int(odds['matchOdds3rdOU']['under'])/100
            uo35_over=int(odds['matchOdds3rdOU']['over'])/100
            uo35_threshold = odds['matchOdds3rdOU']['threshold']/10
            if uo35_threshold!=3.5:
                #print("@#(573258#@)%*@#%*#@)%&#@)%&#@)%#@)%&",uo35_threshold,"not correct uo3.5 !!!!!!!!!!!!! setting to zero for now")
                uo35_under=0
                uo35_over=0
        except:
            uo35_under=0
            uo35_over=0

        #DC
        try:
            dc_12=int(odds['doubleChanceOdds102']['o0'])/100
            dc_1x=int(odds['doubleChanceOdds102']['o1'])/100
            dc_x2=int(odds['doubleChanceOdds102']['o2'])/100
        except:
            dc_12=0
            dc_1x=0
            dc_x2=0

        #HT
        try:
            ht_x=int(odds['firstHalftimeOdds102']['o0'])/100
            ht_1=int(odds['firstHalftimeOdds102']['o1'])/100
            ht_2=int(odds['firstHalftimeOdds102']['o2'])/100
        except:
            ht_1=0
            ht_x=0
            ht_2=0


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
        #print("match json",match_data)
        retval.append(match_data)
        
        try:
            pass#do_odds_history_insert("qrbet", match['id'],outcomes,extra_markets)
        except Exception as msg:
            pass#print("err on odds history insert..",str(msg))   
    #print("dumping:")
    #with open("/home/arb_bot/beta_bingoal_fastbf/qr_dumps/" +  compid['name']  + ".json","w") as f:
    #    f.write(json.dumps(retval))

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

def align_matches(book_data,ref_data,league):
    #here i run through,, so loop over book data,,
    books_left=[]
    matched=0
    total_bookdata=len(book_data)
    total_refdata = len(ref_data)
    

    print("qrbet_align:",total_bookdata,total_refdata)
    
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

                    insert_to_database_qrbet(tt,rd,league)
                    
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
                        insert_to_database_qrbet(tt,rd,league)
                    
            if not found:
                unmatched.append(bd)

def do_insert_qrbet(qrbet_data,betfair_data,league,qrbet_teams):
    #global qrbet_teams
    #print("doing fuzzy and insert contra")

    
    #pull all bf matches, and subsequent team names.. for fuzzy match
    
    bf_data = betfair_data
    #convert into list of lists
    #print("contra:",len(contra_data),"bf:",len(betfair_data),league)
    try:        
        if len(qrbet_data)>0 and len(betfair_data)>0:
            bf_data=convert_ref_matches(betfair_data)
            align_matches(qrbet_data,bf_data,league)
    except Exception as msg:
        print("alignment error:",str(msg))
