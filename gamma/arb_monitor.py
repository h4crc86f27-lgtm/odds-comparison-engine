#betfair API market puller
"""
arb_monitor.py - Main orchestration loop for the odds comparison engine.

Pulls competition data from Betfair Exchange and all active bookmaker
providers, matches events per competition, runs each provider's insert
routine to write comparison records to the database, and updates the
last-scan timestamp. Designed to run as a persistent background process.

Usage:
    python arb_monitor.py [book1 book2 ...]

    If no book arguments are supplied, a default list is used.
"""
from asyncio import subprocess
import time
from operator import le
import betfairlightweight
from betfairlightweight import filters
import pandas as pd
import numpy as np
import os
import datetime
import json
import requests
import pickle
from fuzzywuzzy import fuzz
import pymysql
import concurrent.futures
import random
import unicodedata
from threading import Thread
import subprocess as sp
import sys

from arber_modules.unibet import *
from arber_modules.toto import *
from arber_modules.contra import *
from arber_modules.qrbet import *
from arber_modules.betfair import *
from arber_modules.winkel_toto import *
from arber_modules.bingoal import *
from arber_modules.yess365 import *
#from arber_modules.betalpha import *
from arber_modules.bet3000 import *
from arber_modules.m8bets import *
from arber_modules.bet635 import *
from arber_modules.polymarket import (
    pull_data_polymarket,
    align_matches as align_matches_polymarket,
)



unibet_teams=[]
contra_teams=[]
toto_teams=[]
qrbet_teams=[]
winkel_toto_teams=[]

kvalue=None
ust=""
b_session=""

with open("/home/arb_bot/proxies") as f:
    proxies = f.read().split("\n")

try:
    proxies.remove('')
except:
    pass


version="beta"
db_name="arb_db_"+ version



if len(sys.argv)>1:
    #get the books.
    book_list = sys.argv[1:]

else:
    print("default book list")
    book_list = ["bet3000","toto","bingoal","qrbet","winkel_toto","unibet","contra","yess365","betalpha","m8bets"]

if book_list==['bet3000']:
    thread_count= 3
elif book_list==['bet635']:
    thread_count=3
elif book_list==['unibet']:
    thread_count=20
elif book_list==['winkel_toto']:
    thread_count=4
elif book_list==['toto']:
    thread_count=2
elif book_list==['polymarket']:
    thread_count=5
else:
    thread_count=2

print(book_list)
def mud(rows):
    """Return a shuffled subset of rows for randomised processing order."""
    if 0:
        md  = int(len(rows)/3)
        print(len(rows))
        print(len(rows[0:md]))
        print(len(rows[md:]))

        rnd =  random.randint(1,3)
        if rnd==1:
            return rows[0:md]
        elif rnd==2:
            return rows[md:md*2]
        else:
            return rows[md*2:]
    else:
        md = int(len(rows)*random.randint(10,10)/10)
        l = rows[0:md]

        random.shuffle(l)
        return l

m8bets_alldata={}

def process_comp(comp_meta):#toto_id,bf_id,league):
    """
    Pull and insert odds data for a single competition.

    Fetches Betfair data first; if successful, concurrently fetches data
    from all active bookmakers in book_list, then calls each provider's
    insert function to write comparison records to the database.
    """
    global comp_dict
    global k_value,b_session,ust
    global bf_comps_active
    global betfair_data_dict

    global toto_teams,unibet_teams,contra_teams
    global betfair_pull_time,betfair_pull_err_time,unibet_pull_time,contra_pull_time,qrbet_pull_time,winkel_toto_pull_time,toto_pull_time
    global betfair_splice_time,unibet_splice_time,contra_splice_time,qrbet_splice_time,winkel_toto_splice_time,toto_splice_time

    global m8bets_alldata ## this will pull in from the thingy..

    global book_list
    btime=time.time()

    try:
        print("pulling betfair")
        print("processing >> " ,comp_meta['league'])
        #print(betfair_data_dict)
        #betfair_data = pull_betfair_data(comp_meta['betfair'],comp_meta['league'])
        if int(comp_meta['betfair']) in comp_dict:
            pass#print("found:",int(comp_meta['betfair'])," in compdict")
        else:
            print("NOTFOUND:",int(comp_meta['betfair'])," in compdict")
        betfair_data = pull_betfair_data(comp_meta['betfair'],comp_meta['league'],comp_dict[int(comp_meta['betfair'])],betfair_data_dict,comp_dict[int(comp_meta['betfair'])])
        #print("done bf..")
        if len(betfair_data)>0:
            betfair_pull_time+=time.time()-btime
            bf_comps_active+=1
            print(len(betfair_data)," bf match data:",comp_meta['league'])
        else:
            print("zero bf match data:",comp_meta['league'])
            betfair_pull_err_time+=time.time()-btime
        #print(betfair_pull_time,"...")
    except Exception as msg:
        betfair_data=None
        print("process err (bf):",str(msg))
        betfair_pull_err_time+=time.time()-btime
        return 0


    if betfair_data:
        btime=time.time()

        #book_list =["yess365","toto","contra","winkel_toto"]
        unibet_data={}
        qrbet_data={}
        bingoal_data={}
        winkel_toto_data={}
        toto_data={}
        yess365_data={}
        contra_data={}
        betalpha_data={}
        bet3000_data={}
        bet635_data={}
        polymarket_data={}

        try:
            #print("m8bets compname:",comp_meta['m8bets'])
            #print("len m8betsalldata:",len(m8bets_alldata))

            m8bets_data=m8bets_alldata[comp_meta['m8bets']]


            #print("IN COMP M8BETS MATCHES::",len(m8bets_data))
        except Exception as msg:
            pass#print("IN COMP M8BETS ERROR::",str(msg))



        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # Start the load operations and mark each future with its URL
            #executor.submit(pull_data_winkel_toto,  comp_meta['winkel_toto'], comp_meta['league']): "winkel_toto",
            #,executor.submit(pull_betfair_data,  comp_meta['betfair'], comp_meta['league'],betfair_markets): "betfair"
            #{executor.submit(pull_betfair_data,  comp_meta['betfair'], comp_meta['league'],betfair_markets,"",comp_dict[int(comp_meta['betfair'])]): "betfair",
            future_to_url = {}
            if "bet3000" in book_list:
                future_to_url[executor.submit(pull_data_bet3000,  comp_meta['bet3000'], comp_meta['league'])]="bet3000"

            if "betalpha" in book_list:
                future_to_url[executor.submit(pull_data_betalpha,  comp_meta['betalpha'], comp_meta['league'])]="betalpha"

            if "yess365" in book_list:
                future_to_url[executor.submit(pull_data_yess365,  comp_meta['yess365'], comp_meta['league'])]="yess365"

            if "toto" in book_list and comp_meta['toto'] != "":
                future_to_url[executor.submit(pull_data_toto,  comp_meta['toto'], comp_meta['league'])]="toto"

            if "unibet" in book_list:
                future_to_url[executor.submit(pull_data_unibet,  comp_meta['unibet'], comp_meta['league'])]="unibet"

            if "contra" in book_list:
                future_to_url[executor.submit(pull_data_contra,  comp_meta['contra'], comp_meta['league'])]="contra"

            if "qrbet" in book_list:
                future_to_url[executor.submit(pull_data_qrbet,  comp_meta['qrbet'], comp_meta['league'])]="qrbet"

            if "winkel_toto" in book_list:
                future_to_url[executor.submit(pull_data_winkel_toto,  comp_meta['winkel_toto'], comp_meta['league'])]="winkel_toto"

            if "bingoal" in book_list:
                future_to_url[executor.submit(pull_data_bingoal,  comp_meta['bingoal'], comp_meta['league'],{"kvalue":kvalue,"b_session":b_session,"ust":ust})] = "bingoal"

            if "winkel_toto" in book_list:
                future_to_url[executor.submit(pull_data_winkel_toto,  comp_meta['winkel_toto'], comp_meta['league'])]= "winkel_toto"

            if "bet635" in book_list:
                future_to_url[executor.submit(pull_data_bet635,  comp_meta['bet635'], comp_meta['league'])]= "bet635"

            if "polymarket" in book_list and comp_meta['polymarket'] != "":
                future_to_url[executor.submit(pull_data_polymarket, comp_meta['polymarket'], comp_meta['league'])]= "polymarket"


            #if "m8bets" in book_list:
            #    future_to_url[executor.submit(pull_data_m8bets,  comp_meta['m8bets'], comp_meta['league'])]= "m8bets"

            #
            #bingoal_data={}
            #
            for future in concurrent.futures.as_completed(future_to_url):
                book = future_to_url[future]
                #rint(book)
                try:
                    data = future.result()
                    if book=="bet3000":
                        bet3000_data = data
                        print("done bet3000..")
                    elif book=="bet635":
                        bet635_data = data
                    elif book=="polymarket":
                        polymarket_data = data
                        print(f"Polymarket events: {len(polymarket_data)}")

                    elif book=="betalpha":
                        betalpha_data = data

                    elif book=="toto":
                        toto_data = data
                        #print(toto_data)
                    elif book=="unibet":
                        unibet_data=data
                    elif book=="contra":
                        contra_data = data
                    elif book=="qrbet":
                        qrbet_data = data
                    elif book=="betfair":
                        betfair_data = data
                        if len(betfair_data)==0:
                            print("zero:",time.time()- comp_start_time)
                            return None
                    elif book=="winkel_toto":
                        winkel_toto_data = data
                    elif book=="bingoal":
                        bingoal_data = data
                    elif book=="yess365":
                        yess365_data = data
                    elif book=="m8bets":
                        m8bets_data = data
                except Exception as exc:
                    pass#print('%r generated an exception: %s' % (book, exc))
                else:
                    #print(book, data)
                    if book=="bet3000":
                        bet3000_data = data
                        print("done bet3000..")
                    elif book=="bet635":
                        bet635_data = data
                    elif book=="polymarket":
                        polymarket_data = data
                        print(f"Polymarket events: {len(polymarket_data)}")

                    elif book=="betalpha":
                        betalpha_data = data

                    elif book=="toto":
                        toto_data = data
                        #print(toto_data)
                    elif book=="unibet":
                        unibet_data=data
                    elif book=="contra":
                        contra_data = data
                    elif book=="qrbet":
                        qrbet_data = data
                    elif book=="betfair":
                        betfair_data = data
                        if len(betfair_data)==0:
                            print("zero:",time.time()- comp_start_time)
                            return None
                    elif book=="winkel_toto":
                        winkel_toto_data = data
                    elif book=="bingoal":
                        bingoal_data = data
                    elif book=="yess365":
                        yess365_data = data
                    elif book=="m8bets":
                        m8bets_data = data

        btime = time.time()



        try:
            pass#btime =time.time()
            #print("inserting yess365 data..")
            if bet635_data !={}:
                do_insert_bet635(bet635_data,betfair_data,comp_meta['league'],[])
            #bingoal_splice_time+=time.time()-btime
        except Exception as msg:
            #toto_splice_time+=time.time()-btime
            print("err on bet635 insert",str(msg))


        try:
            pass#btime =time.time()
            #print("inserting yess365 data..")
            if bet3000_data !={}:
                do_insert_bet3000(bet3000_data,betfair_data,comp_meta['league'],[])
            #bingoal_splice_time+=time.time()-btime
        except Exception as msg:
            #toto_splice_time+=time.time()-btime
            print("err on bet3000 insert",str(msg))


        try:
            pass#btime =time.time()
            #print("inserting yess365 data..")
            if betalpha_data !={}:
                do_insert_betalpha(betalpha_data,betfair_data,comp_meta['league'],betalpha_teams)
            #bingoal_splice_time+=time.time()-btime
        except Exception as msg:
            #toto_splice_time+=time.time()-btime
            pass#print("err on yess insert",str(msg))


        try:
            pass#btime =time.time()
            #print("inserting yess365 data..")
            if yess365_data !={}:
                do_insert_yess365(yess365_data,betfair_data,comp_meta['league'],yess365_teams)
            #bingoal_splice_time+=time.time()-btime
        except Exception as msg:
            #toto_splice_time+=time.time()-btime
            pass#print("err on yess insert",str(msg))


        try:
            pass#btime =time.time()
            #print("inserting bingoal data..")
            if bingoal_data !={}:
                do_insert_bingoal(bingoal_data,betfair_data,comp_meta['league'],bingoal_teams)
            #bingoal_splice_time+=time.time()-btime
        except:
            #toto_splice_time+=time.time()-btime
            pass#print("err on bingoal insert")

        try:
            #pass#print("attempting winkel_toto insert!!")
            if comp_meta['winkel_toto']=="":
                pass#print("kipping winkto insert")
            else:
                pass#print("attempting winkel_toto insert!!")

                if winkel_toto_data!={}:
                    do_insert_winkel_toto(winkel_toto_data,betfair_data,comp_meta['league'],winkel_toto_teams)
                winkel_toto_splice_time+=time.time()-btime

            #pass#print("finished winkel_toto insert <><>")
        except Exception as msg:
            winkel_toto_splice_time+=time.time()-btime
            #print(str(msg),"err on winkel_toto insert")


        ##toto check
        btime = time.time()
        try:
            #btime =time.time()
            if toto_data != {}:
                do_insert_toto(toto_data,betfair_data,comp_meta['league'],toto_teams)
            toto_splice_time+=time.time()-btime
        except:
            toto_splice_time+=time.time()-btime
            pass#print("err on toto insert")

        btime = time.time()

        try:

            if unibet_data !={}:
                do_insert_unibet(unibet_data,betfair_data,comp_meta['league'],unibet_teams)
            unibet_splice_time+=time.time()-btime
        except Exception as msg:
            unibet_splice_time+=time.time()-btime
            pass#print("err on unibet insert:",str(msg))
        btime = time.time()
        try:
            pass#print("INSERTTING CONTRA!!!!!!!!!!!")

            if contra_data!={}:
                do_insert_contra(contra_data,betfair_data,comp_meta['league'],contra_teams)
            contra_splice_time+=time.time()-btime
            pass#print("CONTRA INSERT COMPLETED")
        except Exception as msg:
            contra_splice_time+=time.time()-btime
            pass#print("err on contra insert:",str(msg))
        btime = time.time()
        try:
            #btime = time.time()
            if qrbet_data!={}:
                do_insert_qrbet(qrbet_data,betfair_data,comp_meta['league'],qrbet_teams)
            qrbet_splice_time+=time.time()-btime
        except Exception as msg:
            qrbet_splice_time+=time.time()-btime
            pass#print("err on qrbet insert:",str(msg))

        try:
            #btime = time.time()
            if m8bets_data!={}:
                do_insert_m8bets(m8bets_data,betfair_data,comp_meta['league'],m8bets_teams)
            #qrbet_splice_time+=time.time()-btime
        except Exception as msg:
            #qrbet_splice_time+=time.time()-btime
            pass#print("err on qrbet insert:",str(msg))

        try:
            if polymarket_data and len(polymarket_data) > 0:
                bf_data = convert_ref_matches(betfair_data)
                polymarket_matches = align_matches_polymarket(
                    polymarket_data,
                    bf_data,
                    comp_meta['league']
                )
                print(f"Polymarket matched events: {len(polymarket_matches)}")
                for match in polymarket_matches:
                    print(f"  {match['polymarket_event_id']} | {match['betfair_event_id']} | {match['polymarket_home']} vs {match['polymarket_away']} | {match['betfair_home']} vs {match['betfair_away']} | {match['home_fuzzy']}/{match['away_fuzzy']} | flipped={match['flipped']}")
        except Exception as msg:
            print("Polymarket alignment error:", str(msg))
    else:
        pass#pass#print("skipping crawl for this comp-- betfair_data ((NONE))")

    ##unibet check
    pass#print("finished processing :",comp_meta['league'],"<<<<<<<<<<>>>>>>>>>>>")


def dump():
    """
    Write auxiliary market snapshots to pickle files for the frontend.

    Dumps asian-handicap match odds, horse racing win/place markets, and
    tennis match/set odds to /var/www/html/ as pickle files consumed by
    the PHP frontend.
    """
    out={}
    price_filter=betfairlightweight.filters.price_projection(price_data=['EX_BEST_OFFERS'])
    events = trading.betting.list_events(filter={"competitionIds":[str(11196870)]})
    for event in events:
        try:
            #print(event.event.name)
            marketid = pull_markets([event.event.id],"COMBINED_TOTAL")[0].market_id
            odds=[]
            book =trading.betting.list_market_book(market_ids=[marketid],price_projection=price_filter)

            if len(book)>0:
                #print("book nonzero")
                runners = book[0].runners

                for runner in runners:
                    if len(runner.ex.available_to_back)>0:
                        #print("adding odds..",runner.handicap)
                        odds.append([runner.handicap,runner.ex.available_to_back[0].price])
                    else:
                        odds.append([runner.handicap,0])


                out[event.event.id] = {"match":event.event.name,"marketid":marketid,"odds":odds}
        except:
            pass
    #dump
    with open("/var/www/html/dump.pkl","wb") as f:
        pickle.dump(out,f)



    ## r win

    eventids=[]#pull_type_events()#[32426621,32428487]

    market_dict = {}
    id_dict={} # this is for mapping back to market dict

    cats = pull_markets_r(eventids,"WIN")
    for cat in cats:
        track =cat.event.venue
        #print(cat.market_name)
        racenum = cat.market_name.split(" ")[0].replace("R","")
        market_id = cat.market_id
        eventid= cat.event.id
        market_start_time = cat.market_start_time
        try:
            event_type = cat.event_type.id
        except Exception as msg:
            event_type = ""
        #    print("!!!!!!!",str(msg))

        try:
            tracku = track.upper()
        except:
            tracku=""
        if str(event_type)=="4339":
            race_code = "G"
        else:
            race_code = "H"

        market_dict[tracku + "-" + racenum + "_" + race_code] = {"event_type":event_type,"event_id":eventid,"market_id":market_id,"start_time":market_start_time,"market":[]}
        id_dict[cat.market_id] = tracku + "-" + racenum + "_" + race_code

    market_ids = []
    for md in market_dict:
        market_ids.append(market_dict[md]['market_id'])

    price_filter=betfairlightweight.filters.price_projection(price_data=['EX_BEST_OFFERS','EX_TRADED']) # EX_TRADED


    #books =trading.betting.list_market_book(market_ids=market_ids,price_projection=price_filter)

    chunk_size = 5  # Set the desired chunk size
    books = []  # List to store the book responses

    # Break the market_ids into chunks
    chunks = [market_ids[i:i + chunk_size] for i in range(0, len(market_ids), chunk_size)]

    # Iterate over each chunk and make the API request
    for chunk in chunks:
        book_response = trading.betting.list_market_book(market_ids=chunk, price_projection=price_filter)
        books.extend(book_response)

    for book in books:
        mid = book.market_id
        runners = book.runners
        for runner in runners:
            runner_id = runner.selection_id
            lpt = runner.last_price_traded
            #traded_volume = runner.ex.traded_volume
            traded=runner.ex.traded_volume
            #for tv in traded_volume:
            #    traded+=tv.size
            if lpt is None:
                lpt = 0
            backs= runner.ex.available_to_back
            lays = runner.ex.available_to_lay
            market_dict[id_dict[mid]]['market'].append({"runner_id":runner_id,"lpt":lpt,"backs":backs,"lays":lays,"traded":traded})

    with open("/var/www/html/dmp.pkl","wb") as f:
        pickle.dump(market_dict,f)


    ## r place
    if 1:
        eventids=[]#pull_type_events()#[32426621,32428487]

        market_dict = {}
        id_dict={} # this is for mapping back to market dict

        cats = pull_markets_r(eventids,"PLACE")
        for cat in cats:
            track = cat.event.venue #event.name.split("(")[0].strip()
            #racenum = cat.market_name.split(" ")[0].replace("R","")
            eventid= cat.event.id
            market_id = cat.market_id
            market_start_time = cat.market_start_time

            try:
                event_type = cat.event_type.id
            except Exception as msg:
                event_type = ""
            #    print("!!!!!!!",str(msg))


            try:
                tracku = track.upper()
            except:
                tracku=""

            market_dict[tracku + "-" + str(market_id)] = {"event_type":event_type,"event_id":eventid,"market_id":market_id,"start_time":market_start_time,"market":[]}
            id_dict[cat.market_id] = tracku + "-" + str(market_id)

        market_ids = []
        for md in market_dict:
            market_ids.append(market_dict[md]['market_id'])

        price_filter=betfairlightweight.filters.price_projection(price_data=['EX_BEST_OFFERS'])


        #books =trading.betting.list_market_book(market_ids=market_ids,price_projection=price_filter)

        chunk_size = 20  # Set the desired chunk size
        books = []  # List to store the book responses

        # Break the market_ids into chunks
        chunks = [market_ids[i:i + chunk_size] for i in range(0, len(market_ids), chunk_size)]

        # Iterate over each chunk and make the API request
        for chunk in chunks:
            book_response = trading.betting.list_market_book(market_ids=chunk, price_projection=price_filter)
            books.extend(book_response)

        for book in books:
            mid = book.market_id
            runners = book.runners
            for runner in runners:
                runner_id = runner.selection_id
                lpt = runner.last_price_traded
                #traded_volume = runner.ex.traded_volume
                #traded=0
                #for tv in traded_volume:
                #    traded+=tv.size
                if lpt is None:
                    lpt = 0
                backs= runner.ex.available_to_back
                lays = runner.ex.available_to_lay
                market_dict[id_dict[mid]]['market'].append({"runner_id":runner_id,"lpt":lpt,"backs":backs,"lays":lays})

        with open("/var/www/html/dmp_plc.pkl","wb") as f:
            pickle.dump(market_dict,f)
    #wim
    mens={}
    mens_events=[]
    id_dict={}
    filter = {"competitionIds":[str(12803182)]}
    events = trading.betting.list_events(filter=filter)
    for event in events:
        if event.event.name.find(" v ")>-1:
            mens[event.event.id] = {"match":event.event.name,"match_id":event.event.id,"h2h_id":0,"set_id":0,"h2h_data":[],"set_data":[]}
            mens_events.append(event.event.id)
    #here pull down the match ods
    match_ids= pull_markets(mens_events,"MATCH_ODDS")
    for mi in match_ids:
        mens[mi.event.id]['h2h_id']=mi.market_id
        id_dict[mi.market_id] = [mi.event.id,"h2h_data"]
    #here pull down the set ods
    set_ids= pull_markets(mens_events,"SET_BETTING")
    for si in set_ids:
        mens[si.event.id]['set_id']=si.market_id
        id_dict[si.market_id] = [si.event.id,"set_data"]
    #now pull books
    price_filter=betfairlightweight.filters.price_projection(price_data=['EX_BEST_OFFERS'])
    chunk_size = 20  # Set the desired chunk size
    books = []  # List to store the book responses
    market_ids = list(id_dict)
    # Break the market_ids into chunks
    chunks = [market_ids[i:i + chunk_size] for i in range(0, len(market_ids), chunk_size)]
    # Iterate over each chunk and make the API request
    for chunk in chunks:
        book_response = trading.betting.list_market_book(market_ids=chunk, price_projection=price_filter)
        books.extend(book_response)
    for book in books:
        mid = book.market_id
        runners = book.runners
        for runner in runners:
            backs= runner.ex.available_to_back
            lays = runner.ex.available_to_lay
            lpt = runner.last_price_traded
            if lpt is None:
                lpt = 0
            event_id, which_market = id_dict[mid]
            mens[event_id][which_market].append({"backs":backs,"lays":lays,"lpt":lpt,"total_matched":runner.total_matched})

    with open("/var/www/html/menwim.pkl","wb") as f:
        pickle.dump(mens,f)
    #fems=[]
    womens={}
    womens_events=[]
    id_dict={}
    filter = {"competitionIds":[str(12803186)]}
    events = trading.betting.list_events(filter=filter)
    for event in events:
        if event.event.name.find(" v ")>-1:
            womens[event.event.id] = {"match":event.event.name,"match_id":event.event.id,"h2h_id":0,"set_id":0,"h2h_data":[],"set_data":[]}
            womens_events.append(event.event.id)
    #here pull down the match ods
    match_ids= pull_markets(womens_events,"MATCH_ODDS")
    for mi in match_ids:
        womens[mi.event.id]['h2h_id']=mi.market_id
        id_dict[mi.market_id] = [mi.event.id,"h2h_data"]
    #here pull down the set ods
    set_ids= pull_markets(womens_events,"SET_BETTING")
    for si in set_ids:
        womens[si.event.id]['set_id']=si.market_id
        id_dict[si.market_id] = [si.event.id,"set_data"]
    #now pull books
    price_filter=betfairlightweight.filters.price_projection(price_data=['EX_BEST_OFFERS'])
    chunk_size = 20  # Set the desired chunk size
    books = []  # List to store the book responses
    market_ids = list(id_dict)
    # Break the market_ids into chunks
    chunks = [market_ids[i:i + chunk_size] for i in range(0, len(market_ids), chunk_size)]
    # Iterate over each chunk and make the API request
    for chunk in chunks:
        book_response = trading.betting.list_market_book(market_ids=chunk, price_projection=price_filter)
        books.extend(book_response)
    for book in books:
        mid = book.market_id
        runners = book.runners
        for runner in runners:
            backs= runner.ex.available_to_back
            lays = runner.ex.available_to_lay
            lpt = runner.last_price_traded
            if lpt is None:
                lpt = 0
            event_id, which_market = id_dict[mid]
            womens[event_id][which_market].append({"backs":backs,"lays":lays,"lpt":lpt,"total_matched":runner.total_matched})
    #fems=[]
    with open("/var/www/html/womenwim.pkl","wb") as f:
        pickle.dump(womens,f)


#comps=[{"toto":"567","betfair":"10932509","league":"epl"}]
def get_comp_list():
    """
    Load active competitions from the database and build comp metadata dicts.

    Queries the comps table for all non-ignored competitions whose Betfair
    competition ID is currently active, and returns a list of per-competition
    metadata dicts keyed by provider name, for use by process_comp().
    """
    global active_betfair_comps
    print("bfactives:",len(active_betfair_comps))
    comps=[]
    conn = pymysql.connect(host='127.0.0.1',user='local',passwd='oeijifjwejfio',db=db_name)
    cur  = conn.cursor()
    cur.execute("select * from comps where ignore_comp=0")# and id=40")# and id=56")#and (id=144 or id=78 or id=56 or id=14 or id=40)") # 144 eerste and (id=14 or id=40)")#40")#UEFA 207")# where id=6") #40 is EPL#56 engcha
    rows = cur.fetchall()
    conn.close()
    for row in rows:
        if str(row[2]) not in active_betfair_comps:
            #print(str(row[2]),row[1],"not active")
            continue
        if row[12] is not None:
            winkel_id = row[12]
        else:
            winkel_id=""
        if row[16] is not None:
            yess365=row[16]
        else:
            yess365=""

        if row[18] is not None:
            betalpha=row[18]
        else:
            betalpha=""


        if row[20] is not None:
            bet3000 = row[20]
        else:
            bet3000 = ""

        if row[22] is not None:
            m8bets = row[22]
        else:
            m8bets = ""



        if row[24] is not None:
            bet635 = row[24]
        else:
            bet635 = ""

        polymarket = row[26] if row[26] is not None else ""


        if row[6] is None:
            if row[8] is None:
                if row[10] is not None:
                    if row[14] is not None:
                        comps.append({"polymarket":polymarket,"bet635":bet635,"m8bets":m8bets,"bet3000":bet3000,"betalpha":betalpha,"yess365":yess365,"bingoal":row[14],"winkel_toto":winkel_id,"toto":str(row[4]),"betfair":str(row[2]),"unibet":str(""),"contra":"","qrbet":{"name":row[9],"id":row[10]},"league":row[1]}) # << here just need to splice in something benign for ub if null
                    else:
                        comps.append({"polymarket":polymarket,"bet635":bet635,"m8bets":m8bets,"bet3000":bet3000,"betalpha":betalpha,"yess365":yess365,"bingoal":"","winkel_toto":winkel_id,"toto":str(row[4]),"betfair":str(row[2]),"unibet":str(""),"contra":"","qrbet":{"name":row[9],"id":row[10]},"league":row[1]}) # << here just need to splice in something benign for ub if null
                else:
                    if row[14] is not None:
                        comps.append({"polymarket":polymarket,"bet635":bet635,"m8bets":m8bets,"bet3000":bet3000,"betalpha":betalpha,"yess365":yess365,"bingoal":row[14],"winkel_toto":winkel_id,"toto":str(row[4]),"betfair":str(row[2]),"unibet":str(""),"contra":"","qrbet":{"name":"","id":""},"league":row[1]}) # << here just need to splice in something benign for ub if null
                    else:
                        comps.append({"polymarket":polymarket,"bet635":bet635,"m8bets":m8bets,"bet3000":bet3000,"betalpha":betalpha,"yess365":yess365,"bingoal":"","winkel_toto":winkel_id,"toto":str(row[4]),"betfair":str(row[2]),"unibet":str(""),"contra":"","qrbet":{"name":"","id":""},"league":row[1]}) # << here just need to splice in something benign for ub if null

            else:
                if row[10] is not None:
                    if row[14] is not None:
                        comps.append({"polymarket":polymarket,"bet635":bet635,"m8bets":m8bets,"bet3000":bet3000,"betalpha":betalpha,"yess365":yess365,"bingoal":row[14],"winkel_toto":winkel_id,"toto":str(row[4]),"betfair":str(row[2]),"unibet":str(""),"contra":"","qrbet":{"name":row[9],"id":row[10]},"league":row[1]}) # << here just need to splice in something benign for ub if null
                    else:
                        comps.append({"polymarket":polymarket,"bet635":bet635,"m8bets":m8bets,"bet3000":bet3000,"betalpha":betalpha,"yess365":yess365,"bingoal":"","winkel_toto":winkel_id,"toto":str(row[4]),"betfair":str(row[2]),"unibet":str(""),"contra":"","qrbet":{"name":row[9],"id":row[10]},"league":row[1]}) # << here just need to splice in something benign for ub if null
                else:
                    if row[14] is not None:
                        comps.append({"polymarket":polymarket,"bet635":bet635,"m8bets":m8bets,"bet3000":bet3000,"betalpha":betalpha,"yess365":yess365,"bingoal":row[14],"winkel_toto":winkel_id,"toto":str(row[4]),"betfair":str(row[2]),"unibet":str(""),"contra":row[8],"qrbet":{"name":"","id":""},"league":row[1]}) # << here just need to splice in something benign for ub if null
                    else:
                        comps.append({"polymarket":polymarket,"bet635":bet635,"m8bets":m8bets,"bet3000":bet3000,"betalpha":betalpha,"yess365":yess365,"bingoal":"","winkel_toto":winkel_id,"toto":str(row[4]),"betfair":str(row[2]),"unibet":str(""),"contra":row[8],"qrbet":{"name":"","id":""},"league":row[1]}) # << here just need to splice in something benign for ub if null
        else:
            if row[8] is None:
                if row[10] is not None:
                    if row[14] is not None:
                        comps.append({"polymarket":polymarket,"bet635":bet635,"m8bets":m8bets,"bet3000":bet3000,"betalpha":betalpha,"yess365":yess365,"bingoal":row[14],"winkel_toto":winkel_id,"toto":str(row[4]),"betfair":str(row[2]),"unibet":str(row[6]),"contra":"","qrbet":{"name":row[9],"id":row[10]},"league":row[1]})
                    else:
                        comps.append({"polymarket":polymarket,"bet635":bet635,"m8bets":m8bets,"bet3000":bet3000,"betalpha":betalpha,"yess365":yess365,"bingoal":"","winkel_toto":winkel_id,"toto":str(row[4]),"betfair":str(row[2]),"unibet":str(row[6]),"contra":"","qrbet":{"name":row[9],"id":row[10]},"league":row[1]})
                else:
                    if row[14] is not None:
                        comps.append({"polymarket":polymarket,"bet635":bet635,"m8bets":m8bets,"bet3000":bet3000,"betalpha":betalpha,"yess365":yess365,"bingoal":row[14],"winkel_toto":winkel_id,"toto":str(row[4]),"betfair":str(row[2]),"unibet":str(row[6]),"contra":"","qrbet":{"name":"","id":""},"league":row[1]}) # << here just need to splice in something benign for ub if null
                    else:
                        comps.append({"polymarket":polymarket,"bet635":bet635,"m8bets":m8bets,"bet3000":bet3000,"betalpha":betalpha,"yess365":yess365,"bingoal":"","winkel_toto":winkel_id,"toto":str(row[4]),"betfair":str(row[2]),"unibet":str(row[6]),"contra":"","qrbet":{"name":"","id":""},"league":row[1]}) # << here just need to splice in something benign for ub if null

            else:
                if row[10] is not None:
                    if row[14] is not None:
                        comps.append({"polymarket":polymarket,"bet635":bet635,"m8bets":m8bets,"bet3000":bet3000,"betalpha":betalpha,"yess365":yess365,"bingoal":row[14],"winkel_toto":winkel_id,"toto":str(row[4]),"betfair":str(row[2]),"unibet":str(row[6]),"contra":row[8],"qrbet":{"name":row[9],"id":row[10]},"league":row[1]})
                    else:
                        comps.append({"polymarket":polymarket,"bet635":bet635,"m8bets":m8bets,"bet3000":bet3000,"betalpha":betalpha,"yess365":yess365,"bingoal":"","winkel_toto":winkel_id,"toto":str(row[4]),"betfair":str(row[2]),"unibet":str(row[6]),"contra":row[8],"qrbet":{"name":row[9],"id":row[10]},"league":row[1]})
                else:
                    if row[14] is not None:
                        comps.append({"polymarket":polymarket,"bet635":bet635,"m8bets":m8bets,"bet3000":bet3000,"betalpha":betalpha,"yess365":yess365,"bingoal":row[14],"winkel_toto":winkel_id,"toto":str(row[4]),"betfair":str(row[2]),"unibet":str(row[6]),"contra":row[8],"qrbet":{"name":"","id":""},"league":row[1]}) # << here just need to splice in something benign for ub if null
                    else:
                        comps.append({"polymarket":polymarket,"bet635":bet635,"m8bets":m8bets,"bet3000":bet3000,"betalpha":betalpha,"yess365":yess365,"bingoal":"","winkel_toto":winkel_id,"toto":str(row[4]),"betfair":str(row[2]),"unibet":str(row[6]),"contra":row[8],"qrbet":{"name":"","id":""},"league":row[1]}) # << here just need to splice in something benign for ub if null
    print("complen:",len(comps))
    #with open("/home/arb_bot/comp_dump.pickle","wb") as f:
    #    pickle.dump(comps,f)
    #time.sleep(2)
    #comps = mud(comps)
    #pass#
    #print("comps:",comps)
    #time.sleep(5)
    return comps



def go(comps):
    """
    Run process_comp() for each competition using a thread pool.

    If m8bets is in the active book list, pre-fetches all m8bets data once
    before distributing per-competition work across threads.
    """
    global thread_count,m8bets_alldata
    #so you only need to do m8bets once,, for all comps,, then it just gets split up..
    #so maybe call it here,, and then global it or send it in as a param..
    if "m8bets" in book_list:
        for count in range(100):
            try:
                m8bets_alldata = pull_data_m8bets() # <<
                with open("/home/arb_bot/gamma/m8bet_comp_data.pickle","wb") as f:
                    pickle.dump(m8bets_alldata,f)

                print(list(m8bets_alldata))
                break
            except Exception as msg:
                print("retrying m8bets pull..",str(msg))
                time.sleep(1)

    threads = min(len(comps),thread_count)

    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        executor.map(process_comp, comps )


last_cycle_time=time.time()

while 1:#isnt_running:
    stime=time.time()
    try:
        bf_comps_active=0

        betfair_pull_time=0
        betfair_pull_err_time=0
        contra_pull_time=0
        toto_pull_time=0
        unibet_pull_time=0
        winkel_toto_pull_time=0
        qrbet_pull_time=0


        betfair_splice_time=0
        contra_splice_time=0
        toto_splice_time=0
        unibet_splice_time=0
        winkel_toto_splice_time=0
        qrbet_splice_time=0
        print("about to login..")
        #time.sleep(3)
        if trading.session_expired:
            #attempt logout.. and then login..
            try:
                trading.logout()
            except:
                pass
            trading.login()
            conn2 = pymysql.connect(host='127.0.0.1',user='local',passwd='oeijifjwejfio',db=db_name)
            cur2  = conn2.cursor()
            x=cur2.execute("insert into arber_logins (book_list,timestamp) values(%s,%s)",(json.dumps(book_list),str(datetime.datetime.now())[0:19]))
            conn2.commit()
            conn2.close()

            print("logging in!")
        else:
            print("trading session is not yet logged out..")

        print("team time..")
        contra_teams = {}#get_team_list_contra()
        pass#print("got contra")
        toto_teams = {}#get_team_list_toto()
        pass#print("goto toto")
        unibet_teams = {}#get_team_list_unibet()
        pass#print("got unibet")
        qrbet_teams = {}#get_team_list_qrbet()
        pass#print("got qrbet")
        winkel_toto_teams = {}#get_team_list_winkel_toto()
        pass#print("got winkel_toto")

        betalpha_teams ={}# get_team_list_betalpha()
        pass#print("got winkel_toto")

        bingoal_teams ={}# get_team_list_bingoal()
        pass#print("got winkel_toto")

        yess365_teams = {}#get_team_list_yess365()
        pass#print("got winkel_toto")

        m8bets_teams={}

        ##    print("teams took:",time.time()-stime)

        bet635_teams={}

        rtime=time.time()

        try:
            if random.randint(1,100)==1:
                print("doing bet3000 raw")
                do_bet3000_raw()
        except Exception as msg:
            print("err on bet3000_raw",str(msg))


        try:
            if random.randint(1,100)==1:
                print("doing bingoal raw")
                do_bingoal_raw()
        except Exception as msg:
            print("err on bingoal_raw",str(msg))

        try:
            if random.randint(1,100)==1:
                do_winkel_toto_raw()
        except Exception as msg:
            pass#print("err on winkel_toto_raw",str(msg))

        try:
            if random.randint(1,100)==1:
                do_toto_raw()
        except Exception as msg:
            pass#print("err on toto_raw",str(msg))

        try:
            if random.randint(1,100)==1:
                do_betfair_raw()
        except Exception as msg:
            pass#print("err on betfair_raw",str(msg))

        if book_list == ['bet3000'] or book_list ==['unibet']:
            try:

                dump()

            except Exception as msg:
                pass#print("dumperr:",str(msg))


        try:
            if random.randint(1,100)==1:
                do_unibet_raw()
        except Exception as msg:
            pass#print("err on unibet_raw",str(msg))

        try:
            if random.randint(1,100)==1:
                do_qrbet_raw()
        except Exception as msg:
            pass#print("err on qrbet_raw",str(msg))


        try:
            if random.randint(1,180)==1:#change this to happen once every few hours,, so 1,180 would be 1hr,, (assuming 20s scan time)
                do_contra_raw() # >> when i decide on course of action
        except Exception as msg:
            pass#print("err on contra_raw",str(msg))
        #if random.randint(1,2)==1:



        try:
            if random.randint(1,180)==1:#change this to happen once every few hours,, so 1,180 would be 1hr,, (assuming 20s scan time)
                pass#do_m8bets_raw() # >> when i decide on course of action
        except Exception as msg:
            pass#print("err on contra_raw",str(msg))

        pass#print("raw took:",time.time()-stime)

        print("raw took:",time.time()-rtime)

        active_betfair_comps = pull_active_comps()
        #time.sleep(1)#lets look at contras raws..
        p_time=time.time()
        conn = pymysql.connect(host='127.0.0.1',user='local',passwd='oeijifjwejfio',db=db_name)
        cur  = conn.cursor()

        compids=[]
        for abc in active_betfair_comps:
            compids.append(str(abc))



        #now i create the comp dict.. based on the events coming out of all_events.. and join via the lookup
        #here pull down the event lookup into event_dict. with comp key..comp dict?
        event_lookup={}
        comp_dict={}
        cur.execute("select event_id,comp_id from betfair_lookup")
        rows = cur.fetchall()
        for row in rows:
            event_lookup[row[0]]=row[1]#so all eventids are related to a compid via this dict..

        #with open("event_lookup.pickle","wb") as f:
        #    pickle.dump(event_lookup,f)

        #with open("all_events.pickle","wb") as f:
        #    pickle.dump(all_events,f)

        #print(event_lookup)
        #print(len(event_lookup))
        #now i loop over all events,, and if found in the event lookup, add to the comp dict..

        conn.close()

        #here do random bingoal sec check..
        if 'bingoal' in book_list and (random.randint(1,3600)==1 or not kvalue):
            print("doing bingoal security check")
            while 1:
                try:
                    res = requests.get("https://www.bingoal.nl",timeout=10,proxies = {"https":random.choice(proxies)})
                    sof = res.text.find("_k")
                    kvalue = res.text[sof+6:sof+10]
                    cookie_dict = res.cookies.get_dict()
                    ust = cookie_dict['ust']
                    b_session = cookie_dict['CSPSESSIONID-SP-80-UP-']
                    print(kvalue,ust,b_session)
                    break
                except Exception as msg:
                    print("looping bingoal..",str(msg))
                    pass
        else:
            #k_value=""
            #ust=""
            pass#b_session=""
        ztime = time.time()



        if 1:#try:
            ttime = time.time()
            #print("building all events")
            comps = get_comp_list()
            all_comps=[]
            for c in comps:
                all_comps.append(c['betfair'])
            all_events =  pull_all_events(all_comps) ## this s


            print("all_events:",len(all_events))
            for ae in all_events:
                #print(ae.event.id)
                event_id = int(ae.event.id )
                if event_id in event_lookup:
                    #add to the comp_dict
                    #print("Adding:",event_id)

                    if event_lookup[event_id] not in comp_dict:
                        comp_dict[event_lookup[event_id] ]=[]
                    comp_dict[event_lookup[event_id] ].append(ae)

            #print("lencompdict:",len(comp_dict))
            print(comp_dict)
            #print("epl cd len:",len(comp_dict[10932509]))

            print("lookup took:",time.time()  - p_time,"seconds")
            betfair_data_dict = betfair_dictbuilder(all_comps)
            with open("/home/arb_bot/gamma/betfair_dict.json","wb") as f:
                pickle.dump(betfair_data_dict,f)

            print("betfair data dict took:",time.time()-ztime,len(betfair_data_dict))
            print("got comps..took ",time.time()-ttime)
            go(comps)

        else:#except Exception as msg:
            pass#print("err on scan",str(msg))

        ## insert into last scan
        conn = pymysql.connect(host='127.0.0.1',user='local',passwd='oeijifjwejfio',db=db_name)
        cur  = conn.cursor()
        cur.execute("update log_table set timestamp=%s where log_type='last_scan'",(time.time()))# where toto_id=587")
        conn.commit()
        conn.close()

        print("scan took(" + str(int(time.time()-stime)) + " seconds (" + str(thread_count) + ") threads)..NOSleep..0 (GAMMA):" + str(datetime.datetime.now())[0:19])#
        print("bf_comps_active:",bf_comps_active)
        print("betfair_pull:",betfair_pull_time)
        print("betfair_pull_err_time >> :",betfair_pull_err_time)
        #trading.logout()
        print("logged out!")
    except Exception as msg:
        print("error in main loop",str(msg))

    timenow = time.time()
    elapsed = timenow - last_cycle_time
    print("elapsed:",elapsed)
    #here update scan times table..
    conn = pymysql.connect(host='127.0.0.1',user='local',passwd='oeijifjwejfio',db=db_name)
    cur  = conn.cursor()
    cur.execute("insert into arber_scan_times (book_list,start_time,scan_time) values(%s,%s,%s)",(json.dumps(book_list),str(datetime.datetime.now())[0:19],round(int(time.time()-stime))))
    conn.commit()
    conn.close()
    print("inserted..")

    time.sleep(1)
    if elapsed<60:
        time.sleep(60-elapsed)#sleep 5secs before redownload
#process_comp(comps[0])
pass#print("didnt start another instance")
