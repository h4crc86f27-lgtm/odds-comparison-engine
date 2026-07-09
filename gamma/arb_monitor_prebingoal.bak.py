#betfair API market puller
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
from arber_modules.unibet import *
from arber_modules.toto import *
from arber_modules.contra import *
from arber_modules.qrbet import *
from arber_modules.betfair import *
from arber_modules.winkel_toto import *


thread_count= 40

unibet_teams=[]
contra_teams=[]
toto_teams=[]
qrbet_teams=[]
winkel_toto_teams=[]

"""with open("/home/arb_bot/proxies") as f:
    proxies = f.read().split("\n")

try:
    proxies.remove('')
except:
    pass
"""

version="beta"
db_name="arb_db_"+ version


##ok,, from here, its matched, and has its fuzzy flag.. now just insert to db
## after consolidating ofc..


def process_comp_threaded(comp_meta):#toto_id,bf_id,league):
    try:
        #toto_data = pull_data_toto(comp_meta['toto'],comp_meta['league'])
        t1 = Thread(target=pull_data_toto, args=(comp_meta['toto'], comp_meta['league']))
    except Exception as msg:
        pass#pass#print("process err (toto):",str(msg))

    try:
        #betfair_data = pull_betfair_data(comp_meta['betfair'],comp_meta['league'])
        t2 = Thread(target=pull_betfair_data, args=(comp_meta['betfair']+ comp_meta['league']))

    except Exception as msg:
        pass#print("process err (bf):",str(msg))

    try:
        if comp_meta['unibet']=="":
            pass#print("skipping unibet for " + comp_meta['league'] + " >>  no compurl yet")
        else:
            unibet_data = pull_data_unibet(comp_meta['unibet'],comp_meta['league'])
            t1 = Thread(target=pull_data_toto, args=(comp_meta['toto']+ comp_meta['league']))

    except Exception as msg:
        pass#print("err on unibet pull:",str(msg))

    try:
        if comp_meta['contra']=="":
            pass#print("skipping contra for " + comp_meta['league'] + " >>  no compurl yet")
        else:
            contra_data = pull_data_contra(comp_meta['contra'],comp_meta['league'])
    except Exception as msg:
        pass#print("err on contra pull:",str(msg))

    try:
        if comp_meta['qrbet']=="":
            pass#print("skipping qrbet for " + comp_meta['league'] + " >>  no compurl yet")
        else:
            qrbet_data = pull_data_qrbet(comp_meta['qrbet'],comp_meta['league'])
    except Exception as msg:
        pass#print("err on qrbet pull:",str(msg))

    try:
        if comp_meta['winkel_toto']=="":
            pass#print("skipping winkel_toto for " + comp_meta['league'] + " >>  no compurl yet")
        else:
            winkel_toto_data = pull_data_winkel_toto(comp_meta['winkel_toto'],comp_meta['league'])
    except Exception as msg:
        pass#print("err on winkel_toto pull:",str(msg))


    ##toto check
    try:
        do_insert_toto(toto_data,betfair_data,comp_meta['league'])
    except:
        pass#print("err on toto insert")

    try:
        do_insert_unibet(unibet_data,betfair_data,comp_meta['league'])
    except Exception as msg:
        pass#print("err on unibet insert:",str(msg))

    try:
        do_insert_contra(contra_data,betfair_data,comp_meta['league'])
    except Exception as msg:
        pass#print("err on contra insert:",str(msg))

    try:
        do_insert_qrbet(qrbet_data,betfair_data,comp_meta['league'])
    except Exception as msg:
        pass#print("err on qrbet insert:",str(msg))

    try:
        do_insert_winkel_toto(winkel_toto_data,betfair_data,comp_meta['league'])
    except Exception as msg:
        pass#print("err on qrbet insert:",str(msg))


    ##qrbet check
    pass#print("finished processing :",comp_meta['league'],"<<<<<<<<<<>>>>>>>>>>>")


def process_comp(comp_meta):#toto_id,bf_id,league):
    global bf_comps_active

    global toto_teams,unibet_teams,contra_teams
    global betfair_pull_time,betfair_pull_err_time,unibet_pull_time,contra_pull_time,qrbet_pull_time,winkel_toto_pull_time,toto_pull_time
    global betfair_splice_time,unibet_splice_time,contra_splice_time,qrbet_splice_time,winkel_toto_splice_time,toto_splice_time

    btime=time.time()

    try:
        #print("pulling betfair")
        betfair_data = pull_betfair_data(comp_meta['betfair'],comp_meta['league'])
        #print("done bf..")
        if len(betfair_data)>0:
            betfair_pull_time+=time.time()-btime
            bf_comps_active+=1
        else:
            betfair_pull_err_time+=time.time()-btime
        #print(betfair_pull_time,"...")
    except Exception as msg:
        betfair_data=None
        #print("process err (bf): skipping other books.. no point",str(msg))
        betfair_pull_err_time+=time.time()-btime
        return 0


    if betfair_data:
        btime=time.time()
        try:
            #pass#print("running winkel_toto DATA>>>>>>>>>>>")
            if comp_meta['winkel_toto'] not in ["","https://winkel.toto.nl/nl/wedden/voetbal/"]:
                #print("PULLING WINKEL_TOTO")
                
                winkel_toto_data = pull_data_winkel_toto(comp_meta['winkel_toto'],comp_meta['league'])
                winkel_toto_pull_time+=time.time()-btime
                #print("WINKEL_TOTO PULLED")
            else:
                winkel_toto_pull_time+=time.time()-btime
                pass#print("skipping comp for winkel")
            #pass#print("done winkeltoto")
        except Exception as msg:
            winkel_toto_pull_time+=time.time()-btime
            print("process err (winkel_toto):",str(msg))


        btime=time.time()
        try:
            #print("PULLING TOTO")
            
            toto_data = pull_data_toto(comp_meta['toto'],comp_meta['league'])
            
            #print("TOTO PULLED")
        except Exception as msg:
            toto_pull_time+=time.time()-btime
            pass#print("process err (toto):",str(msg))


        btime=time.time()
        try:
            if comp_meta['unibet']=="":
                pass#print("skipping unibet for " + comp_meta['league'] + " >>  no compurl yet")
            else:
                #print("pulling UNIBET")
                
                unibet_data = pull_data_unibet(comp_meta['unibet'],comp_meta['league'])
                
                #print("UNIBET PULLED")
        except Exception as msg:
            unibet_pull_time+=time.time()-btime
            pass#print("err on unibet pull:",str(msg))

        btime=time.time()

        try:
            if comp_meta['contra']=="":
                pass#print("skipping contra for " + comp_meta['league'] + " >>  no compurl yet")
            else:
                #print("RUNNING CONTRA PULL!!!!")
                
                contra_data = pull_data_contra(comp_meta['contra'],comp_meta['league'])
                contra_pull_time+=time.time()-btime
                #print("CONTRA DONE..")
        except Exception as msg:
            contra_pull_time+=time.time()-btime
            pass#print("err on contra pull:",str(msg))

        btime = time.time()
        try:
            if comp_meta['qrbet']['name']=="":
                pass#print("skipping qrbet for " + comp_meta['league'] + " >>  no compurl yet")
            else:
                #print("qrbet pull")
                qrbet_data = pull_data_qrbet(comp_meta['qrbet']['id'],comp_meta['qrbet']['name'])
                qrbet_pull_time+=time.time()-btime
                #print("qrbet done")
        except Exception as msg:
            qrbet_pull_time+=time.time()-btime
            pass#print("err on qrbet pull:",str(msg))

        btime = time.time()
        try:
            #pass#print("attempting winkel_toto insert!!")
            if comp_meta['winkel_toto']=="":
                pass#print("kipping winkto insert")
            else:
                pass#print("attempting winkel_toto insert!!")
                
                do_insert_winkel_toto(winkel_toto_data,betfair_data,comp_meta['league'],winkel_toto_teams)
                winkel_toto_splice_time+=time.time()-btime
                
            #pass#print("finished winkel_toto insert <><>")
        except Exception as msg:
            winkel_toto_splice_time+=time.time()-btime
            print(str(msg),"err on winkel_toto insert")


        ##toto check
        btime = time.time()
        try:
            #btime =time.time()
            do_insert_toto(toto_data,betfair_data,comp_meta['league'],toto_teams)
            toto_splice_time+=time.time()-btime
        except:
            toto_splice_time+=time.time()-btime
            pass#print("err on toto insert")

        btime = time.time()

        try:
            
            do_insert_unibet(unibet_data,betfair_data,comp_meta['league'],unibet_teams)
            unibet_splice_time+=time.time()-btime
        except Exception as msg:
            unibet_splice_time+=time.time()-btime
            pass#print("err on unibet insert:",str(msg))
        btime = time.time()
        try:
            pass#print("INSERTTING CONTRA!!!!!!!!!!!")
            
            do_insert_contra(contra_data,betfair_data,comp_meta['league'],contra_teams)
            contra_splice_time+=time.time()-btime
            pass#print("CONTRA INSERT COMPLETED")
        except Exception as msg:
            contra_splice_time+=time.time()-btime
            pass#print("err on contra insert:",str(msg))
        btime = time.time()
        try:
            #btime = time.time()
            do_insert_qrbet(qrbet_data,betfair_data,comp_meta['league'],qrbet_teams)
            qrbet_splice_time+=time.time()-btime
        except Exception as msg:
            qrbet_splice_time+=time.time()-btime
            pass#print("err on qrbet insert:",str(msg))
    else:
        pass#pass#print("skipping crawl for this comp-- betfair_data ((NONE))")

    ##unibet check
    pass#print("finished processing :",comp_meta['league'],"<<<<<<<<<<>>>>>>>>>>>")

"""comps=[{"toto":"591","betfair":"129","league":"sweall"},
{"toto":"826","betfair":"12117172","league":"aleague"},
{"toto":"567","betfair":"10932509","league":"epl"},
{"toto":"1001","betfair":"12206014","league":"bahpre"},
{"toto":"4319","betfair":"12231751","league":"canpre"}]
"""

#comps=[{"toto":"567","betfair":"10932509","league":"epl"}]
def get_comp_list():
    comps=[]
    conn = pymysql.connect(host='127.0.0.1',user='local',passwd='oeijifjwejfio',db=db_name)
    cur  = conn.cursor()
    cur.execute("select * from comps where ignore_comp=0")# where id=40")#UEFA 207")# where id=6") #40 is EPL
    rows = cur.fetchall()
    conn.close()
    for row in rows:
        if row[12] is not None:
            winkel_id = row[12]
        else:
            winkel_id=""

        if row[6] is None:
            if row[8] is None:
                if row[10] is not None:
                    comps.append({"winkel_toto":winkel_id,"toto":str(row[4]),"betfair":str(row[2]),"unibet":str(""),"contra":"","qrbet":{"name":row[9],"id":row[10]},"league":row[1]}) # << here just need to splice in something benign for ub if null
                else:
                    comps.append({"winkel_toto":winkel_id,"toto":str(row[4]),"betfair":str(row[2]),"unibet":str(""),"contra":"","qrbet":{"name":"","id":""},"league":row[1]}) # << here just need to splice in something benign for ub if null
            else:
                if row[10] is not None:
                    comps.append({"winkel_toto":winkel_id,"toto":str(row[4]),"betfair":str(row[2]),"unibet":str(""),"contra":"","qrbet":{"name":row[9],"id":row[10]},"league":row[1]}) # << here just need to splice in something benign for ub if null
                else:
                    comps.append({"winkel_toto":winkel_id,"toto":str(row[4]),"betfair":str(row[2]),"unibet":str(""),"contra":row[8],"qrbet":{"name":"","id":""},"league":row[1]}) # << here just need to splice in something benign for ub if null
        else:
            if row[8] is None:
                if row[10] is not None:
                    comps.append({"winkel_toto":winkel_id,"toto":str(row[4]),"betfair":str(row[2]),"unibet":str(row[6]),"contra":"","qrbet":{"name":row[9],"id":row[10]},"league":row[1]}) 
                else:
                    comps.append({"winkel_toto":winkel_id,"toto":str(row[4]),"betfair":str(row[2]),"unibet":str(row[6]),"contra":"","qrbet":{"name":"","id":""},"league":row[1]}) # << here just need to splice in something benign for ub if null
 
            else:
                if row[10] is not None:
                    comps.append({"winkel_toto":winkel_id,"toto":str(row[4]),"betfair":str(row[2]),"unibet":str(row[6]),"contra":row[8],"qrbet":{"name":row[9],"id":row[10]},"league":row[1]})
                else:
                    comps.append({"winkel_toto":winkel_id,"toto":str(row[4]),"betfair":str(row[2]),"unibet":str(row[6]),"contra":row[8],"qrbet":{"name":"","id":""},"league":row[1]}) # << here just need to splice in something benign for ub if null
    pass#print("complen:",len(comps))
    #time.sleep(2)
    #pass#print(comps)
    #time.sleep(5)
    return comps



def go(comps):
    global thread_count
    threads = min(len(comps),thread_count)

    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        executor.map(process_comp, comps )


"""
isnt_running=True
output = sp.check_output(["pgrep","--list-full","python"])
lines = output.decode("utf8").split("\n")
for line in lines:
    pass#print(line)
    if line.find("arb_monitor.py")>-1:
        isnt_running=False
        pass#print("monitor is running")
        break"""

while 1:#isnt_running:
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
        #print("about to login..")
        trading.login()
        #print("logged in!")
        stime=time.time()
        print("team time..")
        contra_teams = get_team_list_contra()
        pass#print("got contra")
        toto_teams = get_team_list_toto()
        pass#print("goto toto")
        unibet_teams = get_team_list_unibet()
        pass#print("got unibet")
        qrbet_teams = get_team_list_qrbet()
        pass#print("got qrbet")
        winkel_toto_teams = get_team_list_winkel_toto()
        pass#print("got winkel_toto")
        print("teams took:",time.time()-stime)
        rtime=time.time()

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

        pass#print("raw took:",time.time()-stime)

        print("raw took:",time.time()-rtime)
        
        #time.sleep(1)#lets look at contras raws..

        if 1:#try:
            ttime = time.time()
            pass#print("getting comps")
            comps = get_comp_list()
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

        print("scan took(" + str(int(time.time()-stime)) + " seconds (" + str(thread_count) + ") threads)..NOSleep..0 (" +version.upper() + "):" + str(datetime.datetime.now())[0:19])#
        print("bf_comps_active:",bf_comps_active)
        print("betfair_pull:",betfair_pull_time)
        print("betfair_pull_err_time >> :",betfair_pull_err_time)
        print("unibet_pull:",unibet_pull_time)
        print("contra_pull:",contra_pull_time)
        print("qrbet_pull:",qrbet_pull_time)
        print("toto_pull:",toto_pull_time)
        print("winkel_toto_pull:",winkel_toto_splice_time)
        print("betfair_insert:",betfair_splice_time)
        print("unibet_insert:",unibet_splice_time)
        print("contra_insert:",contra_splice_time)
        print("qrbet_insert:",qrbet_splice_time)
        print("toto_insert:",toto_splice_time)
        print("winkel_toto_insert:",winkel_toto_splice_time)
        trading.logout()
        print("logged out!")
    except Exception as msg:
        print("error in main loop",str(msg))
    
    time.sleep(5)#sleep 5secs before redownload
#process_comp(comps[0])
pass#print("didnt start another instance")
