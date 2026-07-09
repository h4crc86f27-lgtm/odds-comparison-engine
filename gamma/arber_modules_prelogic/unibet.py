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


def pull_extra_markets_unibet(eventid):#="1018556845"):
    retval={"2.5":{"Over":0,"Under":0},
            "3.5":{"Over":0,"Under":0},
            "DNB":{"Home":0,"Away":0},
            "1x2_HT":{"1":0,"X":0,"2":0},
            "DC":{"1X":0,"12":0,"X2":0}
            }

    url="https://o1-api.aws.kambicdn.com/offering/v2018/ubau/betoffer/event/" + str(eventid) + ".json?lang=en_AU&market=AU&client_id=2&channel_id=1&includeParticipants=true"
    res = requests.get(url,proxies = {"https":random.choice(proxies)},timeout=timeout_count)
    data = res.json()
    offers = data['betOffers']
    for o in offers:
        if o['betOfferType']['name']=="Head to Head" and o['criterion']['label']=="Draw No Bet":
            retval['DNB']['Home']=o['outcomes'][0]['odds']/1000
            retval['DNB']['Away']=o['outcomes'][1]['odds']/1000
        elif o['betOfferType']['name']=="Totals" and o['criterion']['label']=="Total Goals" and o['outcomes'][0]['line']==2500:
            retval['2.5'][o['outcomes'][0]['label']]=o['outcomes'][0]['odds']/1000
            retval['2.5'][o['outcomes'][1]['label']]=o['outcomes'][1]['odds']/1000
        elif o['betOfferType']['name']=="Totals" and o['criterion']['label']=="Total Goals" and o['outcomes'][0]['line']==3500:
            retval['3.5'][o['outcomes'][0]['label']]=o['outcomes'][0]['odds']/1000
            retval['3.5'][o['outcomes'][1]['label']]=o['outcomes'][1]['odds']/1000
        elif o['betOfferType']['name']=="Double Chance" and o['criterion']['label']=="Double Chance":
            order = ["1X","X2","12"]
            adds = {}
            try:
                adds[o['outcomes'][0]['label']] = o['outcomes'][0]['odds']/1000
            except:
                pass
            
            try:
                adds[o['outcomes'][1]['label']] = o['outcomes'][1]['odds']/1000
            except:
                pass
            
            try:
                adds[o['outcomes'][2]['label']] = o['outcomes'][2]['odds']/1000
            except:
                pass
            
            for o in order:
                try:
                    retval['DC'][o]=adds[o]#['outcomes'][0]['odds']/1000
                except:
                    retval['DC'][o]=0
                    
            #retval['DC'][o['outcomes'][1]['label']]=o['outcomes'][1]['odds']/1000
            #retval['DC'][o['outcomes'][2]['label']]=o['outcomes'][2]['odds']/1000
        elif o['betOfferType']['name']=="Head to Head" and o['criterion']['label']=="Half Time":
            retval['1x2_HT'][o['outcomes'][0]['label']]=o['outcomes'][0]['odds']/1000
            retval['1x2_HT'][o['outcomes'][1]['label']]=o['outcomes'][1]['odds']/1000
            retval['1x2_HT'][o['outcomes'][2]['label']]=o['outcomes'][2]['odds']/1000
            

    return retval

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

    res= requests.get(url,proxies = {"https":random.choice(proxies)},timeout=timeout_count)
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
                #("adding unibet comp:",gg['name'])
                x=cur.execute("insert into raw_comps(comp_name,comp_id,site,timestamp) values(%s,%s,%s,%s)",(gg['name'],compid,"unibet",time.time()))

    conn.commit()
    conn.close()

def unibet_data_thread(e,events):
        outcomes=[]
        extra_markets=[]
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
                break
            #elif offers[f]['eventId']==events[e]['event']['id'] and offers[f]['betOfferType']['id']==6:
            #    ou_25_odds_a= offers[f]['outcomes'][0]['odds']/1000
            #    ou_25_odds_b= offers[f]['outcomes'][1]['odds']/1000
            #   
            #    extra_markets.append({"name":str(round(offers[f]['outcomes'][0]['line']/1000,1)) + "_" + offers[1]['outcomes'][0]['label'],"price":ou_25_odds_a})
            #    extra_markets.append({"name":str(round(offers[f]['outcomes'][1]['line']/1000,1)) + "_" + offers[1]['outcomes'][1]['label'],"price":ou_25_odds_b})
        for counter in range(3):
            try:
                other_markets = pull_extra_markets_unibet(eid)
        
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
                pass#print("err in unibet extra markets loop:",str(msg))#pass#try again

        #print ("unibet:",{"id":eid,"book":outcomes,"markets":extra_markets,"start_time":timestamp})
        return {"id":eid,"book":outcomes,"markets":extra_markets,"start_time":timestamp}


def pull_data_unibet(compid,league):

    #print("UNIBET DATA >>>")
    comp_data=[]
    #compid=england/premier_league
    #premier league
    url="https://o1-api.aws.kambicdn.com/offering/v2018/ubau/listView/football/" + compid + ".json?lang=en_AU&market=UK&client_id=2&channel_id=1&ncid=1651722023500&useCombined=true"
    #url="https://o1-api.aws.kambicdn.com/offering/v2018/ubau/listView/football/bulgaria/pfl_2.json?lang=en_AU&market=UK&client_id=2&channel_id=1&ncid=1651722023500&useCombined=true"
    for counter in range(3):
        try:
            res = requests.get(url,proxies = {"https":random.choice(proxies)},timeout=timeout_count)
            #print(res.reason)
            break
        except:
            #print("retrying unibet,, failed comp pull")
            pass
    #print("unibet comp pulled")
    data=res.json()
    events=data['events']
    #offers=data['betoffers']
    e_list=[]

    for e in range(0,len(events)):
        e_list.append([e,events])

    #print("unibet event_list_len:",len(e_list))

    with concurrent.futures.ThreadPoolExecutor(max_workers=thread_count) as executor:
        future_to_url = {executor.submit(unibet_data_thread, e[0],e[1]): e for e in e_list}
        for future in concurrent.futures.as_completed(future_to_url):
            #url = future_to_url[future]
            try:
                data = future.result()
                comp_data.append(data)
            except Exception as exc:
                pass#print('%r generated an exception: %s' % ("brr", exc))


    #print("UNIBET MARKETS STUFF::::",len(comp_data))
    for cd in comp_data:
        try:
            do_odds_history_insert("unibet", cd['id'],cd['book'],cd['markets'])
        except Exception as msg:
            print("UB err on odds history insert..",str(msg))  
    #    print(">>",cd)
    #print("--END UNIBET--")
    #print("dumping unibet..",league)

    #with open("/home/arb_bot/beta_bingoal_fastbf/unibet_dumps/" +  league  + ".json","w") as f:
    #    f.write(json.dumps(comp_data))

    return comp_data

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

def insert_to_database_unibet(t,b,league):
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
    odds_json={"unibet_1_odds":toto_1_odds,"unibet_x_odds":toto_x_odds,"unibet_2_odds":toto_2_odds,"unibet_over_2.5":unibet_over_2p5,"unibet_under_2.5":unibet_under_2p5,"unibet_over_3.5":unibet_over_3p5,"unibet_under_3.5":unibet_under_3p5,"unibet_dnb_home":unibet_dnb_home,"unibet_dnb_away":unibet_dnb_away,
            "unibet_dc_1x":unibet_dc_1x,"unibet_dc_12":unibet_dc_12,"unibet_dc_x2":unibet_dc_x2,
           "unibet_1_ht":unibet_1_ht,"unibet_x_ht":unibet_x_ht,"unibet_2_ht":unibet_2_ht,
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
    cur.execute("select * from unibet_matches where unibet_event_id=%s and betfair_event_id=%s",(t['event_id'],b['event_id']))
    rows = cur.fetchall()
    if len(rows)>0:
        #print("found event,, updating",t['event_id'],b['event_id'])
        cur.execute("update unibet_matches set flipped=%s,timestamp=%s,unibet_data=%s,t1_unibet_fuzzy=%s,t2_unibet_fuzzy=%s where unibet_event_id=%s and betfair_event_id=%s",
                (b['flipped'],b['timestamp'],json.dumps(odds_json),t1fuzzy,t2fuzzy,t['event_id'],b['event_id']))
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

        cur.execute("insert into unibet_matches (timestamp,unibet_event_id,betfair_event_id,team_1_unibet,team_2_unibet,team_1_betfair,team_2_betfair,unibet_data,t1_unibet_fuzzy,t2_unibet_fuzzy,ignored,league,flipped) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (b['timestamp'],t['event_id'],b['event_id'],unibet_teamnames[0],unibet_teamnames[1],bf_teamnames[0],bf_teamnames[1],json.dumps(odds_json),t1fuzzy,t2fuzzy,0,league,b['flipped']))
    conn.commit()
    conn.close()


def do_insert_unibet(unibet_data,betfair_data,league,unibet_teams):
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
                insert_error(str(msg),"err on betfair (ub) match check:",teama,teamb,str(msg))
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
                
                insert_to_database_unibet(t,b,league)
                found=1
                break
            else:
                pass#print("UNMATCHED<<<<<",t['matchup'],b['matchup'],t['start_time'][0:10],int(b['timestamp']),str(datetime.datetime.utcfromtimestamp(int(b['timestamp'])).strftime('%Y-%m-%d %H:%M:%S'))[0:10])
            
                
    if not found:
        #print("NOT MATCHED:",t['matchup'],b['matchup'])
        conn = pymysql.connect(host='localhost',user='local',passwd='oeijifjwejfio',db=db_name)
        cur  = conn.cursor()
        #print("select * from unmatched where start_time=%s and team1=%s and team2=%s",(t['start_time'],t['matchup_raw'][0],t['matchup_raw'][1]))

        cur.execute("select * from unibet_unmatched where start_time=%s and team1=%s and team2=%s",(t['start_time'],t['matchup_raw'][0],t['matchup_raw'][1]))
        rows =cur.fetchall()
        if len(rows)==0:
            cur.execute("insert into unibet_unmatched (team1,team2,league,start_time,timestamp) values(%s,%s,%s,%s,%s)",(t['matchup_raw'][0],t['matchup_raw'][1],league,t['start_time'],time.time()))
            conn.commit()
        conn.close()  