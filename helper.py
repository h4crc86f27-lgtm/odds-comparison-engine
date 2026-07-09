import pymysql

## change db stuff here
bookname="live90bet"
after="yess365"

conn = pymysql.connect(host='localhost',user='local',passwd='oeijifjwejfio',db="arb_db_beta")
cur = conn.cursor()

#create new matches table

cur.execute("create table " + bookname + "_matches like yess_matches")
cur.execute("alter table "+ bookname + "_matches change column bet3000_event_id " + bookname  + "_event_id int")
cur.execute("alter table "+ bookname + "_matches change column team_1_bet3000 team_1_" + bookname  + " text")
cur.execute("alter table "+ bookname + "_matches change column team_2_bet3000 team_2_" + bookname  + " text")
cur.execute("alter table "+ bookname + "_matches change column bet3000_data " + bookname + "_data" + " text")
cur.execute("alter table "+ bookname + "_matches change column t1_bet3000_fuzzy t1_" + bookname + "_fuzzy" + " text")
cur.execute("alter table "+ bookname + "_matches change column t2_bet3000_fuzzy t2_" + bookname + "_fuzzy" + " text")

cur.execute("alter table comps add column " + bookname + "_id text after " + after + "_id")
cur.execute("alter table comps add column " + bookname + "_name text after " + after + "_id")


cur.execute("alter table user_views add column " + bookname + " int")
cur.execute("alter table user_views add column " +bookname + "alerts"+ " int")
cur.execute("alter table user_views add column " +bookname + "alertsht"+ " int")
cur.execute("alter table user_views add column " +bookname + "alertsdc"+ " int")
cur.execute("alter table user_views add column " +bookname + "alerts1x2"+ " int")
cur.execute("alter table user_views add column " +bookname + "alertsuo25"+ " int")
cur.execute("alter table user_views add column " +bookname + "alertsuo35"+ " int")
cur.execute("alter table user_views add column " +bookname + "alertsdnb"+ " int")

cur.execute("update user_views set " + bookname + "=0;")
cur.execute("update user_views set " + bookname + "alerts=0;")
cur.execute("update user_views set " + bookname + "alertsht=0;")
cur.execute("update user_views set " + bookname + "alertsdc=0;")
cur.execute("update user_views set " + bookname + "alerts1x2=0;")
cur.execute("update user_views set " + bookname + "alertsuo25=0;")
cur.execute("update user_views set " + bookname + "alertsuo35=0;")
cur.execute("update user_views set " + bookname + "alertsdnb=0;")

conn.commit()

conn.close()

## need to chg match_query bb/bl .php

## change user_dashboard.php

## change telegram

## change arb_monitor

## add book module

## prefill raw comps table..manually


#
