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



def pull_extra_markets_contra(eventid):# = "5316624"):
    #print("..in extra..",eventid)
    res = requests.post("https://s2.bettendo.com/api/front/events/details",
                        data={"EventId":str(eventid)},proxies = {"https":random.choice(proxies)},timeout=timeout_count)
    #print("out extra..",res.reason,eventid)
    data = res.json()
    #print("is json")
    event_data = json.loads(data['MarketsString'].replace("\\",""))
    #print("jsonloaded")
    retval={"2.5":{"Over":0,"Under":0},
            "3.5":{"Over":0,"Under":0},
            "DNB":{"Home":0,"Away":0},
            "1x2_HT":{"1":0,"X":0,"2":0},
            "DC":{"1X":0,"12":0,"X2":0}
            }
    for e in event_data:
        if e['Group']=="OU" and e['Key']=='2':
            for line in e['Lines']:
                if line['Specifier'] in ['2.5','3.5']:
                    try:
                        retval[line['Specifier']][line['Odds'][0]['Outcome']]=line['Odds'][0]['Value']
                    except:
                        pass

                    try:
                        retval[line['Specifier']][line['Odds'][1]['Outcome']]=line['Odds'][1]['Value']
                    except:
                        pass
        elif e['Group']=='DNB' and e['Key']=='52':
            try:
                retval['DNB']['Home']=e['Lines'][0]['Odds'][0]['Value']
            except:
                pass
        
            try:
                retval['DNB']['Away']=e['Lines'][0]['Odds'][1]['Value']
            except:
                pass
        """elif e['Group']=="DC":
            adds={}
            order=['1X','X2','12']
            adds[e['Lines'][0]['Odds'][0]['Outcome']]=e['Lines'][0]['Odds'][0]['Value']
            adds[e['Lines'][0]['Odds'][1]['Outcome']]=e['Lines'][0]['Odds'][1]['Value']
            adds[e['Lines'][0]['Odds'][2]['Outcome']]=e['Lines'][0]['Odds'][2]['Value']
            
            for o in order:
                retval['DC'][o] = adds[o]
                
            #retval['DC'][e['Lines'][0]['Odds'][0]['Outcome']]=e['Lines'][0]['Odds'][0]['Value']
            #retval['DC'][e['Lines'][0]['Odds'][1]['Outcome']]=e['Lines'][0]['Odds'][1]['Value']
            #retval['DC'][e['Lines'][0]['Odds'][2]['Outcome']]=e['Lines'][0]['Odds'][2]['Value']
        elif e['Group']=="1x2_H1":
            adds ={}
            order=["1","X","2"]
            adds[e['Lines'][0]['Odds'][0]['Outcome']] = e['Lines'][0]['Odds'][0]['Value']
            adds[e['Lines'][0]['Odds'][1]['Outcome']] = e['Lines'][0]['Odds'][1]['Value']
            adds[e['Lines'][0]['Odds'][2]['Outcome']] = e['Lines'][0]['Odds'][2]['Value']
            for o in order:
                retval['1x2_HT'][o]=adds[o]

            #retval['1x2_HT'][e['Lines'][0]['Odds'][0]['Outcome']]=e['Lines'][0]['Odds'][0]['Value']
            #retval['1x2_HT'][e['Lines'][0]['Odds'][1]['Outcome']]=e['Lines'][0]['Odds'][1]['Value']
            #retval['1x2_HT'][e['Lines'][0]['Odds'][2]['Outcome']]=e['Lines'][0]['Odds'][2]['Value']"""
    print(eventid,retval)
    return retval


def do_contra_raw():
    conn = pymysql.connect(host='localhost',user='local',passwd='oeijifjwejfio',db=db_name)
    cur  = conn.cursor()
    cur.execute("select * from raw_comps where site='contra'")
    rows = cur.fetchall()
    ids_done=[]
    for row in rows:
        ids_done.append(row[2])

    comps={}
    # soccer events pull
    for p in range(0,5):
        payload={"Sport":"football","Take":300,"Page":p}
        #old >> 
        res=requests.post("https://s2.bettendo.com/api/front/events",data=payload,proxies = {"https":random.choice(proxies)},timeout=3)
        data = res.json()
        for d in data:
            #comps[d['TournamentId']]={"category":d['Category'],"name":d['Tournament'],"events":d['DateEvents']}
            compid = d['Category'] + "_" + d['Tournament']
            if compid not in ids_done:
                #print("adding contra comp:",d['Category'] + " " + d['Tournament'])
                x=cur.execute("insert into raw_comps(comp_name,comp_id,site,timestamp) values(%s,%s,%s,%s)",(d['Category'] + " " + d['Tournament'],compid,"contra",time.time()))

        if len(data)<300:
            break
    conn.commit()
    conn.close()
    #return comps



## CONTRA

def contra_data_thread(e):
    outcomes=[]
    extra_markets=[]
    home = e['Home']
    away = e['Away']
    timestamp = e['Date'] +"Z"
    markets= json.loads(e['MarketsString'].replace("\\",""))
    #print("contra:",home,away ,">>>>>>>")
    #with open("/home/arb_bot/gamma/contra_dumps/" + str(e['EventId']) + ".json","w") as f:
    #    f.write(json.dumps(e))
    #with open("/home/arb_bot/gamma/contra_dumps/" + str(e['EventId']) + "-markets.json","w") as f:
    #    f.write(json.dumps(markets))
    

    for m in markets:
        #print(m['Key'])
        if m['Group']=='1x2' and m['Key']=='1':
            #h2h odds..
            le_odds={"1":0,"X":0,"2":0}
            for odd in m['Lines'][0]['Odds']:
                le_odds[odd['Outcome']] = odd['Value']

            #print(home,away,le_odds)
            

           
            outcomes.append({"name":home,"price":le_odds['1']})
            outcomes.append({"name":"X","price":le_odds['X']})
            outcomes.append({"name":away,"price":le_odds['2']})
            break
    #print("contra:",outcomes)
    ## extra markets pull here..
    try:
        extra_contra_markets = pull_extra_markets_contra(e['EventId'])
    except Exception as msg:
        pass#print("contra extra err:",home,away,str(msg))
    extra_markets.append({"name":"2.5_Under","price":extra_contra_markets['2.5']['Under']})
    extra_markets.append({"name":"2.5_Over","price":extra_contra_markets['2.5']['Over']})
    extra_markets.append({"name":"3.5_Under","price":extra_contra_markets['3.5']['Under']})
    extra_markets.append({"name":"3.5_Over","price":extra_contra_markets['3.5']['Over']})
    extra_markets.append({"name":"DNB_Home","price":extra_contra_markets['DNB']['Home']})
    extra_markets.append({"name":"DNB_Away","price":extra_contra_markets['DNB']['Away']})
    extra_markets.append({"name":"DC_1X","price":extra_contra_markets['DC']['1X']})
    extra_markets.append({"name":"DC_X2","price":extra_contra_markets['DC']['X2']})
    extra_markets.append({"name":"DC_12","price":extra_contra_markets['DC']['12']})
    extra_markets.append({"name":"1_HT","price":extra_contra_markets['1x2_HT']['1']})
    extra_markets.append({"name":"X_HT","price":extra_contra_markets['1x2_HT']['X']})
    extra_markets.append({"name":"2_HT","price":extra_contra_markets['1x2_HT']['2']})
    
    #print("contra:",outcomes,extra_markets)

    return {"id":e['EventId'],"book":outcomes,"markets":extra_markets,"start_time":timestamp} 
    #just once? has all outcomes in there..

def pull_data_contra(compid,league):#country,tourny):
    #print("CONTRA DATA>>>>>>")

    cat,tourn = compid.split("_")
    payload={"Live":"true","Sport":"football",
             "Categories[]":cat.lower(),
             "DateTo":"",
             "Tournaments[]":tourn.lower()}

    comp_data=[]
    for counter in range(3):
        try: 
            #old url >> s.linex11
            
            res=requests.post("https://s2.bettendo.com/api/front/events",data=payload,proxies = {"https":random.choice(proxies)},timeout=timeout_count)
            #print("contra,, got there..>> ",compid,res.text[0:20],res.status_code)
            break
        except Exception as msg:
            pass#print("contra comp err,, retrying",str(msg))

    data = res.json()
    e_list=[]
    event_dates = data[0]['DateEvents']
    for ed in event_dates:
        events = ed['Events']
        for e in events:
            e_list.append(e)
    #here, send off e_list to threadPool.. get results, and then append them all to comp_data
    #print("contra elistlen:",len(e_list))

    with concurrent.futures.ThreadPoolExecutor(max_workers=thread_count) as executor:
        future_to_url = {executor.submit(contra_data_thread, e): e for e in e_list}
        for future in concurrent.futures.as_completed(future_to_url):
            #url = future_to_url[future]
            try:
                data = future.result()
                comp_data.append(data)
                
            except Exception as exc:
                pass#print('CONTRA.. %r generated an exception: %s' % ("brr", exc))
    #print(":::CONTRA--:::",len(comp_data))
    #for cd in comp_data:
    #    print(">>",cd)
    #print("--END CONTRA--")
    for cd in comp_data:
        try:
            pass#do_odds_history_insert("contra", cd['id'],cd['book'],cd['markets'])
        except Exception as msg:
            pass#print("err on odds history insert..",str(msg))   
    #print(comp_data)
    #print("^^ CON CD")

    #with open("/home/arb_bot/beta_bingoal_fastbf/contra_dumps/" +  compid  + ".json","w") as f:
    #    f.write(json.dumps(comp_data))

    return comp_data


def get_team_list_contra():
    #print("<building team list>")
    conn = pymysql.connect(host='localhost',user='local',passwd='oeijifjwejfio',db=db_name)
    cur  = conn.cursor()
    cur.execute("select contra_name,betfair_name from contra_teams")
    rows = cur.fetchall()
    teams={}
    for row in rows:
        teams[row[0].upper()]=row[1]
        teams[strip_accents(row[0]).upper()]=row[1]
    conn.close()
    #print("<team list built>")
    return teams


def insert_to_database_contra(t,b,league):
    conn = pymysql.connect(host='localhost',user='local',passwd='oeijifjwejfio',db=db_name)
    cur  = conn.cursor()
    contra_teamnames = t['matchup_raw']
    #print("CONTRA INSERT AREA:::",t,b)
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


        temp = contra_teamnames[0]
        contra_teamnames[0] = contra_teamnames[1]
        contra_teamnames[1] = temp
        

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
    contra_over_2p5=0
    contra_under_2p5=0
    contra_over_3p5=0
    contra_under_3p5=0

    for outcome in t['markets']:
        if outcome['name']=='2.5_Over':
            contra_over_2p5 = outcome['price']
        elif outcome['name']=='2.5_Under':
            contra_under_2p5 = outcome['price']
        elif outcome['name']=='3.5_Under':
            contra_under_3p5 = outcome['price']
        elif outcome['name']=='3.5_Over':
            contra_over_3p5 = outcome['price']
        elif outcome['name']=='DNB_Home':
            contra_dnb_home = outcome['price']
        elif outcome['name']=='DNB_Away':
            contra_dnb_away = outcome['price']
        elif outcome['name']=='DC_1X':
            if 0:#b['flipped']:
                contra_dc_x2 = outcome['price']
            else:
                contra_dc_1x = outcome['price']
        elif outcome['name']=='DC_12':
            contra_dc_12 = outcome['price']
        elif outcome['name']=='DC_X2':
            if 0:#b['flipped']:
                contra_dc_1x = outcome['price']
            else:
                contra_dc_x2 = outcome['price']
        elif outcome['name']=='1_HT':
            if 0:#b['flipped']:
                contra_2_ht = outcome['price']
            else:
                contra_1_ht = outcome['price']
        elif outcome['name']=='X_HT':
            contra_x_ht = outcome['price']
        elif outcome['name']=='2_HT':
            if 0:#b['flipped']:
                contra_1_ht = outcome['price']
            else:
                contra_2_ht = outcome['price']

    #print("### READY...",b)
    #insert section  here need to add the extra market odds..
    odds_json={"contra_1_odds":toto_1_odds,"contra_x_odds":toto_x_odds,"contra_2_odds":toto_2_odds,
           "contra_over_2.5":contra_over_2p5,"contra_under_2.5":contra_under_2p5,
           "contra_over_3.5":contra_over_3p5,"contra_under_3.5":contra_under_3p5,
           "contra_dnb_home":contra_dnb_home,"contra_dnb_away":contra_dnb_away,
           "contra_dc_1x":contra_dc_1x,"contra_dc_12":contra_dc_12,"contra_dc_x2":contra_dc_x2,
           "contra_1_ht":contra_1_ht,"contra_x_ht":contra_x_ht,"contra_2_ht":contra_2_ht,
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
    
    #print("<><ARE WE THERE YET><>",odds_json)



    #here check for existing..
    cur.execute("select * from contra_matches where contra_event_id=%s and betfair_event_id=%s",(t['event_id'],b['event_id']))
    rows = cur.fetchall()
    if len(rows)>0:
        #print("found CONTRA event,, updating",t['event_id'],b['event_id'])
        cur.execute("update contra_matches set timestamp=%s,contra_data=%s,t1_contra_fuzzy=%s,t2_contra_fuzzy=%s where contra_event_id=%s and betfair_event_id=%s",
                (b['timestamp'],json.dumps(odds_json),t1fuzzy,t2fuzzy,t['event_id'],b['event_id']))
        #print("updated:",t['event_id'],b['event_id'])
    else:
        #print("NO event,, inserting",t['event_id'],b['event_id'])
        #here i do an extra ratio check on toto teams, because somehow are flipping sometimes..
        if fuzz.ratio(contra_teamnames[0],bf_teamnames[0])>fuzz.ratio(contra_teamnames[0],bf_teamnames[1]):
            pass#should be right 
        else:
            #print("flipping:",contra_teamnames[0],contra_teamnames[1])
            temp = contra_teamnames[0]
            contra_teamnames[0] = contra_teamnames[1]
            contra_teamnames[1] = temp

        cur.execute("insert into contra_matches (timestamp,contra_event_id,betfair_event_id,team_1_contra,team_2_contra,team_1_betfair,team_2_betfair,contra_data,t1_contra_fuzzy,t2_contra_fuzzy,ignored,league) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (b['timestamp'],t['event_id'],b['event_id'],contra_teamnames[0],contra_teamnames[1],bf_teamnames[0],bf_teamnames[1],json.dumps(odds_json),t1fuzzy,t2fuzzy,0,league))
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

                    insert_to_database_contra(tt,rd,league)
                    
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
                        insert_to_database_contra(tt,rd,league)
                    
            if not found:
                unmatched.append(bd)

def do_insert_contra(contra_data,betfair_data,league,contra_teams):
    #global contra_teams
    #print("doing fuzzy and insert contra")

    
    #pull all bf matches, and subsequent team names.. for fuzzy match
    
    bf_data = betfair_data
    #convert into list of lists
    #print("contra:",len(contra_data),"bf:",len(betfair_data),league)
    try:        
        if len(contra_data)>0 and len(betfair_data)>0:
            bf_data=convert_ref_matches(betfair_data)
            align_matches(contra_data,bf_data,league)
    except Exception as msg:
        print("alignment error:",str(msg))