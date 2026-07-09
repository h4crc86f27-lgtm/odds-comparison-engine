import pymysql
import betfairlightweight
from betfairlightweight import filters

my_username ="morpheusalexander123@gmail.com"# cred['username']
my_password = "Ezmerelda_32*"#cred['password']
my_app_key ="o4DESE5fzU4r1fkv"# cred['app_key']

trading = betfairlightweight.APIClient(username=my_username,
                                       password=my_password,
                                       app_key=my_app_key,
                                       certs="/home/arb_bot/certs")

trading.login()

conn = pymysql.connect(host='127.0.0.1',user='local',passwd='oeijifjwejfio',db='arb_db_beta')
cur = conn.cursor()

cur.execute("select betfair_id from comps where ignore_comp=0")
rows = cur.fetchall()
comp_list=[]
for row in rows:
    comp_list.append(str(row[0]))


def pull_events(compid):
	filter={"competitionIds":[str(compid)]}

	events = trading.betting.list_events(
    		filter=filter
	)
	return events

cur.execute("delete from betfair_lookup")


for cl in comp_list:
    events = pull_events(cl)
    print(cl,len(events))
    for event in events:
        x=cur.execute("insert into betfair_lookup (event_id,comp_id) values(%s,%s)",(event.event.id,cl))
trading.logout()



def old_seen_matches():
    lookup={}

    cur.execute("select betfair_event_id,league from unibet_matches")
    rows= cur.fetchall()
    for row in rows:
        lookup[row[0]] = row[1]
        
    cur.execute("select betfair_event_id,league from contra_matches")
    rows= cur.fetchall()
    for row in rows:
        lookup[row[0]] = row[1]
        
    cur.execute("select betfair_event_id,league from toto_matches")
    rows= cur.fetchall()
    for row in rows:
        lookup[row[0]] = row[1]
        
    cur.execute("select betfair_event_id,league from winkel_toto_matches")
    rows= cur.fetchall()
    for row in rows:
        lookup[row[0]] = row[1]
        
    cur.execute("select betfair_event_id,league from qrbet_matches")
    rows= cur.fetchall()
    for row in rows:
        lookup[row[0]] = row[1]
        
    cur.execute("select betfair_event_id,league from bingoal_matches")
    rows= cur.fetchall()
    for row in rows:
        lookup[row[0]] = row[1]

    cur.execute("select betfair_id,betfair_name from comps")
    rows = cur.fetchall()

    comp_dict={}

    for row in rows:
        comp_dict[row[1]]=row[0]

    inserts={}
    for l in lookup:
        eid=l
        cid=comp_dict[lookup[l]]
        inserts[eid]=cid

    print(len(inserts))

    cur.execute("delete from betfair_lookup")

    for i in inserts:
        x=cur.execute("insert into betfair_lookup (event_id,comp_id) values(%s,%s)",(i,inserts[i]))

conn.commit()
conn.close()
