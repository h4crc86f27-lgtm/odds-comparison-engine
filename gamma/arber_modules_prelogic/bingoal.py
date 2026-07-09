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
#ust="20220830203345945f4cc83391633e0ee596df36ace1e0499741ade97c1f9b691e7a5cced59a3f"
#users="01d009000000fYxPOW3dt52ZvBERny9bluh5uzVKMmn9EkI62O"
#hjs="eyJpZCI6ImM1OGMzNjJhLTUzZDAtNTAyMy05M2I4LTYyYWU2OWRhNzA0NCIsImNyZWF0ZWQiOjE2NjA4NzAwNzUyODAsImV4aXN0aW5nIjp0cnVlfQ=="

#cookie="ust=" + ust + "; cookieMode=all; lastType=1; menuArr=m_SOCCER_GB%7Cm_SOCCER%7Cm_SOCCER_ES%7Cm_SOCCER_JP; _ga_3G40M6Y9V9=GS1.1.1661502360.13.0.1661502360.0.0.0; _ga=GA1.2.1347652800.1660797748; _fbp=fb.1.1660817969593.1136747434; _hjSessionUser_2935299=" + hjs + "; liveMenuArr=m_SOCCER; _gid=GA1.2.627081937.1661482008; CSPSESSIONID-SP-80-UP-=" + users + "; lastBets=; spoMenu=37"

#b_headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br', 'Accept-Language': 'en-US,en;q=0.5', 'Cache-Control': 'no-cache', 'Connection': 'keep-alive', 'Content-Length': '64', 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'Cookie': cookie, 'Host': 'www.bingoal.nl', 'Origin': 'https://www.bingoal.nl', 'Pragma': 'no-cache', 'Referer': 'https://www.bingoal.nl/nl/Sport', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:103.0) Gecko/20100101 Firefox/103.0', 'X-Requested-With': 'XMLHttpRequest'}
#k_code="3015"

thread_count=20
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


def do_bingoal_raw():

    conn = pymysql.connect(host='127.0.0.1',user='local',passwd='oeijifjwejfio',db=db_name)
    cur  = conn.cursor()
    cur.execute("select * from raw_comps where site='bingoal'")
    rows = cur.fetchall()
    ids_done=[]
    for row in rows:
        ids_done.append(int(row[2]))

    
    #print("pulling bingoal homepage")
    res = requests.get("https://www.bingoal.nl/nl/Sport#",timeout=timeout_count,proxies = {"https":random.choice(proxies)})
    soup = BeautifulSoup(res.text)
    #print("..souping..")
    li = soup.find("li",attrs={"id":"m_SOCCER"})

    uls = li.findAll("ul")
    for ul in uls:
        lis = ul.findAll("li")
        country = lis[0].find("a").text
        for li in lis:
            sub_uls = li.findAll("ul")
            for sub_u in sub_uls:
                sub_lis = sub_u.findAll("li")
                for sl in sub_lis:
                    #comps.append([country,sl.text,sl.get("data-div")])
                    x=cur.execute("insert into raw_comps(comp_name,comp_id,site,timestamp,country) values(%s,%s,%s,%s,%s)",(sl.text.split("-")[0],sl.get("data-div"),"bingoal",time.time(),sl.get("id").split("_")[2]))
    #print("done bingoal raw")
    conn.commit()
    conn.close()




def bingoal_data_thread(eventid,session_cookies):
    global k_code,b_headers
    global bingoal_cookies
    #global kvalue,ust,b_session
    hjs="eyJpZCI6ImM1OGMzNjJhLTUzZDAtNTAyMy05M2I4LTYyYWU2OWRhNzA0NCIsImNyZWF0ZWQiOjE2NjA4NzAwNzUyODAsImV4aXN0aW5nIjp0cnVlfQ=="
    ust = session_cookies['ust']
    kvalue  = session_cookies['kvalue']
    b_session = session_cookies['b_session']
    cookie="ust=" + ust + "; cookieMode=all; lastType=1; menuArr=m_SOCCER_GB%7Cm_SOCCER%7Cm_SOCCER_ES%7Cm_SOCCER_JP; _ga_3G40M6Y9V9=GS1.1.1661502360.13.0.1661502360.0.0.0; _ga=GA1.2.1347652800.1660797748; _fbp=fb.1.1660817969593.1136747434; _hjSessionUser_2935299=" + hjs + "; liveMenuArr=m_SOCCER; _gid=GA1.2.627081937.1661482008; CSPSESSIONID-SP-80-UP-=" + b_session + "; lastBets=; spoMenu=37"
    b_headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br', 'Accept-Language': 'en-US,en;q=0.5', 'Cache-Control': 'no-cache', 'Connection': 'keep-alive', 'Content-Length': '64', 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'Cookie': cookie, 'Host': 'www.bingoal.nl', 'Origin': 'https://www.bingoal.nl', 'Pragma': 'no-cache', 'Referer': 'https://www.bingoal.nl/nl/Sport', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:103.0) Gecko/20100101 Firefox/103.0', 'X-Requested-With': 'XMLHttpRequest'}
    k_code=kvalue#"3015"

    params={'func': 'detail', 'snr': 'false', 'id': str(eventid), 'b': '1', 'ts': str(datetime.datetime.now())[0:19].replace("-",""), 'k': k_code}
    url="https://www.bingoal.nl/A/sport"
    #b_headers={'Cookie':'ust=202208190247397003b29f9cf40226e5fd09bb775187c96a15440c7c2aed7a0daa4206f4bead54; cookieMode=all; lastType=1; menuArr=m_SOCCER_GB%7Cm_SOCCER; _ga_3G40M6Y9V9=GS1.1.1660872628.6.1.1660872809.0.0.0; _ga=GA1.1.1347652800.1660797748; _gid=GA1.2.66422849.1660797757; _fbp=fb.1.1660817969593.1136747434; CSPSESSIONID-SP-80-UP-=002008000000arKSwG2mY0SSeDr_kR2Nzsj9DF_Mc8hXSnhoSX; lastBets=; spoMenu=; _hjSessionUser_2935299=eyJpZCI6ImM1OGMzNjJhLTUzZDAtNTAyMy05M2I4LTYyYWU2OWRhNzA0NCIsImNyZWF0ZWQiOjE2NjA4NzAwNzUyODAsImV4aXN0aW5nIjpmYWxzZX0=; liveMenuArr=m_SOCCER','Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8', 'Accept-Encoding': 'gzip, deflate, br', 'Accept-Language': 'en-US,en;q=0.5', 'Connection': 'keep-alive', 'Host': 'www.bingoal.nl', 'Sec-Fetch-Dest': 'document', 'Sec-Fetch-Mode': 'navigate', 'Sec-Fetch-Site': 'none', 'Sec-Fetch-User': '?1', 'Upgrade-Insecure-Requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:103.0) Gecko/20100101 Firefox/103.0'}
    headers=b_headers#
    res = requests.get(url,data=params,headers=headers,timeout=timeout_count,proxies = {"https":random.choice(proxies)})
    #print(eventid,res.reason,len(res.text))
    data =res.json()

    box = data['box']
    matchtime=data['box'][0]['relatedDate']
    match = box[0]['match']
    matchid =match['ID']
    homeTeam = match['team1']['name']
    awayTeam = match['team2']['name']


    cats =  match['categories']

    main_markets=None
    half_markets=None
    for cat in cats:
        if cat['name']=='Meest gespeeld':
            main_markets = cat['subbets']

        if cat['name']=="Helft":
            half_markets = cat['subbets']

        if main_markets:# and half_markets:
            break
        
        
    other_markets={"2.5":{"Over":0,"Under":0},
                "3.5":{"Over":0,"Under":0},
                "DNB":{"Home":0,"Away":0},
                "1x2_HT":{"1":0,"X":0,"2":0},
                "DC":{"1X":0,"12":0,"X2":0}
                }

    outcomes = []
    extra_markets=[]

    if main_markets:
        for market in main_markets:
            if market['name']=="1X2":
                outcomes.append({"name":market['tips'][0]['name'],"price":float(market['tips'][0]['odd'])})
                outcomes.append({"name":market['tips'][1]['name'],"price":float(market['tips'][1]['odd'])})
                outcomes.append({"name":market['tips'][2]['name'],"price":float(market['tips'][2]['odd'])})
            elif market['name']=="Dubbele kans":
                other_markets['DC'][market['tips'][0]['name']]=float(market['tips'][0]['odd'])
                other_markets['DC'][market['tips'][1]['name']]=float(market['tips'][1]['odd'])
                other_markets['DC'][market['tips'][2]['name']]=float(market['tips'][2]['odd'])
            elif market['name']=="Draw No Bet (geld terug indien gelijkspel)":
                other_markets['DNB'][str(market['tips'][0]['team']).replace("1","Home").replace("2","Away")]=float(market['tips'][0]['odd'])
                other_markets['DNB'][str(market['tips'][1]['team']).replace("1","Home").replace("2","Away")]=float(market['tips'][1]['odd'])
            elif market['name']=='Totaal aantal doelpunten':
                for tip in market['tips']:
                    if tip['sov'] in other_markets:
                        uo = tip['shortName'].split(" ")[0].replace("U","Under").replace("O","Over")
                        other_markets[tip['sov']][uo]=float(tip['odd'])

    if 0:#half_markets:
        for market in half_markets:
            if market['name']=='1e helft - 1X2':
                half_tips = market['tips']
                for ht in half_tips:
                    other_markets['1x2_HT'][ht['shortName']] = float(ht['odd'])

                break
                

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
    return {"id":matchid,"book":outcomes,"markets":extra_markets,"start_time":convert_euro_time(matchtime.replace(" ","T"))}


def pull_data_bingoal(compid,league,session_cookies):#add comp_data as mutable param
    
    global b_headers,k_code
    global bingoal_cookies
    #global kvalue,ust,b_session
    ust = session_cookies['ust']
    kvalue  = session_cookies['kvalue']
    b_session = session_cookies['b_session']
    
    hjs="eyJpZCI6ImM1OGMzNjJhLTUzZDAtNTAyMy05M2I4LTYyYWU2OWRhNzA0NCIsImNyZWF0ZWQiOjE2NjA4NzAwNzUyODAsImV4aXN0aW5nIjp0cnVlfQ=="
    cookie="ust=" + ust + "; cookieMode=all; lastType=1; menuArr=m_SOCCER_GB%7Cm_SOCCER%7Cm_SOCCER_ES%7Cm_SOCCER_JP; _ga_3G40M6Y9V9=GS1.1.1661502360.13.0.1661502360.0.0.0; _ga=GA1.2.1347652800.1660797748; _fbp=fb.1.1660817969593.1136747434; _hjSessionUser_2935299=" + hjs + "; liveMenuArr=m_SOCCER; _gid=GA1.2.627081937.1661482008; CSPSESSIONID-SP-80-UP-=" + b_session + "; lastBets=; spoMenu=37"
    b_headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br', 'Accept-Language': 'en-US,en;q=0.5', 'Cache-Control': 'no-cache', 'Connection': 'keep-alive', 'Content-Length': '64', 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'Cookie': cookie, 'Host': 'www.bingoal.nl', 'Origin': 'https://www.bingoal.nl', 'Pragma': 'no-cache', 'Referer': 'https://www.bingoal.nl/nl/Sport', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:103.0) Gecko/20100101 Firefox/103.0', 'X-Requested-With': 'XMLHttpRequest'}
    k_code=kvalue#"3015"
    #print(k_code,ust,b_session)

    #print(session_cookies)
    #bingoal_cookies["ust"]=session_cookies['ust']
    #bingoal_cookies["CSPSESSIONID-SP-80-UP-"]=session_cookies['b_session']
    #k_code = session_cookies['k_value']
    #
    #b_headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br', 'Accept-Language': 'en-US,en;q=0.5', 'Cache-Control': 'no-cache', 'Connection': 'keep-alive', 'Content-Length': '64', 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'Cookie': cookie, 'Host': 'www.bingoal.nl', 'Origin': 'https://www.bingoal.nl', 'Pragma': 'no-cache', 'Referer': 'https://www.bingoal.nl/nl/Sport', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:103.0) Gecko/20100101 Firefox/103.0', 'X-Requested-With': 'XMLHttpRequest'}


    #print("BINGOAL DATA >>>")
    params={
        "func": "sport",
        "action": "SOCCER",
        "id": str(compid),#EPL ID
        "ts": str(datetime.datetime.now())[0:19].replace("-",""),# << DOES THIS MATTER? just make it now timestamps
        "k": k_code#CAT/COUNTRY ID?
    }


    url="https://www.bingoal.nl/A/sport"
    
    #headers={'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br', 'Accept-Language': 'en-US,en;q=0.5', 'Cache-Control': 'no-cache', 'Connection': 'keep-alive', 'Content-Length': '64', 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'Cookie': 'ust=202208190247397003b29f9cf40226e5fd09bb775187c96a15440c7c2aed7a0daa4206f4bead54; cookieMode=all; lastType=1; menuArr=m_SOCCER%7Cm_SOCCER_GB; _ga_3G40M6Y9V9=GS1.1.1660869361.5.1.1660870335.0.0.0; _ga=GA1.2.1347652800.1660797748; _gid=GA1.2.66422849.1660797757; _fbp=fb.1.1660817969593.1136747434; CSPSESSIONID-SP-80-UP-=00s008000000arKSwG2mY0FdBvlHaRlEDLj1YL1Fks8dG4iCvb; lastBets=; spoMenu=35; _hjSessionUser_2935299=eyJpZCI6ImM1OGMzNjJhLTUzZDAtNTAyMy05M2I4LTYyYWU2OWRhNzA0NCIsImNyZWF0ZWQiOjE2NjA4NzAwNzUyODAsImV4aXN0aW5nIjpmYWxzZX0=; _hjFirstSeen=1; _hjIncludedInSessionSample=0; _hjSession_2935299=eyJpZCI6ImM4MGZkZTI4LThjOGYtNGI2NC1hOTg4LTFkZjg5MzY1NTg1ZCIsImNyZWF0ZWQiOjE2NjA4NzAwNzUzODEsImluU2FtcGxlIjpmYWxzZX0=; _hjAbsoluteSessionInProgress=0; _gat_UA-30529581-8=1', 'Host': 'www.bingoal.nl', 'Origin': 'https://www.bingoal.nl', 'Pragma': 'no-cache', 'Referer': 'https://www.bingoal.nl/nl/Sport/', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:103.0) Gecko/20100101 Firefox/103.0', 'X-Requested-With': 'XMLHttpRequest'}
    headers=b_headers#{'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br', 'Accept-Language': 'en-US,en;q=0.5', 'Cache-Control': 'no-cache', 'Connection': 'keep-alive', 'Content-Length': '64', 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'Cookie': 'ust=2022082604445680246c6974e685fdd6a453248ac799502f3b115399229de8e97cef45ddd90901; cookieMode=all; lastType=1; menuArr=m_SOCCER_GB%7Cm_SOCCER%7Cm_SOCCER_ES%7Cm_SOCCER_JP; _ga_3G40M6Y9V9=GS1.1.1661486812.12.0.1661486812.0.0.0; _ga=GA1.2.1347652800.1660797748; _fbp=fb.1.1660817969593.1136747434; _hjSessionUser_2935299=eyJpZCI6ImM1OGMzNjJhLTUzZDAtNTAyMy05M2I4LTYyYWU2OWRhNzA0NCIsImNyZWF0ZWQiOjE2NjA4NzAwNzUyODAsImV4aXN0aW5nIjp0cnVlfQ==; liveMenuArr=m_SOCCER; CSPSESSIONID-SP-80-UP-=01e008000000kONCu7JSQvYnlxWoCPLzrdfe19anlb4ualGWNs; lastBets=; spoMenu=35; _gid=GA1.2.627081937.1661482008; _gat_UA-30529581-8=1', 'Host': 'www.bingoal.nl', 'Origin': 'https://www.bingoal.nl', 'Pragma': 'no-cache', 'Referer': 'https://www.bingoal.nl/nl/Sport', 'Sec-Fetch-Dest': 'empty', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-origin', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:103.0) Gecko/20100101 Firefox/103.0', 'X-Requested-With': 'XMLHttpRequest'}

    #print("ready to pull bingoal comp..")
    for counter in range(3):
        try:
            xtime=time.time()
            res = requests.post(url,headers=headers,data=params,timeout=timeout_count,proxies = {"https":random.choice(proxies)})
            #print(res.reason,len(res.text),time.time()-xtime)
            break
        except Exception as msg:
            pass#print("binggoal comppull err.. ",str(msg))

    e_list=[]


    data = res.json()
    if data:
        for day in data['sports']:
            for match in day['matches']:
                e_list.append(match['ID'])
            
    #print(">> TOTO thread pull")
    #print("bingoal e_list:",e_list)    
    comp_data=[]

    with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(e_list),thread_count)) as executor:
        future_to_url = {executor.submit(bingoal_data_thread, e,session_cookies): e for e in e_list}
        for future in concurrent.futures.as_completed(future_to_url):
            #url = future_to_url[future]
            try:
                data = future.result()
                comp_data.append(data)
            except Exception as exc:
                pass#print('%r generated an exception: %s' % ("brr", exc))

    for cd in comp_data:
        try:
            do_odds_history_insert("bingoal", cd['id'],cd['book'],cd['markets'])
        except Exception as msg:
            pass#print("err on odds history insert..",str(msg))  
    #    print(">>",cd)
    #print("--END TOTO--")
    #with open("/home/arb_bot/beta_bingoal_fastbf/bingoal_dumps/" +  compid  + ".json","w") as f:
    #    f.write(json.dumps(comp_data))
    return comp_data



def get_team_list_bingoal():
    #print("<building team list>")
    conn = pymysql.connect(host='localhost',user='local',passwd='oeijifjwejfio',db=db_name)
    cur  = conn.cursor()
    cur.execute("select bingoal_name,betfair_name from bingoal_teams")
    rows = cur.fetchall()
    teams={}
    for row in rows:
        teams[row[0].upper()]=row[1]
        teams[strip_accents(row[0]).upper()]=row[1]
    conn.close()
    #print("<team list built>")
    return teams



def insert_to_database_bingoal(t,b,league):
    
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

    #insert section
    #print("TOTO###",b)
    odds_json={"bingoal_1_odds":toto_1_odds,"bingoal_x_odds":toto_x_odds,"bingoal_2_odds":toto_2_odds,"bingoal_under_2.5":toto_under_2p5,"bingoal_over_2.5":toto_over_2p5,"bingoal_under_3.5":toto_under_3p5,"bingoal_over_3.5":toto_over_3p5,"bingoal_dnb_home":toto_dnb_home,"bingoal_dnb_away":toto_dnb_away,
               "bingoal_dc_1x":toto_dc_1x,"bingoal_dc_12":toto_dc_12,"bingoal_dc_x2":toto_dc_x2,
           "bingoal_1_ht":toto_1_ht,"bingoal_x_ht":toto_x_ht,"bingoal_2_ht":toto_2_ht,
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
    cur.execute("select * from bingoal_matches where bingoal_event_id=%s and betfair_event_id=%s",(t['event_id'],b['event_id']))
    rows = cur.fetchall()
    if len(rows)>0:
        #print("found event,, updating",t['event_id'],b['event_id'])
        cur.execute("update bingoal_matches set timestamp=%s,bingoal_data=%s,t1_bingoal_fuzzy=%s,t2_bingoal_fuzzy=%s where bingoal_event_id=%s and betfair_event_id=%s",
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

            
        cur.execute("insert into bingoal_matches (timestamp,bingoal_event_id,betfair_event_id,team_1_bingoal,team_2_bingoal,team_1_betfair,team_2_betfair,bingoal_data,t1_bingoal_fuzzy,t2_bingoal_fuzzy,ignored,league) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (b['timestamp'],t['event_id'],b['event_id'],toto_teamnames[0],toto_teamnames[1],bf_teamnames[0],bf_teamnames[1],json.dumps(odds_json),t1fuzzy,t2fuzzy,0,league))
    conn.commit()
    conn.close()
    

def do_insert_bingoal(toto_data,betfair_data,league,toto_teams):
    #global toto_teams
    #print("doing fuzzy and insert BINGOAL")

    
    #pull all bf matches, and subsequent team names.. for fuzzy match
    
    bf_data = betfair_data
    #convert into list of lists
    #print("toto:",len(toto_data),"bf:",len(betfair_data),league)
    bf_matches=[]
    for b in bf_data:
        #print("CHECK:",bf_data[b])
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
                insert_error(str(msg),"err on betfair (bingoal) match check:",teama,teamb,str(msg))
            except Exception as msg:
                pass#print(">>> insert err error..",str(msg))
    #print("thru bf stuff..")

    #for b in bf_matches:
    #    print(b)

    #print("------------------------>")
    
    tt_data = toto_data#pickle.load(f)

    #here pull from db, and whittle down to unique,, then create the list..
    #toto_teams = get_team_list_toto()
    #unibet_teams = get_team_list_unibet()

    #print("there are:",len(toto_teams),"teams")   

    bf_teams=[]
    for b in bf_data:
        for name in bf_data[b]['name'].split(" v "):
            bf_teams.append(name)
    bf_teams=list(set(bf_teams))

    tt_matches=[]
    #conn = pymysql.connect(host='localhost',user='local',passwd='oeijifjwejfio',db=db_name)
    #cur = conn.cursor()
    #print("about to iterate on bingoal data")
    for t in  tt_data:
        match_data=[]
        matchteams=[]
        matchteams_raw=[]
        for runner in t['book']:
            if runner['name']!='X':
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
                        if r>maxfuzz and r>=40:
                            maxfuzz=r
                            likely_team=b
                            if r>85:
                                break
                    #try:
                    #    cur.execute("insert into toto_teams (back_name,betfair_name) values(%s,%s)",(runner['name'],likely_team))
                    #    conn.commit()
                    #except:
                    #    pass
                    match_data.append([likely_team,runner['price'],1])
                    matchteams.append(likely_team)
            else:
                match_data.append(["X",runner['price'],0])
        matchteams.sort()
        matchteams_raw.sort()
        tt_matches.append({"matchup":matchteams,"matchup_raw":matchteams_raw,"book":match_data,"markets":t['markets'],'event_id':t['id'],'start_time':t['start_time']})
    #conn.close()
    #for t in tt_matches:
    #    print("bingoal",t)
    found=0
    for t in tt_matches:
        found=0
        for b in bf_matches:
            #print("date match:",t['start_time'][0:10],str(datetime.datetime.utcfromtimestamp(int(b['timestamp'])).strftime('%Y-%m-%d %H:%M:%S'))[0:10])
            #print("<><><>",t['matchup'],b['matchup'],t['start_time'][0:10],int(b['timestamp']),str(datetime.datetime.utcfromtimestamp(int(b['timestamp'])).strftime('%Y-%m-%d %H:%M:%S'))[0:10])
            if t['matchup']==b['matchup'] and convert_midnight(t['start_time'])==str(datetime.datetime.utcfromtimestamp(int(b['timestamp'])).strftime('%Y-%m-%d %H:%M:%S'))[0:10]:
                #print("MATCHED>>>>",t['matchup'],b['matchup'],t['start_time'][0:10],int(b['timestamp']),str(datetime.datetime.utcfromtimestamp(int(b['timestamp'])).strftime('%Y-%m-%d %H:%M:%S'))[0:10])
                try:
                    insert_to_database_bingoal(t,b,league)
                except Exception as msg:
                    pass#print("INSERT NOPE! TOTO..check the extra markets likely",str(msg))
                found=1
                break
            else:
                pass#print("<<<<UNMATCHED",t['matchup'],b['matchup'],t['start_time'][0:10],int(b['timestamp']),str(datetime.datetime.utcfromtimestamp(int(b['timestamp'])).strftime('%Y-%m-%d %H:%M:%S'))[0:10])
    if not found:
        #print("NOT MATCHED:",t['matchup'],b['matchup'])
        conn = pymysql.connect(host='localhost',user='local',passwd='oeijifjwejfio',db=db_name)
        cur  = conn.cursor()
        #print("select * from unmatched where start_time=%s and team1=%s and team2=%s",(t['start_time'],t['matchup_raw'][0],t['matchup_raw'][1]))

        cur.execute("select * from bingoal_unmatched where start_time=%s and team1=%s and team2=%s",(t['start_time'],t['matchup_raw'][0],t['matchup_raw'][1]))
        rows =cur.fetchall()
        if len(rows)==0:
            cur.execute("insert into bingoal_unmatched (team1,team2,league,start_time,timestamp) values(%s,%s,%s,%s,%s)",(t['matchup_raw'][0],t['matchup_raw'][1],league,t['start_time'],time.time()))
            conn.commit()
        conn.close()        
