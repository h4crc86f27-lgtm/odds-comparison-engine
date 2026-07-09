import pymysql
conn = pymysql.connect(user='local',host='localhost',passwd='oeijifjwejfio',db='arb_db')
cur=conn.cursor()
conn.close()

