#"insert into odds_history_archive select a.id, a.timestamp,a.match_key,a.matchid,a.book,a.odds from odds_history a,contra_matches b where book='contra' and matchid=contra_event_id and b.timestamp<unix_timestamp();"select a.id, a.timestamp,a.match_key,a.matchid,a.book,a.odds from odds_history a,contra_matches b where book='contra' and matchid=contra_event_id and b.timestamp<unix_timestamp();"
import pymysql
conn = pymysql.connect(host='127.0.0.1',user='local',passwd='oeijifjwejfio',db='arb_db_beta')
cur = conn.cursor()

#PROCESSED_HISTORICAL AREA

#BETFAIR..
#use the bf_ids_expired view to purge these.. so pull the list of expired bfids.. and then just
##need a better method, takes ages with a million records,, but lets do the intial, and then it should speed up anyway.
print("purging betfair processed")
cur.execute("select * from bf_ids_expired")
rows = cur.fetchall()
expired_bf_ids = []
for row in rows:
    expired_bf_ids.append(row[0])

for ebi in expired_bf_ids:
    print(ebi)
    cur.execute("select id,matchid, timestamp,odds,book,market from processed_historical where book='betfair' and matchid=%s",(ebi))
    rows = cur.fetchall()
    print(expired_bf_ids.index(ebi),len(expired_bf_ids),len(rows))
    for row in rows:
        try:
            x= cur.execute("insert into processed_historical_archive (matchid,timestamp,odds,book,market) values(%s,%s,%s,%s,%s)",tuple(row[1:]))
        except:
            pass
    print("inserted")
    for row in rows:
        cur.execute("delete from processed_historical where id=%s",(row[0]))
    print("deleted")
    conn.commit()

#..just make sure
for b in expired_bf_ids:
    x=cur.execute("delete from processed_historical where matchid=%s",(b))
    conn.commit()
    
#CONTRA
cur.execute("select a.id,a.matchid, a.timestamp,a.odds,a.book,a.market from processed_historical a,contra_matches b where book='contra' and matchid=contra_event_id and b.timestamp<unix_timestamp();")
rows = cur.fetchall()

print("found CONTRA processed:",len(rows))

for row in rows:
    try:
        x= cur.execute("insert into processed_historical_archive (matchid,timestamp,odds,book,market) values(%s,%s,%s,%s,%s)",tuple(row[1:]))
    except:
        pass

for row in rows:
    x= cur.execute("delete from processed_historical where id=%s",(row[0]))

conn.commit()
#UNIBET
cur.execute("select a.id,a.matchid, a.timestamp,a.odds,a.book,a.market from processed_historical a,unibet_matches b where book='unibet' and matchid=unibet_event_id and b.timestamp<unix_timestamp();")
rows = cur.fetchall()

print("found UNIBET processed:",len(rows))

for row in rows:
    try:
        x= cur.execute("insert into processed_historical_archive (matchid,timestamp,odds,book,market) values(%s,%s,%s,%s,%s)",tuple(row[1:]))
    except:
        pass

for row in rows:
    x= cur.execute("delete from processed_historical where id=%s",(row[0]))

conn.commit()
#QRET
cur.execute("select a.id,a.matchid, a.timestamp,a.odds,a.book,a.market from processed_historical a,qrbet_matches b where book='qrbet' and matchid=qrbet_event_id and b.timestamp<unix_timestamp();")
rows = cur.fetchall()

print("found QRBET processed:",len(rows))

for row in rows:
    try:
        x= cur.execute("insert into processed_historical_archive (matchid,timestamp,odds,book,market) values(%s,%s,%s,%s,%s)",tuple(row[1:]))
    except:
        pass

for row in rows:
    x= cur.execute("delete from processed_historical where id=%s",(row[0]))

conn.commit()
#TOTO
cur.execute("select a.id,a.matchid, a.timestamp,a.odds,a.book,a.market from processed_historical a,toto_matches b where book='toto' and matchid=toto_event_id and b.timestamp<unix_timestamp();")
rows = cur.fetchall()

print("found TOTO processed:",len(rows))

for row in rows:
    try:
        x= cur.execute("insert into processed_historical_archive (matchid,timestamp,odds,book,market) values(%s,%s,%s,%s,%s)",tuple(row[1:]))
    except:
        pass

for row in rows:
    x= cur.execute("delete from processed_historical where id=%s",(row[0]))

conn.commit()
#WINKELtoto
cur.execute("select a.id,a.matchid, a.timestamp,a.odds,a.book,a.market from processed_historical a,winkel_toto_matches b where book='winkel_toto' and matchid=winkel_toto_event_id and b.timestamp<unix_timestamp();")
rows = cur.fetchall()

print("found WINKELTOTO processed:",len(rows))

for row in rows:
    try:
        x= cur.execute("insert into processed_historical_archive (matchid,timestamp,odds,book,market) values(%s,%s,%s,%s,%s)",tuple(row[1:]))
    except:
        pass

for row in rows:
    x= cur.execute("delete from processed_historical where id=%s",(row[0]))

conn.commit()


#Betalpha
cur.execute("select a.id,a.matchid, a.timestamp,a.odds,a.book,a.market from processed_historical a,betalpha_matches b where book='betalpha' and matchid=betalpha_event_id and b.timestamp<unix_timestamp();")
rows = cur.fetchall()

print("found betalpha processed:",len(rows))

for row in rows:
    try:
        x= cur.execute("insert into processed_historical_archive (matchid,timestamp,odds,book,market) values(%s,%s,%s,%s,%s)",tuple(row[1:]))
    except:
        pass

for row in rows:
    x= cur.execute("delete from processed_historical where id=%s",(row[0]))

conn.commit()

#Bingoal
cur.execute("select a.id,a.matchid, a.timestamp,a.odds,a.book,a.market from processed_historical a,bingoal_matches b where book='bingoal' and matchid=bingoal_event_id and b.timestamp<unix_timestamp();")
rows = cur.fetchall()

print("found bingoal processed:",len(rows))

for row in rows:
    try:
        x= cur.execute("insert into processed_historical_archive (matchid,timestamp,odds,book,market) values(%s,%s,%s,%s,%s)",tuple(row[1:]))
    except:
        pass

for row in rows:
    x= cur.execute("delete from processed_historical where id=%s",(row[0]))

conn.commit()

#Yess365
cur.execute("select a.id,a.matchid, a.timestamp,a.odds,a.book,a.market from processed_historical a,yess365_matches b where book='yess365' and matchid=yess365_event_id and b.timestamp<unix_timestamp();")
rows = cur.fetchall()

print("found yess365 processed:",len(rows))

for row in rows:
    try:
        x= cur.execute("insert into processed_historical_archive (matchid,timestamp,odds,book,market) values(%s,%s,%s,%s,%s)",tuple(row[1:]))
    except:
        pass

for row in rows:
    x= cur.execute("delete from processed_historical where id=%s",(row[0]))

conn.commit()

#Bet3000
cur.execute("select a.id,a.matchid, a.timestamp,a.odds,a.book,a.market from processed_historical a,bet3000_matches b where book='bet3000' and matchid=bet3000_event_id and b.timestamp<unix_timestamp();")
rows = cur.fetchall()

print("found bet3000 processed:",len(rows))

for row in rows:
    try:
        x= cur.execute("insert into processed_historical_archive (matchid,timestamp,odds,book,market) values(%s,%s,%s,%s,%s)",tuple(row[1:]))
    except:
        pass

for row in rows:
    x= cur.execute("delete from processed_historical where id=%s",(row[0]))

conn.commit()


############################################

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

#Bingoal
cur.execute("select a.id, a.timestamp,a.match_key,a.matchid,a.book,a.odds from odds_history a,bingoal_matches b where book='bingoal' and matchid=bingoal_event_id and b.timestamp<unix_timestamp();")
rows = cur.fetchall()

print("found BINGOAL:",len(rows))

for row in rows:
    try:
        x= cur.execute("insert into odds_history_archive (timestamp,match_key,matchid,book,odds) values(%s,%s,%s,%s,%s)",tuple(row[1:]))
    except:
        pass
for row in rows:
    x= cur.execute("delete from odds_history where id=%s",(row[0]))

conn.commit()

#Bet3000
cur.execute("select a.id, a.timestamp,a.match_key,a.matchid,a.book,a.odds from odds_history a,bet3000_matches b where book='bet3000' and matchid=bet3000_event_id and b.timestamp<unix_timestamp();")
rows = cur.fetchall()

print("found bet3000:",len(rows))

for row in rows:
    try:
        x= cur.execute("insert into odds_history_archive (timestamp,match_key,matchid,book,odds) values(%s,%s,%s,%s,%s)",tuple(row[1:]))
    except:
        pass
for row in rows:
    x= cur.execute("delete from odds_history where id=%s",(row[0]))

conn.commit()

#betalpha
cur.execute("select a.id, a.timestamp,a.match_key,a.matchid,a.book,a.odds from odds_history a,betalpha_matches b where book='betalpha' and matchid=betalpha_event_id and b.timestamp<unix_timestamp();")
rows = cur.fetchall()

print("found betalpha:",len(rows))

for row in rows:
    try:
        x= cur.execute("insert into odds_history_archive (timestamp,match_key,matchid,book,odds) values(%s,%s,%s,%s,%s)",tuple(row[1:]))
    except:
        pass
for row in rows:
    x= cur.execute("delete from odds_history where id=%s",(row[0]))

conn.commit()

#yess365
cur.execute("select a.id, a.timestamp,a.match_key,a.matchid,a.book,a.odds from odds_history a,yess365_matches b where book='yess365' and matchid=yess365_event_id and b.timestamp<unix_timestamp();")
rows = cur.fetchall()

print("found yess365:",len(rows))

for row in rows:
    try:
        x= cur.execute("insert into odds_history_archive (timestamp,match_key,matchid,book,odds) values(%s,%s,%s,%s,%s)",tuple(row[1:]))
    except:
        pass
for row in rows:
    x= cur.execute("delete from odds_history where id=%s",(row[0]))

conn.commit()

conn.close()
