#yess365.com scraper
import requests
import random

def pull_raw_comps():
    url="http://yess365.com/services/pregame/Pregame.Service.php"
    params = {"action":"get-filters","type":"champs-by-sport","sport":"1","onlytoday":"false"}
    res = requests.post(url,data =params,proxies={"https":proxies[0]})
    data = res.json()
    data = data['data']['DATASET']
    comps = []
    for nation in data:
        for comp in data[nation]:
            comps.append([nation,comp['id'],comp['label']])
        
    return comps

with open("/home/arb_bot/proxies") as f:
    proxies = f.read().split("\n")

try:
    proxies.remove('')
except:
    pass


def pull_comp_events(compid):
    url="http://yess365.com/services/pregame/Pregame.Service.php"
    params={"action":"get-data","type":"matches","sport":"1","champs[]":str(compid),"sort":"date","offset":"0","src":"champ"}
    res = requests.post(url,data=params,proxies={"https":proxies[0]})
    data = res.json()
    events = data['data']['DATASET']
    event_list=[]
    for event in events:
        start_time = event['gamedate'] + " " + event['gametime'] ## << what timezone is this?
        event_id = event['gamecode']
        event_name = event['teams']
        home_team,away_team = event_name.split("-")
        markets  = event['markets']
        home_odds = markets['point1']['valueDec']
        draw_odds = markets['pointX']['valueDec']
        away_odds = markets['point2']['valueDec']
        
def pull_extra_markets(eventid):
    url="http://yess365.com/services/pregame/Pregame.Service.php"
    params = {"action":"get-data","type":"match-details","sport":"1","gamecode":str(eventid)}
    res = requests.post(url,data =params,proxies={"https":proxies[0]})
    markets = res.json()['data']['DATASET']['markets']
    dnb_home = markets['Draw No Bet']['odds'][1]['valueDec']
    dnb_away = markets['Draw No Bet']['odds'][2]['valueDec']
    over_25 = markets['Goal Line']['odds']['Over 2.5']['valueDec']
    under_25 = markets['Goal Line']['odds']['Under 2.5']['valueDec']
    

