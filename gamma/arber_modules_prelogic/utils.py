import datetime
import pymysql
import configparser
import time
import unicodedata
import json

config = configparser.ConfigParser()
config.read('config.ini')
print(config.sections())
db_name="arb_db_beta"#db_name = config['DEFAULT']['db_name']


def do_odds_history_insert(book,event_id,odds_data,market_data,vwap_data = None):
    
    od = odds_data.copy()
    md = market_data.copy()
	
    od_dump=""
    
    
    if book=="betfair":
        #print("BF ODDS HIST DUMP>>>>")
        #print(od)
        #print("END DUMP<<<<<<<<<<<<<<<")
        od_contents={} 
        # currently is overwriting the book odds,, coz same names,,
        # either need to change the names, add more subcats,, or split them up like with 
        # the books.
        
        for o in od[0]:
            od_contents[o + "_1"]=od[0][o]
        
        for o in od[1]:
            od_contents[o + "_X"]=od[1][o]
        
        for o in od[2]:
            od_contents[o + "_2"]=od[2][o]
        
        for o in md:
            od_contents.update(o)
        #print(od_contents)
    	
        for v in vwap_data:
            od_contents['vwap_' + v] = vwap_data[v]

        for o in od_contents:
            od_dump+=str(od_contents[o]) + "_"
    else:
        od_contents=[]
        for o in od:
            od_contents.append(o)
            od_dump+=str(o['price']) + "_"
        for o in md:
            od_contents.append(o)
            od_dump+=str(o['price']) + "_"

    
    

    #print(">>>",len(od_dump))
    #od.update(md)
    #now create key from match_id and od dump
    #od_dump = json.dumps(od_contents)
    match_key = str(event_id) + "_" + od_dump
    try:
        conn = pymysql.connect(host='127.0.0.1',user='local',passwd='oeijifjwejfio',db=db_name)
        cur  = conn.cursor()
        cur.execute("insert into odds_history (timestamp,match_key,matchid,book,odds) values(%s,%s,%s,%s,%s)",(int(time.time()),match_key,event_id,book,json.dumps(od_contents)))
        conn.commit()
        conn.close()
    except Exception as msg:
        pass#print("err in historical odds inject",book,str(msg),od_dump)

def convert_euro_time(inny):
	#print(inny)
	x,y = inny.split("T")
	yr,mt,dt = x.split("-")
	hr,mn,sc = y.split(":")

	return str(datetime.datetime(int(yr),int(mt),int(dt),int(hr),int(mn),int(sc)) - datetime.timedelta(hours=2))[0:19].replace(" ","T")

def convert_yess_time(inny):
	#print(inny)
	x,y = inny.split(" ")
	yr,mt,dt = x.split("-")
	hr,mn,sc = y.split(":")

	return str(datetime.datetime(int(yr),int(mt),int(dt),int(hr),int(mn),int(sc)) - datetime.timedelta(hours=3))[0:19].replace(" ","T")


def convert_midnight(inny):
	#print(inny)
	x,y = inny.split("T")
	yr,mt,dt = x.split("-")
	retval = x
	if y=='00:00:00Z':
		#add a day.
		retval = str(datetime.datetime(int(yr),int(mt),int(dt)) + datetime.timedelta(days=1))[0:10]
	return retval

def strip_accents(s):
   return ''.join(c for c in unicodedata.normalize('NFD', s)
                  if unicodedata.category(c) != 'Mn')

def insert_error(err_str,misc=""):
    conn = pymysql.connect(host='localhost',user='local',passwd='oeijifjwejfio',db=db_name)
    cur  = conn.cursor()
    cur.execute("insert into errors (timestamp,err_msg,misc) values(%s,%s,%s)",(time.time(),err_str,misc))
    conn.commit()
    conn.close()

