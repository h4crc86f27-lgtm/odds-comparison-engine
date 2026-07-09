servername = "127.0.0.1"
username = "local"
password = "oeijifjwejfio"
dbname = "arb_db_beta"
from asyncio import events
import pymysql
conn = pymysql.connect(host=servername, user=username, passwd = password, db = dbname)
cur = conn.cursor()
cur.execute("select betfair_event_id,count(*) from contra_matches group by betfair_event_id order by 2")
rows = cur.fetchall()
print("START")
for row in rows:
    if row[1]>1:
        print("found dupe")
        x=cur.execute("select id,contra_event_id from contra_matches where betfair_event_id=%s",(row[0]))
        event_ids = cur.fetchall()
        if len(event_ids)>1:
            print("deleting:",event_ids[0][0],event_ids[0][1])
            cur.execute("delete from contra_matches where id=%s",(event_ids[0][0]))
            #print("leaving:",event_ids[1][0],event_ids[1][1])
            #print("--")
print("STOP")

conn.commit()
conn.close()    
