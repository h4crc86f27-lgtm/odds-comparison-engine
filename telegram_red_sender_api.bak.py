from telethon import TelegramClient, sync, events
from telethon.errors import SessionPasswordNeededError
from telethon.sync import TelegramClient
from telethon.tl.types import InputPeerUser, InputPeerChannel
#red checker
import pymysql
import json
import telegram_send
import time
import datetime


user_dict={}

# (1) Use your own values here
api_id = 18636796
api_hash = 'e3aa3eee61c9a84eb8af071d48a3802f'

phone = '61448407770'
username = '@Arber_bot'

# (2) Create the client and connect
print("/home/arb_bot/" + username + ".session")

client = TelegramClient("/home/arb_bot/" + username + ".session", api_id, api_hash)
client.connect()

# Ensure you're authorized
if not client.is_user_authorized():
    client.send_code_request(phone)
    try:
        client.sign_in(phone, input('Enter the code: '))
    except SessionPasswordNeededError:
        client.sign_in(password=input('Password: '))

me = client.get_me()
print(me)

# send messages..
"""

entity = client.get_entity('@Arberbot')
receiver = InputPeerUser(entity.id,entity.access_hash)
client.send_message(receiver, "testing testing, don't block me telegram", parse_mode='html')

"""

def send_alert_checker(send_str,insert_str,matchup,b1,bx,b2,bf1,bfx,bf2,league,market,flag1,flag2,flag3):


    global user_dict
    #print("inchecker:",user_dict)
    #time.sleep(5)
    print("Attempting send..",send_str,insert_str)
    if flag1 and bf1==0:# or bf2==0:
        print("bailing due to betfair_odds:",bf1)
        return
    if flag2 and bfx==0:# or bf2==0:
        print("bailing due to betfair_odds:",bfx)
        return
    if flag3 and bf2==0:# or bf2==0:
        print("bailing due to betfair_odds:",bf2)
        return

    print("--------->")

    #here set any rows to expired matching current insert, but older than 1800s,,
    #i guess i need to get the previous odds first..??
    cur.execute("select odds from red_alerts where str=%s order by id desc",insert_str)
    rows = cur.fetchall()
    if len(rows)>0:
        prior_odds = rows[0][0]
        
    else:
        prior_odds=""
    cur.execute("update red_alerts set str = %s where str=%s and unix_timestamp()-send_timestamp>1800",(insert_str + "_exp_" + str(int(time.time())),insert_str))
    conn.commit()

    odds = {"book":{"1":b1,"x":bx,"2":b2},"betfair":{"1":bf1,"x":bfx,"2":bf2}}
    #need to check specific odds relating to which market and which side..
    #not just raw check of entire odds.. right?
    if json.dumps(odds)==prior_odds:
        print("odds same -- no send")
        print("current:",json.dumps(odds))
        print("prior:",prior_odds)
        print(send_str)
        nosend=True
    else:
        print("odds changed -- send")
        print("current:",json.dumps(odds))
        print("prior:",prior_odds)
        print(send_str)
        nosend=False
    cur.execute("insert into red_alerts (send_timestamp,str,league,matchup,odds) values(%s,%s,%s,%s,%s)",(int(time.time()),insert_str,league,matchup,json.dumps(odds)))
    whichbook=""
    if send_str.find("**TOTO")>-1:
        whichbook="toto" + market
    elif send_str.find("UNIBET")>-1:
        whichbook="unibet" + market
    elif send_str.find("CONTRA")>-1:
        whichbook="contra" + market
    elif send_str.find("QRBET")>-1:
        whichbook="qrbet" + market
    elif send_str.find("WINKEL_TOTO")>-1:
        whichbook="winkel_toto" + market
    #here change to loop

    for ud in user_dict:
        try:
            if user_dict[ud][whichbook]==1 and not nosend:# and bf1>1 and bf2>1:   
                try:
                    print("sent >> ",user_dict[ud]['tag']) 
            
                    client.send_message(user_dict[ud]['tag'],send_str[0:4096])#'@Heisenferd'
                except Exception as msg:
                    print("send err",ud,str(msg))
            else:
                print("user:",ud," not flagged for ",whichbook)
        except Exception as mg:
            print(str(msg),"outer ERR..prob with user_dict??:",ud,"..but tried")
    """
    if user_dict[13][whichbook]==1 and not nosend and bf1>1 and bf2>1:   
        print("sent heisen") 
        try:
            client.send_message('@Heisenferd',send_str[0:4096])
        except Exception as msg:
            print("err",str(msg))
    if  user_dict[14][whichbook]==1 and not nosend and bf1>1 and bf2>1: 
        print("sent dave") 
        try:
            client.send_message('@dave_goldie',send_str[0:4096])
        except Exception as msg:
            print("err",str(msg))

    if  user_dict[19][whichbook]==1 and not nosend and bf1>1 and bf2>1:
        print("sent donny")      
        try:
            client.send_message('@donny5078',send_str[0:4096])
        except Exception as msg:
            print("err",str(msg))

    if  user_dict[18][whichbook]==1 and not nosend and bf1>1 and bf2>1: 
        print("sent danny")     
        try:
            client.send_message('@danielcyprus2626',send_str[0:4096])
        except Exception as msg:
            print("err",str(msg))

    if  user_dict[16][whichbook]==1 and not nosend and bf1>1 and bf2>1:   
        print("sent cup")   
        try:
            client.send_message('@kwilten',send_str[0:4096])
        except Exception as msg:
            print("err",str(msg))
    """

    conn.commit()
    print("<--------")

def send_1x2(a,b,c,d,e,f,g,h,i,j,x,y,z,league):
    valid_odds=False
    send_str=a + b + " -VS- " + c + " :: " + str(d) + "-" + str(e) + "-" + str(f) + " <> "  + str(g) + "-" + str(h) + "-" + str(i)
    #here,, add exact string,, and then only resend if its not in the table already
    insert_str = str(j)+a+b+c + "_1x2"#+c+"_" + str(d) + "_" + str(e) + "_" + str(f) + "_" + str(g) + "_"+ str(h) + "_" + str(i)
    #print("insert >> ",insert_str)
    send_str = a + "\n" + b + " - " + c + ", " + str(datetime.datetime.fromtimestamp(int(j))+datetime.timedelta(hours=1))[0:10] + "(" +  league + ")" + "\nMarket: 1x2\n"
    if x and d>=1.5 and g>=1.5:
        send_str+="1 = " + str(d) + " versus " + str(g) + " (" + str(round(d/g*100-100,2)) + "%)\n"
        valid_odds=True
    if y and e>=1.5 and h>=1.5:
        send_str+="x = " + str(e) + " versus " + str(h) + " (" + str(round(e/h*100-100,2)) + "%)\n"
        valid_odds=True
    if z and f>=1.5 and i>=1.5:
        send_str+="2 = " + str(f) + " versus " + str(i) + " (" + str(round(f/i*100-100,2)) + "%)\n"
        valid_odds=True
    send_str+="**/END"
    #print("send >> ",send_str)
    try:
        #here send off to check whether alert has been sent, or if its expired, and can be sent again..
        #perhaps,, you need to alter the prior alert key,, with some extra appendage,, perhaps timestamp that it
        #became obsolete
        if valid_odds:
            send_alert_checker(send_str,insert_str,b + " -VS- " + c,d,e,f,g,h,i,league,"_1x2",x,y,z)  
        else:
            pass#print("skipping due to inadequate odds")  
    except Exception as msg:
        print("ext err..1x2",send_str,insert_str,b + " -VS- " + c,d,e,f,g,h,i,league,"_1x2",str(msg))

def send_uo25(a,b,c,d,e,f,g,h,i,j,x,y,z,league):
    valid_odds=False
    send_str=a + b + " -VS- " + c + " :: " + str(d) + "-" + str(e) + "-" + str(f) + " <> "  + str(g) + "-" + str(h) + "-" + str(i)
    #here,, add exact string,, and then only resend if its not in the table already
    insert_str = str(j)+a+b+c + "_uo25"#+c+"_" + str(d) + "_" + str(e) + "_" + str(f) + "_" + str(g) + "_"+ str(h) + "_" + str(i)
    #print("insert >> ",insert_str)
    send_str = a + "\n" + b + " - " + c + ", " + str(datetime.datetime.fromtimestamp(int(j))+datetime.timedelta(hours=1))[0:10] + "(" +  league + ")" + "\nMarket: UO2.5\n"
    if x and d>=1.5 and g>=1.5:
        send_str+="Under = " + str(d) + " versus " + str(g) + " (" + str(round(d/g*100-100,2)) + "%)\n"
        valid_odds=True
    if y and e>=1.5 and h>=1.5:
        send_str+="x = " + str(e) + " versus " + str(h) + " (" + str(round(e/h*100-100,2)) + "%)\n"
        valid_odds=True
    if z and f>=1.5 and i>=1.5:
        send_str+="Over = " + str(f) + " versus " + str(i) + " (" + str(round(f/i*100-100,2)) + "%)\n"
        valid_odds=True
    send_str+="**/END"
    #print("send >> ",send_str)
    try:
        #here send off to check whether alert has been sent, or if its expired, and can be sent again..
        #perhaps,, you need to alter the prior alert key,, with some extra appendage,, perhaps timestamp that it
        #became obsolete
        if valid_odds:
            send_alert_checker(send_str,insert_str,b + " -VS- " + c,d,e,f,g,h,i,league,"_uo25",x,y,z)    
        else:
            pass#print("skipping due to inadequate odds") 
    except Exception as msg:
        print("ext err..uo25",send_str,insert_str,b + " -VS- " + c,d,e,f,g,h,i,league,"_uo25",str(msg))

def send_uo35(a,b,c,d,e,f,g,h,i,j,x,y,z,league):
    valid_odds=False
    send_str=a + b + " -VS- " + c + " :: " + str(d) + "-" + str(e) + "-" + str(f) + " <> "  + str(g) + "-" + str(h) + "-" + str(i)
    #here,, add exact string,, and then only resend if its not in the table already
    insert_str = str(j)+a+b+c + "_uo35"#+c+"_" + str(d) + "_" + str(e) + "_" + str(f) + "_" + str(g) + "_"+ str(h) + "_" + str(i)
    #print("insert >> ",insert_str)
    send_str = a + "\n" + b + " - " + c + ", " + str(datetime.datetime.fromtimestamp(int(j))+datetime.timedelta(hours=1))[0:10] + "(" +  league + ")" + "\nMarket: UO3.5\n"
    if x and d>=1.5 and g>=1.5:
        send_str+="Under = " + str(d) + " versus " + str(g) + " (" + str(round(d/g*100-100,2)) + "%)\n"
        valid_odds=True
    if y and e>=1.5 and h>=1.5:
        send_str+="x = " + str(e) + " versus " + str(h) + " (" + str(round(e/h*100-100,2)) + "%)\n"
        valid_odds=True
    if z and f>=1.5 and i>=1.5:
        send_str+="Over = " + str(f) + " versus " + str(i) + " (" + str(round(f/i*100-100,2)) + "%)\n"
        valid_odds=True
    send_str+="**/END"
    #print("send >> ",send_str)
    try:
        #here send off to check whether alert has been sent, or if its expired, and can be sent again..
        #perhaps,, you need to alter the prior alert key,, with some extra appendage,, perhaps timestamp that it
        #became obsolete
        if valid_odds:
            send_alert_checker(send_str,insert_str,b + " -VS- " + c,d,e,f,g,h,i,league,"_uo35",x,y,z)
        else:
            pass#print("skipping due to inadequate odds")     
    except Exception as msg:
        print("ext err..uo35",send_str,insert_str,b + " -VS- " + c,d,e,f,g,h,i,league,"_uo35",str(msg))

def send_dnb(a,b,c,d,e,f,g,h,i,j,x,y,z,league):
    valid_odds=False
    send_str=a + b + " -VS- " + c + " :: " + str(d) + "-" + str(e) + "-" + str(f) + " <> "  + str(g) + "-" + str(h) + "-" + str(i)
    #here,, add exact string,, and then only resend if its not in the table already
    insert_str = str(j)+a+b+c + "_dnb"#+c+"_" + str(d) + "_" + str(e) + "_" + str(f) + "_" + str(g) + "_"+ str(h) + "_" + str(i)
    #print("insert >> ",insert_str)
    send_str = a + "\n" + b + " - " + c + ", " + str(datetime.datetime.fromtimestamp(int(j))+datetime.timedelta(hours=1))[0:10] + "(" +  league + ")" + "\nMarket: DNB\n"
    if x and d>=1.5 and g>=1.5:
        send_str+="1 = " + str(d) + " versus " + str(g) + " (" + str(round(d/g*100-100,2))+ "%)\n"
        valid_odds=True
    if y and e>=1.5 and h>=1.5:
        send_str+="x = " + str(e) + " versus " + str(h) + " (" + str(round(e/h*100-100,2)) + "%)\n"
        valid_odds=True
    if z and f>=1.5 and i>=1.5:
        send_str+="2 = " + str(f) + " versus " + str(i) + " (" + str(round(f/i*100-100,2)) + "%)\n"
        valid_odds=True
    send_str+="**/END"
    #print("send >> ",send_str)
    try:
        #here send off to check whether alert has been sent, or if its expired, and can be sent again..
        #perhaps,, you need to alter the prior alert key,, with some extra appendage,, perhaps timestamp that it
        #became obsolete
        if valid_odds:
            send_alert_checker(send_str,insert_str,b + " -VS- " + c,d,e,f,g,h,i,league,"_dnb",x,y,z)
        else:
            pass#print("skipping due to inadequate odds")     
    except Exception as msg:
        print("ext err DNB..",send_str,insert_str,b + " -VS- " + c,d,e,f,g,h,i,league,"_dnb",str(msg))


def send_ht(a,b,c,d,e,f,g,h,i,j,x,y,z,league):
    valid_odds=False
    
    send_str=a + b + " -VS- " + c + " :: " + str(d) + "-" + str(e) + "-" + str(f) + " <> "  + str(g) + "-" + str(h) + "-" + str(i)
    #here,, add exact string,, and then only resend if its not in the table already
    insert_str = str(j)+a+b+c + "_ht"#+c+"_" + str(d) + "_" + str(e) + "_" + str(f) + "_" + str(g) + "_"+ str(h) + "_" + str(i)
    #print("insert >> ",insert_str)
    send_str = a + "\n" + b + " - " + c + ", " + str(datetime.datetime.fromtimestamp(int(j))+datetime.timedelta(hours=1))[0:10] + "(" +  league + ")" + "\nMarket: HT\n"
    if x and d>=1.5 and g>=1.5:
        send_str+="1 = " + str(d) + " versus " + str(g) + " (" + str(round(d/g*100-100,2))+ "%)\n"
        valid_odds=True
    if y and e>=1.5 and h>=1.5:
        send_str+="x = " + str(e) + " versus " + str(h) + " (" + str(round(e/h*100-100,2)) + "%)\n"
        valid_odds=True
    if z and f>=1.5 and i>=1.5:
        send_str+="2 = " + str(f) + " versus " + str(i) + " (" + str(round(f/i*100-100,2)) + "%)\n"
        valid_odds=True
    send_str+="**/END"
    #print("send >> ",send_str)
    try:
        #here send off to check whether alert has been sent, or if its expired, and can be sent again..
        #perhaps,, you need to alter the prior alert key,, with some extra appendage,, perhaps timestamp that it
        #became obsolete
        if valid_odds:
            send_alert_checker(send_str,insert_str,b + " -VS- " + c,d,e,f,g,h,i,league,"_ht",x,y,z)
        else:
            pass#print("skipping due to inadequate odds")     
    except Exception as msg:
        print("ext err HT..",send_str,insert_str,b + " -VS- " + c,d,e,f,g,h,i,league,"_ht",str(msg))

def send_dc(a,b,c,d,e,f,g,h,i,j,x,y,z,league):
    valid_odds=False
    
    send_str=a + b + " -VS- " + c + " :: " + str(d) + "-" + str(e) + "-" + str(f) + " <> "  + str(g) + "-" + str(h) + "-" + str(i)
    #here,, add exact string,, and then only resend if its not in the table already
    insert_str = str(j)+a+b+c + "_dc"#+c+"_" + str(d) + "_" + str(e) + "_" + str(f) + "_" + str(g) + "_"+ str(h) + "_" + str(i)
    #print("insert >> ",insert_str)
    send_str = a + "\n" + b + " - " + c + ", " + str(datetime.datetime.fromtimestamp(int(j))+datetime.timedelta(hours=1))[0:10] + "(" +  league + ")" + "\nMarket: DC\n"
    if x and d>=1.0 and g>=1.0:
        send_str+="1X = " + str(d) + " versus " + str(g) + " (" + str(round(d/g*100-100,2))+ "%)\n"
        valid_odds=True
    if y and e>=1.0 and h>=1.0:
        send_str+="X2 = " + str(e) + " versus " + str(h) + " (" + str(round(e/h*100-100,2)) + "%)\n"
        valid_odds=True
    if z and f>=1.0 and i>=1.0:
        send_str+="12 = " + str(f) + " versus " + str(i) + " (" + str(round(f/i*100-100,2)) + "%)\n"
        valid_odds=True
    send_str+="**/END"
    #print("send >> ",send_str)
    try:
        #here send off to check whether alert has been sent, or if its expired, and can be sent again..
        #perhaps,, you need to alter the prior alert key,, with some extra appendage,, perhaps timestamp that it
        #became obsolete
        if valid_odds:
            send_alert_checker(send_str,insert_str,b + " -VS- " + c,d,e,f,g,h,i,league,"_dc",x,y,z)
        else:
            pass#print("skipping due to inadequate odds")     
    except Exception as msg:
        print("ext err DC..",send_str,insert_str,b + " -VS- " + c,d,e,f,g,h,i,league,"_dc",str(msg))

def check_toto(odds_data):
        #print("Checking:",odds_data)
#here, run thru the 1x2,, then each of the other markets,, one by one..
        if odds_data['toto_1_odds']>odds_data['bf_1_odds']['lay_price'] or odds_data['toto_x_odds']>odds_data['bf_x_odds']['lay_price'] or odds_data['toto_2_odds']>odds_data['bf_2_odds']['lay_price']:
           if odds_data['toto_1_odds']>odds_data['bf_1_odds']['lay_price'] and odds_data['bf_1_odds']['lay_price']>0:
               #odds 1 of interest
               odds_1_flagged=True
           else:
               odds_1_flagged=False

           if odds_data['toto_x_odds']>odds_data['bf_x_odds']['lay_price']:
               #odds 1 of interest
               odds_x_flagged=True
           else:
               odds_x_flagged=False

           if odds_data['toto_2_odds']>odds_data['bf_2_odds']['lay_price'] and odds_data['bf_2_odds']['lay_price']>0:
               #odds 2 of interest
               odds_2_flagged=True
           else:
               odds_2_flagged=False

           send_1x2("**TOTO**",row[4],row[5],odds_data['toto_1_odds'],odds_data['toto_x_odds'],odds_data['toto_2_odds'],odds_data['bf_1_odds']['lay_price'],odds_data['bf_x_odds']['lay_price'],odds_data['bf_2_odds']['lay_price'],row[1],odds_1_flagged,odds_x_flagged,odds_2_flagged,row[-1])

        if odds_data['toto_under_2.5']>odds_data['bf_Under_2.5']['lay_price'] or odds_data['toto_over_2.5']>odds_data['bf_Over_2.5']['lay_price']:
           if odds_data['toto_under_2.5']>odds_data['bf_Under_2.5']['lay_price'] and odds_data['bf_Under_2.5']['lay_price']>0:
               #odds 1 of interest
               odds_1_flagged=True
           else:
               odds_1_flagged=False

           if 0:#odds_data['toto_x_odds']>odds_data['bf_x_odds']['lay_price']:
               #odds 1 of interest
               odds_x_flagged=True
           else:
               odds_x_flagged=False

           if odds_data['toto_over_2.5']>odds_data['bf_Over_2.5']['lay_price'] and odds_data['bf_Over_2.5']['lay_price']>0:
               #odds 2 of interest
               odds_2_flagged=True
           else:
               odds_2_flagged=False

           send_uo25("**TOTO**",row[4],row[5],odds_data['toto_under_2.5'],"",odds_data['toto_over_2.5'],odds_data['bf_Under_2.5']['lay_price'],"",odds_data['bf_Over_2.5']['lay_price'],row[1],odds_1_flagged,0,odds_2_flagged,row[-1])

        if odds_data['toto_under_3.5']>odds_data['bf_Under_3.5']['lay_price'] or odds_data['toto_over_3.5']>odds_data['bf_Over_3.5']['lay_price']:
           if odds_data['toto_under_3.5']>odds_data['bf_Under_3.5']['lay_price'] and odds_data['bf_Under_3.5']['lay_price']>0:
               #odds 1 of interest
               odds_1_flagged=True
           else:
               odds_1_flagged=False

           if 0:#odds_data['toto_x_odds']>odds_data['bf_x_odds']['lay_price']:
               #odds 1 of interest
               odds_x_flagged=True
           else:
               odds_x_flagged=False

           if odds_data['toto_over_3.5']>odds_data['bf_Over_3.5']['lay_price'] and odds_data['bf_Over_3.5']['lay_price']>0:
               #odds 2 of interest
               odds_2_flagged=True
           else:
               odds_2_flagged=False

           send_uo35("**TOTO**",row[4],row[5],odds_data['toto_under_3.5'],"",odds_data['toto_over_3.5'],odds_data['bf_Under_3.5']['lay_price'],"",odds_data['bf_Over_3.5']['lay_price'],row[1],odds_1_flagged,0,odds_2_flagged,row[-1])

        if odds_data['toto_dnb_home']>odds_data['bf_dnb_home']['lay_price'] or odds_data['toto_dnb_away']>odds_data['bf_dnb_away']['lay_price']:
           if odds_data['toto_dnb_home']>odds_data['bf_dnb_home']['lay_price'] and odds_data['bf_dnb_home']['lay_price']>0:
               #odds 1 of interest
               odds_1_flagged=True
           else:
               odds_1_flagged=False

           if 0:#odds_data['toto_x_odds']>odds_data['bf_x_odds']['lay_price']:
               #odds 1 of interest
               odds_x_flagged=True
           else:
               odds_x_flagged=False

           if odds_data['toto_dnb_away']>odds_data['bf_dnb_away']['lay_price'] and odds_data['bf_dnb_away']['lay_price']>0:
               #odds 2 of interest
               odds_2_flagged=True
           else:
               odds_2_flagged=False

           send_dnb("**TOTO**",row[4],row[5],odds_data['toto_dnb_home'],"",odds_data['toto_dnb_away'],odds_data['bf_dnb_home']['lay_price'],"",odds_data['bf_dnb_away']['lay_price'],row[1],odds_1_flagged,0,odds_2_flagged,row[-1])

        if odds_data['toto_1_ht']>odds_data['bf_1_ht']['lay_price'] or odds_data['toto_x_ht']>odds_data['bf_x_ht']['lay_price'] or odds_data['toto_2_ht']>odds_data['bf_2_ht']['lay_price']:
           if odds_data['toto_1_ht']>odds_data['bf_1_ht']['lay_price'] and odds_data['bf_1_ht']['lay_price']>0:
               #odds 1 of interest
               odds_1_flagged=True
           else:
               odds_1_flagged=False

           if odds_data['toto_x_ht']>odds_data['bf_x_ht']['lay_price']:
               #odds 1 of interest
               odds_x_flagged=True
           else:
               odds_x_flagged=False

           if odds_data['toto_2_ht']>odds_data['bf_2_ht']['lay_price'] and odds_data['bf_2_ht']['lay_price']>0:
               #odds 2 of interest
               odds_2_flagged=True
           else:
               odds_2_flagged=False

           send_ht("**TOTO**",row[4],row[5],odds_data['toto_1_ht'],odds_data['toto_x_ht'],odds_data['toto_2_ht'],odds_data['bf_1_ht']['lay_price'],odds_data['bf_x_ht']['lay_price'],odds_data['bf_2_ht']['lay_price'],row[1],odds_1_flagged,odds_x_flagged,odds_2_flagged,row[-1])

        if odds_data['toto_dc_1x']>odds_data['bf_dc_1x']['lay_price'] or odds_data['toto_dc_x2']>odds_data['bf_dc_x2']['lay_price'] or odds_data['toto_dc_12']>odds_data['bf_dc_12']['lay_price']:
           if odds_data['toto_dc_1x']>odds_data['bf_dc_1x']['lay_price'] and odds_data['bf_dc_1x']['lay_price']>0:
               #odds 1 of interest
               odds_1_flagged=True
           else:
               odds_1_flagged=False

           if odds_data['toto_dc_x2']>odds_data['bf_dc_x2']['lay_price']:
               #odds 1 of interest
               odds_x_flagged=True
           else:
               odds_x_flagged=False

           if odds_data['toto_dc_12']>odds_data['bf_dc_12']['lay_price'] and odds_data['bf_dc_12']['lay_price']>0:
               #odds 2 of interest
               odds_2_flagged=True
           else:
               odds_2_flagged=False

           send_dc("**TOTO**",row[4],row[5],odds_data['toto_dc_1x'],odds_data['toto_dc_x2'],odds_data['toto_dc_12'],odds_data['bf_dc_1x']['lay_price'],odds_data['bf_dc_x2']['lay_price'],odds_data['bf_dc_12']['lay_price'],row[1],odds_1_flagged,odds_x_flagged,odds_2_flagged,row[-1])


def check_contra(odds_data):
        #print("Checking:",odds_data)
#here, run thru the 1x2,, then each of the other markets,, one by one..
        if odds_data['contra_1_odds']>odds_data['bf_1_odds']['lay_price'] or odds_data['contra_x_odds']>odds_data['bf_x_odds']['lay_price'] or odds_data['contra_2_odds']>odds_data['bf_2_odds']['lay_price']:
           if odds_data['contra_1_odds']>odds_data['bf_1_odds']['lay_price'] and odds_data['bf_1_odds']['lay_price']>0:
               #odds 1 of interest
               odds_1_flagged=True
           else:
               odds_1_flagged=False

           if odds_data['contra_x_odds']>odds_data['bf_x_odds']['lay_price']:
               #odds 1 of interest
               odds_x_flagged=True
           else:
               odds_x_flagged=False

           if odds_data['contra_2_odds']>odds_data['bf_2_odds']['lay_price'] and odds_data['bf_2_odds']['lay_price']>0:
               #odds 2 of interest
               odds_2_flagged=True
           else:
               odds_2_flagged=False

           send_1x2("**CONTRA**",row[4],row[5],odds_data['contra_1_odds'],odds_data['contra_x_odds'],odds_data['contra_2_odds'],odds_data['bf_1_odds']['lay_price'],odds_data['bf_x_odds']['lay_price'],odds_data['bf_2_odds']['lay_price'],row[1],odds_1_flagged,odds_x_flagged,odds_2_flagged,row[-1])

        if odds_data['contra_under_2.5']>odds_data['bf_Under_2.5']['lay_price'] or odds_data['contra_over_2.5']>odds_data['bf_Over_2.5']['lay_price']:
           if odds_data['contra_under_2.5']>odds_data['bf_Under_2.5']['lay_price'] and odds_data['bf_Under_2.5']['lay_price']>0:
               #odds 1 of interest
               odds_1_flagged=True
           else:
               odds_1_flagged=False

           if 0:#odds_data['contra_x_odds']>odds_data['bf_x_odds']['lay_price']:
               #odds 1 of interest
               odds_x_flagged=True
           else:
               odds_x_flagged=False

           if odds_data['contra_over_2.5']>odds_data['bf_Over_2.5']['lay_price'] and odds_data['bf_Over_2.5']['lay_price']>0:
               #odds 2 of interest
               odds_2_flagged=True
           else:
               odds_2_flagged=False

           send_uo25("**CONTRA**",row[4],row[5],odds_data['contra_under_2.5'],"",odds_data['contra_over_2.5'],odds_data['bf_Under_2.5']['lay_price'],"",odds_data['bf_Over_2.5']['lay_price'],row[1],odds_1_flagged,0,odds_2_flagged,row[-1])

        if odds_data['contra_under_3.5']>odds_data['bf_Under_3.5']['lay_price'] or odds_data['contra_over_3.5']>odds_data['bf_Over_3.5']['lay_price']:
           if odds_data['contra_under_3.5']>odds_data['bf_Under_3.5']['lay_price'] and odds_data['bf_Under_3.5']['lay_price']>0:
               #odds 1 of interest
               odds_1_flagged=True
           else:
               odds_1_flagged=False

           if 0:#odds_data['contra_x_odds']>odds_data['bf_x_odds']['lay_price']:
               #odds 1 of interest
               odds_x_flagged=True
           else:
               odds_x_flagged=False

           if odds_data['contra_over_3.5']>odds_data['bf_Over_3.5']['lay_price'] and odds_data['bf_Over_3.5']['lay_price']>0:
               #odds 2 of interest
               odds_2_flagged=True
           else:
               odds_2_flagged=False

           send_uo35("**CONTRA**",row[4],row[5],odds_data['contra_under_3.5'],"",odds_data['contra_over_3.5'],odds_data['bf_Under_3.5']['lay_price'],"",odds_data['bf_Over_3.5']['lay_price'],row[1],odds_1_flagged,0,odds_2_flagged,row[-1])

        if odds_data['contra_dnb_home']>odds_data['bf_dnb_home']['lay_price'] or odds_data['contra_dnb_away']>odds_data['bf_dnb_away']['lay_price']:
           if odds_data['contra_dnb_home']>odds_data['bf_dnb_home']['lay_price'] and odds_data['bf_dnb_home']['lay_price']>0:
               #odds 1 of interest
               odds_1_flagged=True
           else:
               odds_1_flagged=False

           if 0:#odds_data['contra_x_odds']>odds_data['bf_x_odds']['lay_price']:
               #odds 1 of interest
               odds_x_flagged=True
           else:
               odds_x_flagged=False

           if odds_data['contra_dnb_away']>odds_data['bf_dnb_away']['lay_price'] and odds_data['bf_dnb_away']['lay_price']>0:
               #odds 2 of interest
               odds_2_flagged=True
           else:
               odds_2_flagged=False

           send_dnb("**CONTRA**",row[4],row[5],odds_data['contra_dnb_home'],"",odds_data['contra_dnb_away'],odds_data['bf_dnb_home']['lay_price'],"",odds_data['bf_dnb_away']['lay_price'],row[1],odds_1_flagged,0,odds_2_flagged,row[-1])
        
        if odds_data['contra_1_ht']>odds_data['bf_1_ht']['lay_price'] or odds_data['contra_x_ht']>odds_data['bf_x_ht']['lay_price'] or odds_data['contra_2_ht']>odds_data['bf_2_ht']['lay_price']:
           if odds_data['contra_1_ht']>odds_data['bf_1_ht']['lay_price'] and odds_data['bf_1_ht']['lay_price']>0:
               #odds 1 of interest
               odds_1_flagged=True
           else:
               odds_1_flagged=False

           if odds_data['contra_x_ht']>odds_data['bf_x_ht']['lay_price']:
               #odds 1 of interest
               odds_x_flagged=True
           else:
               odds_x_flagged=False

           if odds_data['contra_2_ht']>odds_data['bf_2_ht']['lay_price'] and odds_data['bf_2_ht']['lay_price']>0:
               #odds 2 of interest
               odds_2_flagged=True
           else:
               odds_2_flagged=False
           #if odds_data['bf_1_ht']['lay_price']>0:
           # print("FOUND A HT HOT!!!")
           # print("**CONTRA**",row[4],row[5],odds_data['contra_1_ht'],odds_data['contra_x_ht'],odds_data['contra_2_ht'],odds_data['bf_1_ht']['lay_price'],odds_data['bf_x_ht']['lay_price'],odds_data['bf_2_ht']['lay_price'],row[1],odds_1_flagged,odds_x_flagged,odds_2_flagged,row[-1])

           # time.sleep(1.5)


           send_ht("**CONTRA**",row[4],row[5],odds_data['contra_1_ht'],odds_data['contra_x_ht'],odds_data['contra_2_ht'],odds_data['bf_1_ht']['lay_price'],odds_data['bf_x_ht']['lay_price'],odds_data['bf_2_ht']['lay_price'],row[1],odds_1_flagged,odds_x_flagged,odds_2_flagged,row[-1])

        if odds_data['contra_dc_1x']>odds_data['bf_dc_1x']['lay_price'] or odds_data['contra_dc_x2']>odds_data['bf_dc_x2']['lay_price'] or odds_data['contra_dc_12']>odds_data['bf_dc_12']['lay_price']:
           if odds_data['contra_dc_1x']>odds_data['bf_dc_1x']['lay_price'] and odds_data['bf_dc_1x']['lay_price']>0:
               #odds 1 of interest
               odds_1_flagged=True
           else:
               odds_1_flagged=False

           if odds_data['contra_dc_x2']>odds_data['bf_dc_x2']['lay_price']:
               #odds 1 of interest
               odds_x_flagged=True
           else:
               odds_x_flagged=False

           if odds_data['contra_dc_12']>odds_data['bf_dc_12']['lay_price'] and odds_data['bf_dc_12']['lay_price']>0:
               #odds 2 of interest
               odds_2_flagged=True
           else:
               odds_2_flagged=False

           send_dc("**CONTRA**",row[4],row[5],odds_data['contra_dc_1x'],odds_data['contra_dc_x2'],odds_data['contra_dc_12'],odds_data['bf_dc_1x']['lay_price'],odds_data['bf_dc_x2']['lay_price'],odds_data['bf_dc_12']['lay_price'],row[1],odds_1_flagged,odds_x_flagged,odds_2_flagged,row[-1])


def check_unibet(odds_data):
        #print(row)
        #print("Checking:",odds_data)
#here, run thru the 1x2,, then each of the other markets,, one by one..
        if odds_data['unibet_1_odds']>odds_data['bf_1_odds']['lay_price'] or odds_data['unibet_x_odds']>odds_data['bf_x_odds']['lay_price'] or odds_data['unibet_2_odds']>odds_data['bf_2_odds']['lay_price']:
           if odds_data['unibet_1_odds']>odds_data['bf_1_odds']['lay_price'] and odds_data['bf_1_odds']['lay_price']>0:
               #odds 1 of interest
               odds_1_flagged=True
           else:
               odds_1_flagged=False

           if odds_data['unibet_x_odds']>odds_data['bf_x_odds']['lay_price']:
               #odds 1 of interest
               odds_x_flagged=True
           else:
               odds_x_flagged=False

           if odds_data['unibet_2_odds']>odds_data['bf_2_odds']['lay_price'] and odds_data['bf_2_odds']['lay_price']>0:
               #odds 2 of interest
               odds_2_flagged=True
           else:
               odds_2_flagged=False

           send_1x2("**UNIBET**",row[4],row[5],odds_data['unibet_1_odds'],odds_data['unibet_x_odds'],odds_data['unibet_2_odds'],odds_data['bf_1_odds']['lay_price'],odds_data['bf_x_odds']['lay_price'],odds_data['bf_2_odds']['lay_price'],row[1],odds_1_flagged,odds_x_flagged,odds_2_flagged,row[-2])

        if odds_data['unibet_under_2.5']>odds_data['bf_Under_2.5']['lay_price'] or odds_data['unibet_over_2.5']>odds_data['bf_Over_2.5']['lay_price']:
           if odds_data['unibet_under_2.5']>odds_data['bf_Under_2.5']['lay_price'] and odds_data['bf_Under_2.5']['lay_price']>0:
               #odds 1 of interest
               odds_1_flagged=True
           else:
               odds_1_flagged=False

           if 0:#odds_data['unibet_x_odds']>odds_data['bf_x_odds']['lay_price']:
               #odds 1 of interest
               odds_x_flagged=True
           else:
               odds_x_flagged=False

           if odds_data['unibet_over_2.5']>odds_data['bf_Over_2.5']['lay_price'] and odds_data['bf_Over_2.5']['lay_price']>0:
               #odds 2 of interest
               odds_2_flagged=True
           else:
               odds_2_flagged=False

           send_uo25("**UNIBET**",row[4],row[5],odds_data['unibet_under_2.5'],"",odds_data['unibet_over_2.5'],odds_data['bf_Under_2.5']['lay_price'],"",odds_data['bf_Over_2.5']['lay_price'],row[1],odds_1_flagged,0,odds_2_flagged,row[-2])

        if odds_data['unibet_under_3.5']>odds_data['bf_Under_3.5']['lay_price'] or odds_data['unibet_over_3.5']>odds_data['bf_Over_3.5']['lay_price']:
           if odds_data['unibet_under_3.5']>odds_data['bf_Under_3.5']['lay_price'] and odds_data['bf_Under_3.5']['lay_price']>0:
               #odds 1 of interest
               odds_1_flagged=True
           else:
               odds_1_flagged=False

           if 0:#odds_data['unibet_x_odds']>odds_data['bf_x_odds']['lay_price']:
               #odds 1 of interest
               odds_x_flagged=True
           else:
               odds_x_flagged=False

           if odds_data['unibet_over_3.5']>odds_data['bf_Over_3.5']['lay_price'] and odds_data['bf_Over_3.5']['lay_price']>0:
               #odds 2 of interest
               odds_2_flagged=True
           else:
               odds_2_flagged=False

           send_uo35("**UNIBET**",row[4],row[5],odds_data['unibet_under_3.5'],"",odds_data['unibet_over_3.5'],odds_data['bf_Under_3.5']['lay_price'],"",odds_data['bf_Over_3.5']['lay_price'],row[1],odds_1_flagged,0,odds_2_flagged,row[-2])

        if odds_data['unibet_dnb_home']>odds_data['bf_dnb_home']['lay_price'] or odds_data['unibet_dnb_away']>odds_data['bf_dnb_away']['lay_price']:
           if odds_data['unibet_dnb_home']>odds_data['bf_dnb_home']['lay_price'] and odds_data['bf_dnb_home']['lay_price']>0:
               #odds 1 of interest
               odds_1_flagged=True
           else:
               odds_1_flagged=False

           if 0:#odds_data['unibet_x_odds']>odds_data['bf_x_odds']['lay_price']:
               #odds 1 of interest
               odds_x_flagged=True
           else:
               odds_x_flagged=False

           if odds_data['unibet_dnb_away']>odds_data['bf_dnb_away']['lay_price'] and odds_data['bf_dnb_away']['lay_price']>0:
               #odds 2 of interest
               odds_2_flagged=True
           else:
               odds_2_flagged=False

           send_dnb("**UNIBET**",row[4],row[5],odds_data['unibet_dnb_home'],"",odds_data['unibet_dnb_away'],odds_data['bf_dnb_home']['lay_price'],"",odds_data['bf_dnb_away']['lay_price'],row[1],odds_1_flagged,0,odds_2_flagged,row[-2])

        if odds_data['unibet_1_ht']>odds_data['bf_1_ht']['lay_price'] or odds_data['unibet_x_ht']>odds_data['bf_x_ht']['lay_price'] or odds_data['unibet_2_ht']>odds_data['bf_2_ht']['lay_price']:
           if odds_data['unibet_1_ht']>odds_data['bf_1_ht']['lay_price'] and odds_data['bf_1_ht']['lay_price']>0:
               #odds 1 of interest
               odds_1_flagged=True
           else:
               odds_1_flagged=False

           if odds_data['unibet_x_ht']>odds_data['bf_x_ht']['lay_price']:
               #odds 1 of interest
               odds_x_flagged=True
           else:
               odds_x_flagged=False

           if odds_data['unibet_2_ht']>odds_data['bf_2_ht']['lay_price'] and odds_data['bf_2_ht']['lay_price']>0:
               #odds 2 of interest
               odds_2_flagged=True
           else:
               odds_2_flagged=False

           send_ht("**UNIBET**",row[4],row[5],odds_data['unibet_1_ht'],odds_data['unibet_x_ht'],odds_data['unibet_2_ht'],odds_data['bf_1_ht']['lay_price'],odds_data['bf_x_ht']['lay_price'],odds_data['bf_2_ht']['lay_price'],row[1],odds_1_flagged,odds_x_flagged,odds_2_flagged,row[-2])

        if odds_data['unibet_dc_1x']>odds_data['bf_dc_1x']['lay_price'] or odds_data['unibet_dc_x2']>odds_data['bf_dc_x2']['lay_price'] or odds_data['unibet_dc_12']>odds_data['bf_dc_12']['lay_price']:
           if odds_data['unibet_dc_1x']>odds_data['bf_dc_1x']['lay_price'] and odds_data['bf_dc_1x']['lay_price']>0:
               #odds 1 of interest
               odds_1_flagged=True
           else:
               odds_1_flagged=False

           if odds_data['unibet_dc_x2']>odds_data['bf_dc_x2']['lay_price']:
               #odds 1 of interest
               odds_x_flagged=True
           else:
               odds_x_flagged=False

           if odds_data['unibet_dc_12']>odds_data['bf_dc_12']['lay_price'] and odds_data['bf_dc_12']['lay_price']>0:
               #odds 2 of interest
               odds_2_flagged=True
           else:
               odds_2_flagged=False

           send_dc("**UNIBET**",row[4],row[5],odds_data['unibet_dc_1x'],odds_data['unibet_dc_x2'],odds_data['unibet_dc_12'],odds_data['bf_dc_1x']['lay_price'],odds_data['bf_dc_x2']['lay_price'],odds_data['bf_dc_12']['lay_price'],row[1],odds_1_flagged,odds_x_flagged,odds_2_flagged,row[-2])

def check_qrbet(odds_data):
        #print("Checking:",odds_data)
#here, run thru the 1x2,, then each of the other markets,, one by one..
        if odds_data['qrbet_1_odds']>odds_data['bf_1_odds']['lay_price'] or odds_data['qrbet_x_odds']>odds_data['bf_x_odds']['lay_price'] or odds_data['qrbet_2_odds']>odds_data['bf_2_odds']['lay_price']:
           if odds_data['qrbet_1_odds']>odds_data['bf_1_odds']['lay_price'] and odds_data['bf_1_odds']['lay_price']>0:
               #odds 1 of interest
               odds_1_flagged=True
           else:
               odds_1_flagged=False

           if odds_data['qrbet_x_odds']>odds_data['bf_x_odds']['lay_price']:
               #odds 1 of interest
               odds_x_flagged=True
           else:
               odds_x_flagged=False

           if odds_data['qrbet_2_odds']>odds_data['bf_2_odds']['lay_price'] and odds_data['bf_2_odds']['lay_price']>0:
               #odds 2 of interest
               odds_2_flagged=True
           else:
               odds_2_flagged=False

           send_1x2("**QRBET**",row[4],row[5],odds_data['qrbet_1_odds'],odds_data['qrbet_x_odds'],odds_data['qrbet_2_odds'],odds_data['bf_1_odds']['lay_price'],odds_data['bf_x_odds']['lay_price'],odds_data['bf_2_odds']['lay_price'],row[1],odds_1_flagged,odds_x_flagged,odds_2_flagged,row[-1])

        if odds_data['qrbet_under_2.5']>odds_data['bf_Under_2.5']['lay_price'] or odds_data['qrbet_over_2.5']>odds_data['bf_Over_2.5']['lay_price']:
           if odds_data['qrbet_under_2.5']>odds_data['bf_Under_2.5']['lay_price'] and odds_data['bf_Under_2.5']['lay_price']>0:
               #odds 1 of interest
               odds_1_flagged=True
           else:
               odds_1_flagged=False

           if 0:#odds_data['unibet_x_odds']>odds_data['bf_x_odds']['lay_price']:
               #odds 1 of interest
               odds_x_flagged=True
           else:
               odds_x_flagged=False

           if odds_data['qrbet_over_2.5']>odds_data['bf_Over_2.5']['lay_price'] and odds_data['bf_Over_2.5']['lay_price']>0:
               #odds 2 of interest
               odds_2_flagged=True
           else:
               odds_2_flagged=False

           send_uo25("**QRBET**",row[4],row[5],odds_data['qrbet_under_2.5'],"",odds_data['qrbet_over_2.5'],odds_data['bf_Under_2.5']['lay_price'],"",odds_data['bf_Over_2.5']['lay_price'],row[1],odds_1_flagged,0,odds_2_flagged,row[-1])

        if odds_data['qrbet_under_3.5']>odds_data['bf_Under_3.5']['lay_price'] or odds_data['qrbet_over_3.5']>odds_data['bf_Over_3.5']['lay_price']:
           if odds_data['qrbet_under_3.5']>odds_data['bf_Under_3.5']['lay_price'] and odds_data['bf_Under_3.5']['lay_price']>0:
               #odds 1 of interest
               odds_1_flagged=True
           else:
               odds_1_flagged=False

           if 0:#odds_data['unibet_x_odds']>odds_data['bf_x_odds']['lay_price']:
               #odds 1 of interest
               odds_x_flagged=True
           else:
               odds_x_flagged=False

           if odds_data['qrbet_over_3.5']>odds_data['bf_Over_3.5']['lay_price'] and odds_data['bf_Over_3.5']['lay_price']>0:
               #odds 2 of interest
               odds_2_flagged=True
           else:
               odds_2_flagged=False

           send_uo35("**QRBET**",row[4],row[5],odds_data['qrbet_under_3.5'],"",odds_data['qrbet_over_3.5'],odds_data['bf_Under_3.5']['lay_price'],"",odds_data['bf_Over_3.5']['lay_price'],row[1],odds_1_flagged,0,odds_2_flagged,row[-1])

        if odds_data['qrbet_dnb_home']>odds_data['bf_dnb_home']['lay_price'] or odds_data['qrbet_dnb_away']>odds_data['bf_dnb_away']['lay_price']:
           if odds_data['qrbet_dnb_home']>odds_data['bf_dnb_home']['lay_price'] and odds_data['bf_dnb_home']['lay_price']>0:
               #odds 1 of interest
               odds_1_flagged=True
           else:
               odds_1_flagged=False

           if 0:#odds_data['unibet_x_odds']>odds_data['bf_x_odds']['lay_price']:
               #odds 1 of interest
               odds_x_flagged=True
           else:
               odds_x_flagged=False

           if odds_data['qrbet_dnb_away']>odds_data['bf_dnb_away']['lay_price'] and odds_data['bf_dnb_away']['lay_price']>0:
               #odds 2 of interest
               odds_2_flagged=True
           else:
               odds_2_flagged=False

           send_dnb("**QRBET**",row[4],row[5],odds_data['qrbet_dnb_home'],"",odds_data['qrbet_dnb_away'],odds_data['bf_dnb_home']['lay_price'],"",odds_data['bf_dnb_away']['lay_price'],row[1],odds_1_flagged,0,odds_2_flagged,row[-1])

        if odds_data['qrbet_1_ht']>odds_data['bf_1_ht']['lay_price'] or odds_data['qrbet_x_ht']>odds_data['bf_x_ht']['lay_price'] or odds_data['qrbet_2_ht']>odds_data['bf_2_ht']['lay_price']:
           if odds_data['qrbet_1_ht']>odds_data['bf_1_ht']['lay_price'] and odds_data['bf_1_ht']['lay_price']>0:
               #odds 1 of interest
               odds_1_flagged=True
           else:
               odds_1_flagged=False

           if odds_data['qrbet_x_ht']>odds_data['bf_x_ht']['lay_price']:
               #odds 1 of interest
               odds_x_flagged=True
           else:
               odds_x_flagged=False

           if odds_data['qrbet_2_ht']>odds_data['bf_2_ht']['lay_price'] and odds_data['bf_2_ht']['lay_price']>0:
               #odds 2 of interest
               odds_2_flagged=True
           else:
               odds_2_flagged=False

           send_ht("**QRBET**",row[4],row[5],odds_data['qrbet_1_ht'],odds_data['qrbet_x_ht'],odds_data['qrbet_2_ht'],odds_data['bf_1_ht']['lay_price'],odds_data['bf_x_ht']['lay_price'],odds_data['bf_2_ht']['lay_price'],row[1],odds_1_flagged,odds_x_flagged,odds_2_flagged,row[-1])

        if odds_data['qrbet_dc_1x']>odds_data['bf_dc_1x']['lay_price'] or odds_data['qrbet_dc_x2']>odds_data['bf_dc_x2']['lay_price'] or odds_data['qrbet_dc_12']>odds_data['bf_dc_12']['lay_price']:
           if odds_data['qrbet_dc_1x']>odds_data['bf_dc_1x']['lay_price'] and odds_data['bf_dc_1x']['lay_price']>0:
               #odds 1 of interest
               odds_1_flagged=True
           else:
               odds_1_flagged=False

           if odds_data['qrbet_dc_x2']>odds_data['bf_dc_x2']['lay_price']:
               #odds 1 of interest
               odds_x_flagged=True
           else:
               odds_x_flagged=False

           if odds_data['qrbet_dc_12']>odds_data['bf_dc_12']['lay_price'] and odds_data['bf_dc_12']['lay_price']>0:
               #odds 2 of interest
               odds_2_flagged=True
           else:
               odds_2_flagged=False

           send_dc("**QRBET**",row[4],row[5],odds_data['qrbet_dc_1x'],odds_data['qrbet_dc_x2'],odds_data['qrbet_dc_12'],odds_data['bf_dc_1x']['lay_price'],odds_data['bf_dc_x2']['lay_price'],odds_data['bf_dc_12']['lay_price'],row[1],odds_1_flagged,odds_x_flagged,odds_2_flagged,row[-1])


def check_winkel_toto(odds_data):
        #print("Checking:",odds_data)
#here, run thru the 1x2,, then each of the other markets,, one by one..
        if odds_data['winkel_toto_1_odds']>odds_data['bf_1_odds']['lay_price'] or odds_data['winkel_toto_x_odds']>odds_data['bf_x_odds']['lay_price'] or odds_data['winkel_toto_2_odds']>odds_data['bf_2_odds']['lay_price']:
           if odds_data['winkel_toto_1_odds']>odds_data['bf_1_odds']['lay_price'] and odds_data['bf_1_odds']['lay_price']>0:
               #odds 1 of interest
               odds_1_flagged=True
           else:
               odds_1_flagged=False

           if odds_data['winkel_toto_x_odds']>odds_data['bf_x_odds']['lay_price']:
               #odds 1 of interest
               odds_x_flagged=True
           else:
               odds_x_flagged=False

           if odds_data['winkel_toto_2_odds']>odds_data['bf_2_odds']['lay_price'] and odds_data['bf_2_odds']['lay_price']>0:
               #odds 2 of interest
               odds_2_flagged=True
           else:
               odds_2_flagged=False

           send_1x2("**WINKEL_TOTO**",row[4],row[5],odds_data['winkel_toto_1_odds'],odds_data['winkel_toto_x_odds'],odds_data['winkel_toto_2_odds'],odds_data['bf_1_odds']['lay_price'],odds_data['bf_x_odds']['lay_price'],odds_data['bf_2_odds']['lay_price'],row[1],odds_1_flagged,odds_x_flagged,odds_2_flagged,row[-1])

        if odds_data['winkel_toto_under_2.5']>odds_data['bf_Under_2.5']['lay_price'] or odds_data['winkel_toto_over_2.5']>odds_data['bf_Over_2.5']['lay_price']:
           if odds_data['winkel_toto_under_2.5']>odds_data['bf_Under_2.5']['lay_price'] and odds_data['bf_Under_2.5']['lay_price']>0:
               #odds 1 of interest
               odds_1_flagged=True
           else:
               odds_1_flagged=False

           if 0:#odds_data['unibet_x_odds']>odds_data['bf_x_odds']['lay_price']:
               #odds 1 of interest
               odds_x_flagged=True
           else:
               odds_x_flagged=False

           if odds_data['winkel_toto_over_2.5']>odds_data['bf_Over_2.5']['lay_price'] and odds_data['bf_Over_2.5']['lay_price']>0:
               #odds 2 of interest
               odds_2_flagged=True
           else:
               odds_2_flagged=False

           send_uo25("**WINKEL_TOTO**",row[4],row[5],odds_data['winkel_toto_under_2.5'],"",odds_data['winkel_toto_over_2.5'],odds_data['bf_Under_2.5']['lay_price'],"",odds_data['bf_Over_2.5']['lay_price'],row[1],odds_1_flagged,0,odds_2_flagged,row[-1])

        if odds_data['winkel_toto_under_3.5']>odds_data['bf_Under_3.5']['lay_price'] or odds_data['winkel_toto_over_3.5']>odds_data['bf_Over_3.5']['lay_price']:
           if odds_data['winkel_toto_under_3.5']>odds_data['bf_Under_3.5']['lay_price'] and odds_data['bf_Under_3.5']['lay_price']>0:
               #odds 1 of interest
               odds_1_flagged=True
           else:
               odds_1_flagged=False

           if 0:#odds_data['unibet_x_odds']>odds_data['bf_x_odds']['lay_price']:
               #odds 1 of interest
               odds_x_flagged=True
           else:
               odds_x_flagged=False

           if odds_data['winkel_toto_over_3.5']>odds_data['bf_Over_3.5']['lay_price'] and odds_data['bf_Over_3.5']['lay_price']>0:
               #odds 2 of interest
               odds_2_flagged=True
           else:
               odds_2_flagged=False

           send_uo35("**WINKEL_TOTO**",row[4],row[5],odds_data['winkel_toto_under_3.5'],"",odds_data['winkel_toto_over_3.5'],odds_data['bf_Under_3.5']['lay_price'],"",odds_data['bf_Over_3.5']['lay_price'],row[1],odds_1_flagged,0,odds_2_flagged,row[-1])

        if odds_data['winkel_toto_dnb_home']>odds_data['bf_dnb_home']['lay_price'] or odds_data['winkel_toto_dnb_away']>odds_data['bf_dnb_away']['lay_price']:
           if odds_data['winkel_toto_dnb_home']>odds_data['bf_dnb_home']['lay_price'] and odds_data['bf_dnb_home']['lay_price']>0:
               #odds 1 of interest
               odds_1_flagged=True
           else:
               odds_1_flagged=False

           if 0:#odds_data['unibet_x_odds']>odds_data['bf_x_odds']['lay_price']:
               #odds 1 of interest
               odds_x_flagged=True
           else:
               odds_x_flagged=False

           if odds_data['winkel_toto_dnb_away']>odds_data['bf_dnb_away']['lay_price'] and odds_data['bf_dnb_away']['lay_price']>0:
               #odds 2 of interest
               odds_2_flagged=True
           else:
               odds_2_flagged=False

           send_dnb("**WINKEL_TOTO**",row[4],row[5],odds_data['winkel_toto_dnb_home'],"",odds_data['winkel_toto_dnb_away'],odds_data['bf_dnb_home']['lay_price'],"",odds_data['bf_dnb_away']['lay_price'],row[1],odds_1_flagged,0,odds_2_flagged,row[-1])

        if odds_data['winkel_toto_1_ht']>odds_data['bf_1_ht']['lay_price'] or odds_data['winkel_toto_x_ht']>odds_data['bf_x_ht']['lay_price'] or odds_data['winkel_toto_2_ht']>odds_data['bf_2_ht']['lay_price']:
           if odds_data['winkel_toto_1_ht']>odds_data['bf_1_ht']['lay_price'] and odds_data['bf_1_ht']['lay_price']>0:
               #odds 1 of interest
               odds_1_flagged=True
           else:
               odds_1_flagged=False

           if odds_data['winkel_toto_x_ht']>odds_data['bf_x_ht']['lay_price']:
               #odds 1 of interest
               odds_x_flagged=True
           else:
               odds_x_flagged=False

           if odds_data['winkel_toto_2_ht']>odds_data['bf_2_ht']['lay_price'] and odds_data['bf_2_ht']['lay_price']>0:
               #odds 2 of interest
               odds_2_flagged=True
           else:
               odds_2_flagged=False

           send_ht("**WINKEL_TOTO**",row[4],row[5],odds_data['winkel_toto_1_ht'],odds_data['winkel_toto_x_ht'],odds_data['winkel_toto_2_ht'],odds_data['bf_1_ht']['lay_price'],odds_data['bf_x_ht']['lay_price'],odds_data['bf_2_ht']['lay_price'],row[1],odds_1_flagged,odds_x_flagged,odds_2_flagged,row[-1])

        if odds_data['winkel_toto_dc_1x']>odds_data['bf_dc_1x']['lay_price'] or odds_data['winkel_toto_dc_x2']>odds_data['bf_dc_x2']['lay_price'] or odds_data['winkel_toto_dc_12']>odds_data['bf_dc_12']['lay_price']:
           if odds_data['winkel_toto_dc_1x']>odds_data['bf_dc_1x']['lay_price'] and odds_data['bf_dc_1x']['lay_price']>0:
               #odds 1 of interest
               odds_1_flagged=True
           else:
               odds_1_flagged=False

           if odds_data['winkel_toto_dc_x2']>odds_data['bf_dc_x2']['lay_price']:
               #odds 1 of interest
               odds_x_flagged=True
           else:
               odds_x_flagged=False

           if odds_data['winkel_toto_dc_12']>odds_data['bf_dc_12']['lay_price'] and odds_data['bf_dc_12']['lay_price']>0:
               #odds 2 of interest
               odds_2_flagged=True
           else:
               odds_2_flagged=False

           send_dc("**WINKEL_TOTO**",row[4],row[5],odds_data['winkel_toto_dc_1x'],odds_data['winkel_toto_dc_x2'],odds_data['winkel_toto_dc_12'],odds_data['bf_dc_1x']['lay_price'],odds_data['bf_dc_x2']['lay_price'],odds_data['bf_dc_12']['lay_price'],row[1],odds_1_flagged,odds_x_flagged,odds_2_flagged,row[-1])


while 1:
    
    conn = pymysql.connect(user='local',host='127.0.0.1',passwd='oeijifjwejfio',db='arb_db_beta')
    cur = conn.cursor()


    #here, pull out the alert settings for each user..
    cur.execute("select * from user_views where telegram_id like '@%'")# user,totoalerts,unibetalerts,contraalerts from user_views")
    rows = cur.fetchall()
    #here, ,build up dynamic dict of telegram,, from users with handles..
    #user_dict={13:{"tag":'@Heisenferd'},14:{'tag':'@dave_goldie'},16:{'tag':'@kwilten'},18:{'tag':'@danielcyprus2626'},19:{'tag':'@donny5078'}}
    user_dict={}
    for row in rows:
        if row[2] and row[2]!="":
            user_dict[row[1]]={"tag":row[2]}
    #print(user_dict)
    #time.sleep(5)
    for row in rows:
        if row[1] in user_dict:
            user_dict[row[1]]['toto_1x2'] = row[13]
            user_dict[row[1]]['toto_uo25'] = row[14]
            user_dict[row[1]]['toto_uo35'] = row[15]
            user_dict[row[1]]['toto_dnb'] = row[16]
            user_dict[row[1]]['toto_ht'] = row[35]
            user_dict[row[1]]['toto_dc'] = row[34]
            
            user_dict[row[1]]['unibet_1x2'] = row[17]
            user_dict[row[1]]['unibet_uo25'] = row[18]
            user_dict[row[1]]['unibet_uo35'] = row[19]
            user_dict[row[1]]['unibet_dnb'] = row[20]
            user_dict[row[1]]['unibet_ht'] = row[36]
            user_dict[row[1]]['unibet_dc'] = row[37]

            user_dict[row[1]]['contra_1x2'] = row[21]
            user_dict[row[1]]['contra_uo25'] = row[22]
            user_dict[row[1]]['contra_uo35'] = row[23]
            user_dict[row[1]]['contra_dnb'] = row[24]
            user_dict[row[1]]['contra_ht'] = row[39]
            user_dict[row[1]]['contra_dc'] = row[38]

            user_dict[row[1]]['qrbet_1x2'] = row[26]
            user_dict[row[1]]['qrbet_uo25'] = row[27]
            user_dict[row[1]]['qrbet_uo35'] = row[28]
            user_dict[row[1]]['qrbet_dnb'] = row[29]
            user_dict[row[1]]['qrbet_ht'] = row[40]
            user_dict[row[1]]['qrbet_dc'] = row[41]

            user_dict[row[1]]['winkel_toto_1x2'] = row[44]
            user_dict[row[1]]['winkel_toto_uo25'] = row[45]
            user_dict[row[1]]['winkel_toto_uo35'] = row[46]
            user_dict[row[1]]['winkel_toto_dnb'] = row[47]
            user_dict[row[1]]['winkel_toto_ht'] = row[43]
            user_dict[row[1]]['winkel_toto_dc'] = row[42]

    #print(user_dict)
    #time.sleep(5)
    cur.execute("select * from toto_matches where timestamp>unix_timestamp()")
    rows = cur.fetchall()

    for row in rows:
        odds_data = json.loads(row[8])
        if (datetime.datetime.fromtimestamp(int(row[1]))-datetime.datetime.now()).days <=14:
            check_toto(odds_data)
        else:
            pass#print("match outside of 14days")

    cur.execute("select * from unibet_matches where timestamp>unix_timestamp()")
    rows = cur.fetchall()

    for row in rows:
        odds_data = json.loads(row[8])
        if (datetime.datetime.fromtimestamp(int(row[1]))-datetime.datetime.now()).days <=14:
            check_unibet(odds_data)
        else:
            pass#print("match outside of 14days")

    cur.execute("select * from contra_matches where timestamp>unix_timestamp()")
    rows = cur.fetchall()

    for row in rows:
        odds_data = json.loads(row[8])
        if (datetime.datetime.fromtimestamp(int(row[1]))-datetime.datetime.now()).days <=14:
            check_contra(odds_data)
        else:
            pass#print("match outside of 14days")

    cur.execute("select * from qrbet_matches where timestamp>unix_timestamp()")
    rows = cur.fetchall()

    for row in rows:
        odds_data = json.loads(row[8])
        if (datetime.datetime.fromtimestamp(int(row[1]))-datetime.datetime.now()).days <=14:
            check_qrbet(odds_data)
        else:
            pass#print("match outside of 14days")

    cur.execute("select * from winkel_toto_matches where timestamp>unix_timestamp()")
    rows = cur.fetchall()

    for row in rows:
        odds_data = json.loads(row[8])
        if (datetime.datetime.fromtimestamp(int(row[1]))-datetime.datetime.now()).days <=14:
            check_winkel_toto(odds_data)
        else:
            pass#print("match outside of 14days")


    #here do a new raw comps added for dave..
    
    cur.execute("select compid from comp_alerts")
    dones={}
    rows = cur.fetchall()
    for row in rows:
        dones[row[0]]=""
    send_msg="New comps added recently:\n"

    cur.execute("select id,comp_name,site from raw_comps where timestamp-unix_timestamp()>-86400")
    rows  =cur.fetchall()
    for row in rows:
        if row[0] not in dones:
            cur.execute("insert into comp_alerts(compid) values(" + str(row[0]) + ")")
            send_msg+=row[1] + " (" + row[2] + ")\n"
    if send_msg!="New comps added recently:\n":
        print("sending comps update")
        print(send_msg)
        try:
            client.send_message('@dave_goldie',send_msg)
            client.send_message('@Heisenferd',send_msg)
        except:
            print("send msg err,,too long prob")
    conn.commit()
    
    conn.close()
    time.sleep(60)
