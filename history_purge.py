#"insert into odds_history_archive select a.id, a.timestamp,a.match_key,a.matchid,a.book,a.odds from odds_history a,contra_matches b where book='contra' and matchid=contra_event_id and b.timestamp<unix_timestamp();"select a.id, a.timestamp,a.match_key,a.matchid,a.book,a.odds from odds_history a,contra_matches b where book='contra' and matchid=contra_event_id and b.timestamp<unix_timestamp();"
import pymysql
conn = pymysql.connect(host='127.0.0.1',user='local',passwd='oeijifjwejfio',db='arb_db_beta')
cur = conn.cursor()


#BETFAIR..
#use the bf_ids_expired view to purge these.. so pull the list of expired bfids.. and then just
##need a better method, takes ages with a million records,, but lets do the intial, and then it should speed up anyway.
cur.execute("select * from bf_ids")
rows = cur.fetchall()
ids = []
for row in rows:
    ids.append(row[0])

#now remove any from odds_history that aren't in ids

print("bfids:",len(ids))

dels=[]

print("deleting oddshistorys")
cur.execute("select * from odds_history")
rows = cur.fetchall()
for row in rows:
    if int(row[3]) not in ids:
        #x=cur.execute("delete from odds_history where id=%s",(row[0]))
        dels.append(row[0])

print("there are:",len(dels),"odds history to delete")

batch_size = 50000

# Split the id numbers into batches
batches = [dels[i:i+batch_size] for i in range(0, len(dels), batch_size)]
for batch in batches:
    # Convert the list of id numbers to a comma-separated string
    id_string = ','.join([str(id) for id in batch])

    # Construct the DELETE query
    query = f"DELETE FROM odds_history WHERE id IN ({id_string})"

    # Execute the query
    cur.execute(query)
    print("deleted batch:",batches.index(batch))

print("deleted",len(dels),"from history")
conn.commit()


#now remove any from processed_historical that aren't in ids


dels=[]
print("deleting processed")
cur.execute("select * from processed_historical")
rows = cur.fetchall()
for row in rows:
    if int(row[1]) not in ids:
        #x=cur.execute("delete from processed_historical where id=%s",(row[0]))
        dels.append(row[0])
print("------")
print("there are:",len(dels),"odds processed to delete")
batches = [dels[i:i+batch_size] for i in range(0, len(dels), batch_size)]
for batch in batches:
    # Convert the list of id numbers to a comma-separated string
    id_string = ','.join([str(id) for id in batch])

    # Construct the DELETE query
    query = f"DELETE FROM processed_historical WHERE id IN ({id_string})"

    # Execute the query
    cur.execute(query)
    print("deleted batch:",batches.index(batch))

print("deleted",len(dels),"from processed")
conn.commit()
conn.close()

