import pymysql
conn = pymysql.connect(user='local',host='127.0.0.1',passwd='oeijifjwejfio',db='arb_db_beta')
cur=conn.cursor()
cur.execute("select id,timestamp -unix_timestamp() from users")
rows = cur.fetchall()
for row in rows:
	try:
		if row[1]<-600:
			x=cur.execute("update users set logged_in=0 where id=%s",(row[0]))
			print("logging out:",row)
	except:
		pass
conn.commit()
conn.close()

