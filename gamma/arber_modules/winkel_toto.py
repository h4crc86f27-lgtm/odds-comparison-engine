import pymysql
import configparser
import requests
import random
import json
from arber_modules.utils import *
import time
from fuzzywuzzy import fuzz
import concurrent.futures
import urllib3
import pickle

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

thread_count=5
timeout_count=10

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


def do_winkel_toto_raw():
    conn = pymysql.connect(host='localhost',user='local',passwd='oeijifjwejfio',db=db_name)
    cur  = conn.cursor()
    cur.execute("select * from raw_comps where site='winkel_toto'")
    rows = cur.fetchall()
    ids_done=[]
    for row in rows:
        ids_done.append(row[2])

    comps={}
    # soccer events pull
    url="https://totowinkel.nederlandseloterij.nl/nl/wedden/voetbal"
    res = requests.post(url,verify=False,headers={"content-type":"application/json","accept-encoding":"gzip, deflate, br"})

    data = res.json()
    models = data['models']

    all_comps=[]

    for model in models:
        if models[model]['className']=="SportViewContainer":
            #this is the tourny list..
            categories = models[model]['data']['categories']
            for cat in categories:
                cat_name = cat['categoryName']
                for tourny in cat['tournaments']:
                    comp_id = tourny['tournamentUrl'].split("/")[-1]
                    t_name = tourny['tournamentName']
                    t_id = tourny['tournamentId']
                    #all_comps.append({"cat":cat_name,"url":url,"t_name":t_name,"t_id":t_id})

                    comp_name = cat_name + " " + t_name
                    if comp_id not in ids_done:
                        #print("adding winkel_toto comp:",d['Category'] + " " + d['Tournament'])
                        x=cur.execute("insert into raw_comps(comp_name,comp_id,site,timestamp) values(%s,%s,%s,%s)",(comp_name,comp_id,"winkel_toto",time.time()))


    conn.commit()
    conn.close()
    #return comps

## winkel_toto

def winkel_toto_data_thread(e):
    #here i pull down the data from the e which is the eventUrl..
    #rint("winkelurl:",e)
    res = requests.post(e,verify=False,headers={"content-type":"application/json","accept-encoding":"gzip, deflate, br"},proxies = {"https":random.choice(proxies)},timeout=timeout_count) # 
    #print("winkto_event_response",res.reason)
    data = res.json(    )
    #print("winkto_event_data >> ")
    models = data['models']

    for model in models:
        if models[model]['className']=="EventContainer":
            break
    event = models[model]['data']['event']
    eventid = event['matchId']
    markets = models[model]['data']['event']['markets']

    outcomes=[]
    extra_markets=[]
    
    home = event['homeTeam']['name']
    away = event['awayTeam']['name']

    timestamp = convert_euro_time(event['date'][0:19]) + "Z"#e['Date'] +"Z"

    all_done=0

    for m in markets:

        if m['type']=='SOCCER:FT:AXB':
            #h2h odds..
            home_odds = m['odds'][0]['odd']
            draw_odds = m['odds'][1]['odd']
            away_odds = m['odds'][2]['odd']
            outcomes.append({"name":home,"price":home_odds})
            outcomes.append({"name":"X","price":draw_odds})
            outcomes.append({"name":away,"price":away_odds})
            all_done+=1
            if all_done>2:
                break
        elif m['type']=="SOCCER:FT:OU" and m['subGroupId']=="M#3.5":
            extra_markets.append({"name":"3.5_Under","price":m['odds'][0]['odd']})
            extra_markets.append({"name":"3.5_Over","price":m['odds'][1]['odd']})
        elif m['type']=="SOCCER:FT:OU" and m['subGroupId']=="M#2.5":
            extra_markets.append({"name":"2.5_Under","price":m['odds'][0]['odd']})
            extra_markets.append({"name":"2.5_Over","price":m['odds'][1]['odd']})
            all_done+=1
            if all_done>2:
                break
        elif m['type']=="SOCCER:FT:DNB":
            extra_markets.append({"name":"DNB_Home","price":m['odds'][0]['odd']})
            extra_markets.append({"name":"DNB_Away","price":m['odds'][1]['odd']})
            all_done+=1
            if all_done>2:
                break
        elif m['type']=="SOCCER:FT:DBLC":
            adds={}
            order=['1X','X2','12']
            adds[m['odds'][0]['clean'].replace(" of 2","2")] = m['odds'][0]['odd']
            adds[m['odds'][1]['clean'].replace(" of 2","2")] = m['odds'][1]['odd']
            adds[m['odds'][2]['clean'].replace(" of 2","2")] = m['odds'][2]['odd']
            for o in order:
                extra_markets.append({"name":"DC_" + o,"price":adds[o]})

            #extra_markets.append({"name":"DC_" + m['odds'][0]['clean'],"price":m['odds'][0]['odd']})
            #extra_markets.append({"name":"DC_" + m['odds'][1]['clean'],"price":m['odds'][1]['odd']})
            #extra_markets.append({"name":"DC_" + m['odds'][2]['clean'].replace(" of 2","2"),"price":m['odds'][2]['odd']})           
        elif m['type']=="SOCCER:P:AXB_H1":
            extra_markets.append({"name": m['odds'][0]['clean'] + "_HT","price":m['odds'][0]['odd']})
            extra_markets.append({"name": m['odds'][1]['clean'] + "_HT","price":m['odds'][1]['odd']})
            extra_markets.append({"name": m['odds'][2]['clean'] + "_HT","price":m['odds'][2]['odd']}) 



    #print("WINKTO!!!!>>",outcomes,extra_markets)
    return {"id":eventid,"book":outcomes,"markets":extra_markets,"start_time":timestamp} 
    #just once? has all outcomes in there..

def pull_data_winkel_toto(compid,league):#country,tourny):
    #compid="tanzania-premier-league"
    url="https://totowinkel.nederlandseloterij.nl/nl/wedden/voetbal/" + compid
    #print("winkel_comp_url:",url)
    res = requests.post(url,verify=False,headers={"content-type":"application/json","accept-encoding":"gzip, deflate, br"},proxies = {"https":random.choice(proxies)},timeout=timeout_count)
    #print("winkelresponse:",res.reason)
    data = res.json()
    #print("winkel_data:>>")
    models = data['models']
    #with open("/home/arb_bot/gamma/winkel_toto_dumps/" + league + "-events.pickle","wb") as f:
    #    pickle.dump(data,f)
    e_list = []
    comp_data=[]
    
    for model in models:
        if models[model]['className']=="TournamentViewContainer":
            events = models[model]['data']['events']
            for event in events:
                e_list.append("https://totowinkel.nederlandseloterij.nl" + event['eventUrl'])

    print("winkel_toto events:",e_list)

    with concurrent.futures.ThreadPoolExecutor(max_workers=thread_count) as executor:
        future_to_url = {executor.submit(winkel_toto_data_thread, e): e for e in e_list}
        for future in concurrent.futures.as_completed(future_to_url):
            #url = future_to_url[future]
            try:
                data = future.result()
                comp_data.append([data,future_to_url[future].replace("https://totowinkel.nederlandseloterij.nl","")])
                
            except Exception as exc:
                print('%r generated an exception: %s' % ("dataThread", exc))

    #for cd in comp_data:
    #   print(">> !WINKELTOTO! <<",cd)
    #print("--END winkel_toto--")
    for cd in comp_data:
        try:
            pass#do_odds_history_insert("winkel_toto", cd[1],cd[0]['book'],cd[0]['markets'])
        except Exception as msg:
            pass#print("WINKEL err on odds history insert..",str(msg))   
    #print("completed winkel historical insert")
    #with open("/home/arb_bot/gamma/winkel_toto_dumps/comp_data-" +  compid  + ".json","w") as f:
    #    f.write(json.dumps(comp_data))
    return comp_data


def get_team_list_winkel_toto():
    #print("<building team list>")
    conn = pymysql.connect(host='localhost',user='local',passwd='oeijifjwejfio',db=db_name)
    cur  = conn.cursor()
    cur.execute("select winkel_toto_name,betfair_name from winkel_toto_teams")
    rows = cur.fetchall()
    teams={}
    for row in rows:
        teams[row[0].upper()]=row[1]
        teams[strip_accents(row[0]).upper()]=row[1]
    conn.close()
    #print("<team list built>")
    return teams


def insert_to_database_winkel_toto(t,b,league):##< this is for the event url..
    #print("WINKEL INSERT AREA",t,league)
    #e_data,e_url = t
    #t = e_data

    conn = pymysql.connect(host='localhost',user='local',passwd='oeijifjwejfio',db=db_name)
    cur  = conn.cursor()
    winkel_toto_teamnames = t['matchup_raw']
    print("winkel_toto INSERT AREA:::",t,b)
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
        temp = winkel_toto_teamnames[0]
        winkel_toto_teamnames[0] = winkel_toto_teamnames[1]
        winkel_toto_teamnames[1] = temp
        

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
    winkel_toto_over_2p5=0
    winkel_toto_under_2p5=0
    winkel_toto_over_3p5=0
    winkel_toto_under_3p5=0
    winkel_toto_dnb_home=0
    winkel_toto_dnb_away=0
    winkel_toto_dc_x2=0
    winkel_toto_dc_12=0
    winkel_toto_dc_1x=0
    winkel_toto_1_ht=0
    winkel_toto_x_ht=0
    winkel_toto_2_ht=0
    print("WINKTO ready to markets..")
    for outcome in t['markets']:
        if outcome['name']=='2.5_Over':
            winkel_toto_over_2p5 = outcome['price']
        elif outcome['name']=='2.5_Under':
            winkel_toto_under_2p5 = outcome['price']
        elif outcome['name']=='3.5_Under':
            winkel_toto_under_3p5 = outcome['price']
        elif outcome['name']=='3.5_Over':
            winkel_toto_over_3p5 = outcome['price']
        elif outcome['name']=='DNB_Home':
            winkel_toto_dnb_home = outcome['price']
        elif outcome['name']=='DNB_Away':
            winkel_toto_dnb_away = outcome['price']
        elif outcome['name']=='DC_1X':
            if 0:#b['flipped']:
                winkel_toto_dc_x2 = outcome['price']
            else:
                winkel_toto_dc_1x = outcome['price']
        elif outcome['name']=='DC_12':
            winkel_toto_dc_12 = outcome['price']
        elif outcome['name']=='DC_X2':
            if 0:#b['flipped']:
                winkel_toto_dc_1x = outcome['price']
            else:
                winkel_toto_dc_x2 = outcome['price']
        elif outcome['name']=='1_HT':
            if 0:#b['flipped']:
                winkel_toto_2_ht = outcome['price']
            else:
                winkel_toto_1_ht = outcome['price']
        elif outcome['name']=='X_HT':
            winkel_toto_x_ht = outcome['price']
        elif outcome['name']=='2_HT':
            if 0:#b['flipped']:
                winkel_toto_1_ht = outcome['price']
            else:
                winkel_toto_2_ht = outcome['price']
    #print("###",b)
    #insert section  here need to add the extra market odds..
    #print("<< PREWINKTO >>")

    odds_json={"winkel_toto_1_odds":toto_1_odds,"winkel_toto_x_odds":toto_x_odds,"winkel_toto_2_odds":toto_2_odds,"winkel_toto_over_2.5":winkel_toto_over_2p5,"winkel_toto_under_2.5":winkel_toto_under_2p5,"winkel_toto_over_3.5":winkel_toto_over_3p5,"winkel_toto_under_3.5":winkel_toto_under_3p5,"winkel_toto_dnb_home":winkel_toto_dnb_home,"winkel_toto_dnb_away":winkel_toto_dnb_away,
               "winkel_toto_dc_1x":winkel_toto_dc_1x,"winkel_toto_dc_12":winkel_toto_dc_12,"winkel_toto_dc_x2":winkel_toto_dc_x2,
           "winkel_toto_1_ht":winkel_toto_1_ht,"winkel_toto_x_ht":winkel_toto_x_ht,"winkel_toto_2_ht":winkel_toto_2_ht,
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
    cur.execute("select * from winkel_toto_matches where winkel_toto_event_id=%s and betfair_event_id=%s",(t['event_id'],b['event_id']))
    rows = cur.fetchall()
    if len(rows)>0:
        #print("found winkel_toto event,, updating",t['event_id'],b['event_id'])
        cur.execute("update winkel_toto_matches set timestamp=%s,winkel_toto_data=%s,t1_winkel_toto_fuzzy=%s,t2_winkel_toto_fuzzy=%s where winkel_toto_event_id=%s and betfair_event_id=%s",
                (b['timestamp'],json.dumps(odds_json),t1fuzzy,t2fuzzy,t['event_id'], b['event_id']))
        #print("updated:",t['event_id'],b['event_id'])
    else:
        #print("NO event,, inserting",t['event_id'],b['event_id'])
        #here i do an extra ratio check on toto teams, because somehow are flipping sometimes..
        if fuzz.ratio(winkel_toto_teamnames[0],bf_teamnames[0])>fuzz.ratio(winkel_toto_teamnames[0],bf_teamnames[1]):
            pass#should be right 
        else:
            #print("flipping:",winkel_toto_teamnames[0],winkel_toto_teamnames[1])
            temp = winkel_toto_teamnames[0]
            winkel_toto_teamnames[0] = winkel_toto_teamnames[1]
            winkel_toto_teamnames[1] = temp

        cur.execute("insert into winkel_toto_matches (timestamp,winkel_toto_event_id,betfair_event_id,team_1_winkel_toto,team_2_winkel_toto,team_1_betfair,team_2_betfair,winkel_toto_data,t1_winkel_toto_fuzzy,t2_winkel_toto_fuzzy,ignored,league) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (b['timestamp'],t['event_id'],b['event_id'],winkel_toto_teamnames[0],winkel_toto_teamnames[1],bf_teamnames[0],bf_teamnames[1],json.dumps(odds_json),t1fuzzy,t2fuzzy,0,league))
    conn.commit()
    conn.close()


def align_matches(book_data,ref_data,league):
    #here i run through,, so loop over book data,,
    books_left=[]
    matched=0
    total_bookdata=len(book_data)
    total_refdata = len(ref_data)
    
    #print("winkto_align:",total_bookdata,total_refdata)
    #print(book_data[0])

    # look for a single team exact match,, and a timestamp match..
    for bd in book_data:
        found=False
        match_data=[]
        #print("--",bd,"--")
        #if bd['book']==[]:
        #    continue
        for rd in ref_data:#this is a list not the dict version
            #print("winkcheck:",bd,rd)
            if type(bd)==type([]):
                bd = bd[0]
            ##print(abs(convert_string_timestamp(bd['start_time'])- convert_string_timestamp(rd['start_time'])))
            if abs(convert_string_timestamp(bd['start_time'])- convert_string_timestamp(rd['start_time']))<=3600:#within 30s of each other..
                print("TIMESTAMP OK HANSOLO>>>>.")
                rd_teams_raw=[rd['matchup'][0],rd['matchup'][1]]
                rd_teams=[rd['matchup'][0].lower(),rd['matchup'][1].lower()]
                #print(rd_teams_raw)

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

                
                print("ready for intersect HANSOLO")
                if len(set(book_names_lower).intersection(set(rd_teams)))>0:# in rd_teams or bd['book'][1]['name'].lower() in rd_teams or bd['book'][2]['name'].lower() in rd_teams:prin
                    print("BINGO!!")
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
                    print("inserting..",bd['book'],rd_teams)
                    insert_to_database_winkel_toto(tt,rd,league)
                    
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
                #print("winkto_wookie_mode:",bd,rd)
                if abs(convert_string_timestamp(bd['start_time'])- convert_string_timestamp(rd['start_time']))<=3600:#within 10mins of each other..
                    print("TIMESTAMP OK WOOKIE!!!!!!")
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
                    threshold=80
                    print("ready for intersect CHEWY")
                    if (r00>threshold or book_names_lower[0].find(rd_teams[0])>-1 or rd_teams[0].find(book_names_lower[0])>-1 or  r01>threshold or book_names_lower[0].find(rd_teams[1])>-1 or rd_teams[1].find(book_names_lower[0])>-1 ) or  (r10>threshold or book_names_lower[1].find(rd_teams[0])>-1 or rd_teams[0].find(book_names_lower[1])>-1 or r11>threshold or book_names_lower[1].find(rd_teams[1])>-1  or rd_teams[1].find( book_names_lower[1])>-1):
                        #looks good for fuzz..
                        print("FUZZ!!!")
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
                        print("INSERTING >> ",tt)
                        insert_to_database_winkel_toto(tt,rd,league)
                    
            if not found:
                unmatched.append(bd)
                    

def do_insert_winkel_toto(winkel_toto_data,betfair_data,league,winkel_toto_teams):
    #global winkel_toto_teams
    #print("doing fuzzy and insert winkel_toto")

    
    #pull all bf matches, and subsequent team names.. for fuzzy match
    
    try:        
        if len(winkel_toto_data)>0 and len(betfair_data)>0:
            #print("about to convert..",betfair_data)
            bf_data=convert_ref_matches(betfair_data)
            print("winkto-prealign:",len(winkel_toto_data),len(bf_data))
            align_matches(winkel_toto_data,bf_data,league)
    except Exception as msg:
        print("alignment error:",str(msg))