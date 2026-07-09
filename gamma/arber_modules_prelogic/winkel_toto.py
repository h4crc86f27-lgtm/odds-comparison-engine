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
    url="https://winkel.toto.nl/nl/wedden/voetbal"
    res = requests.post(url,headers={"content-type":"application/json","accept-encoding":"gzip, deflate, br"})

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
    #print("winkelurl:",e)
    res = requests.post(e,headers={"content-type":"application/json","accept-encoding":"gzip, deflate, br"},proxies = {"https":random.choice(proxies)},timeout=timeout_count)
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


    for m in markets:

        if m['type']=='SOCCER:FT:AXB':
            #h2h odds..
            home_odds = m['odds'][0]['odd']
            draw_odds = m['odds'][1]['odd']
            away_odds = m['odds'][2]['odd']
            outcomes.append({"name":home,"price":home_odds})
            outcomes.append({"name":"X","price":draw_odds})
            outcomes.append({"name":away,"price":away_odds})
        elif m['type']=="SOCCER:FT:OU" and m['subGroupId']=="M#3.5":
            extra_markets.append({"name":"3.5_Under","price":m['odds'][0]['odd']})
            extra_markets.append({"name":"3.5_Over","price":m['odds'][1]['odd']})
        elif m['type']=="SOCCER:FT:OU" and m['subGroupId']=="M#2.5":
            extra_markets.append({"name":"2.5_Under","price":m['odds'][0]['odd']})
            extra_markets.append({"name":"2.5_Over","price":m['odds'][1]['odd']})
        elif m['type']=="SOCCER:FT:DNB":
            extra_markets.append({"name":"DNB_Home","price":m['odds'][0]['odd']})
            extra_markets.append({"name":"DNB_Away","price":m['odds'][1]['odd']})
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



    #print("WINKTO!!!!>>",extra_markets)
    return {"id":eventid,"book":outcomes,"markets":extra_markets,"start_time":timestamp} 
    #just once? has all outcomes in there..

def pull_data_winkel_toto(compid,league):#country,tourny):
    #compid="tanzania-premier-league"
    url="https://winkel.toto.nl/nl/wedden/voetbal/" + compid
    #print("winkel_comp_url:",url)
    res = requests.post(url,headers={"content-type":"application/json","accept-encoding":"gzip, deflate, br"},proxies = {"https":random.choice(proxies)},timeout=timeout_count)
    #print("winkelresponse:",res.reason)
    data = res.json()
    #print("winkel_data:>>")
    models = data['models']

    e_list = []
    comp_data=[]
    
    for model in models:
        if models[model]['className']=="TournamentViewContainer":
            events = models[model]['data']['events']
            for event in events:
                e_list.append("https://winkel.toto.nl" + event['eventUrl'])

    #print("winkel_toto events:",len(e_list))

    with concurrent.futures.ThreadPoolExecutor(max_workers=thread_count) as executor:
        future_to_url = {executor.submit(winkel_toto_data_thread, e): e for e in e_list}
        for future in concurrent.futures.as_completed(future_to_url):
            #url = future_to_url[future]
            try:
                data = future.result()
                comp_data.append([data,future_to_url[future].replace("https://winkel.toto.nl","")])
                
            except Exception as exc:
                pass#print('%r generated an exception: %s' % ("brr", exc))

    #for cd in comp_data:
    #   print(">> !WINKELTOTO! <<",cd)
    #print("--END winkel_toto--")
    for cd in comp_data:
        try:
            do_odds_history_insert("winkel_toto", cd[1],cd[0]['book'],cd[0]['markets'])
        except Exception as msg:
            pass#print("WINKEL err on odds history insert..",str(msg))   
    #print("completed winkel historical insert")
    #with open("/home/arb_bot/beta_bingoal_fastbf/winkel_toto_dumps/" +  compid  + ".json","w") as f:
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
    #print("winkel_toto INSERT AREA:::",t,b)
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
    #print("WINKTO ready to markets..")
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


def do_insert_winkel_toto(winkel_toto_data,betfair_data,league,winkel_toto_teams):
    #global winkel_toto_teams
    #print("doing fuzzy and insert winkel_toto")

    
    #pull all bf matches, and subsequent team names.. for fuzzy match
    
    bf_data = betfair_data
    #convert into list of lists
    #print("winkel_toto:",len(winkel_toto_data),"bf:",len(betfair_data),league)
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
                insert_error(str(msg),"err on betfair (winkel_toto) match check:",teama,teamb,str(msg))
            except Exception as msg:
                pass#print(">>> insert err error..",str(msg))

            
    #print("bf data check")
    #for b in bf_matches:
    #    print(b)

    #print("------------------------>")
    
    tt_data = winkel_toto_data#pickle.load(f)
    #print("winkel_toto>>>>>>>")
    #print(tt_data[0])
    #print("<<<<<<<<")
    #here pull from db, and whittle down to unique,, then create the list..
    #toto_teams = get_team_list_toto()
    #winkel_toto_teams = get_team_list_winkel_toto()

    #print("there are:",len(winkel_toto_teams),"teams")   

    bf_teams=[]
    for b in bf_data:
        for name in bf_data[b]['name'].split(" v "):
            bf_teams.append(name)
    bf_teams=list(set(bf_teams))
    #conn = pymysql.connect(host='localhost',user='local',passwd='oeijifjwejfio',db=db_name)
    #cur = conn.cursor()
    tt_matches=[]
    #print("WInKEL tt_data pre-loop")
    for z in  tt_data:
        t=z[0]
        #print(z[1],z[0])
        match_data=[]
        matchteams=[]
        matchteams_raw=[]
        for runner in t['book']:
            #print(">>",runner['name'],"<<")
            if runner['name']!='Draw' and runner['name']!='' and   runner['name']!='X':
                matchteams_raw.append(runner['name'])
                #try to match it,, if not,, fuzzy?
                if runner['name'].upper() in winkel_toto_teams and winkel_toto_teams[runner['name'].upper()]!="":
                    match_data.append([winkel_toto_teams[runner['name'].upper()],runner['price'],0])
                    matchteams.append(winkel_toto_teams[runner['name'].upper()])
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
                    #    cur.execute("insert into winkel_toto_teams (winkel_toto_name,betfair_name) values(%s,%s)",(runner['name'],likely_team))
                    #    conn.commit()
                    #except:
                    #    pass#rint("err on fyzzy insert")
                    match_data.append([likely_team,runner['price'],1])
                    #print("fuzzy",likely_team,runner['name'],maxfuzz)
                    matchteams.append(likely_team)
            else:
                match_data.append(["X",runner['price'],0])
        try:
            matchteams.remove('')
        except:
            pass
        matchteams.sort()
        matchteams_raw.sort()
        tt_matches.append({"matchup":matchteams,"matchup_raw":matchteams_raw,"book":match_data,"markets":t['markets'],'event_id':z[1],'start_time':t['start_time']})
    #conn.close()

    #print("WINKTO <><><><><>")
    #for t in tt_matches:
    #    print("winkel_toto",t)
    
    #print("<< WINKTO MATCHUPS =====")
    found=0
    for t in tt_matches:
        found=0
        for b in bf_matches:
            #print("<><><>",t['matchup'],b['matchup'],t['start_time'][0:10],int(b['timestamp']),str(datetime.datetime.utcfromtimestamp(int(b['timestamp'])).strftime('%Y-%m-%d %H:%M:%S'))[0:10])
            #print("date match:",t['start_time'][0:10],str(datetime.datetime.utcfromtimestamp(int(b['timestamp'])).strftime('%Y-%m-%d %H:%M:%S'))[0:10])
            
            if t['matchup']==b['matchup'] and convert_midnight(t['start_time'])==str(datetime.datetime.utcfromtimestamp(int(b['timestamp'])).strftime('%Y-%m-%d %H:%M:%S'))[0:10]:
                
                insert_to_database_winkel_toto(t,b,league)
                found=1
                break
            else:
                pass#print("UNMATCHED<<<<<",t['matchup'],b['matchup'],t['start_time'][0:10],int(b['timestamp']),str(datetime.datetime.utcfromtimestamp(int(b['timestamp'])).strftime('%Y-%m-%d %H:%M:%S'))[0:10])
            
                
    if not found:
        #print("NOT MATCHED:",t['matchup'],b['matchup'])
        conn = pymysql.connect(host='localhost',user='local',passwd='oeijifjwejfio',db=db_name)
        cur  = conn.cursor()
        #print("select * from unmatched where start_time=%s and team1=%s and team2=%s",(t['start_time'],t['matchup_raw'][0],t['matchup_raw'][1]))

        cur.execute("select * from winkel_toto_unmatched where start_time=%s and team1=%s and team2=%s",(t['start_time'],t['matchup_raw'][0],t['matchup_raw'][1]))
        rows =cur.fetchall()
        if len(rows)==0:
            cur.execute("insert into winkel_toto_unmatched (team1,team2,league,start_time,timestamp) values(%s,%s,%s,%s,%s)",(t['matchup_raw'][0],t['matchup_raw'][1],league,t['start_time'],time.time()))
            conn.commit()
        conn.close()    

