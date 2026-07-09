import pymysql
import configparser
import requests
import random
import datetime
from arber_modules.utils import *
import time
from fuzzywuzzy import fuzz
from websocket import create_connection
import json
import concurrent.futures

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


def do_betalpha_raw():

    conn = pymysql.connect(host='127.0.0.1',user='local',passwd='oeijifjwejfio',db=db_name)
    cur  = conn.cursor()
    cur.execute("select * from raw_comps where site='toto'")
    rows = cur.fetchall()
    ids_done=[]
    for row in rows:
        ids_done.append(int(row[2]))

    url="https://content.toto.nl/content-service/api/v1/q/drilldown-tree?drilldownNodeIds=11&eventState=OPEN_EVENT"
    res = requests.get(url,timeout=timeout_count)#,proxies = {"https":random.choice(proxies)})
    data = res.json()

    countries = data['data']['drilldownNodes'][0]['drilldownNodes'][0]['drilldownNodes']

    all_leagues={}
    for c in countries:
        for ddn in c['drilldownNodes']:
            if int(ddn['id']) not in ids_done:
                #all_leagues[ddn['name']]=ddn['id'] add to table
                #print("adding toto comp:",ddn['name'],ddn['id'])
                x=cur.execute("insert into raw_comps(comp_name,comp_id,site,timestamp) values(%s,%s,%s,%s)",(ddn['name'],ddn['id'],"toto",time.time()))
    conn.commit()
    conn.close()



def get_extra_markets_betalpha(ld,teams,tournyid):
    #print("--",ld,"--")
    #retdata={"2.5":[],"3.5":[],"DNB":[]}
    retdata={"2.5":{"Over":0,"Under":0},
            "3.5":{"Over":0,"Under":0},
            "DNB":{"Home":0,"Away":0},
            "1x2_HT":{"1":0,"X":0,"2":0},
            "DC":{"1X":0,"12":0,"X2":0}
            }
    outcomes=[]
    #print("extra markets betalpha:",ld,teams,tournyid)

    ws = create_connection("wss://www.betonalfa.com.cy/ws/",http_proxy_host=proxies[0].split(":")[0],http_proxy_port=proxies[0].split(":")[1])

    #print("trying -->",ld,"<--")
    ws.send(json.dumps({"subscribe":{"object":"match","ids":str(ld),"pathname":"match/t/"+ str(tournyid) +"/id/" + str(ld),"wakeupCount":0,"marketfilter":"all","comp":"selected-match","dl":"0"}}))
    retval = ws.recv()# this gets request confirmation..
    #print(len(retval))
    retval = ws.recv()# this gets garbage
    #print(len(retval))
    while 1:
        retval = ws.recv()# this is the response data json
        data = json.loads(retval) # have to loop this until you get the confirmation.. then load one more and break
        if 'subscription' in data:
            if 'request' in data['subscription']:
                retval = ws.recv()
                data = json.loads(retval)
                
                #print("betalpha found:",ld,"data")
                for msg in data['messages']:
                    if msg['object']=='market':
                        if msg['marketTypeId']==40 and msg['special']=='2.5':
                            #uo25..
                            #print("located UO25")
                            #print("UO25:",msg['selections'][0]['outcome'],msg['selections'][0]['odds'])
                            retdata['2.5'][msg['selections'][0]['outcome']]=msg['selections'][0]['odds']
                            #print("UO25:",msg['selections'][1]['outcome'],msg['selections'][1]['odds'])
                            retdata['2.5'][msg['selections'][1]['outcome']]=msg['selections'][1]['odds']
                            #print("finished UO25")

                        elif msg['marketTypeId']==34:
                            #DNB
                            #print("located DNB")
                            #print("DNB:",msg['selections'][0]['outcome'],msg['selections'][0]['odds'])
                            retdata['DNB'][msg['selections'][0]['outcome'].replace("1","Home").replace("2","Away")]=msg['selections'][0]['odds']

                            #print("DNB:",msg['selections'][1]['outcome'],msg['selections'][1]['odds'])
                            retdata['DNB'][msg['selections'][1]['outcome'].replace("1","Home").replace("2","Away")]=msg['selections'][1]['odds']
                            #print("finished UO25")

                        elif msg['marketTypeId']==28:
                            #print("located 1x2")
                            #print("1x2:",msg['selections'][0]['outcome'],msg['selections'][0]['odds'])
                            outcomes.append({"name":teams[0],"price":msg['selections'][0]['odds']})
                            #print("1x2:",msg['selections'][1]['outcome'],msg['selections'][1]['odds'])
                            outcomes.append({"name":"X","price":msg['selections'][2]['odds']})
                            #print("1x2:",msg['selections'][2]['outcome'],msg['selections'][2]['odds'])
                            outcomes.append({"name":teams[1],"price":msg['selections'][1]['odds']})
                            #print("finished 1x2")

                #print("")            
                break
        else:
            pass#print(data.keys())
        #time.sleep(0.1)
    ws.close()
    #now pull these marketids for this event, and extract the POIs
    """try:
        outcomes.append({"name":teams[0],"price":home_outcome})
        outcomes.append({"name":"X","price":draw_outcome})
        outcomes.append({"name":teams[1],"price":away_outcome})
        
    except:
        pass"""

    #if len(retdata['2.5'])<2:
    #    retdata['2.5']=[0,0]
    #if len(retdata['3.5'])<2:
    #    retdata['3.5']=[0,0]
    #if len(retdata['DNB'])<2:
    #    retdata['DNB']=[0,0]
    #print(outcomes,retdata)

    return outcomes,retdata

def betalpha_data_thread(f,compid):
            #print(f['id'])
            outcomes=[]
            extra_markets=[]

            """outcomes=[]
            
            markets = f['markets']
            home_outcome= markets[0]['outcomes'][0]['prices'][0]['decimal']
            home = markets[0]['outcomes'][0]['name']
            draw_outcome=markets[0]['outcomes'][1]['prices'][0]['decimal']
            draw =markets[0]['outcomes'][1]['name']
            away_outcome=markets[0]['outcomes'][2]['prices'][0]['decimal']
            away = markets[0]['outcomes'][2]['name']
            outcomes.append({"name":home,"price":home_outcome})
            outcomes.append({"name":draw,"price":draw_outcome})
            outcomes.append({"name":away,"price":away_outcome})"""
            #print(outcomes)
            #here check for other markets.. totals dnb
            #here you call in the other markets for this eventId=
            try:
                #print("attempting betalpha outomes/other_markets:",f)
                outcomes,other_markets = get_extra_markets_betalpha(f[0],f[1],compid)
            except Exception as msg:
                pass#print("err in extra markets",str(msg))#print("extra markets >> ")

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
            #print({"id":f[0],"book":outcomes,"markets":extra_markets,"start_time":f[2]})
            return {"id":f[0],"book":outcomes,"markets":extra_markets,"start_time":f[2]}

def pull_data_betalpha(compid,league):#add comp_data as mutable param
    #print("BETALPHA MAIN >>>")

    comp_data=[]
    e_list=[]

            
    #print(">> TOTO thread pull")
    #create connection
    ws = create_connection("wss://www.betonalfa.com.cy/ws/",http_proxy_host=proxies[0].split(":")[0],http_proxy_port=proxies[0].split(":")[1])

    #get fixture list for tourny 51 = EPL
    ws.send(json.dumps({"subscribe":{"object":"tournament","ids":str(compid),"pathname":"sports/t/"+ str(compid) + "/sf/3","wakeupCount":0,"marketfilter":"primary","comp":"sports-coupon-selection","dl":"0"}}))

    retval = ws.recv()# this gets request confirmation..
    retval = ws.recv()# this gets garbage
    while 1:
        retval = ws.recv()# this is the response data json
        data = json.loads(retval) # have to loop this until you get the confirmation.. then load one more and break
        if 'subscription' in data:
            if 'request' in data['subscription']:
                retval = ws.recv()
                data = json.loads(retval)
                #print("FOUND BETALPHA DATA..")
                break

    ws.close()

    matchids=[]
    #print("BETALPHA building matchlist..",len(data['messages']))
    for msg in data['messages']:
        #print(msg['object'])
        if msg['object']=='match':
            matchid = msg['id']
            if matchid not in matchids:
                try:
                    e_list.append([matchid,[msg['competitors'][0],msg['competitors'][1]],str(msg['startTs'])[0:10]])
                except Exception as msg:
                    pass#print("err with alphabuild:",str(msg))
        
    #print(e_list)
    #print("e_list_len:",len(e_list))    

    with concurrent.futures.ThreadPoolExecutor(max_workers=thread_count) as executor:
        future_to_url = {executor.submit(betalpha_data_thread, e,compid): e for e in e_list}
        for future in concurrent.futures.as_completed(future_to_url):
            #url = future_to_url[future]
            try:
                data = future.result()
                comp_data.append(data)
            except Exception as exc:
                pass#print('%r generated an exception: %s' % ("brr", exc))

    for cd in comp_data:
        try:
            pass#do_odds_history_insert("betalpha", cd['id'],cd['book'],cd['markets'])
        except Exception as msg:
            pass#print("err on odds history insert..",str(msg))  
    #    print(">>",cd)
    #print("--END TOTO--")
    with open("/home/arb_bot/gamma/betalpha_dumps/" +  compid  + ".json","w") as f:
        f.write(json.dumps(comp_data))
    return comp_data



def get_team_list_betalpha():
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



def insert_to_database_betalpha(t,b,league):
    conn = pymysql.connect(host='localhost',user='local',passwd='oeijifjwejfio',db=db_name)
    cur  = conn.cursor()
    toto_teamnames = t['matchup_raw']
    t1fuzzy,t2fuzzy=0,0
    #print("betalpha YO>>>>>>>>>>",t,b)
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
    odds_json={"betalpha_1_odds":toto_1_odds,"betalpha_x_odds":toto_x_odds,"betalpha_2_odds":toto_2_odds,"betalpha_under_2.5":toto_under_2p5,"betalpha_over_2.5":toto_over_2p5,"betalpha_under_3.5":toto_under_3p5,"betalpha_over_3.5":toto_over_3p5,"betalpha_dnb_home":toto_dnb_home,"betalpha_dnb_away":toto_dnb_away,
               "betalpha_dc_1x":toto_dc_1x,"betalpha_dc_12":toto_dc_12,"betalpha_dc_x2":toto_dc_x2,
           "betalpha_1_ht":toto_1_ht,"betalpha_x_ht":toto_x_ht,"betalpha_2_ht":toto_2_ht,
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
    cur.execute("select * from betalpha_matches where betalpha_event_id=%s and betfair_event_id=%s",(t['event_id'],b['event_id']))
    rows = cur.fetchall()
    if len(rows)>0:
        #print("found event,, updating",t['event_id'],b['event_id'])
        cur.execute("update betalpha_matches set timestamp=%s,betalpha_data=%s,t1_betalpha_fuzzy=%s,t2_betalpha_fuzzy=%s where betalpha_event_id=%s and betfair_event_id=%s",
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
        """if len(b['back_25'])==0:
            b['back_25'] = [["Under_2.5",0,0,0,0],["Over_2.5",0,0,0,0]]

        if len(b['lay_25'])==0:
            b['back_25'] = [["Under_2.5",0,0],["Over_2.5",0,0]]


        if len(b['back_35'])==0:
            b['back_35'] = [["Under_3.5",0,0,0,0],["Over_3.5",0,0,0,0]]

        if len(b['lay_35'])==0:
            b['back_35'] = [["Under_3.5",0,0],["Over_3.5",0,0]]
               

        if len(b['back_dnb'])==0:
            b['back_dnb'] = [["dnb_home",0,0,0,0],["dnb_away",0,0,0,0]]

        if len(b['lay_dnb'])==0:
            b['back_25'] = [["dnb_home",0,0],["dnb_away",0,0]]"""
            
        cur.execute("insert into betalpha_matches (timestamp,betalpha_event_id,betfair_event_id,team_1_betalpha,team_2_betalpha,team_1_betfair,team_2_betfair,betalpha_data,t1_betalpha_fuzzy,t2_betalpha_fuzzy,ignored,league) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (b['timestamp'],t['event_id'],b['event_id'],toto_teamnames[0],toto_teamnames[1],bf_teamnames[0],bf_teamnames[1],json.dumps(odds_json),t1fuzzy,t2fuzzy,0,league))
    conn.commit()
    conn.close()
    

def align_matches(book_data,ref_data,league):
    #here i run through,, so loop over book data,,
    books_left=[]
    matched=0
    total_bookdata=len(book_data)
    total_refdata = len(ref_data)
    
    print("betalpha-ALIGN:",total_bookdata,total_refdata)

        
    # look for a single team exact match,, and a timestamp match..
    for bd in book_data:
        found=False
        match_data=[]
        if bd['book']==[]:
            continue
        for rd in ref_data:#this is a list not the dict version
            print("aligning:",bd,rd)
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

                    insert_to_database_betalpha(tt,rd,league)
                    
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
                        insert_to_database_betalpha(tt,rd,league)
                    
            if not found:
                unmatched.append(bd)

def do_insert_betalpha(toto_data,betfair_data,league,toto_teams):
    #global toto_teams
    #print("doing fuzzy and insert TOTO")

    
    #pull all bf matches, and subsequent team names.. for fuzzy match
    
    
    #convert into list of lists
    #print("toto:",len(toto_data),"bf:",len(betfair_data),league)
    
    try:
        
        if len(toto_data)>0 and len(betfair_data)>0:
            print("betalpha-INSERT:",len(toto_data),"bf:",len(betfair_data),league)
            bf_data=convert_ref_matches(betfair_data)
            align_matches(toto_data,bf_data,league)
    except Exception as msg:
        print("alignment error:",str(msg))
