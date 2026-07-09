import pymysql
import betfairlightweight
from betfairlightweight import filters
import pandas as pd
import numpy as np
import datetime
import time
import concurrent.futures
import pickle
from arber_modules.utils import *
import json

#with open("comp_dump.pickle","rb") as f:
#    cd = pickle.load(f)

#comps=[]
#for c in cd:
#    comps.append(c['betfair'])

market_get_time=0

thread_count=1
#print(config.sections())
db_name="arb_db_beta"#db_name = config['DEFAULT']['db_name']


my_username ="Marlonallenallen@gmail.com"# cred['username']
my_password = "Ilovepears8#"#cred['password']
my_app_key ="cbAGZjVhp1Rsos3U"# cred['app_key']

trading = betfairlightweight.APIClient(username=my_username,
                                       password=my_password,
                                       app_key=my_app_key,
                                       certs="/home/arb_bot/certs")

trading.login()
#print("logged in!")

# Get a datetime object in a week and convert to string
datetime_in_a_week = (datetime.datetime.utcnow() + datetime.timedelta(weeks=4)).strftime("%Y-%m-%dT%TZ")

def process_event_odds(event_id,event_data):
    retval={"odds":[],"markets":[],
        'vwaps':{"1":0,"X":0,"2":0,
        "Under_2.5":0,"Over_2.5":0,
        "Under_3.5":0,"Over_3.5":0,
        "DNB_Home":0,"DNB_Away":0,
        "DC_12":0,"DC_1X":0,"DC_X2":0,
        "1_HT":0,"2_HT":0,"X_HT":0
        }}
    #retval={"odds":[],"vwaps":{"1":0,"X":0,"2":0}}

    match_book = event_data['match_data']
    
    uo25_book = event_data['uo25_data']
    dnb_book = event_data['dnb_data']
    #print("h2h ..")
    which_side=0
    try:
        if not match_book:
            z=1/0
        for runner in match_book:
            #print(vars(runner))
            which_side+=1
            if which_side==1:
                which_market="1"
            elif which_side==2:
                which_market="X"
            else:
                which_market="2"##presumably..
            #traded_table={}
            last_back_vol = 0
            #print("---")#,runner.name)
            #last_back_price = runner.last_price_traded
            vwap = 0
            total_vol =0
            for tv in runner.ex.traded_volume:
                #if last_back_price == tv.price:
                try:
                    last_back_vol += tv.size
                    #print(tv.price,tv.size)
                    #break
                    vwap += tv.size*tv.price
                    total_vol+=tv.size
                except:
                    pass
            try:
                vwap = vwap/total_vol
            except:
                pass
            #print("<<<")
            try:
                last_back_price = runner.ex.available_to_back[0].price
            except:
                last_back_price =0 
            try:
                lay_price = runner.ex.available_to_lay[0].price
            except:
                lay_price = 0
            try:
                lay_volume = runner.ex.available_to_lay[0].size
            except:
                lay_volume = 0
            retval['vwaps'][which_market]=round(vwap,2)
            retval['odds'].append({"last_back_price":last_back_price,"last_back_vol":last_back_vol,"lowest_back_price":0,"lowest_back_vol":0,"lay_price":lay_price,"lay_vol":lay_volume})  
    except Exception as msg:
        #insert_error(str(msg),"error in getting betfair book:" + event_id + " -- " + event.event.name + " ("  + ")")
        print(str(msg),"H2H",event_id,which_market)
        retval['odds'].append({"last_back_price":0,"last_back_vol":0,"lowest_back_price":0,"lowest_back_vol":0,"lay_price":lay_price,"lay_vol":0})
        

    #uo25
    #print("UO25..")
    try:
        books = uo25_book#get_market_books([ou25_id])
        #print("runnercount:(2.5)",len(books[0].runners))
        which_side=0
        if not uo25_book:
            z=1/0
        for runner in books:
            which_side+=1
            if which_side==1:
                which_market="Under_2.5"
            else:
                which_market="Over_2.5"
            #traded_table={}
            last_back_vol_ou25 = 0
            vwap = 0
            total_vol =0
            for tv in runner.ex.traded_volume:
                #if last_back_price == tv.price:
                try:
                    last_back_vol_ou25 += tv.size
                    vwap += tv.size*tv.price
                    total_vol+=tv.size
                except:
                    pass

            try:
                vwap = vwap/total_vol
            except:
                pass
            try:
                last_back_price_ou25 = runner.ex.available_to_back[0].price
            except:
                last_back_price_ou25 =0 

            try:
                lay_price_ou25 = runner.ex.available_to_lay[0].price
            except:
                lay_price_ou25 = 0

            try:
                lay_volume_ou25 = runner.ex.available_to_lay[0].size
            except:
                lay_volume_ou25 = 0
            retval['vwaps'][which_market]=round(vwap,2)
            retval['markets'].append({"last_back_price_"+which_market:last_back_price_ou25,"last_back_vol_"+which_market:last_back_vol_ou25,"lowest_back_price_"+which_market:0,"lowest_back_vol_"+which_market:0,"lay_price_"+which_market:lay_price_ou25,"lay_vol_"+which_market:lay_volume_ou25})
    except Exception as msg:
        which_market="Under_2.5"
        retval['markets'].append({"last_back_price_"+which_market:0,"last_back_vol_"+which_market:0,"lowest_back_price_"+which_market:0,"lowest_back_vol_"+which_market:0,"lay_price_"+which_market:0,"lay_vol_"+which_market:0})
        which_market="Over_2.5"
        retval['markets'].append({"last_back_price_"+which_market:0,"last_back_vol_"+which_market:0,"lowest_back_price_"+which_market:0,"lowest_back_vol_"+which_market:0,"lay_price_"+which_market:0,"lay_vol_"+which_market:0})
        

    #uo35
    #print("Uo35..")
    which_market="Under_3.5"
    retval['markets'].append({"last_back_price_"+which_market:0,"last_back_vol_"+which_market:0,"lowest_back_price_"+which_market:0,"lowest_back_vol_"+which_market:0,"lay_price_"+which_market:0,"lay_vol_"+which_market:0})
    which_market="Over_3.5"
    retval['markets'].append({"last_back_price_"+which_market:0,"last_back_vol_"+which_market:0,"lowest_back_price_"+which_market:0,"lowest_back_vol_"+which_market:0,"lay_price_"+which_market:0,"lay_vol_"+which_market:0})
    


    #dnb
    #print("DNB..")
    try:
        books = dnb_book#get_market_books([dnb_id])
        if not dnb_book:
            z=1/0
        if 1:#len(books)>0:
            #print("runnercount(DNB):",len(books[0].runners))
            which_side=0
            for runner in books:
                which_side+=1
                if which_side==1:
                    which_market="DNB_Home"
                else:
                    which_market="DNB_Away"
                #traded_table={}
                last_back_vol_dnb = 0
                vwap = 0
                total_vol =0
                for tv in runner.ex.traded_volume:
                    #if last_back_price == tv.price:
                    try:
                        last_back_vol_dnb += tv.size
                        vwap += tv.size*tv.price
                        total_vol+=tv.size
                    except Exception as msg:
                        pass#print("DNB_loop:",str(msg))

                try:
                    vwap = vwap/total_vol
                except Exception as msg:
                    pass#print("DNB_vwap:",str(msg))

                try:
                    last_back_price_dnb= runner.ex.available_to_back[0].price
                except Exception as msg:
                    #print("DNB_lastback:",str(msg))
                    last_back_price_dnb=0 

                try:
                    lay_price_dnb= runner.ex.available_to_lay[0].price
                except Exception as msg:
                    #print("DNB_lastlay:",str(msg))
                    lay_price_dnb= 0

                try:
                    lay_volume_dnb= runner.ex.available_to_lay[0].size
                except Exception as msg:
                    #print("DNB_volume:",str(msg))
                    lay_volume_dnb= 0
                retval['vwaps'][which_market]=round(vwap,2)
                retval['markets'].append({"last_back_price_"+which_market:last_back_price_dnb,"last_back_vol_"+which_market:last_back_vol_dnb,"lowest_back_price_"+which_market:0,"lowest_back_vol_"+which_market:0,"lay_price_"+which_market:lay_price_dnb,"lay_vol_"+which_market:lay_volume_dnb})
                #print(event_id,retval)


    except Exception as msg:
        #print("DNB err in bf markets:",str(msg))
        which_market="DNB_Home"
        
        retval['markets'].append({"last_back_price_"+which_market:0,"last_back_vol_"+which_market:0,"lowest_back_price_"+which_market:0,"lowest_back_vol_"+which_market:0,"lay_price_"+which_market:0,"lay_vol_"+which_market:0})
        which_market="DNB_Away"
        
        retval['markets'].append({"last_back_price_"+which_market:0,"last_back_vol_"+which_market:0,"lowest_back_price_"+which_market:0,"lowest_back_vol_"+which_market:0,"lay_price_"+which_market:0,"lay_vol_"+which_market:0})


    #HT
    #print("HT..")
    which_market="1_HT"
    retval['markets'].append({"last_back_price_"+which_market:0,"last_back_vol_"+which_market:0,"lowest_back_price_"+which_market:0,"lowest_back_vol_"+which_market:0,"lay_price_"+which_market:0,"lay_vol_"+which_market:0})
    which_market="2_HT"
    retval['markets'].append({"last_back_price_"+which_market:0,"last_back_vol_"+which_market:0,"lowest_back_price_"+which_market:0,"lowest_back_vol_"+which_market:0,"lay_price_"+which_market:0,"lay_vol_"+which_market:0})
    which_market="X_HT"
    retval['markets'].append({"last_back_price_"+which_market:0,"last_back_vol_"+which_market:0,"lowest_back_price_"+which_market:0,"lowest_back_vol_"+which_market:0,"lay_price_"+which_market:0,"lay_vol_"+which_market:0})
    
    #DC
    #print("DC..")
    which_market="DC_1X"        
    retval['markets'].append({"last_back_price_"+which_market:0,"last_back_vol_"+which_market:0,"lowest_back_price_"+which_market:0,"lowest_back_vol_"+which_market:0,"lay_price_"+which_market:0,"lay_vol_"+which_market:0})
    which_market="DC_X2"
    retval['markets'].append({"last_back_price_"+which_market:0,"last_back_vol_"+which_market:0,"lowest_back_price_"+which_market:0,"lowest_back_vol_"+which_market:0,"lay_price_"+which_market:0,"lay_vol_"+which_market:0})
    which_market="DC_12"
    retval['markets'].append({"last_back_price_"+which_market:0,"last_back_vol_"+which_market:0,"lowest_back_price_"+which_market:0,"lowest_back_vol_"+which_market:0,"lay_price_"+which_market:0,"lay_vol_"+which_market:0})
    


    return retval

def do_betfair_raw():
    conn = pymysql.connect(host='127.0.0.1',user='local',passwd='oeijifjwejfio',db=db_name)
    cur  = conn.cursor()
    cur.execute("select * from raw_comps where site='betfair'")
    rows = cur.fetchall()
    ids_done=[]
    for row in rows:
        ids_done.append(int(row[2]))

    # Create a competition filter
    competition_filter = betfairlightweight.filters.market_filter(
        event_type_ids=[1], # Soccer's event type id is 1
        market_start_time={
            'to': datetime_in_a_week
        })

    # Get a list of competitions for soccer
    competitions = trading.betting.list_competitions(
        filter=competition_filter
    )
    
    for comp in competitions:
        if int(comp.competition.id) not in ids_done:
            #print("adding bf comp:",comp.competition.name,comp.competition.id)
            x=cur.execute("insert into raw_comps (comp_name,comp_id,site,timestamp) values(%s,%s,%s,%s)",(comp.competition.name,comp.competition.id,"betfair",time.time()))
    conn.commit()
    conn.close()

def pull_markets(eventids,market_filter):
	market_catalogue_filter={"eventIds":eventids,"marketTypeCodes":[market_filter]}#,'marketBettingTypes':['MATCH ODDS']
	market_catalogues = trading.betting.list_market_catalogue(
    		filter=market_catalogue_filter,
    		max_results='1000',
    		sort='FIRST_TO_START',
            market_projection=['EVENT']
	)
	return market_catalogues

def betfair_dictbuilder(complist):
    stime=time.time()
    #pull down all events from complist
    events = pull_all_events(complist)
    comp_dict={}

    for e in events:
        comp_dict[str(e.event.id)]={"name":e.event.name,"match_id":None,"uo25_id":None,"dnb_id":None,"match_data":None,"uo25_data":None,"dnb_data":None}
    #pull all matchodds markets for eventlist

    match_ids={}
    uo25_ids={}
    dnb_ids={}
    

    markets = pull_markets(list(comp_dict),"MATCH_ODDS")
    for market in markets:
        comp_dict[market.event.id]['match_id']=market.market_id
        match_ids[market.market_id] = market.event.id

    #pull all uo25 markets for eventlist
    markets = pull_markets(list(comp_dict),"OVER_UNDER_25")
    for market in markets:
        comp_dict[market.event.id]['uo25_id']=market.market_id
        uo25_ids[market.market_id] = market.event.id
    #pull all dnb markets for eventlist
    markets = pull_markets(list(comp_dict),"DRAW_NO_BET")
    for market in markets:
        comp_dict[market.event.id]['dnb_id']=market.market_id
        dnb_ids[market.market_id] = market.event.id

    #pull the books
    match_chunks = list(chunks(list(match_ids),10))
    for chunk in match_chunks:
        books = get_market_books(chunk)
        for book in books:
            eid = book.market_id
            comp_dict[match_ids[eid]]['match_data']=book.runners
    
    uo25_chunks = list(chunks(list(uo25_ids),10))
    for chunk in uo25_chunks:
        books = get_market_books(chunk)
        #books = get_market_books(list(uo25_ids))
        for book in books:
            eid = book.market_id
            comp_dict[uo25_ids[eid]]['uo25_data']=book.runners
        
    dnb_chunks = list(chunks(list(dnb_ids),10))
    for chunk in dnb_chunks:
        books = get_market_books(chunk)
        #books = get_market_books(list(dnb_ids))
        for book in books:
            eid = book.market_id
            comp_dict[dnb_ids[eid]]['dnb_data']=book.runners
        

    #build the dict

    print(time.time()-stime)
    return comp_dict

def pull_events(compid):
	filter={"competitionIds":[str(compid)]}

	events = trading.betting.list_events(
    		filter=filter
	)
	return events

def pull_all_events(compids):
	filter={"competitionIds":compids}

	events = trading.betting.list_events(
    		filter=filter
	)
	return events

def pull_active_comps():
    #filter={"competitionIds":[str(compid)]}

    comps = trading.betting.list_competitions(
            
    )
    active_comps=[]
    for comp in comps:
        if comp.market_count>0:
            active_comps.append(comp.competition.id)
    return active_comps

def inspect_market_cache(event_id,market_name):
    conn = pymysql.connect(host='127.0.0.1',user='local',passwd='oeijifjwejfio',db=db_name)
    cur  = conn.cursor()
    x=cur.execute("select market_id from betfair_markets where event_id=%s and market=%s",(event_id,market_name))
    if x>0:
        market_id = cur.fetchall()[0][0]
    else:
        market_id=0

    conn.close()

    return float(market_id)

def update_market_cache(event_id,market_name,market_id):
    conn = pymysql.connect(host='127.0.0.1',user='local',passwd='oeijifjwejfio',db=db_name)
    cur  = conn.cursor()
    x=cur.execute("insert into betfair_markets(event_id,market,market_id) values(%s,%s,%s)",(event_id,market_name,market_id))
    conn.commit()
    conn.close()

def get_event_matchodds(markets,eventid): 
    global bf_markets
    #print(len(bf_markets))
    if str(eventid) + "_Match Odds" in bf_markets:
        return bf_markets[str(eventid) + "_Match Odds"]
    #here attempt to get the marketid from 
    market_id = inspect_market_cache(eventid,"Match Odds")
    if market_id>0:
        #print("found:",market_id)
        return market_id
    else:
        for m in markets:
            if m.market_name=='Match Odds':
                #print("pulled:",m.market_id)
                update_market_cache(eventid,"Match Odds",m.market_id)

                return m.market_id
    return 0

def get_event_ou25(markets,eventid):
    global bf_markets
    #print(len(bf_markets))
    if str(eventid) + "_Over/Under 2.5 Goals" in bf_markets:
        return bf_markets[str(eventid) + "_Over/Under 2.5 Goals"]

    market_id = inspect_market_cache(eventid,"Over/Under 2.5 Goals")
    if market_id>0:
        #print("found:",market_id)
        return market_id
    else:
        for m in markets:
            if m.market_name=='Over/Under 2.5 Goals':
                #print("pulled:",m.market_id)
                update_market_cache(eventid,"Over/Under 2.5 Goals",m.market_id)

                return m.market_id
    return 0

def get_event_ou35(markets,eventid):
    global bf_markets
    #print(len(bf_markets))
    if str(eventid) + "_Over/Under 3.5 Goals" in bf_markets:
        return bf_markets[str(eventid) + "_Over/Under 3.5 Goals"]

    market_id = inspect_market_cache(eventid,"Over/Under 3.5 Goals")
    if market_id>0:
        #print("found:",market_id)
        return market_id
    else:
        for m in markets:
            if m.market_name=='Over/Under 3.5 Goals':
                #print("pulled:",m.market_id)
                update_market_cache(eventid,"Over/Under 3.5 Goals",m.market_id)

                return m.market_id
    return 0

def get_event_dnb(markets,eventid):
    global bf_markets
    #print(len(bf_markets))
    if str(eventid) + "_Draw no Bet" in bf_markets:
        return bf_markets[str(eventid) + "_Draw no Bet"]

    market_id = inspect_market_cache(eventid,"Draw no Bet")
    if market_id>0:
        #print("found:",market_id)
        return market_id
    else:
        for m in markets:
            if m.market_name=='Draw no Bet':
                #print("pulled:",m.market_id)
                update_market_cache(eventid,"Draw no Bet",m.market_id)

                return m.market_id
    return 0

def get_event_dc(markets,eventid):
    global bf_markets
    #print(len(bf_markets))
    if str(eventid) + "_Draw Chance" in bf_markets:
        return bf_markets[str(eventid) + "_Double Chance"]

    market_id = inspect_market_cache(eventid,"Double Chance")
    if market_id>0:
        #print("found:",market_id)
        return market_id
    else:
        for m in markets:
            if m.market_name=='Double Chance':
                #print("pulled:",m.market_id)
                update_market_cache(eventid,"Double Chance",m.market_id)

                return m.market_id
    return 0

def get_event_1x2_ht(markets,eventid):
    global bf_markets
    #print(len(bf_markets))
    if str(eventid) + "_Half Time" in bf_markets:
        return bf_markets[str(eventid) + "_Half Time"]

    market_id = inspect_market_cache(eventid,"Half Time")
    if market_id>0:
        #print("found:",market_id)
        return market_id
    else:
        for m in markets:
            if m.market_name=='Half Time':
                #print("pulled:",m.market_id)
                update_market_cache(eventid,"Half Time",m.market_id)

                return m.market_id
    return 0

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def get_market_books(books):
	price_filter=betfairlightweight.filters.price_projection(price_data=['EX_BEST_OFFERS','EX_TRADED'])
	book =trading.betting.list_market_book(market_ids=books,price_projection=price_filter)
	return book



def pull_betfair_data(compid,league,betfair_markets,betfair_data_dict,events=[],foobar=None):
    #print("BETFAIR DATA >>>")
    global bf_markets#,betfair_data_dict

    #print(compid,events)
    bf_markets = betfair_markets

    #events = pull_events(compid) ## << this is where i can skip,, ill have the event list fed in as a param..
    #print("events:",events)
    comp_data={}
    eventids=[]
    h2h_ids = []
    e_list=[]
    e_list_strings=[]


    #here is where i can send off for all marketIds for all events.. using the e_list..
    #returned data, then needs to be grouped by event.id,, and from there i can still send off
    #to separate threads for processing.. i guess.. but i just send off the actual marketId dict with its event id..
    for event in events:
        event_id =event.event.id
        comp_data[event_id]={"name":event.event.name,"odds":[],'markets':[],"vwaps":{},"timestamp":event.event.open_date.timestamp()}
        eventids.append(event_id)
        e_list_strings.append(str(event_id))
        #print("--",event.event.name,"--")
        e_list.append([event_id,event])


    #here pull down all market cats.. 
    #comp_markets = pull_markets(e_list_strings)
    market_dict={}

    #then group into event dict.. and fire off to the thread..as per..
    if 0:#for cm in comp_markets:
        if str(cm.event.id) not in market_dict:
            market_dict[str(cm.event.id)]={}
        market_dict[str(cm.event.id)][cm.market_name] = cm.market_id
    
    #print(">> BF thread pull")
    #print("e_list_len:",len(e_list))    
    #t_count = min(len(e_list),thread_count)
    
    ##if t_count==0:
    #    return {}
    #print("t_count:",t_count)
    #comp_markets = pull_comp_markets(e_list)

    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=t_count) as executor:
        future_to_url = {executor.submit(betfair_data_thread, e[0],e[1],market_dict[str(e[0])]): e for e in e_list}
        for future in concurrent.futures.as_completed(future_to_url):
            #url = future_to_url[future]
            try:
                data,event_id = future.result()
                for d in data['odds']:
                    comp_data[event_id]['odds'].append(d)
                for d in data['markets']:
                    comp_data[event_id]['markets'].append(d)
                for d in data['vwaps']:
                    comp_data[event_id]['vwaps'][d] = data['vwaps'][d]
                
                try:
                    do_odds_history_insert("betfair",event_id,data['odds'],data['markets'],data['vwaps'])
                except Exception as msg:
                    pass#print("err on odds history insert..",str(msg))

            except Exception as exc:
                pass#print("betfair section", '%r generated an exception: %s' % ("brr", exc))
    """
    #here i can splice in the already gathered data,, 
    #print("about to pull bf dict data..")
    #print("eids:",eventids)

    for e in eventids:
        #print(e)
        #pull down the data from betfair_data_dict..
        try:
            retdata = process_event_odds(str(e),betfair_data_dict[str(e)])
            comp_data[e]['odds'] = retdata['odds']
            comp_data[e]['markets'] = retdata['markets']
            comp_data[e]['vwaps'] = retdata['vwaps']
            try:
                do_odds_history_insert("betfair",e,comp_data[e]['odds'],comp_data[e]['markets'],comp_data[e]['vwaps'])
            except Exception as msg:
                print("err on odds history insert..",str(msg))
        except Exception as msg:
            pass#print("processing event odds",str(e),betfair_data_dict[str(e)],str(msg))

        pass#print(retdata)
        
        #print(comp_data)
        #process it. and just save to the current comp_data[event_id]
    #print("betfair data")
    #for cd in comp_data:
    #    print(">>",cd,comp_data[cd])
    #print("--END BF--")



    ## first runner is UNDER, then OVER,, if they swap around, this is where the problem is.. can't locate which odds it refers to.
    ## need to spec which 

    #with open("raw_betfair_data/" + league + "_" + str(compid) + ".json","wb") as f:
    #    f.write(res.content)
    #print(comp_data)
    #with open("/home/arb_bot/beta_bingoal_fastbf/bf_dumps/" + league + "_" + str(compid) + ".json","w") as f:
    #    f.write(json.dumps(comp_data))
    #print("^^^ BETFAIR COMPDATA")
    return comp_data

