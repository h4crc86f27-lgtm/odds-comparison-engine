#this script will take odds_history table, parse it, and simplify to basic arrays per matchid/market,, for the dash to easily pull

import pymysql
import json
import time
import pickle

stime=time.time()

conn = pymysql.connect(user='local',host='localhost',passwd='oeijifjwejfio',db='arb_db_beta')
cur=conn.cursor()

cur.execute("select * from odds_history")
rows = cur.fetchall()
matches={}

print(len(rows))

for row in rows:
    if row[3] not in matches:
        matches[row[3]]={"book":row[4],"odds":{"1":[],"X":[],"2":[],"DNB_Home":[],"DNB_Away":[],"2.5_Under":[],"2.5_Over":[],"3.5_Under":[],"3.5_Over":[],"DC_12":[],"DC_1X":[],"DC_X2":[],"1_HT":[],"X_HT":[],"2_HT":[]}}
    odds_data = json.loads(row[5])
    if row[4] !="betfair":
        m=0
        for market in odds_data:
            m+=1
            if market['name']=="Draw":
                market_name = "X"
            else:
                if m==1:
                    market_name="1"
                elif m==3:
                    market_name="2"
                else:
                    market_name = market['name']

            if market_name in matches[row[3]]['odds']:
                if len(matches[row[3]]['odds'][market_name])>0:
                    #ensure last price isn't the same
                    if matches[row[3]]['odds'][market_name][-1][-1]!=float(market['price']) and float(market['price'])>0:

                        matches[row[3]]['odds'][market_name].append([row[1],market['price']])
                else:
                    if float(market['price'])>0:
                        matches[row[3]]['odds'][market_name].append([row[1],float(market['price'])])
    else:
        #is betfair..
        for market in odds_data:
            #print(market)
            if market not in matches[row[3]]['odds']:
                #add it..
                #print("adding market",market)
                matches[row[3]]['odds'][market]=[]
            if len(matches[row[3]]['odds'][market])>0:
                #add to array
                #print("non zero array)")
                if str(matches[row[3]]['odds'][market][-1][-1])!=str(odds_data[market]) and odds_data[market] and  str(odds_data[market])!="0":

                    matches[row[3]]['odds'][market].append([row[1],odds_data[market]])
                
            else:
                #print("zero array",odds_data[market])
                if odds_data[market] and odds_data[market]>0:
                    matches[row[3]]['odds'][market].append([row[1],odds_data[market]])
            #print(matches[row[3]]['odds'])



#$with open("processed_history.pickle","wb") as f:
#    pickle.dump(matches,f)
print(len(matches))
#here you need to make an insert dict,, and then use this to update the table
#in the event that the match/market already exists in table.. 
cur.execute("select id,matchid,market from processed_historical")
rows = cur.fetchall()
insert_dict={}
for row in rows:
    insert_dict[row[1] + "_" + row[2]] =row[0] 

inserted=0
updated=0

for match in matches:
    #print(match)
    for market in matches[match]['odds']:
        #print(match,)
        #print(match,int(time.time()),json.dumps(matches[match]['odds'][market]),matches[match]['book'])
        if match + "_" + market in insert_dict:
            #print("updating")
            updated+=1
            x=cur.execute("update processed_historical set timestamp=%s,odds=%s where id=%s",(int(time.time()),json.dumps(matches[match]['odds'][market]),insert_dict[match + "_" + market]))
        else:
            #print("inserting")
            inserted+=1
            x=cur.execute("insert into processed_historical (matchid,timestamp,odds,book,market) values(%s,%s,%s,%s,%s)",(match,int(time.time()),json.dumps(matches[match]['odds'][market]),matches[match]['book'],market))
print("DONE!",inserted,updated)
conn.commit()
conn.close()
print(time.time()-stime)
