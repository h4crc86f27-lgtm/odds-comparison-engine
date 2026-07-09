#"insert into odds_history_archive select a.id, a.timestamp,a.match_key,a.matchid,a.book,a.odds from odds_history a,contra_matches b where book='contra' and matchid=contra_event_id and b.timestamp<unix_timestamp();"select a.id, a.timestamp,a.match_key,a.matchid,a.book,a.odds from odds_history a,contra_matches b where book='contra' and matchid=contra_event_id and b.timestamp<unix_timestamp();"
import pymysql
conn = pymysql.connect(host='127.0.0.1',user='local',passwd='oeijifjwejfio',db='arb_db_beta')
cur = conn.cursor()


#BETFAIR..
#use the bf_ids_expired view to purge these.. so pull the list of expired bfids.. and then just
##need a better method, takes ages with a million records,, but lets do the intial, and then it should speed up anyway.
print("purging betfair processed")
cur.execute("select * from bf_ids_expired")
rows = cur.fetchall()
expired_bf_ids = []
for row in rows:
    expired_bf_ids.append(row[0])

print("len(bf_expired):",len(expired_bf_ids))

#betfair
for ebi in expired_bf_ids:
    cur.execute("select a.id, a.timestamp,a.match_key,a.matchid,a.book,a.odds from odds_history a where book='betfair' and matchid=%s",(ebi))
    rows = cur.fetchall()

    print("found BETFAIR:",ebi,len(rows))

    for row in rows:
        try:
            x= cur.execute("insert into odds_history_archive (timestamp,match_key,matchid,book,odds) values(%s,%s,%s,%s,%s)",tuple(row[1:]))
        except:
            pass
    for row in rows:
        x= cur.execute("delete from odds_history where id=%s",(row[0]))

conn.commit()

#ODDS_HISTORY AREA
#CONTRA
cur.execute("select a.id, a.timestamp,a.match_key,a.matchid,a.book,a.odds from odds_history a,contra_matches b where book='contra' and matchid=contra_event_id and b.timestamp<unix_timestamp();")
rows = cur.fetchall()

print("found CONTRA:",len(rows))

for row in rows:
    try:
        x= cur.execute("insert into odds_history_archive (timestamp,match_key,matchid,book,odds) values(%s,%s,%s,%s,%s)",tuple(row[1:]))
    except:
        pass

for row in rows:
    x= cur.execute("delete from odds_history where id=%s",(row[0]))

conn.commit()

#UNIBET
cur.execute("select a.id, a.timestamp,a.match_key,a.matchid,a.book,a.odds from odds_history a,unibet_matches b where book='unibet' and matchid=unibet_event_id and b.timestamp<unix_timestamp();")
rows = cur.fetchall()

print("found UNIBET:",len(rows))

for row in rows:
    try:
        x= cur.execute("insert into odds_history_archive (timestamp,match_key,matchid,book,odds) values(%s,%s,%s,%s,%s)",tuple(row[1:]))
    except:
        pass
for row in rows:
    x= cur.execute("delete from odds_history where id=%s",(row[0]))

conn.commit()

#QRBET
cur.execute("select a.id, a.timestamp,a.match_key,a.matchid,a.book,a.odds from odds_history a,qrbet_matches b where book='qrbet' and matchid=qrbet_event_id and b.timestamp<unix_timestamp();")
rows = cur.fetchall()

print("found QRBET:",len(rows))

for row in rows:
    try:
        x= cur.execute("insert into odds_history_archive (timestamp,match_key,matchid,book,odds) values(%s,%s,%s,%s,%s)",tuple(row[1:]))
    except:
        pass
for row in rows:
    x= cur.execute("delete from odds_history where id=%s",(row[0]))

conn.commit()

#TOTO
cur.execute("select a.id, a.timestamp,a.match_key,a.matchid,a.book,a.odds from odds_history a,toto_matches b where book='toto' and matchid=toto_event_id and b.timestamp<unix_timestamp();")
rows = cur.fetchall()

print("found TOTO:",len(rows))

for row in rows:
    try:
        x= cur.execute("insert into odds_history_archive (timestamp,match_key,matchid,book,odds) values(%s,%s,%s,%s,%s)",tuple(row[1:]))
    except:
        pass
for row in rows:
    x= cur.execute("delete from odds_history where id=%s",(row[0]))

conn.commit()

#WINKELTOTO
cur.execute("select a.id, a.timestamp,a.match_key,a.matchid,a.book,a.odds from odds_history a,winkel_toto_matches b where book='winkel_toto' and matchid=winkel_toto_event_id and b.timestamp<unix_timestamp();")
rows = cur.fetchall()

print("found WINKELTOTO:",len(rows))

for row in rows:
    try:
        x= cur.execute("insert into odds_history_archive (timestamp,match_key,matchid,book,odds) values(%s,%s,%s,%s,%s)",tuple(row[1:]))
    except:
        pass
for row in rows:
    x= cur.execute("delete from odds_history where id=%s",(row[0]))

conn.commit()


conn.close()
