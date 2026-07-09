import pymysql
conn = pymysql.connect(host='127.0.0.1',user='local',passwd='oeijifjwejfio',db="arb_db_beta")
cur = conn.cursor()
cur.execute("delete from unibet_matches where timestamp < unix_timestamp()")
cur.execute("delete from contra_matches where timestamp < unix_timestamp()")
cur.execute("delete from toto_matches where timestamp < unix_timestamp()")
cur.execute("delete from winkel_toto_matches where timestamp < unix_timestamp()")
cur.execute("delete from qrbet_matches where timestamp < unix_timestamp()")
cur.execute("delete from bingoal_matches where timestamp < unix_timestamp()")
cur.execute("delete from yess365_matches where timestamp < unix_timestamp()")
cur.execute("delete from m8bets_matches where timestamp < unix_timestamp()")
cur.execute("delete from bet3000_matches where timestamp < unix_timestamp()")
cur.execute("delete from betalpha_matches where timestamp < unix_timestamp()")

conn.commit()
conn.close()

