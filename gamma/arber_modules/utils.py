"""
utils.py - Shared utility functions for the arber_modules package.

Provides:
- Odds-history deduplication and database insertion.
- Timestamp conversion helpers for provider-specific time formats.
- String normalisation (accent stripping).
- Betfair reference-data transformation.
- Database error logging.
"""
import datetime
import pymysql
import configparser
import time
import unicodedata
import json

config = configparser.ConfigParser()
config.read('config.ini')
print(config.sections())
db_name="arb_db_beta"#db_name = config['DEFAULT']['db_name']

# Cache the last seen odds snapshot per (book, event_id) so we only write
# to odds_history when odds actually changed.
last_match_keys = {}


def do_odds_history_insert(book, event_id, odds_data, market_data, vwap_data=None):
    """
    Insert an odds snapshot into odds_history, skipping duplicates.

    Builds a fingerprint string from the current prices. If the fingerprint
    matches the last recorded snapshot for (book, event_id), the insert is
    skipped. Otherwise the snapshot is written and the cache updated.

    Betfair data (book=="betfair") is keyed by outcome suffix (_1, _X, _2);
    all other books produce a flat list of price values.
    """
    od = odds_data.copy()
    md = market_data.copy()

    parts = []

    if book=="betfair":
        #print("BF ODDS HIST DUMP>>>>")
        #print(od)
        #print("END DUMP<<<<<<<<<<<<<<<")
        od_contents={}
        # Keys from odds[0/1/2] are suffixed with _1/_X/_2 to avoid
        # collisions when all three outcomes share the same field names.

        for o in od[0]:
            od_contents[o + "_1"]=od[0][o]

        for o in od[1]:
            od_contents[o + "_X"]=od[1][o]

        for o in od[2]:
            od_contents[o + "_2"]=od[2][o]

        for o in md:
            od_contents.update(o)
        #print(od_contents)

        if vwap_data:
            for v in vwap_data:
                od_contents['vwap_' + v] = vwap_data[v]

        for o in od_contents:
            parts.append(str(od_contents[o]))
    else:
        od_contents=[]
        for o in od:
            od_contents.append(o)
            parts.append(str(o['price']))
        for o in md:
            od_contents.append(o)
            parts.append(str(o['price']))

    #print(">>>",len(parts))
    #od.update(md)
    #now create key from match_id and od dump
    #od_dump = json.dumps(od_contents)
    od_dump = "_".join(parts)
    match_key = str(event_id) + "_" + od_dump

    # Only store history when the odds snapshot actually changed.
    # Use (book, event_id) so different books for the same event do not collide.
    cache_key = (book, event_id)
    if cache_key in last_match_keys and last_match_keys[cache_key] == match_key:
        return
    last_match_keys[cache_key] = match_key

    try:
        conn = pymysql.connect(host='127.0.0.1',user='local',passwd='oeijifjwejfio',db=db_name)
        cur  = conn.cursor()
        cur.execute("insert into odds_history (timestamp,match_key,matchid,book,odds) values(%s,%s,%s,%s,%s)",(int(time.time()),match_key,event_id,book,json.dumps(od_contents)))
        conn.commit()
        conn.close()
    except Exception as msg:
        print("ODDS_HISTORY_INSERT_ERROR:", book, event_id, str(msg))

def convert_euro_time(inny: str) -> str:
        """Convert a UTC+2 ISO-8601 datetime string to UTC, returning ISO-8601 without timezone."""
        #print(inny)
        x,y = inny.split("T")
        yr,mt,dt = x.split("-")
        hr,mn,sc = y.split(":")

        return str(datetime.datetime(int(yr),int(mt),int(dt),int(hr),int(mn),int(sc)) - datetime.timedelta(hours=2))[0:19].replace(" ","T")

def convert_yess_time(inny: str) -> str:
        """Convert a UTC+3 space-separated datetime string to UTC, returning ISO-8601 without timezone."""
        #print(inny)
        x,y = inny.split(" ")
        yr,mt,dt = x.split("-")
        hr,mn,sc = y.split(":")

        return str(datetime.datetime(int(yr),int(mt),int(dt),int(hr),int(mn),int(sc)) - datetime.timedelta(hours=3))[0:19].replace(" ","T")


def convert_midnight(inny: str) -> str:
        """Advance a date by one day when the time component is exactly midnight (00:00:00Z).

        Returns the date portion only (YYYY-MM-DD) when adjusted, or the
        original date string unchanged for all other times.
        """
        #print(inny)
        x,y = inny.split("T")
        yr,mt,dt = x.split("-")
        retval = x
        if y=='00:00:00Z':
                #add a day.
                retval = str(datetime.datetime(int(yr),int(mt),int(dt)) + datetime.timedelta(days=1))[0:10]
        return retval

def strip_accents(s: str) -> str:
    """Remove diacritical marks from a Unicode string."""
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn')

def insert_error(err_str: str, misc: str = "") -> None:
    """Write an error message to the errors table."""
    conn = pymysql.connect(host='localhost',user='local',passwd='oeijifjwejfio',db=db_name)
    cur  = conn.cursor()
    cur.execute("insert into errors (timestamp,err_msg,misc) values(%s,%s,%s)",(time.time(),err_str,misc))
    conn.commit()
    conn.close()

def convert_string_timestamp(inny) -> int:
    """Return a Unix epoch integer from either a numeric value or an ISO-8601 string.

    Accepts an integer, a string of digits, or a string in the form
    'YYYY-MM-DDTHH:MM:SSZ' (or with a space separator instead of 'T').
    """
        #print(inny)
    #print("about to check timestamp:",inny)
    try:
        return int(inny)
    except:
        pass
    x,y = inny.replace("T"," ").replace("Z","").split(" ")
    yr,mt,dt = x.split("-")
    hr,mn,sc = y.split(":")
    #print("done>>",int(datetime.datetime(int(yr),int(mt),int(dt),int(hr),int(mn),int(sc)).timestamp()))
    return int(datetime.datetime(int(yr),int(mt),int(dt),int(hr),int(mn),int(sc)).timestamp())

def convert_ref_matches(bf_data: dict) -> list:
    """
    Transform a Betfair data dict into a normalised list of match records.

    For each event in bf_data that has odds, builds back/lay lists for the
    match result, over/under 2.5, over/under 3.5, DNB, double chance, and
    half-time markets, plus a VWAP snapshot. Falls back to zeros for any
    market that is missing from the data.

    Returns a list of match dicts keyed by market type, suitable for the
    provider insert functions.
    """
    bf_matches=[]
    #print(bf_data)
    for b in bf_data:

        try:
            if len(bf_data[b]['odds'])>0:
                back_25=[]
                lay_25=[]
                back_35=[]
                lay_35=[]
                back_dnb=[]
                lay_dnb=[]

                back_dc=[]
                lay_dc=[]

                back_ht=[]
                lay_ht=[]

                back_matchlist=[]
                lay_matchlist=[]
                print(bf_data[b]['name'],bf_data[b].keys())
                teama,teamb  = bf_data[b]['name'].split(" v ")
                #print("bfmatches:",teama,teamb)
                #print(bf_data[b]['odds'])
                #print("---")
                matchteams=[teama,teamb]
                matchteams.sort()
                if matchteams!=[teama,teamb]:
                        flipped=1
                else:
                        flipped=0
                #print("bf_data check:",bf_data)
                back_matchlist.append([teama,bf_data[b]['odds'][0]['last_back_price'],bf_data[b]['odds'][0]['last_back_vol'],bf_data[b]['odds'][0]['lowest_back_price'],bf_data[b]['odds'][0]['lowest_back_vol']])
                back_matchlist.append([teamb,bf_data[b]['odds'][1]['last_back_price'],bf_data[b]['odds'][1]['last_back_vol'],bf_data[b]['odds'][2]['lowest_back_price'],bf_data[b]['odds'][1]['lowest_back_vol']])
                back_matchlist.append(["X",bf_data[b]['odds'][2]['last_back_price'],bf_data[b]['odds'][2]['last_back_vol'],bf_data[b]['odds'][1]['lowest_back_price'],bf_data[b]['odds'][2]['lowest_back_vol']])
                lay_matchlist.append([teama,bf_data[b]['odds'][0]['lay_price'],bf_data[b]['odds'][0]['lay_vol']])
                lay_matchlist.append([teamb,bf_data[b]['odds'][1]['lay_price'],bf_data[b]['odds'][1]['lay_vol']])
                lay_matchlist.append(["X",bf_data[b]['odds'][2]['lay_price'],bf_data[b]['odds'][2]['lay_vol']])
 #add extra markets here
                back_25.append(["Under_2.5",bf_data[b]['markets'][0]['last_back_price_Under_2.5'],bf_data[b]['markets'][0]['last_back_vol_Under_2.5'],bf_data[b]['markets'][0]['lowest_back_price_Under_2.5'],bf_data[b]['markets'][0]['lowest_back_vol_Under_2.5']])
                back_25.append(["Over_2.5",bf_data[b]['markets'][1]['last_back_price_Over_2.5'],bf_data[b]['markets'][1]['last_back_vol_Over_2.5'],bf_data[b]['markets'][1]['lowest_back_price_Over_2.5'],bf_data[b]['markets'][1]['lowest_back_vol_Over_2.5']])

                lay_25.append(["Under_2.5",bf_data[b]['markets'][0]['lay_price_Under_2.5'],bf_data[b]['markets'][0]['lay_vol_Under_2.5']])
                lay_25.append(["Over_2.5",bf_data[b]['markets'][1]['lay_price_Over_2.5'],bf_data[b]['markets'][1]['lay_vol_Over_2.5']])

                try:
                    back_35.append(["Under_3.5",bf_data[b]['markets'][2]['last_back_price_Under_3.5'],bf_data[b]['markets'][2]['last_back_vol_Under_3.5'],bf_data[b]['markets'][2]['lowest_back_price_Under_3.5'],bf_data[b]['markets'][2]['lowest_back_vol_Under_3.5']])
                    back_35.append(["Over_3.5",bf_data[b]['markets'][3]['last_back_price_Over_3.5'],bf_data[b]['markets'][3]['last_back_vol_Over_3.5'],bf_data[b]['markets'][3]['lowest_back_price_Over_3.5'],bf_data[b]['markets'][3]['lowest_back_vol_Over_3.5']])
                except:
                    back_35.append(["Under_3.5",0,0,0,0])
                    back_35.append(["Over_3.5",0,0,0,0])

                try:
                    lay_35.append(["Under_3.5",bf_data[b]['markets'][2]['lay_price_Under_3.5'],bf_data[b]['markets'][2]['lay_vol_Under_3.5']])
                    lay_35.append(["Over_3.5",bf_data[b]['markets'][3]['lay_price_Over_3.5'],bf_data[b]['markets'][3]['lay_vol_Over_3.5']])
                except:
                    lay_35.append(["Under_3.5",0,0])
                    lay_35.append(["Over_3.5",0,0])

                try:
                    back_dnb.append(["DNB_Home",bf_data[b]['markets'][4]['last_back_price_DNB_Home'],bf_data[b]['markets'][4]['last_back_vol_DNB_Home'],bf_data[b]['markets'][4]['lowest_back_price_DNB_Home'],bf_data[b]['markets'][4]['lowest_back_vol_DNB_Home']])
                    back_dnb.append(["DNB_Away",bf_data[b]['markets'][5]['last_back_price_DNB_Away'],bf_data[b]['markets'][5]['last_back_vol_DNB_Away'],bf_data[b]['markets'][5]['lowest_back_price_DNB_Away'],bf_data[b]['markets'][5]['lowest_back_vol_DNB_Away']])
                except:
                    #print("err on dnb_home",bf_data[b]['markets'][4])
                    back_dnb.append(["DNB_Home",0,0,0,0])
                    back_dnb.append(["DNB_Away",0,0,0,0])

                try:
                    lay_dnb.append(["DNB_Home",bf_data[b]['markets'][4]['lay_price_DNB_Home'],bf_data[b]['markets'][4]['lay_vol_DNB_Home']])
                    lay_dnb.append(["DNB_Away",bf_data[b]['markets'][5]['lay_price_DNB_Away'],bf_data[b]['markets'][5]['lay_vol_DNB_Away']])
                except:
                    lay_dnb.append(["DNB_Home",0,0])
                    lay_dnb.append(["DNB_Away",0,0])


                #DC
                try:
                    back_dc.append(["DC_1X",bf_data[b]['markets'][6]['last_back_price_DC_1X'],bf_data[b]['markets'][6]['last_back_vol_DC_1X'],bf_data[b]['markets'][6]['lowest_back_price_DC_1X'],bf_data[b]['markets'][6]['lowest_back_vol_DC_1X']])
                    back_dc.append(["DC_X2",bf_data[b]['markets'][7]['last_back_price_DC_X2'],bf_data[b]['markets'][7]['last_back_vol_DC_X2'],bf_data[b]['markets'][7]['lowest_back_price_DC_X2'],bf_data[b]['markets'][7]['lowest_back_vol_DC_X2']])
                    back_dc.append(["DC_12",bf_data[b]['markets'][8]['last_back_price_DC_12'],bf_data[b]['markets'][8]['last_back_vol_DC_12'],bf_data[b]['markets'][8]['lowest_back_price_DC_12'],bf_data[b]['markets'][8]['lowest_back_vol_DC_12']])

                except:
                    #print("err on dnb_home",bf_data[b]['markets'][4])
                    back_dc.append(["DC_1X",0,0,0,0])
                    back_dc.append(["DC_X2",0,0,0,0])
                    back_dc.append(["DC_12",0,0,0,0])


                try:
                    lay_dc.append(["DC_1X",bf_data[b]['markets'][6]['lay_price_DC_1X'],bf_data[b]['markets'][6]['lay_vol_DC_1X']])
                    lay_dc.append(["DC_X2",bf_data[b]['markets'][7]['lay_price_DC_X2'],bf_data[b]['markets'][7]['lay_vol_DC_X2']])
                    lay_dc.append(["DC_12",bf_data[b]['markets'][8]['lay_price_DC_12'],bf_data[b]['markets'][8]['lay_vol_DC_12']])
                except:
                    lay_dc.append(["DC_1X",0,0])
                    lay_dc.append(["DC_X2",0,0])
                    lay_dc.append(["DC_12",0,0])

                #HT
                try:
                    #back_dc.append(["DC_1X",bf_data[b]['markets'][4]['last_back_price_DC_1X'],bf_data[b]['markets'][4]['last_back_price_DC_1X'],bf_data[b]['markets'][4]['last_back_price_DC_1X'],bf_data[b]['markets'][4]['last_back_price_DC_1X']])
                    back_ht.append(["1_HT",bf_data[b]['markets'][9]['last_back_price_1_HT'],bf_data[b]['markets'][9]['last_back_vol_1_HT'],bf_data[b]['markets'][9]['lowest_back_price_1_HT'],bf_data[b]['markets'][9]['lowest_back_vol_1_HT']])
                    back_ht.append(["2_HT",bf_data[b]['markets'][10]['last_back_price_2_HT'],bf_data[b]['markets'][10]['last_back_vol_2_HT'],bf_data[b]['markets'][10]['lowest_back_price_2_HT'],bf_data[b]['markets'][10]['lowest_back_vol_2_HT']])
                    back_ht.append(["X_HT",bf_data[b]['markets'][11]['last_back_price_X_HT'],bf_data[b]['markets'][11]['last_back_vol_X_HT'],bf_data[b]['markets'][11]['lowest_back_price_X_HT'],bf_data[b]['markets'][11]['lowest_back_vol_X_HT']])

                except:
                    #print("err on dnb_home",bf_data[b]['markets'][4])
                    back_ht.append(["1_HT",0,0,0,0])
                    back_ht.append(["2_HT",0,0,0,0])
                    back_ht.append(["X_HT",0,0,0,0])


                try:
                    lay_ht.append(["1_HT",bf_data[b]['markets'][9]['lay_price_1_HT'],bf_data[b]['markets'][9]['lay_vol_1_HT']])
                    lay_ht.append(["2_HT",bf_data[b]['markets'][10]['lay_price_2_HT'],bf_data[b]['markets'][10]['lay_vol_2_HT']])
                    lay_ht.append(["X_HT",bf_data[b]['markets'][11]['lay_price_X_HT'],bf_data[b]['markets'][11]['lay_vol_X_HT']])
                except:
                    lay_ht.append(["1_HT",0,0])
                    lay_ht.append(["2_HT",0,0])
                    lay_ht.append(["X_HT",0,0])
                try:
                    vwaps={"1":bf_data[b]['vwaps']['1'],"X":bf_data[b]['vwaps']['X'],"2":bf_data[b]['vwaps']['2'],
                    "Under_2.5":bf_data[b]['vwaps']['Under_2.5'],"Over_2.5":bf_data[b]['vwaps']['Over_2.5'],
                    "Under_3.5":bf_data[b]['vwaps']['Under_3.5'],"Over_3.5":bf_data[b]['vwaps']['Over_3.5'],
                    "DNB_Home":bf_data[b]['vwaps']['DNB_Home'],"DNB_Away":bf_data[b]['vwaps']['DNB_Away'],
                    "DC_1X":bf_data[b]['vwaps']['DC_1X'],"DC_X2":bf_data[b]['vwaps']['DC_X2'],"DC_12":bf_data[b]['vwaps']['DC_12'],
                    "1_HT":bf_data[b]['vwaps']['1_HT'],"X_HT":bf_data[b]['vwaps']['X_HT'],"2_HT":bf_data[b]['vwaps']['2_HT']}
                    #print("VWAP DICT:",vwaps)
                except Exception as msg:
                    pass#print("VWAP ERROR:",str(msg))

                bf_matches.append({"start_time":bf_data[b]['timestamp'],"matchup":matchteams,"flipped":flipped,"matchup_raw":matchteams,"lay_book":lay_matchlist,"back_book":back_matchlist,"back_25":back_25,"lay_25":lay_25,"back_35":back_35,"lay_35":lay_35,"back_dnb":back_dnb,"lay_dnb":lay_dnb,"back_dc":back_dc,"lay_dc":lay_dc,"back_ht":back_ht,"lay_ht":lay_ht,"vwaps":vwaps,'event_id':b,"timestamp":bf_data[b]['timestamp']})
                #print("PINNY>>",{"start_time":bf_data[b]['start_time'],"matchup":matchteams,"flipped":flipped,"matchup_raw":matchteams,"lay_book":lay_matchlist,"back_book":back_matchlist,'event_id':b,"timestamp":bf_data[b]['timestamp']})
        except Exception as msg:
            print("err on betfair match check:",teama,teamb,str(msg))
            try:
                #print(str(msg),"err on pinny (ub) match check:",teama,teamb)
                insert_error(str(msg),"err on refconvert(bf) match check:",teama,teamb,str(msg))
            except Exception as msg:
                pass#print(">>> unibet insert err error..",str(msg))

    return bf_matches

def remove_draw(inny: list) -> list:
    """Remove all draw-related entries ('draw', 'Draw', 'X', 'x', '') from a team list in-place."""
    try:
        inny.remove("draw")
    except:
        pass
    try:
        inny.remove("Draw")
    except:
        pass
    try:
        inny.remove("X")
    except:
        pass

    try:
        inny.remove("x")
    except:
        pass
    try:
        inny.remove("")
    except:
        pass

    return inny
