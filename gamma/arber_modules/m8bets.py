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
from bs4 import BeautifulSoup
import random
import pickle


def rand_r():
    # Generate a random 10-digit number
    ten_digit_number = random.randint(10**9, (10**10)-1)

    # Print the 10-digit number
    return str(ten_digit_number)



#ust="20220830203345945f4cc83391633e0ee596df36ace1e0499741ade97c1f9b691e7a5cced59a3f"
#users="01d009000000fYxPOW3dt52ZvBERny9bluh5uzVKMmn9EkI62O"
#hjs="eyJpZCI6ImM1OGMzNjJhLTUzZDAtNTAyMy05M2I4LTYyYWU2OWRhNzA0NCIsImNyZWF0ZWQiOjE2NjA4NzAwNzUyODAsImV4aXN0aW5nIjp0cnVlfQ=="

#cookie="ust=" + ust + "; cookieMode=all; lastType=1; menuArr=m_SOCCER_GB%7Cm_SOCCER%7Cm_SOCCER_ES%7Cm_SOCCER_JP; _ga_3G40M6Y9V9=GS1.1.1661502360.13.0.1661502360.0.0.0; _ga=GA1.2.1347652800.1660797748; _fbp=fb.1.1660817969593.1136747434; _hjSessionUser_2935299=" + hjs + "; liveMenuArr=m_SOCCER; _gid=GA1.2.627081937.1661482008; CSPSESSIONID-SP-80-UP-=" + users + "; lastBets=; spoMenu=37"

#b_headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br', 'Accept-Language': 'en-US,en;q=0.5', 'Cache-Control': 'no-cache', 'Connection': 'keep-alive', 'Content-Length': '64', 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'Cookie': cookie, 'Host': 'www.m8bets.nl', 'Origin': 'https://www.m8bets.nl', 'Pragma': 'no-cache', 'Referer': 'https://www.m8bets.nl/nl/Sport', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:103.0) Gecko/20100101 Firefox/103.0', 'X-Requested-With': 'XMLHttpRequest'}
#k_code="3015"

thread_count=1
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


def do_m8bets_raw():
    pass


def pull_data(data):
    #print("--in pulldata--")
    input_format = '%m/%d/%Y %H:%M:%S'
    if data[-2]==1:# use first id..
        matchid = data[0]
    else: # use last ID
        matchid = data[-1]
        
    #compid = data[2]
    compname = data[4]
    timestamp = datetime.datetime.strptime(data[-16], input_format)- datetime.timedelta(hours=8) # this is in UTC+8
    home_team = data[9]
    away_team = data[10]
    if data[19]==2.5:
        over_25 = round(data[92]/10,2)
        if over_25>0 and over_25<1:
            #add 1..
            over_25+=1
        elif over_25<0:
            over_25 = 3+over_25
        under_25 = round(data[93]/10,2)
        if under_25>0 and under_25<1:
            #add 1..
            under_25+=1
        elif under_25<0:
            under_25 = 3+under_25
    else:
        over_25=0
        under_25=0
        
    home_odds,draw_odds,away_odds = [float(d) for d in data[67:70]]
    return {"matchid":matchid,
            "compname":compname,
            "datetime":timestamp,
            "match":home_team  + " v " + away_team,
            "1x2_odds":[home_odds,draw_odds,away_odds],
            "totals_odds":[round(over_25,2),round(under_25,2)]
            }


#with open("/Users/61448/Desktop/freelance/dutch_dave/m8json.txt") as f:
#    txt =f.read()

matches=0

def pull_m8bets_pages():
    match_data={}

    headers={"user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"}
    #clear header
    #
    r = random
    #href_early="https://m8bets.net/_View/svPage/RMOdds1Gen.ashx?ov=0&ot=e&tf=2&TFStatus=0&update=false&r=" + rand_r() + "&mt=0&wd=&ia=0&isWC=False&isSiteFav=False&LID="
    href_early="https://m8bets.net/_View/svPage/RMOdds1Gen.ashx?ov=0&ot=e&tf=2&TFStatus=0&update=false&r=" + rand_r() + "&mt=0&wd=&ia=2&isWC=False&isSiteFav=False&LID="
    res = requests.get(href_early,headers=headers,proxies = {"https":random.choice(proxies)},timeout=5)
    txt = res.text
    
    sof = txt.find("],[],[")+6
    txt = txt[sof:]

    #clear footer
    eof = txt.find("],[],[[")
    txt = txt[:eof]

    # replace font tag..
    txt = txt.replace('<font color=red>LIVE<\/font color>','')

    txt = txt.replace("'",'"').replace(" ,",",").strip()

    lines = txt.split("],[")


    #
    href_today ="https://m8bets.net/_View/svPage/RMOdds1Gen.ashx?ov=0&ot=t&tf=-1&TFStatus=0&update=false&r=" + rand_r() + "&mt=0&wd=&ia=0&isWC=False&isSiteFav=False"

    res = requests.get(href_today,headers=headers,proxies = {"https":random.choice(proxies)},timeout=5)
    txt = res.text
    
    sof = txt.find("],[],[")+6
    txt = txt[sof:]

    #clear footer
    eof = txt.find("],[],[[")
    txt = txt[:eof]

    # replace font tag..
    txt = txt.replace('<font color=red>LIVE<\/font color>','')

    txt = txt.replace("'",'"').replace(" ,",",").strip()

    for line in txt.split("],["):
        lines.append(line)
        
    with open("/home/arb_bot/gamma/m8bet_lines.raw.pickle","wb") as f:
        pickle.dump(lines,f)

    for line in lines:
        data = json.loads("[" + line.replace("[","").replace("]","").strip() + "]")
        if len(data)==98:
            ret = pull_data(data)
            compname = ret['compname']

            #ret =  m8bets_data_process(ret)
            #print("--processed--")

            #here i check per comp first..
            if compname not in match_data:
                match_data[compname]={}
                
            if ret['match'] not in match_data[compname]:
                match_data[compname][ret['match']] = ret
            else:
                #update odds if non zero
                if ret['1x2_odds']!=[0,0,0]:
                    match_data[compname][ret['match']]['1x2_odds'] = ret['1x2_odds']
                if ret['totals_odds']!=[0,0]:
                    match_data[compname][ret['match']]['totals_odds'] = ret['totals_odds']
            #5match_data.append(data)
            #matches+=1
    #print(match_data)
    #print()

    return match_data#,lines


def m8bets_data_process(match_data):
    #b_headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br', 'Accept-Language': 'en-US,en;q=0.5', 'Cache-Control': 'no-cache', 'Connection': 'keep-alive', 'Content-Length': '64', 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'Cookie': cookie, 'Host': 'www.m8bets.nl', 'Origin': 'https://www.m8bets.nl', 'Pragma': 'no-cache', 'Referer': 'https://www.m8bets.nl/nl/Sport', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:103.0) Gecko/20100101 Firefox/103.0', 'X-Requested-With': 'XMLHttpRequest'}

    other_markets={"2.5":{"Over":match_data['totals_odds'][0],"Under":match_data['totals_odds'][1]},
                "3.5":{"Over":0,"Under":0},
                "DNB":{"Home":0,"Away":0},
                "1x2_HT":{"1":0,"X":0,"2":0},
                "DC":{"1X":0,"12":0,"X2":0}
                }

    outcomes = []
    extra_markets=[]
    home_team,away_team =match_data['match'].split(" v ")

    
    outcomes.append({"name":home_team,"price":match_data['1x2_odds'][0]})
    outcomes.append({"name":"X","price":match_data['1x2_odds'][1]})
    outcomes.append({"name":away_team,"price":match_data['1x2_odds'][2]})
    

    extra_markets.append({"name":"2.5_Under","price":other_markets['2.5']['Under']})
    extra_markets.append({"name":"2.5_Over","price":other_markets['2.5']['Over']})
    extra_markets.append({"name":"3.5_Under","price":other_markets['3.5']['Under']})
    extra_markets.append({"name":"3.5_Over","price":other_markets['3.5']['Over']})
    extra_markets.append({"name":"DNB_Home","price":other_markets['DNB']['Home']})
    extra_markets.append({"name":"DNB_Away","price":other_markets['DNB']['Away']})
    extra_markets.append({"name":"DC_1X","price":other_markets['DC']['1X']})
    extra_markets.append({"name":"DC_12","price":other_markets['DC']['12']})
    extra_markets.append({"name":"DC_X2","price":other_markets['DC']['X2']})
    extra_markets.append({"name":"1_HT","price":other_markets['1x2_HT']['1']})
    extra_markets.append({"name":"X_HT","price":other_markets['1x2_HT']['X']})
    extra_markets.append({"name":"2_HT","price":other_markets['1x2_HT']['2']})


    #print({"id":matchid,"book":outcomes,"markets":extra_markets,"start_time":convert_euro_time(matchtime.replace(" ","T"))})
    return {"id":match_data['matchid'],"book":outcomes,"markets":extra_markets,"start_time":match_data['datetime']}



def pull_data_m8bets():#add comp_data as mutable param
    #print("DOING M8BETS DATA PULL!!")
    output_data={}

    comp_data = pull_m8bets_pages()
    
    #now need to go through, and convert to normal comp data format..
    for cd in comp_data:
        if cd not in output_data:
            output_data[cd]=[]
        for match in comp_data[cd]:
            output_data[cd].append(m8bets_data_process(comp_data[cd][match]))
    
    #print("processed comp_data:")
    #print(output_data)
    #print()

    print("m8bets:",len(output_data))
    #print(output_data)
    return output_data




def insert_to_database_m8bets(t,b,league):
    
    conn = pymysql.connect(host='localhost',user='local',passwd='oeijifjwejfio',db=db_name)
    cur  = conn.cursor()
    toto_teamnames = t['matchup_raw']
    t1fuzzy,t2fuzzy=0,0
    #print("TOTO YO>>>>>>>>>>",t,b)
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
        elif outcome['name']=='DC_1X':
            if 0:#b['flipped']:
                toto_dc_x2 = outcome['price']
            else:
                toto_dc_1x = outcome['price']
        elif outcome['name']=='DC_12':
            toto_dc_12 = outcome['price']
        elif outcome['name']=='DC_X2':
            if 0:#b['flipped']:
                toto_dc_1x = outcome['price']
            else:
                toto_dc_x2 = outcome['price']
        elif outcome['name']=='1_HT':
            if 0:#b['flipped']:
                toto_2_ht = outcome['price']
            else:
                toto_1_ht = outcome['price']
        elif outcome['name']=='X_HT':
            toto_x_ht = outcome['price']
        elif outcome['name']=='2_HT':
            if 0:#b['flipped']:
                toto_1_ht = outcome['price']
            else:
                toto_2_ht = outcome['price']

    #insert sectionm8bets_matches
    #print("TOTO###",b)
    odds_json={"m8bets_1_odds":toto_1_odds,"m8bets_x_odds":toto_x_odds,"m8bets_2_odds":toto_2_odds,"m8bets_under_2.5":toto_under_2p5,"m8bets_over_2.5":toto_over_2p5,"m8bets_under_3.5":toto_under_3p5,"m8bets_over_3.5":toto_over_3p5,"m8bets_dnb_home":toto_dnb_home,"m8bets_dnb_away":toto_dnb_away,
               "m8bets_dc_1x":toto_dc_1x,"m8bets_dc_12":toto_dc_12,"m8bets_dc_x2":toto_dc_x2,
           "m8bets_1_ht":toto_1_ht,"m8bets_x_ht":toto_x_ht,"m8bets_2_ht":toto_2_ht,
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
    #print(">>>",odds_json)
    #here check for existing..
    cur.execute("select * from m8bets_matches where m8bets_event_id=%s and betfair_event_id=%s",(t['event_id'],b['event_id']))
    rows = cur.fetchall()
    if len(rows)>0:
        #print("found event,, updating",t['event_id'],b['event_id'])
        cur.execute("update m8bets_matches set timestamp=%s,m8bets_data=%s,t1_m8bets_fuzzy=%s,t2_m8bets_fuzzy=%s where m8bets_event_id=%s and betfair_event_id=%s",
                (b['timestamp'],json.dumps(odds_json),t1fuzzy,t2fuzzy,t['event_id'],b['event_id']))
        #print("inserted:",t['event_id'],b['event_id'])
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

            
        cur.execute("insert into m8bets_matches (timestamp,m8bets_event_id,betfair_event_id,team_1_m8bets,team_2_m8bets,team_1_betfair,team_2_betfair,m8bets_data,t1_m8bets_fuzzy,t2_m8bets_fuzzy,ignored,league) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (b['timestamp'],t['event_id'],b['event_id'],toto_teamnames[0],toto_teamnames[1],bf_teamnames[0],bf_teamnames[1],json.dumps(odds_json),t1fuzzy,t2fuzzy,0,league))
    conn.commit()
    conn.close()
    
def align_matches(book_data,ref_data,league):
    #here i run through,, so loop over book data,,
    books_left=[]
    matched=0
    total_bookdata=len(book_data)
    total_refdata = len(ref_data)
    

        
    # look for a single team exact match,, and a timestamp match..
    for bd in book_data:
        found=False
        match_data=[]
        if bd['book']==[]:
            continue
        for rd in ref_data:#this is a list not the dict version
            #print(abs(convert_string_timestamp(bd['start_time'])- convert_string_timestamp(rd['start_time'])))
            if abs(bd['start_time'].timestamp()- convert_string_timestamp(rd['start_time']))<=20000:#within 30s of each other..
                #print("...inside 20k...")
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

                    print("inserting.. normal")
                    insert_to_database_m8bets(tt,rd,league)
                    
                    #print("inserting..",bd['book'],rd_teams)
                    matched+=1
                    break
        if not found:#
            #add this to the books_left..
            books_left.append(bd)

    unmatched=[]
    
    if len(books_left)>0:
        print("WOOKIE MODE:")
        for bd in books_left:
            
            found=False
            match_data=[]
            if bd['book'] ==[]:
                continue
            for rd in ref_data:

                if abs(bd['start_time'].timestamp()- convert_string_timestamp(rd['start_time']))<=20000:#within 10mins of each other..
                    #print("..inside wookie 20k..")
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
                        print("inserting..wookie")
                        insert_to_database_m8bets(tt,rd,league)
                    
            if not found:
                unmatched.append(bd)

def do_insert_m8bets(toto_data,betfair_data,league,toto_teams):
    #global toto_teams
    #print("doing fuzzy and insert m8bets")

    
    #pull all bf matches, and subsequent team names.. for fuzzy match
    
    #bf_data = betfair_data
    #convert into list of lists
    print("m8bets:",len(toto_data),"bf:",len(betfair_data),league)
    try:        
        if len(toto_data)>0 and len(betfair_data)>0:
            bf_data=convert_ref_matches(betfair_data)
            print(toto_data)
            align_matches(toto_data,bf_data,league)
    except Exception as msg:
        print("alignment error:",str(msg))