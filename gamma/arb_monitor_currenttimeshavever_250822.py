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
from concurrent.futures import ThreadPoolExecutor

from arber_modules.unibet import *
from arber_modules.toto import *
from arber_modules.contra import *
from arber_modules.qrbet import *
from arber_modules.betfair import *
from arber_modules.winkel_toto import *
from arber_modules.bingoal import *

thread_count= 50

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
            pass#unibet_data = pull_data_unibet(comp_meta['unibet'],comp_meta['league'])
            t1 = Thread(target=pull_data_toto, args=(comp_meta['toto']+ comp_meta['league']))

    except Exception as msg:
        pass#print("err on unibet pull:",str(msg))

    try:
        if comp_meta['contra']=="":
            pass#print("skipping contra for " + comp_meta['league'] + " >>  no compurl yet")
        else:
            pass#contra_data = pull_data_contra(comp_meta['contra'],comp_meta['league'])
    except Exception as msg:
        pass#print("err on contra pull:",str(msg))

    try:
        if comp_meta['qrbet']=="":
            pass#print("skipping qrbet for " + comp_meta['league'] + " >>  no compurl yet")
        else:
            pass#qrbet_data = pull_data_qrbet(comp_meta['qrbet'],comp_meta['league'])
    except Exception as msg:
        pass#print("err on qrbet pull:",str(msg))

    try:
        if comp_meta['winkel_toto']=="":
            pass#print("skipping winkel_toto for " + comp_meta['league'] + " >>  no compurl yet")
        else:
            pass#winkel_toto_data = pull_data_winkel_toto(comp_meta['winkel_toto'],comp_meta['league'])
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
    global bingoal_k 
    global comp_dict
    global betfair_markets
    global bf_comps_active
    global market_pull_time
    global toto_teams,unibet_teams,contra_teams
    global betfair_pull_time,betfair_pull_err_time,unibet_pull_time,contra_pull_time,qrbet_pull_time,winkel_toto_pull_time,toto_pull_time
    global betfair_splice_time,unibet_splice_time,contra_splice_time,qrbet_splice_time,winkel_toto_splice_time,toto_splice_time

    btime=time.time()
    comp_start_time=time.time()

    try:

        #qrbet_data = pull_data_qrbet(comp_meta['qrbet']['id'],comp_meta['qrbet']['name'])
        #qrbet_data={}
        #t_qrbet = Thread(name='pull_data_qrbet', target=pull_data_qrbet,args=(comp_meta['qrbet'],comp_meta['league'],qrbet_data))
            
        #print("sending execs")
        """executors_list=[]

        with ThreadPoolExecutor(max_workers=6) as executor:
            executors_list.append(executor.submit(pull_betfair_data, comp_meta['betfair'],comp_meta['league'],betfair_markets,""))
            executors_list.append(executor.submit(pull_data_winkel, comp_meta['winkel_toto'],comp_meta['league'],""))
            executors_list.append(executor.submit(pull_data_toto, comp_meta['toto'],comp_meta['league'],""))
            executors_list.append(executor.submit(pull_data_qrbet, comp_meta['qrbet'],comp_meta['league'],""))
            executors_list.append(executor.submit(pull_data_unibet, comp_meta['unibet'],comp_meta['league'],""))
            executors_list.append(executor.submit(pull_data_contra, comp_meta['contra'],comp_meta['league'],""))

        print("done..")

        betfair_data = executors_list[0].result()
        winkel_toto_data = executors_list[1].result()
        toto_data = executors_list[2].result()
        qrbet_data = executors_list[3].result()
        unibet_data = executors_list[4].result()
        contra_data = executors_list[5].result()"""
        winkel_toto_data={}

        

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            # Start the load operations and mark each future with its URL
            #executor.submit(pull_data_winkel_toto,  comp_meta['winkel_toto'], comp_meta['league']): "winkel_toto",
            #,

            betfair_data={}

            future_to_url = {executor.submit(pull_betfair_data,  comp_meta['betfair'], comp_meta['league'],betfair_markets,"",comp_dict[int(comp_meta['betfair'])]): "betfair" }
            for future in concurrent.futures.as_completed(future_to_url,timeout=30):
                book = future_to_url[future]
                #rint(book)
                try:
                    betfair_data = future.result()
                    if len(betfair_data)==0:
                        print("bfzero:",time.time()-comp_start_time)
                        return None
                    else:
                        pass#print("bf>0:",time.time() - comp_start_time)

                except Exception as msg:
                    pass#print("bf err:",str(msg))
            if betfair_data=={}:
                #print("bf timeout i suppose")
                return None
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # Start the load operations and mark each future with its URL
            #executor.submit(pull_data_winkel_toto,  comp_meta['winkel_toto'], comp_meta['league']): "winkel_toto",
            #,executor.submit(pull_betfair_data,  comp_meta['betfair'], comp_meta['league'],betfair_markets): "betfair"
            #{executor.submit(pull_betfair_data,  comp_meta['betfair'], comp_meta['league'],betfair_markets,"",comp_dict[int(comp_meta['betfair'])]): "betfair",
            future_to_url = {
            executor.submit(pull_data_toto,  comp_meta['toto'], comp_meta['league']): "toto",
            executor.submit(pull_data_unibet,  comp_meta['unibet'], comp_meta['league']): "unibet",
            executor.submit(pull_data_contra,  comp_meta['contra'], comp_meta['league']): "contra",
            executor.submit(pull_data_qrbet,  comp_meta['qrbet'], comp_meta['league']): "qrbet", 
            executor.submit(pull_data_winkel_toto,  comp_meta['winkel_toto'], comp_meta['league']): "winkel_toto" 
            }
            #, executor.submit(pull_data_winkel_toto,  comp_meta['winkel_toto'], comp_meta['league']): "winkel_toto"            
            for future in concurrent.futures.as_completed(future_to_url):
                book = future_to_url[future]
                #rint(book)
                try:
                    data = future.result()
                    if book=="toto":
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
                    
                except Exception as exc:
                    pass#print('%r generated an exception: %s' % (book, exc))
                else:
                    #print(book, data)
                    if book=="toto":
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
        

        """print(betfair_data)
        time.sleep(1)
        print(winkel_toto_data)
        time.sleep(1)
        print(toto_data)
        time.sleep(1)
        print(qrbet_data)
        time.sleep(1)
        print(unibet_data)
        time.sleep(1)
        print(contra_data)
        time.sleep(1)"""
        
        if len(betfair_data)==0:
            #print("returning none")
            print("zero comp took:",time.time() - comp_start_time)
            return None
        btime = time.time()
        try:
            #btime =time.time()
            #print("inserting bingoal data..")
            pass#do_insert_bingoal(bingoal_data,betfair_data,comp_meta['league'],bingoal_teams)
            #bingoal_splice_time+=time.time()-btime
        except Exception as msg:
            #toto_splice_time+=time.time()-btime
            print("err on bingoal insert:",str(msg))

        try:
            #pass#print("attempting winkel_toto insert!!")
            if comp_meta['winkel_toto']=="":
                pass#print("kipping winkto insert")
            else:
                pass#print("attempting winkel_toto insert!!")
                
                do_insert_winkel_toto(winkel_toto_data,betfair_data,comp_meta['league'],winkel_toto_teams,"")
                winkel_toto_splice_time+=time.time()-btime
                
            #pass#print("finished winkel_toto insert <><>")
        except Exception as msg:
            winkel_toto_splice_time+=time.time()-btime
            #print(str(msg),"err on winkel_toto insert")


        ##toto check
        btime = time.time()
        try:
            #btime =time.time()
            #print("inserting toto",len(toto_data),len(betfair_data))
            do_insert_toto(toto_data,betfair_data,comp_meta['league'],toto_teams)
            toto_splice_time+=time.time()-btime
        except Exception as msg:
            toto_splice_time+=time.time()-btime
            print("err on toto insert",str(msg))

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
   
        pass#print("finished processing :",comp_meta['league'],"<<<<<<<<<<>>>>>>>>>>>")
    except Exception as msg:
        print(str(msg))

def process_comp_seq(comp_meta):#toto_id,bf_id,league):
    global bingoal_k 
    global comp_dict
    global betfair_markets
    global bf_comps_active
    global market_pull_time
    global toto_teams,unibet_teams,contra_teams
    global betfair_pull_time,betfair_pull_err_time,unibet_pull_time,contra_pull_time,qrbet_pull_time,winkel_toto_pull_time,toto_pull_time
    global betfair_splice_time,unibet_splice_time,contra_splice_time,qrbet_splice_time,winkel_toto_splice_time,toto_splice_time

    btime=time.time()

    betfair_data={}
    #betfair_data = pull_betfair_data(comp_meta['betfair'],comp_meta['league'],betfair_markets)
    #t_betfair = Thread(name='pull_betfair_data', target=pull_betfair_data,args=(comp_meta['betfair'],comp_meta['league'],betfair_markets,betfair_data))
    #t_betfair.start()

    try:
        #print("pulling betfair")
        betfair_data = pull_betfair_data(comp_meta['betfair'],comp_meta['league'],betfair_markets,"",comp_dict[int(comp_meta['betfair'])])
        
        #print("done bf..")
        if len(betfair_data)>0:
            betfair_pull_time+=time.time()-btime
            bf_comps_active+=1
        else:
            betfair_pull_err_time+=time.time()-btime
        #print(betfair_pull_time,"...")
    except Exception as msg:
        betfair_data=None
        ##print("process err (bf): skipping other books.. no point",str(msg))
        betfair_pull_err_time+=time.time()-btime
        return 0

    #print("skipping other pulls..")

    if betfair_data:
        btime=time.time()

        try:
            #print("PULLING bingoal")
            if comp_meta['bingoal']!='':
                pass#print("skip bingoal")#bingoal_data = {}#pull_data_bingoal(comp_meta['bingoal'],comp_meta['league'],bingoal_k)
            else:
                pass#print("skipping empty bingoal comp")
                bingoal_data={}
            #print("TOTO PULLED")
        except Exception as msg:
            #toto_pull_time+=time.time()-btime
            print("process err (bingoal):",str(msg))

        try:
            #pass#print("running winkel_toto DATA>>>>>>>>>>>")
            if comp_meta['winkel_toto'] not in ["","https://winkel.toto.nl/nl/wedden/voetbal/"]:
                #print("PULLING WINKEL_TOTO")
                
                winkel_toto_data = pull_data_winkel_toto(comp_meta['winkel_toto'],comp_meta['league'],"")
                winkel_toto_pull_time+=time.time()-btime
                #print("WINKEL_TOTO PULLED")
            else:
                winkel_toto_pull_time+=time.time()-btime
                pass#print("skipping comp for winkel")
            #pass#print("done winkeltoto")
        except Exception as msg:
            winkel_toto_pull_time+=time.time()-btime
            #print("process err (winkel_toto):",str(msg))


        btime=time.time()
        try:
            #print("PULLING TOTO")
            
            toto_data = pull_data_toto(comp_meta['toto'],comp_meta['league'],"")
            
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
                
                unibet_data = pull_data_unibet(comp_meta['unibet'],comp_meta['league'],"")
                
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
                
                contra_data = pull_data_contra(comp_meta['contra'],comp_meta['league'],"")
                contra_pull_time+=time.time()-btime
                #print("CONTRA DONE..")
        except Exception as msg:
            contra_pull_time+=time.time()-btime
            pass#print("err on contra pull:",str(msg))

        #contra_data={}

        #t_contra = Thread(name='pull_data_contra', target=pull_data_contra,args=(comp_meta['contra'],comp_meta['league'],contra_data))
        #t_contra.start()

        btime = time.time()
        try:
            if comp_meta['qrbet']['name']=="":
                pass#print("skipping qrbet for " + comp_meta['league'] + " >>  no compurl yet")
            else:
                #print("qrbet pull")
                qrbet_data = pull_data_qrbet(comp_meta['qrbet']['id'],comp_meta['qrbet']['name'],"")
                qrbet_pull_time+=time.time()-btime
                #print("qrbet done")
        except Exception as msg:
            qrbet_pull_time+=time.time()-btime
            pass#print("err on qrbet pull:",str(msg))


        #t_betfair.join()
        #t_contra.join()

        btime = time.time()
        try:
            #btime =time.time()
            #print("inserting bingoal data..")
            pass#do_insert_bingoal(bingoal_data,betfair_data,comp_meta['league'],bingoal_teams)
            #bingoal_splice_time+=time.time()-btime
        except Exception as msg:
            #toto_splice_time+=time.time()-btime
            print("err on bingoal insert:",str(msg))

        try:
            #pass#print("attempting winkel_toto insert!!")
            if comp_meta['winkel_toto']=="":
                pass#print("kipping winkto insert")
            else:
                pass#print("attempting winkel_toto insert!!")
                
                do_insert_winkel_toto(winkel_toto_data,betfair_data,comp_meta['league'],winkel_toto_teams,"")
                winkel_toto_splice_time+=time.time()-btime
                
            #pass#print("finished winkel_toto insert <><>")
        except Exception as msg:
            winkel_toto_splice_time+=time.time()-btime
            #print(str(msg),"err on winkel_toto insert")


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
    global active_betfair_comps
    print("bfactives:",len(active_betfair_comps))
    comps=[]
    conn = pymysql.connect(host='127.0.0.1',user='local',passwd='oeijifjwejfio',db=db_name)
    cur  = conn.cursor()
    cur.execute("select * from comps where ignore_comp=0")# and (id=14 or id= 40)")#UEFA 207")# where id=6") #40 is EPL
    rows = cur.fetchall()
    conn.close()


    for row in rows:
        if str(row[2]) not in active_betfair_comps:
            #print(str(row[2]),"not active")
            continue
        if row[12] is not None:
            winkel_id = row[12]
        else:
            winkel_id=""

        if row[6] is None:
            if row[8] is None:
                if row[10] is not None:
                    if row[14] is not None:
                        comps.append({"bingoal":row[14],"winkel_toto":winkel_id,"toto":str(row[4]),"betfair":str(row[2]),"unibet":str(""),"contra":"","qrbet":{"name":row[9],"id":row[10]},"league":row[1]}) # << here just need to splice in something benign for ub if null
                    else:
                        comps.append({"bingoal":"","winkel_toto":winkel_id,"toto":str(row[4]),"betfair":str(row[2]),"unibet":str(""),"contra":"","qrbet":{"name":row[9],"id":row[10]},"league":row[1]}) # << here just need to splice in something benign for ub if null
                else:
                    if row[14] is not None:
                        comps.append({"bingoal":row[14],"winkel_toto":winkel_id,"toto":str(row[4]),"betfair":str(row[2]),"unibet":str(""),"contra":"","qrbet":{"name":"","id":""},"league":row[1]}) # << here just need to splice in something benign for ub if null
                    else:
                        comps.append({"bingoal":"","winkel_toto":winkel_id,"toto":str(row[4]),"betfair":str(row[2]),"unibet":str(""),"contra":"","qrbet":{"name":"","id":""},"league":row[1]}) # << here just need to splice in something benign for ub if null
           
            else:
                if row[10] is not None:
                    if row[14] is not None:
                        comps.append({"bingoal":row[14],"winkel_toto":winkel_id,"toto":str(row[4]),"betfair":str(row[2]),"unibet":str(""),"contra":"","qrbet":{"name":row[9],"id":row[10]},"league":row[1]}) # << here just need to splice in something benign for ub if null
                    else:
                        comps.append({"bingoal":"","winkel_toto":winkel_id,"toto":str(row[4]),"betfair":str(row[2]),"unibet":str(""),"contra":"","qrbet":{"name":row[9],"id":row[10]},"league":row[1]}) # << here just need to splice in something benign for ub if null
                else:
                    if row[14] is not None:
                        comps.append({"bingoal":row[14],"winkel_toto":winkel_id,"toto":str(row[4]),"betfair":str(row[2]),"unibet":str(""),"contra":row[8],"qrbet":{"name":"","id":""},"league":row[1]}) # << here just need to splice in something benign for ub if null
                    else:
                        comps.append({"bingoal":"","winkel_toto":winkel_id,"toto":str(row[4]),"betfair":str(row[2]),"unibet":str(""),"contra":row[8],"qrbet":{"name":"","id":""},"league":row[1]}) # << here just need to splice in something benign for ub if null
        else:
            if row[8] is None:
                if row[10] is not None:
                    if row[14] is not None:
                        comps.append({"bingoal":row[14],"winkel_toto":winkel_id,"toto":str(row[4]),"betfair":str(row[2]),"unibet":str(row[6]),"contra":"","qrbet":{"name":row[9],"id":row[10]},"league":row[1]}) 
                    else:
                        comps.append({"bingoal":"","winkel_toto":winkel_id,"toto":str(row[4]),"betfair":str(row[2]),"unibet":str(row[6]),"contra":"","qrbet":{"name":row[9],"id":row[10]},"league":row[1]}) 
                else:
                    if row[14] is not None:
                        comps.append({"bingoal":row[14],"winkel_toto":winkel_id,"toto":str(row[4]),"betfair":str(row[2]),"unibet":str(row[6]),"contra":"","qrbet":{"name":"","id":""},"league":row[1]}) # << here just need to splice in something benign for ub if null
                    else:
                        comps.append({"bingoal":"","winkel_toto":winkel_id,"toto":str(row[4]),"betfair":str(row[2]),"unibet":str(row[6]),"contra":"","qrbet":{"name":"","id":""},"league":row[1]}) # << here just need to splice in something benign for ub if null
 
            else:
                if row[10] is not None:
                    if row[14] is not None:
                        comps.append({"bingoal":row[14],"winkel_toto":winkel_id,"toto":str(row[4]),"betfair":str(row[2]),"unibet":str(row[6]),"contra":row[8],"qrbet":{"name":row[9],"id":row[10]},"league":row[1]})
                    else:
                        comps.append({"bingoal":"","winkel_toto":winkel_id,"toto":str(row[4]),"betfair":str(row[2]),"unibet":str(row[6]),"contra":row[8],"qrbet":{"name":row[9],"id":row[10]},"league":row[1]})
                else:
                    if row[14] is not None:
                        comps.append({"bingoal":row[14],"winkel_toto":winkel_id,"toto":str(row[4]),"betfair":str(row[2]),"unibet":str(row[6]),"contra":row[8],"qrbet":{"name":"","id":""},"league":row[1]}) # << here just need to splice in something benign for ub if null
                    else:
                        comps.append({"bingoal":"","winkel_toto":winkel_id,"toto":str(row[4]),"betfair":str(row[2]),"unibet":str(row[6]),"contra":row[8],"qrbet":{"name":"","id":""},"league":row[1]}) # << here just need to splice in something benign for ub if null
    pass#print("complen:",len(comps))
    #time.sleep(2)
    #pass#
    print("comps:",len(comps))
    time.sleep(1)
    return comps



def go(comps):
    global thread_count
    threads = min(len(comps),thread_count)

    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        #executor.map(process_comp,comps)# fastest           ~170s >> some wrong odds..
        executor.map(process_comp_seq, comps ) # failsafe  ~220s


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
        market_pull_time=0
        betfair_pull_time=0
        betfair_pull_err_time=0
        contra_pull_time=0
        toto_pull_time=0
        unibet_pull_time=0
        winkel_toto_pull_time=0
        qrbet_pull_time=0
        betfair_markets={}
        comp_dict={}




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

        bingoal_teams = get_team_list_bingoal()
        pass#print("got winkel_toto")

        #here do bingoal k check..
        #bingoal_k = get_bingoal_k()


        print("teams took:",time.time()-stime)
        rtime=time.time()
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
        conn = pymysql.connect(host='127.0.0.1',user='local',passwd='oeijifjwejfio',db=db_name)
        cur  = conn.cursor()
        cur.execute("select event_id,market,market_id from betfair_markets")
        rows = cur.fetchall()
        betfair_markets={}
        for row in rows:
            betfair_markets[str(row[0]) + "_" + str(row[1])]=float(row[2])


        
        p_time= time.time()
        
        active_betfair_comps = pull_active_comps()
        compids=[]
        for abc in active_betfair_comps:
            compids.append(str(abc))

        all_events =  pull_all_events(compids) ## this s
        
        print("all_events:",len(all_events))

        #now i create the comp dict.. based on the events coming out of all_events.. and join via the lookup
        #here pull down the event lookup into event_dict. with comp key..comp dict?
        event_lookup={}
        comp_dict={}
        cur.execute("select event_id,comp_id from betfair_lookup")
        rows = cur.fetchall()
        for row in rows:
            event_lookup[row[0]]=row[1]#so all eventids are related to a compid via this dict..

        with open("event_lookup.pickle","wb") as f:
            pickle.dump(event_lookup,f)
        
        with open("all_events.pickle","wb") as f:
            pickle.dump(all_events,f)

        #print(event_lookup)
        #print(len(event_lookup))
        #now i loop over all events,, and if found in the event lookup, add to the comp dict..
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
        print("epl cd len:",len(comp_dict[10932509]))

        print("lookup took:",time.time()  - p_time,"seconds")

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
        print("market_pull_time:",market_pull_time)
        print("betfair_pull:",betfair_pull_time)
        print("betfair_pull_err_time >> :",betfair_pull_err_time)
        print("unibet_pull:",unibet_pull_time)
        print("contra_pull:",contra_pull_time)
        print("qrbet_pull:",qrbet_pull_time)
        print("toto_pull:",toto_pull_time)
        print("winkel_toto_pull:",winkel_toto_splice_time)
        """print("betfair_insert:",betfair_splice_time)
        print("unibet_insert:",unibet_splice_time)
        print("contra_insert:",contra_splice_time)
        print("qrbet_insert:",qrbet_splice_time)
        print("toto_insert:",toto_splice_time)
        print("winkel_toto_insert:",winkel_toto_splice_time)"""
        trading.logout()
        print("logged out!")
    except Exception as msg:
        print("error in main loop",str(msg))
    
    time.sleep(5)#sleep 5secs before redownload
#process_comp(comps[0])
pass#print("didnt start another instance")
