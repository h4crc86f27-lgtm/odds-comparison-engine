"""
Polymarket provider module.

Responsibilities:
- Fetch event data and odds from Polymarket API
- Match Polymarket events against Betfair reference events
- Transform and normalize Polymarket data to internal format
- Insert matched events and odds into database

Implements read-only Polymarket soccer 1X2 fetch and normalization.
No database writes. No staging. Feature branch only.
"""

import json
import urllib.request
import urllib.error
import sys
from datetime import datetime, timezone


def safe_float(value, default=0.0):
    """
    Safely convert a value to float with fallback.
    
    Args:
        value: Value to convert (may be string, int, float, or None)
        default (float): Value to return on conversion failure
        
    Returns:
        float: Converted numeric value or default
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_event_title(title):
    """
    Parse event title to extract league, home team, and away team.
    
    Handles league prefix separated by colon:
        "EPL: Tottenham vs Everton" → ("EPL", "Tottenham", "Everton")
    
    Args:
        title (str): Event title
        
    Returns:
        tuple: (league, home_team, away_team) or ("", "", "") if parsing fails
    """
    if not title:
        return ("", "", "")
    
    league = ""
    text = title
    
    # Extract league prefix if present (before colon)
    if ':' in title:
        parts = title.split(':', 1)
        league = parts[0].strip()
        text = parts[1].strip()
    
    # Common separators for vs matches
    separators = [" vs ", " v ", " vs. ", " vs, ", " at "]
    for sep in separators:
        if sep in text:
            parts = text.split(sep, 1)
            if len(parts) == 2:
                home = parts[0].strip()
                away = parts[1].strip()
                return (league, home, away)
    
    return ("", "", "")


def is_excluded_event_title(title):
    """
    Check if event title contains keywords indicating non-1X2 match markets.
    
    Excludes: Second Half Result, Halftime, More Markets, Exact Score, Winner, Qualify,
    Golden Boot, Player of the Year, Coach of the Year, Ballon
    
    Args:
        title (str): Event title to check
        
    Returns:
        bool: True if title should be excluded
    """
    if not title:
        return False
    
    title_lower = title.lower()
    
    excluded_keywords = [
        'second half result',
        'halftime',
        'more markets',
        'exact score',
        'winner',
        'qualify',
        'golden boot',
        'player of the year',
        'coach of the year',
        'ballon',
    ]
    
    for keyword in excluded_keywords:
        if keyword in title_lower:
            return True
    
    return False


def is_excluded_market_question(question):
    """
    Check if market question contains keywords indicating non-1X2 markets.
    
    Excludes: second half, halftime, exact score, spread, over, under
    
    Args:
        question (str): Market question to check
        
    Returns:
        bool: True if question should be excluded
    """
    if not question:
        return False
    
    question_lower = question.lower()
    
    excluded_keywords = [
        'second half',
        'halftime',
        'exact score',
        'spread',
        'over ',
        'under ',
    ]
    
    for keyword in excluded_keywords:
        if keyword in question_lower:
            return True
    
    return False


def is_future_event(event):
    """
    Check if event's endDate is in the future.
    
    Args:
        event (dict): Event dict with endDate field
        
    Returns:
        bool: True if endDate is in the future
    """
    end_date_str = event.get('endDate') or event.get('endDateIso') or event.get('end')
    
    if not end_date_str:
        return False
    
    try:
        # Parse ISO format date
        if end_date_str.endswith('Z'):
            end_date_str = end_date_str[:-1] + '+00:00'
        
        try:
            end_date = datetime.fromisoformat(end_date_str)
        except (ValueError, TypeError):
            end_date = datetime.fromisoformat(end_date_str.replace('Z', ''))
            end_date = end_date.replace(tzinfo=timezone.utc)
        
        now = datetime.now(timezone.utc)
        
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)
        
        return end_date > now
        
    except Exception:
        return False


def identify_1x2_markets(event):
    """
    Identify 1X2 (three-way) markets within an event.
    
    Looks for exactly 3 markets: home win, draw, away win.
    Uses market questions to classify:
    - "draw" → draw market
    - "beat" or "win" → home/away win markets
    
    Filters out market questions containing excluded keywords.
    
    Args:
        event (dict): Event dict with 'markets' field
        
    Returns:
        dict or None: Dict with keys '1', 'X', '2' (market dicts) or None if not 1X2
    """
    markets = event.get('markets', [])
    
    if not markets or len(markets) != 3:
        return None
    
    draw_market = None
    win_markets = []
    
    for market in markets:
        question = market.get('question', '')
        
        # Skip if question contains excluded keywords
        if is_excluded_market_question(question):
            return None
        
        question_lower = question.lower()
        
        if 'draw' in question_lower:
            draw_market = market
        elif 'beat' in question_lower or 'win' in question_lower:
            win_markets.append(market)
    
    # Valid 1X2 has exactly 1 draw and 2 win markets
    if draw_market and len(win_markets) == 2:
        # Order win markets: first is home, second is away
        return {
            '1': win_markets[0],
            'X': draw_market,
            '2': win_markets[1]
        }
    
    return None


def extract_best_ask_and_odds(market):
    """
    Extract bestAsk price from market and calculate decimal odds.
    
    decimal_odds = 1 / bestAsk
    
    Args:
        market (dict): Market dict
        
    Returns:
        tuple: (best_ask, decimal_odds) or (None, None) if not available
    """
    if not market:
        return (None, None)
    
    best_ask = market.get('bestAsk')
    
    if best_ask is None:
        return (None, None)
    
    try:
        best_ask_float = float(best_ask)
        if best_ask_float <= 0:
            return (None, None)
        decimal_odds = 1.0 / best_ask_float
        return (best_ask_float, decimal_odds)
    except (TypeError, ValueError):
        return (None, None)


def fetch_soccer_1x2_events():
    """
    Fetch events from tag_id=100350 (soccer tag) with pagination.
    
    Paginates with limit=100 and offset until no more events.
    Deduplicates by event_id, keeping first record for each id.
    Filters:
    - Excludes non-match event titles
    - Includes only events with future endDate
    - Identifies exactly 1X2 (3 markets: 1, X, 2)
    - Filters out non-match market questions
    - Sorts by endDate ascending (soonest first)
    
    Returns:
        list: List of candidate event dicts sorted by endDate
    """
    base_url = "https://gamma-api.polymarket.com/events"
    raw_events = []
    offset = 0
    limit = 100
    
    try:
        # Phase 1: Fetch all raw events with pagination
        while True:
            url = f"{base_url}?tag_id=100350&active=true&closed=false&limit={limit}&offset={offset}"
            
            request = urllib.request.Request(
                url,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            
            with urllib.request.urlopen(request, timeout=30) as response:
                events = json.loads(response.read().decode('utf-8'))
            
            if not events:
                break
            
            raw_events.extend(events)
            
            # Continue pagination if we got a full batch
            if len(events) < limit:
                break
            
            offset += limit
        
        # Phase 2: Deduplicate by event_id, keeping first record
        seen_ids = set()
        unique_events = []
        
        for event in raw_events:
            if not isinstance(event, dict):
                continue
            
            event_id = event.get('id')
            if not event_id:
                continue
            
            if event_id in seen_ids:
                continue
            
            seen_ids.add(event_id)
            unique_events.append(event)
        
        # Phase 3: Filter and identify 1X2 candidates
        candidates = []
        
        for event in unique_events:
            title = event.get('title') or event.get('name') or ''
            
            # Check for excluded event titles
            if is_excluded_event_title(title):
                continue
            
            # Check if event is in the future
            if not is_future_event(event):
                continue
            
            markets_1x2 = identify_1x2_markets(event)
            if markets_1x2:
                # Add 1X2 market info to event
                candidate = {
                    'event_id': event.get('id'),
                    'end_date': event.get('endDate') or event.get('endDateIso') or '',
                    'title': title,
                    'markets_1x2': markets_1x2,
                    'raw': event
                }
                candidates.append(candidate)
        
        # Sort by endDate ascending (soonest first)
        candidates.sort(key=lambda c: c.get('end_date', ''))
        
        return candidates
        
    except urllib.error.URLError as e:
        return []
    except Exception as e:
        return []


def event_has_series_id(event, comp_id):
    """
    Check if an event's series list contains a specific series ID.
    
    Compares series IDs as strings. Handles series as list of dicts or list of strings.
    
    Args:
        event (dict): Raw Polymarket event dict
        comp_id (str): Polymarket series ID to search for
        
    Returns:
        bool: True if comp_id is found in event's series list
    """
    if not event or not comp_id:
        return False
    
    series = event.get('series', [])
    if not series:
        return False
    
    # Series can be list of dicts with 'id' or list of strings
    for item in series:
        if isinstance(item, dict):
            item_id = item.get('id')
        else:
            item_id = item
        
        if str(item_id) == str(comp_id):
            return True
    
    return False


def normalize_1x2_candidate(candidate):
    """
    Convert candidate event to normalized dictionary format.
    
    Extracts Polymarket series metadata from raw event if available.
    
    Args:
        candidate (dict): Candidate event dict from fetch_soccer_1x2_events()
        
    Returns:
        dict: Normalized candidate with extracted fields
    """
    markets = candidate.get('markets_1x2', {})
    league, home, away = parse_event_title(candidate.get('title', ''))
    
    m1 = markets.get('1', {})
    mx = markets.get('X', {})
    m2 = markets.get('2', {})
    
    ask_1, odds_1 = extract_best_ask_and_odds(m1)
    ask_x, odds_x = extract_best_ask_and_odds(mx)
    ask_2, odds_2 = extract_best_ask_and_odds(m2)
    
    # Extract Polymarket series metadata from raw event
    raw_event = candidate.get('raw', {})
    series = raw_event.get('series', [])
    comp_name = ''
    comp_id = ''
    series_slug = ''
    sport_code = ''
    
    if series and isinstance(series, list) and len(series) > 0:
        first_series = series[0]
        if isinstance(first_series, dict):
            comp_name = first_series.get('title', '')
            comp_id = first_series.get('id', '')
            series_slug = first_series.get('slug', '')
    
    # Extract sport code from event metadata
    sport = raw_event.get('sport', {})
    if isinstance(sport, dict):
        sport_code = sport.get('sport')
    
    return {
        'event_id': candidate.get('event_id'),
        'end_date': candidate.get('end_date'),
        'title': candidate.get('title'),
        'league': league,
        'home_team': home,
        'away_team': away,
        'market_1_id': m1.get('id'),
        'market_x_id': mx.get('id'),
        'market_2_id': m2.get('id'),
        'best_ask_1': ask_1,
        'best_ask_x': ask_x,
        'best_ask_2': ask_2,
        'decimal_odds_1': odds_1,
        'decimal_odds_x': odds_x,
        'decimal_odds_2': odds_2,
        'polymarket_comp_name': comp_name,
        'polymarket_comp_id': comp_id,
        'polymarket_series_slug': series_slug,
        'polymarket_sport_code': sport_code,
    }


def pull_data_polymarket(comp_id=None, league=None):
    """
    Fetch event and market data from Polymarket API.
    
    Returns normalized list of upcoming soccer 1X2 events with best ask prices
    and calculated decimal odds.
    
    When comp_id is provided, filters results to events belonging to that
    Polymarket series only. Comparison is string-based.
    
    Args:
        comp_id (str, optional): Polymarket series ID to filter by. When provided,
                                  only returns events belonging to this series.
                                  Defaults to None (returns all upcoming soccer events).
        league (str, optional): Sport/league identifier. Accepted for compatibility
                               with existing provider calling pattern but not used
                               for API filtering. Defaults to None.
    
    Returns:
        list: List of normalized event dicts with soccer 1X2 odds
    """
    candidates = fetch_soccer_1x2_events()
    
    if not candidates:
        return []
    
    # Normalize candidates for output
    normalized = [normalize_1x2_candidate(c) for c in candidates]
    
    # Final deduplication by event_id
    seen_event_ids = set()
    unique_normalized = []
    for item in normalized:
        event_id = item.get('event_id')
        if event_id not in seen_event_ids:
            seen_event_ids.add(event_id)
            unique_normalized.append(item)
    
    # Filter by comp_id (series ID) if provided
    if comp_id:
        filtered = []
        for item in unique_normalized:
            if str(item.get('polymarket_comp_id')) == str(comp_id):
                filtered.append(item)
        return filtered
    
    return unique_normalized


def align_matches(polymarket_data, betfair_events):
    """
    Match Polymarket events against Betfair reference events.
    
    Args:
        polymarket_data (dict): Market data from Polymarket API
        betfair_events (dict): Reference event data from Betfair
    
    Intended behavior (not yet implemented):
    - Use event name and timestamp to find corresponding Betfair events
    - Apply fuzzy matching with threshold for name similarity
    - Build alignment mapping: polymarket_event_id -> betfair_event_id
    
    Currently: stub returning empty dict
    """
    return {}


def insert_to_database_polymarket(matched_events):
    """
    Insert matched Polymarket events and odds into database.
    
    Args:
        matched_events (dict): Aligned event and odds data
    
    Intended behavior (not yet implemented):
    - Connect to arb_db_beta database
    - Insert event records and odds into comparison tables
    - Handle upserts for existing events
    - Write odds history for trend tracking
    
    Currently: stub performing no database operations
    """
    pass


def do_insert_polymarket(league, raw_data):
    """
    Orchestrate insert workflow for a specific league.
    
    Args:
        league (str): Sport/league identifier (e.g., 'football', 'tennis')
        raw_data (dict): Raw API data for league
    
    Intended behavior (not yet implemented):
    - Validate raw data structure
    - Transform to internal format
    - Match against Betfair events
    - Call insert_to_database_polymarket() with matched data
    
    Currently: stub performing no operations
    """
    pass

