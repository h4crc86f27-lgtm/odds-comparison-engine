import pymysql
import configparser
import requests
import random
import json
from arber_modules.utils import *
import time
from fuzzywuzzy import fuzz
import json

config = configparser.ConfigParser()
config.read('config.ini')
print(config.sections())
db_name = config['DEFAULT']['db_name']

with open("/home/arb_bot/proxies") as f:
    proxies = f.read().split("\n")

try:
    proxies.remove('')
except:
    pass



def pull_extra_markets_contra(eventid):# = "5316624"):

    res = requests.post("https://s.linex11.com/api/front/events/details",
                        data={"EventId":str(eventid)},proxies = {"https":random.choice(proxies)})
    data = res.json()
    event_data = json.loads(data['MarketsString'].replace("\\",""))
    retval={"2.5":{"Over":0,"Under":0},
            "3.5":{"Over":0,"Under":0},
            "DNB":{"Home":0,"Away":0}
            }
    for e in event_data:
        if e['Key']=="OU":
            for line in e['Lines']:
                if line['Specifier'] in ['2.5','3.5']:
                    retval[line['Specifier']][line['Odds'][0]['Outcome']]=line['Odds'][0]['Value']
                    retval[line['Specifier']][line['Odds'][1]['Outcome']]=line['Odds'][1]['Value']
        elif e['Key']=='DNB':
            retval['DNB']['Home']=e['Lines'][0]['Odds'][0]['Value']
            retval['DNB']['Away']=e['Lines'][0]['Odds'][1]['Value']
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
        res=requests.post("https://s.linex11.com/api/front/events",data=payload,proxies = {"https":random.choice(proxies)})
        data = res.json()
        for d in data:
            #comps[d['TournamentId']]={"category":d['Category'],"name":d['Tournament'],"events":d['DateEvents']}
            compid = d['Category'] + "_" + d['Tournament']
            if compid not in ids_done:
                print("adding contra comp:",d['Category'] + " " + d['Tournament'])
                x=cur.execute("insert into raw_comps(comp_name,comp_id,site,timestamp) values(%s,%s,%s,%s)",(d['Category'] + " " + d['Tournament'],compid,"contra",time.time()))

        if len(data)<300:
            break
    conn.commit()
    conn.close()
    #return comps



## CONTRA

def pull_data_contra(compid,league):#country,tourny):
    print("CONTRA DATA>>>>>>")
    cat,tourn = compid.split("_")
    payload={"Live":"true","Sport":"football",
             "Categories[]":cat.lower(),
             "DateTo":"",
             "Tournaments[]":tourn.lower()}

    comp_data=[]
    for counter in range(3):
        try:
            res=requests.post("https://s.linex11.com/api/front/events",data=payload,proxies = {"https":random.choice(proxies)})
            break
        except:
            print("contra comp err,, retrying")

    data = res.json()
    
    event_dates = data[0]['DateEvents']
    for ed in event_dates:
        events = ed['Events']
        for e in events:
            outcomes=[]
            extra_markets=[]
            home = e['Home']
            away = e['Away']
            timestamp = e['Date'] +"Z"
            markets= json.loads(e['MarketsString'].replace("\\",""))
            
            for m in markets:
                #print(m['Key'])
                if m['Key']=='1x2':
                    #h2h odds..
                    home_odds = m['Lines'][0]['Odds'][0]['Value']
                    draw_odds = m['Lines'][0]['Odds'][1]['Value']
                    away_odds = m['Lines'][0]['Odds'][2]['Value']
                    outcomes.append({"name":home,"price":home_odds})
                    outcomes.append({"name":"X","price":draw_odds})
                    outcomes.append({"name":away,"price":away_odds})
                    break

            ## extra markets pull here..
            extra_contra_markets = pull_extra_markets_contra(e['EventId'])
            extra_markets.append({"name":"2.5_Under","price":extra_contra_markets['2.5']['Under']})
            extra_markets.append({"name":"2.5_Over","price":extra_contra_markets['2.5']['Over']})
            extra_markets.append({"name":"3.5_Under","price":extra_contra_markets['3.5']['Under']})
            extra_markets.append({"name":"3.5_Over","price":extra_contra_markets['3.5']['Over']})
            extra_markets.append({"name":"DNB_Home","price":extra_contra_markets['DNB']['Home']})
            extra_markets.append({"name":"DNB_Away","price":extra_contra_markets['DNB']['Away']})

            comp_data.append({"id":e['EventId'],"book":outcomes,"markets":extra_markets,"start_time":timestamp})#just once? has all outcomes in there..
            print(":::CONTRA--:::",{"id":e['EventId'],"book":outcomes,"markets":extra_markets,"start_time":timestamp})


            
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

    print("###",b)
    #insert section  here need to add the extra market odds..
    odds_json={"contra_1_odds":toto_1_odds,"contra_x_odds":toto_x_odds,"contra_2_odds":toto_2_odds,"contra_over_2.5":contra_over_2p5,"contra_under_2.5":contra_under_2p5,"contra_over_3.5":contra_over_3p5,"contra_under_3.5":contra_under_3p5,"contra_dnb_home":contra_dnb_home,"contra_dnb_away":contra_dnb_away,
               "bf_1_odds":{"last_back_price":bf_1_last_back_odds,"last_back_vol":bf_1_last_back_vol,"lowest_back_price":bf_1_lowest_back_odds,"lowest_back_vol":bf_1_lowest_back_vol,"lay_price":bf_1_lay_odds,"lay_vol":bf_1_lay_vol},"bf_x_odds":{"last_back_price":bf_x_last_back_odds,"last_back_vol":bf_x_last_back_vol,"lowest_back_price":bf_x_lowest_back_odds,"lowest_back_vol":bf_x_lowest_back_vol,"lay_price":bf_x_lay_odds,"lay_vol":bf_x_lay_vol},"bf_2_odds":{"last_back_price":bf_2_last_back_odds,"last_back_vol":bf_2_last_back_vol,"lowest_back_price":bf_2_lowest_back_odds,"lowest_back_vol":bf_2_lowest_back_vol,"lay_price":bf_2_lay_odds,"lay_vol":bf_2_lay_vol},"bf_Under_2.5":{"last_back_price":b['back_25'][0][1],"last_back_vol":b['back_25'][0][2],"lowest_back_price":b['back_25'][0][3],"lowest_back_vol":b['back_25'][0][4],"lay_price":b['lay_25'][0][1],"lay_vol":b['lay_25'][0][1]},"bf_Over_2.5":{"last_back_price":b['back_25'][1][1],"last_back_vol":b['back_25'][1][2],"lowest_back_price":b['back_25'][1][3],"lowest_back_vol":b['back_25'][1][4],"lay_price":b['lay_25'][1][1],"lay_vol":b['lay_25'][1][1]},"bf_Under_3.5":{"last_back_price":b['back_35'][0][1],"last_back_vol":b['back_35'][0][2],"lowest_back_price":b['back_35'][0][3],"lowest_back_vol":b['back_35'][0][4],"lay_price":b['lay_35'][0][1],"lay_vol":b['lay_35'][0][1]},"bf_Over_3.5":{"last_back_price":b['back_35'][1][1],"last_back_vol":b['back_35'][1][2],"lowest_back_price":b['back_35'][1][3],"lowest_back_vol":b['back_35'][1][4],"lay_price":b['lay_35'][1][1],"lay_vol":b['lay_35'][1][1]},"bf_dnb_home":{"last_back_price":b['back_dnb'][0][1],"last_back_vol":b['back_dnb'][0][2],"lowest_back_price":b['back_dnb'][0][3],"lowest_back_vol":b['back_dnb'][0][4],"lay_price":b['lay_dnb'][0][1],"lay_vol":b['lay_dnb'][0][1]},"bf_dnb_away":{"last_back_price":b['back_dnb'][1][1],"last_back_vol":b['back_dnb'][1][2],"lowest_back_price":b['back_dnb'][1][3],"lowest_back_vol":b['back_dnb'][1][4],"lay_price":b['lay_dnb'][1][1],"lay_vol":b['lay_dnb'][1][1]}}
    print("<><><>",odds_json)



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


def do_insert_contra(contra_data,betfair_data,league):
    #print("doing fuzzy and insert contra")

    
    #pull all bf matches, and subsequent team names.. for fuzzy match
    
    bf_data = betfair_data
    #convert into list of lists
    print("contra:",len(contra_data),"bf:",len(betfair_data),league)
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
                    pass
                try:
                    lay_35.append(["Under_3.5",bf_data[b]['markets'][2]['lay_price_Under_3.5'],bf_data[b]['markets'][2]['lay_vol_Under_3.5']])
                    lay_35.append(["Over_3.5",bf_data[b]['markets'][3]['lay_price_Over_3.5'],bf_data[b]['markets'][3]['lay_vol_Over_3.5']])
                except:
                    pass

                try:
                    back_dnb.append(["DNB_Home",bf_data[b]['markets'][4]['last_back_price_DNB_Home'],bf_data[b]['markets'][4]['last_back_vol_DNB_Home'],bf_data[b]['markets'][4]['lowest_back_price_DNB_Home'],bf_data[b]['markets'][4]['lowest_back_vol_DNB_Home']])
                    back_dnb.append(["DNB_Away",bf_data[b]['markets'][5]['last_back_price_DNB_Away'],bf_data[b]['markets'][5]['last_back_vol_DNB_Away'],bf_data[b]['markets'][5]['lowest_back_price_DNB_Away'],bf_data[b]['markets'][5]['lowest_back_vol_DNB_Away']])
                except:
                    print("err on dnb_home",bf_data[b]['markets'][4])
                    pass
                
                try:
                    lay_dnb.append(["DNB_Home",bf_data[b]['markets'][4]['lay_price_DNB_Home'],bf_data[b]['markets'][4]['lay_vol_DNB_Home']])
                    lay_dnb.append(["DNB_Away",bf_data[b]['markets'][5]['lay_price_DNB_Away'],bf_data[b]['markets'][5]['lay_vol_DNB_Away']])
                except:
                    pass

                bf_matches.append({"matchup":matchteams,"flipped":flipped,"matchup_raw":matchteams,"lay_book":lay_matchlist,"back_book":back_matchlist,"back_25":back_25,"lay_25":lay_25,"back_35":back_35,"lay_35":lay_35,"back_dnb":back_dnb,"lay_dnb":lay_dnb,'event_id':b,"timestamp":bf_data[b]['timestamp']})
#print("BF>>",{"matchup":matchteams,"flipped":flipped,"matchup_raw":matchteams,"lay_book":lay_matchlist,"back_book":back_matchlist,'event_id':b,"timestamp":bf_data[b]['timestamp']})

        except Exception as msg:
            print("err on betfair match check:",teama,teamb,str(msg))
            try:
                insert_error(str(msg),"err on betfair (ub) match check:",teama,teamb,str(msg))
            except Exception as msg:
                print(">>> insert err error..",str(msg))

            
    print("bf data check")
    #for b in bf_matches:
    #    print(b)

    print("------------------------>")
    
    tt_data = contra_data#pickle.load(f)
    #print("CONTRA>>>>>>>")
    #print(tt_data[0])
    #print("<<<<<<<<")
    #here pull from db, and whittle down to unique,, then create the list..
    #toto_teams = get_team_list_toto()
    contra_teams = get_team_list_contra()

    print("there are:",len(contra_teams),"teams")   

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
            print(">>",runner['name'],"<<")
            if runner['name']!='Draw' and runner['name']!='' and   runner['name']!='X':
                matchteams_raw.append(runner['name'])
                #try to match it,, if not,, fuzzy?
                if runner['name'].upper() in contra_teams and contra_teams[runner['name'].upper()]!="":
                    match_data.append([contra_teams[runner['name'].upper()],runner['price'],0])
                    matchteams.append(contra_teams[runner['name'].upper()])
                else:
                    #fuzzy..
                    maxfuzz=0
                    likely_team=""
                    for b in bf_teams:
                        r=fuzz.ratio(b,runner['name'])
                        if r>maxfuzz:
                            maxfuzz=r
                            likely_team=b
                    match_data.append([likely_team,runner['price'],1])
                    print("fuzzy",likely_team,t)
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

    for t in tt_matches:
        print("contra",t)
    found=0
    for t in tt_matches:
        found=0
        for b in bf_matches:
            #print("<><><>",t['matchup'],b['matchup'],t['start_time'][0:10],int(b['timestamp']),str(datetime.datetime.utcfromtimestamp(int(b['timestamp'])).strftime('%Y-%m-%d %H:%M:%S'))[0:10])
            #print("date match:",t['start_time'][0:10],str(datetime.datetime.utcfromtimestamp(int(b['timestamp'])).strftime('%Y-%m-%d %H:%M:%S'))[0:10])
            
            if t['matchup']==b['matchup'] and convert_midnight(t['start_time'])==str(datetime.datetime.utcfromtimestamp(int(b['timestamp'])).strftime('%Y-%m-%d %H:%M:%S'))[0:10]:
                
                insert_to_database_contra(t,b,league)
                found=1
                break
            else:
                pass#print("UNMATCHED<<<<<",t['matchup'],b['matchup'],t['start_time'][0:10],int(b['timestamp']),str(datetime.datetime.utcfromtimestamp(int(b['timestamp'])).strftime('%Y-%m-%d %H:%M:%S'))[0:10])
            
                
    if not found:
        #print("NOT MATCHED:",t['matchup'],b['matchup'])
        conn = pymysql.connect(host='localhost',user='local',passwd='oeijifjwejfio',db=db_name)
        cur  = conn.cursor()
        #print("select * from unmatched where start_time=%s and team1=%s and team2=%s",(t['start_time'],t['matchup_raw'][0],t['matchup_raw'][1]))

        cur.execute("select * from contra_unmatched where start_time=%s and team1=%s and team2=%s",(t['start_time'],t['matchup_raw'][0],t['matchup_raw'][1]))
        rows =cur.fetchall()
        if len(rows)==0:
            cur.execute("insert into contra_unmatched (team1,team2,league,start_time,timestamp) values(%s,%s,%s,%s,%s)",(t['matchup_raw'][0],t['matchup_raw'][1],league,t['start_time'],time.time()))
            conn.commit()
        conn.close()    

