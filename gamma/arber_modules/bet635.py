import configparser
import concurrent.futures
import datetime
import json
import random
import time
from typing import Any, Dict, List, Optional, Tuple

import pymysql
import requests
from fuzzywuzzy import fuzz

from arber_modules.utils import *

thread_count = 5
timeout_count = 8

config = configparser.ConfigParser()
config.read('config.ini')
db_name = "arb_db_beta"

with open("/home/arb_bot/proxies") as f:
    proxies = [p for p in f.read().split("\n") if p]

GAMMA_BASE = "https://gamma-api.polymarket.com"
SPORTS_BASE = "https://gamma-api.polymarket.com"
DEFAULT_LIMIT = 500
MAX_PAGES = 10
MAX_SPREAD = 0.10  # internal quality filter only
MIN_BEST_ASK = 0.01
MAX_BEST_ASK = 0.99
MONEYLINE_TYPES = {
    "moneyline",
    "1x2",
    "match_result",
    "three_way_moneyline",
    "3-way_moneyline",
    "3_way_moneyline",
}
LEAGUE_HINTS = {
    "epl": ["premier league", "england premier league", "english premier league"],
    "engcha": ["championship", "efl championship", "english championship"],
    "laliga": ["la liga", "spain primera division"],
    "bundesliga": ["bundesliga", "germany bundesliga"],
    "seriea": ["serie a", "italy serie a"],
    "ligue1": ["ligue 1", "france ligue 1"],
    "ucl": ["champions league", "uefa champions league"],
    "uel": ["europa league", "uefa europa league"],
    "uecl": ["conference league", "uefa conference league"],
}


class PolyError(Exception):
    pass


_session = requests.Session()
_session.headers.update({"User-Agent": "Mozilla/5.0"})


def _pick_proxy() -> Optional[Dict[str, str]]:
    if not proxies:
        return None
    proxy = random.choice(proxies)
    return {"https": proxy, "http": proxy}


def _request_json(url: str, params: Optional[Dict[str, Any]] = None) -> Any:
    last_err = None
    for _ in range(4):
        try:
            res = _session.get(url, params=params, proxies=_pick_proxy(), timeout=timeout_count)
            res.raise_for_status()
            return res.json()
        except Exception as exc:
            last_err = exc
            time.sleep(0.5)
    raise PolyError(f"request failed for {url}: {last_err}")


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return []
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else [parsed]
        except Exception:
            return [v.strip() for v in value.split(",") if v.strip()]
    return [value]


def _clean_name(text: str) -> str:
    if not text:
        return ""
    text = strip_accents(str(text)).lower().strip()
    for ch in ["-", "_", ".", ",", "'", '"', "(", ")", "/", ":"]:
        text = text.replace(ch, " ")
    text = " ".join(text.split())
    aliases = {
        "man utd": "manchester united",
        "man united": "manchester united",
        "psg": "paris saint germain",
        "inter": "inter milan",
        "atletico": "atletico madrid",
        "ath madrid": "atletico madrid",
        "athletic bilbao": "athletic club",
    }
    return aliases.get(text, text)


def _parse_event_title(title: str) -> Tuple[str, str]:
    raw = (title or "").strip()
    for sep in [" vs ", " v ", " @ ", " at ", " - "]:
        if sep in raw:
            left, right = raw.split(sep, 1)
            return left.strip(), right.strip()
    raise PolyError(f"could not parse event title: {title}")


def _parse_outcome_label(market: Dict[str, Any]) -> str:
    for key in ["groupItemTitle", "shortOutcomes", "question"]:
        value = market.get(key)
        if value:
            values = _as_list(value)
            if values and isinstance(values[0], str):
                return values[0].strip()
            if isinstance(value, str):
                return value.strip()
    return ""


def _prob_to_decimal(prob: Any) -> float:
    try:
        p = float(prob)
    except Exception:
        return 0.0
    if p <= 0:
        return 0.0
    if p >= 1.0:
        # defensive fallback in case a future response already sends decimal odds
        return round(p, 3)
    return round(1.0 / p, 3)


def _spread_ok(best_bid: Any, best_ask: Any) -> bool:
    try:
        bid = float(best_bid)
        ask = float(best_ask)
    except Exception:
        return False
    if ask <= 0 or bid < 0:
        return False
    return ((ask - bid) / ask) <= MAX_SPREAD


def _competition_text(market: Dict[str, Any]) -> str:
    parts = []
    for key in ["slug", "seriesSlug", "sportsMarketType", "question", "groupItemTitle"]:
        value = market.get(key)
        if value:
            parts.append(str(value))
    for event in market.get("events") or []:
        for key in ["title", "subtitle", "slug", "seriesSlug"]:
            value = event.get(key)
            if value:
                parts.append(str(value))
    return " ".join(parts).lower()


def _league_matches(league: str, market: Dict[str, Any]) -> bool:
    if not league:
        return True
    text = _competition_text(market)
    hints = LEAGUE_HINTS.get(league.lower(), [league.lower().replace("_", " ")])
    return any(h in text for h in hints)


def _fetch_sports_tags() -> List[int]:
    try:
        sports = _request_json(f"{SPORTS_BASE}/sports")
    except Exception:
        return []
    tag_ids: List[int] = []
    for sport in sports if isinstance(sports, list) else []:
        sport_name = str(sport.get("sport", "")).lower()
        if sport_name not in {"soccer", "football"}:
            continue
        tags = str(sport.get("tags", ""))
        for part in tags.split(","):
            part = part.strip()
            if part.isdigit():
                tag_ids.append(int(part))
    return list(dict.fromkeys(tag_ids))


def _fetch_markets_page(offset: int = 0, tag_id: Optional[int] = None) -> List[Dict[str, Any]]:
    params: Dict[str, Any] = {
        "limit": DEFAULT_LIMIT,
        "offset": offset,
        "closed": "false",
    }
    if tag_id is not None:
        params["tag_id"] = tag_id
        params["related_tags"] = "true"
    return _request_json(f"{GAMMA_BASE}/markets", params=params)


def _looks_like_soccer_1x2_market(market: Dict[str, Any]) -> bool:
    smt = str(market.get("sportsMarketType") or "").strip().lower()
    if smt and smt not in MONEYLINE_TYPES:
        return False
    if not market.get("active", True):
        return False
    if market.get("closed", False):
        return False
    if market.get("acceptingOrders") is False:
        return False
    if market.get("enableOrderBook") is False:
        return False
    best_ask = market.get("bestAsk")
    best_bid = market.get("bestBid")
    try:
        ask = float(best_ask)
        bid = float(best_bid)
    except Exception:
        return False
    if ask < MIN_BEST_ASK or ask > MAX_BEST_ASK:
        return False
    if not _spread_ok(bid, ask):
        return False
    events = market.get("events") or []
    if not events:
        return False
    try:
        _parse_event_title(events[0].get("title", ""))
    except Exception:
        return False
    return True


def _fixture_key(market: Dict[str, Any]) -> str:
    events = market.get("events") or [{}]
    event = events[0]
    game_id = market.get("gameId") or event.get("id") or market.get("conditionId") or market.get("id")
    start_time = market.get("eventStartTime") or event.get("startTime") or event.get("startDate") or market.get("startDate") or ""
    title = event.get("title") or market.get("question") or ""
    return f"{game_id}|{start_time}|{title}"


def _classify_outcome(label: str, home: str, away: str) -> Optional[str]:
    l = _clean_name(label)
    h = _clean_name(home)
    a = _clean_name(away)
    if l in {"draw", "tie", "x"}:
        return "draw"
    if l == h or fuzz.ratio(l, h) >= 88 or l in h or h in l:
        return "home"
    if l == a or fuzz.ratio(l, a) >= 88 or l in a or a in l:
        return "away"
    return None


def _extract_fixture_row(markets: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    sample = markets[0]
    event = (sample.get("events") or [{}])[0]
    event_title = event.get("title") or ""
    home, away = _parse_event_title(event_title)
    start_time = sample.get("eventStartTime") or event.get("startTime") or event.get("startDate") or sample.get("startDate")

    outcome_map: Dict[str, Dict[str, Any]] = {}
    for market in markets:
        label = _parse_outcome_label(market)
        which = _classify_outcome(label, home, away)
        if not which:
            continue
        ask = market.get("bestAsk")
        bid = market.get("bestBid")
        if not _spread_ok(bid, ask):
            continue
        odds = _prob_to_decimal(ask)
        if odds <= 1.0:
            continue
        current = outcome_map.get(which)
        if current is None or float(ask) < float(current["ask"]):
            outcome_map[which] = {
                "name": {"home": home, "draw": "X", "away": away}[which],
                "ask": float(ask),
                "price": odds,
                "market_id": market.get("id"),
                "label": label,
            }

    if not all(k in outcome_map for k in ("home", "draw", "away")):
        return None

    return {
        "id": event.get("id") or sample.get("gameId") or sample.get("id"),
        "book": [
            {"name": home, "price": outcome_map["home"]["price"]},
            {"name": "X", "price": outcome_map["draw"]["price"]},
            {"name": away, "price": outcome_map["away"]["price"]},
        ],
        "markets": [],
        "start_time": start_time,
        "event_title": event_title,
    }


def _fetch_polymarket_soccer_markets(league: str = "") -> List[Dict[str, Any]]:
    markets: List[Dict[str, Any]] = []
    tag_ids = _fetch_sports_tags()

    if tag_ids:
        for tag_id in tag_ids[:1]:
            for page in range(MAX_PAGES):
                page_data = _fetch_markets_page(offset=page * DEFAULT_LIMIT, tag_id=tag_id)
                if not page_data:
                    break
                markets.extend(page_data)
                if len(page_data) < DEFAULT_LIMIT:
                    break
    else:
        for page in range(2):
            page_data = _fetch_markets_page(offset=page * DEFAULT_LIMIT)
            if not page_data:
                break
            markets.extend(page_data)
            if len(page_data) < DEFAULT_LIMIT:
                break

    out: List[Dict[str, Any]] = []
    for market in markets:
        try:
            if not _looks_like_soccer_1x2_market(market):
                continue
            if league and not _league_matches(league, market):
                continue
            out.append(market)
        except Exception:
            continue
    return out


def do_bet365_raw():
    """Best-effort raw market discovery for testing. Saves slugs into raw_comps."""
    conn = pymysql.connect(host='localhost', user='local', passwd='oeijifjwejfio', db=db_name)
    cur = conn.cursor()
    cur.execute("select comp_id from raw_comps where site='bet365'")
    existing = {row[0] for row in cur.fetchall()}

    markets = _fetch_polymarket_soccer_markets(league="")
    for market in markets:
        try:
            event = (market.get("events") or [{}])[0]
            comp_id = str(market.get("slug") or market.get("id"))
            comp_name = str(event.get("subtitle") or event.get("title") or market.get("question") or comp_id)
            if comp_id in existing:
                continue
            cur.execute(
                "insert into raw_comps(comp_name,comp_id,site,timestamp) values(%s,%s,%s,%s)",
                (comp_name, comp_id, "bet365", time.time()),
            )
        except Exception:
            continue

    conn.commit()
    conn.close()


def pull_data_bet365(compid: str, league: str) -> List[Dict[str, Any]]:
    """
    Polymarket-backed 1X2 feed with bookmaker-style output.
    compid is ignored for now; league is used as a soft filter.
    """
    all_markets = _fetch_polymarket_soccer_markets(league=league)
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for market in all_markets:
        key = _fixture_key(market)
        grouped.setdefault(key, []).append(market)

    comp_data: List[Dict[str, Any]] = []
    for _, fixture_markets in grouped.items():
        try:
            row = _extract_fixture_row(fixture_markets)
            if row:
                comp_data.append(row)
        except Exception:
            continue
    return comp_data


def get_team_list_bet365() -> Dict[str, str]:
    conn = pymysql.connect(host='localhost', user='local', passwd='oeijifjwejfio', db=db_name)
    cur = conn.cursor()
    try:
        cur.execute("select bet365_name,betfair_name from bet365_teams")
    except Exception:
        conn.close()
        return {}
    rows = cur.fetchall()
    teams: Dict[str, str] = {}
    for row in rows:
        teams[row[0].upper()] = row[1]
        teams[strip_accents(row[0]).upper()] = row[1]
    conn.close()
    return teams


def insert_to_database_bet365(t: Dict[str, Any], b: Dict[str, Any], league: str) -> None:
    conn = pymysql.connect(host='localhost', user='local', passwd='oeijifjwejfio', db=db_name)
    cur = conn.cursor()

    bet365_teamnames = list(t['matchup_raw'])
    t1fuzzy, t2fuzzy = 0, 0

    for runner in t['book']:
        if runner[0] == t['matchup'][0]:
            bet365_1_odds = runner[1]
            if runner[2] == 1:
                t1fuzzy = 1
        elif runner[0] == t['matchup'][1]:
            bet365_2_odds = runner[1]
            if runner[2] == 1:
                t2fuzzy = 1
        else:
            bet365_x_odds = runner[1]

    bf_teamnames = list(b['matchup_raw'])
    for runner in b['back_book']:
        if runner[0] == b['matchup'][0]:
            bf_1_last_back_odds = runner[1]
            bf_1_last_back_vol = runner[2]
            bf_1_lowest_back_odds = runner[3]
            bf_1_lowest_back_vol = runner[4]
        elif runner[0] == b['matchup'][1]:
            bf_2_last_back_odds = runner[1]
            bf_2_last_back_vol = runner[2]
            bf_2_lowest_back_odds = runner[3]
            bf_2_lowest_back_vol = runner[4]
        else:
            bf_x_last_back_odds = runner[1]
            bf_x_last_back_vol = runner[2]
            bf_x_lowest_back_odds = runner[3]
            bf_x_lowest_back_vol = runner[4]

    for runner in b['lay_book']:
        if runner[0] == b['matchup'][0]:
            bf_1_lay_odds = runner[1]
            bf_1_lay_vol = runner[2]
        elif runner[0] == b['matchup'][1]:
            bf_2_lay_odds = runner[1]
            bf_2_lay_vol = runner[2]
        else:
            bf_x_lay_odds = runner[1]
            bf_x_lay_vol = runner[2]

    if b['flipped']:
        bet365_1_odds, bet365_2_odds = bet365_2_odds, bet365_1_odds
        bet365_teamnames[0], bet365_teamnames[1] = bet365_teamnames[1], bet365_teamnames[0]

        bf_1_last_back_odds, bf_2_last_back_odds = bf_2_last_back_odds, bf_1_last_back_odds
        bf_1_last_back_vol, bf_2_last_back_vol = bf_2_last_back_vol, bf_1_last_back_vol
        bf_1_lowest_back_odds, bf_2_lowest_back_odds = bf_2_lowest_back_odds, bf_1_lowest_back_odds
        bf_1_lowest_back_vol, bf_2_lowest_back_vol = bf_2_lowest_back_vol, bf_1_lowest_back_vol
        bf_1_lay_odds, bf_2_lay_odds = bf_2_lay_odds, bf_1_lay_odds
        bf_1_lay_vol, bf_2_lay_vol = bf_2_lay_vol, bf_1_lay_vol
        bf_teamnames[0], bf_teamnames[1] = bf_teamnames[1], bf_teamnames[0]
        t1fuzzy, t2fuzzy = t2fuzzy, t1fuzzy

    odds_json = {
        "bet365_1_odds": bet365_1_odds,
        "bet365_x_odds": bet365_x_odds,
        "bet365_2_odds": bet365_2_odds,
        "bf_1_odds": {
            "vwap": b['vwaps']['1'],
            "last_back_price": bf_1_last_back_odds,
            "last_back_vol": bf_1_last_back_vol,
            "lowest_back_price": bf_1_lowest_back_odds,
            "lowest_back_vol": bf_1_lowest_back_vol,
            "lay_price": bf_1_lay_odds,
            "lay_vol": bf_1_lay_vol,
        },
        "bf_x_odds": {
            "vwap": b['vwaps']['X'],
            "last_back_price": bf_x_last_back_odds,
            "last_back_vol": bf_x_last_back_vol,
            "lowest_back_price": bf_x_lowest_back_odds,
            "lowest_back_vol": bf_x_lowest_back_vol,
            "lay_price": bf_x_lay_odds,
            "lay_vol": bf_x_lay_vol,
        },
        "bf_2_odds": {
            "vwap": b['vwaps']['2'],
            "last_back_price": bf_2_last_back_odds,
            "last_back_vol": bf_2_last_back_vol,
            "lowest_back_price": bf_2_lowest_back_odds,
            "lowest_back_vol": bf_2_lowest_back_vol,
            "lay_price": bf_2_lay_odds,
            "lay_vol": bf_2_lay_vol,
        },
    }

    cur.execute(
        "select * from bet365_matches where bet365_event_id=%s and betfair_event_id=%s",
        (t['event_id'], b['event_id']),
    )
    rows = cur.fetchall()
    if rows:
        cur.execute(
            "update bet365_matches set flipped=%s,timestamp=%s,bet365_data=%s,t1_bet365_fuzzy=%s,t2_bet365_fuzzy=%s where bet365_event_id=%s and betfair_event_id=%s",
            (b['flipped'], b['timestamp'], json.dumps(odds_json), t1fuzzy, t2fuzzy, t['event_id'], b['event_id']),
        )
    else:
        if fuzz.ratio(bet365_teamnames[0], bf_teamnames[0]) <= fuzz.ratio(bet365_teamnames[0], bf_teamnames[1]):
            bet365_teamnames[0], bet365_teamnames[1] = bet365_teamnames[1], bet365_teamnames[0]

        cur.execute(
            "insert into bet365_matches (timestamp,bet365_event_id,betfair_event_id,team_1_bet365,team_2_bet365,team_1_betfair,team_2_betfair,bet365_data,t1_bet365_fuzzy,t2_bet365_fuzzy,ignored,league,flipped) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                b['timestamp'],
                t['event_id'],
                b['event_id'],
                bet365_teamnames[0],
                bet365_teamnames[1],
                bf_teamnames[0],
                bf_teamnames[1],
                json.dumps(odds_json),
                t1fuzzy,
                t2fuzzy,
                0,
                league,
                b['flipped'],
            ),
        )
    conn.commit()
    conn.close()


def align_matches(book_data: List[Dict[str, Any]], ref_data: List[Dict[str, Any]], league: str) -> None:
    books_left: List[Dict[str, Any]] = []

    for bd in book_data:
        found = False
        if not bd['book']:
            continue
        for rd in ref_data:
            if abs(convert_string_timestamp(bd['start_time']) - convert_string_timestamp(rd['start_time'])) <= 0:
                rd_teams_raw = [rd['matchup'][0], rd['matchup'][1]]
                rd_teams = [rd['matchup'][0].lower(), rd['matchup'][1].lower()]
                book_names_lower = [bd['book'][0]['name'].lower(), bd['book'][1]['name'].lower(), bd['book'][2]['name'].lower()]
                book_names = [bd['book'][0]['name'], bd['book'][1]['name'], bd['book'][2]['name']]

                if book_names_lower[0] in {"x", "draw"}:
                    draw_index = 0
                if book_names_lower[1] in {"x", "draw"}:
                    draw_index = 1
                if book_names_lower[2] in {"x", "draw"}:
                    draw_index = 2

                book_names_lower = remove_draw(book_names_lower)
                book_names = remove_draw(book_names)

                if len(set(book_names_lower).intersection(set(rd_teams))) > 0:
                    found = True
                    ref_data.remove(rd)
                    if book_names_lower[0] == rd_teams[0]:
                        match_data = [
                            [rd_teams_raw[0], bd['book'][0]['price'], 0],
                            ["X", bd['book'][draw_index]['price'], 0],
                            [rd_teams_raw[1], bd['book'][2]['price'], 0],
                        ]
                    else:
                        match_data = [
                            [rd_teams_raw[1], bd['book'][0]['price'], 0],
                            ["X", bd['book'][draw_index]['price'], 0],
                            [rd_teams_raw[0], bd['book'][2]['price'], 0],
                        ]

                    book_names.sort()
                    rd_teams_raw.sort()
                    tt = {
                        "matchup": rd_teams_raw,
                        "matchup_raw": book_names,
                        "book": match_data,
                        "markets": bd['markets'],
                        "event_id": bd['id'],
                        "start_time": bd['start_time'],
                    }
                    insert_to_database_bet365(tt, rd, league)
                    break
        if not found:
            books_left.append(bd)

    for bd in books_left:
        if not bd['book']:
            continue
        for rd in ref_data:
            if abs(convert_string_timestamp(bd['start_time']) - convert_string_timestamp(rd['start_time'])) <= 0:
                rd_teams_raw = [rd['matchup'][0], rd['matchup'][1]]
                rd_teams = [rd['matchup'][0].lower(), rd['matchup'][1].lower()]
                book_names_lower = [bd['book'][0]['name'].lower(), bd['book'][1]['name'].lower(), bd['book'][2]['name'].lower()]
                book_names = [bd['book'][0]['name'], bd['book'][1]['name'], bd['book'][2]['name']]

                if book_names_lower[0] in {"x", "draw"}:
                    draw_index = 0
                if book_names_lower[1] in {"x", "draw"}:
                    draw_index = 1
                if book_names_lower[2] in {"x", "draw"}:
                    draw_index = 2

                book_names_lower = remove_draw(book_names_lower)
                book_names = remove_draw(book_names)

                r00 = fuzz.ratio(book_names_lower[0], rd_teams[0])
                r01 = fuzz.ratio(book_names_lower[0], rd_teams[1])
                r10 = fuzz.ratio(book_names_lower[1], rd_teams[0])
                r11 = fuzz.ratio(book_names_lower[1], rd_teams[1])
                threshold = 80
                if (
                    (r00 > threshold or book_names_lower[0].find(rd_teams[0]) > -1 or rd_teams[0].find(book_names_lower[0]) > -1 or r01 > threshold or book_names_lower[0].find(rd_teams[1]) > -1 or rd_teams[1].find(book_names_lower[0]) > -1)
                    or
                    (r10 > threshold or book_names_lower[1].find(rd_teams[0]) > -1 or rd_teams[0].find(book_names_lower[1]) > -1 or r11 > threshold or book_names_lower[1].find(rd_teams[1]) > -1 or rd_teams[1].find(book_names_lower[1]) > -1)
                ):
                    ref_data.remove(rd)
                    if r00 > r01 or book_names_lower[0].find(rd_teams[0]) > -1 or rd_teams[0].find(book_names_lower[0]) > -1:
                        match_data = [
                            [rd_teams_raw[0], bd['book'][0]['price'], 0],
                            ["X", bd['book'][draw_index]['price'], 1],
                            [rd_teams_raw[1], bd['book'][2]['price'], 1],
                        ]
                    else:
                        match_data = [
                            [rd_teams_raw[1], bd['book'][0]['price'], 1],
                            ["X", bd['book'][draw_index]['price'], 1],
                            [rd_teams_raw[0], bd['book'][2]['price'], 1],
                        ]
                    tt = {
                        "matchup": rd_teams_raw,
                        "matchup_raw": book_names,
                        "book": match_data,
                        "markets": bd['markets'],
                        "event_id": bd['id'],
                        "start_time": bd['start_time'],
                    }
                    insert_to_database_bet365(tt, rd, league)
                    break


def do_insert_bet365(bet365_data: List[Dict[str, Any]], betfair_data: List[Dict[str, Any]], league: str, bet365_teams: Dict[str, str]) -> None:
    try:
        if len(bet365_data) > 0 and len(betfair_data) > 0:
            bf_data = convert_ref_matches(betfair_data)
            align_matches(bet365_data, bf_data, league)
    except Exception as msg:
        print("alignment error:", str(msg))


if __name__ == "__main__":
    test_league = ""
    rows = pull_data_bet365(compid="", league=test_league)
    print(json.dumps(rows[:20], indent=2))
