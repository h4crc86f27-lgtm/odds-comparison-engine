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
import pymysql
db_name="arb_db_beta"
from datetime import datetime, timezone
from fuzzywuzzy import fuzz


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


def convert_string_timestamp(value):
    """
    Convert ISO-8601 string or numeric timestamp to Unix timestamp.

    Handles:
    - ISO-8601 strings: "2026-07-11T21:00:00Z", "2026-07-11T21:00:00+00:00"
    - Naive ISO strings: treated as UTC
    - Numeric values: returned unchanged as float

    Args:
        value: ISO-8601 string or numeric timestamp

    Returns:
        float: Unix timestamp (seconds since epoch)

    Raises:
        ValueError: If value cannot be parsed as timestamp
    """
    # If already numeric, return as float
    if isinstance(value, (int, float)):
        return float(value)

    # Try to parse as string
    if isinstance(value, str):
        value = value.strip()

        # Try common ISO-8601 formats
        formats = [
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%dT%H:%M:%S%z',
            '%Y-%m-%dT%H:%M:%S.%fZ',
            '%Y-%m-%dT%H:%M:%S.%f%z',
            '%Y-%m-%d %H:%M:%S',
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(value, fmt)
                # If no timezone info, assume UTC
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.timestamp()
            except ValueError:
                continue

        # Try fromisoformat for more flexibility
        try:
            # Replace Z with +00:00 for fromisoformat compatibility
            iso_str = value.replace('Z', '+00:00')
            dt = datetime.fromisoformat(iso_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.timestamp()
        except (ValueError, AttributeError):
            pass

    # Could not parse
    raise ValueError(f"Cannot convert '{value}' to Unix timestamp")


def remove_draw(names):
    """
    Return a new list with draw/X entries removed (case-insensitive).

    Does not mutate the input list.

    Args:
        names (list): List of team/outcome names

    Returns:
        list: New list with entries equal to "x" or "draw" removed (case-insensitive)
    """
    if not names:
        return []

    result = []
    for name in names:
        if name and isinstance(name, str):
            name_lower = name.lower().strip()
            if name_lower not in ('x', 'draw'):
                result.append(name)
        elif name:
            result.append(name)

    return result


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


def convert_polymarket_matches(polymarket_data):
    """
    Convert normalized Polymarket events to legacy provider format for matching.

    Transforms normalized Polymarket events into the event structure expected
    by the legacy provider matcher (matching Live90bet pattern).

    Skips events missing critical fields:
    - event_id, start/end time, home/away team, or 1/X/2 odds

    Args:
        polymarket_data (list): Normalized events from pull_data_polymarket()

    Returns:
        list: Events in legacy format with 'id', 'start_time', 'matchup', 'book', 'markets'
    """
    if not polymarket_data:
        return []

    converted = []

    for event in polymarket_data:
        if not event:
            continue

        # Check required fields
        event_id = event.get('event_id')
        start_time = event.get('end_date')
        home = event.get('home_team')
        away = event.get('away_team')
        odds_1 = event.get('decimal_odds_1')
        odds_x = event.get('decimal_odds_x')
        odds_2 = event.get('decimal_odds_2')

        # Skip if missing critical fields
        if not (event_id and start_time and home and away and odds_1 and odds_x and odds_2):
            continue

        # Build legacy format
        converted_event = {
            'id': event_id,
            'start_time': start_time,
            'matchup': [home, away],
            'book': [
                {'name': home, 'price': odds_1},
                {'name': 'X', 'price': odds_x},
                {'name': away, 'price': odds_2}
            ],
            'markets': event  # Keep original for reference
        }
        converted.append(converted_event)

    return converted


def align_matches(polymarket_data, ref_data, league=None):
    """
    Match Polymarket events against Betfair reference events.

    Two-pass matching strategy:

    Pass 1 (Exact):
    - Exact timestamp equality
    - Both team names match exactly in same orientation (case-insensitive)
    - Direct: poly_home == bf_home AND poly_away == bf_away
    - Flipped: poly_home == bf_away AND poly_away == bf_home

    Pass 2 (Fuzzy):
    - Exact timestamp equality
    - For each orientation, both teams >= 80 (fuzz.ratio)
    - Substring containment can upgrade individual score to 100
    - Choose best candidate by highest minimum team score, then average

    Returns list of matched pairs (no insert calls, read-only).
    Does not mutate caller's ref_data or polymarket_data.

    Args:
        polymarket_data (list): Normalized Polymarket events
        ref_data (list): Betfair reference events (from convert_ref_matches)
        league (str, optional): For compatibility, not used

    Returns:
        list: Matched pairs with fields:
            polymarket_event_id, betfair_event_id,
            polymarket_home, polymarket_away,
            betfair_home, betfair_away,
            home_fuzzy, away_fuzzy, flipped,
            polymarket_data, betfair_data
    """
    if not polymarket_data or not ref_data:
        return []

    matched = []
    used_bf_indices = set()

    # Pass 1: Exact timestamp + exact team match (both teams must match)
    for poly_event in polymarket_data:
        if not poly_event:
            continue

        poly_id = poly_event.get('event_id')
        poly_time_str = poly_event.get('end_date')
        poly_home = poly_event.get('home_team')
        poly_away = poly_event.get('away_team')

        # Skip malformed events
        if not (poly_id and poly_time_str and poly_home and poly_away):
            continue

        # Parse Polymarket timestamp
        try:
            poly_ts = convert_string_timestamp(poly_time_str)
        except:
            continue

        poly_home_lower = poly_home.lower()
        poly_away_lower = poly_away.lower()

        # Find exact match
        for bf_idx, bf_event in enumerate(ref_data):
            if bf_idx in used_bf_indices or not bf_event:
                continue

            # Parse Betfair timestamp
            bf_time_str = bf_event.get('start_time') or bf_event.get('openDate') or bf_event.get('matchTime')
            if not bf_time_str:
                continue

            try:
                bf_ts = convert_string_timestamp(bf_time_str)
            except:
                continue

            # Exact timestamp match required
            if poly_ts != bf_ts:
                continue

            # Extract Betfair team names
            bf_matchup = bf_event.get('matchup')
            if not bf_matchup or len(bf_matchup) != 2 or not bf_matchup[0] or not bf_matchup[1]:
                continue

            bf_home = bf_matchup[0]
            bf_away = bf_matchup[1]
            bf_home_lower = bf_home.lower()
            bf_away_lower = bf_away.lower()

            # Check direct orientation (both teams must match)
            if poly_home_lower == bf_home_lower and poly_away_lower == bf_away_lower:
                matched.append({
                    'polymarket_event_id': poly_id,
                    'betfair_event_id': bf_event.get('id') or bf_event.get('event_id') or '',
                    'polymarket_home': poly_home,
                    'polymarket_away': poly_away,
                    'betfair_home': bf_home,
                    'betfair_away': bf_away,
                    'home_fuzzy': 100,
                    'away_fuzzy': 100,
                    'flipped': False,
                    'polymarket_data': poly_event,
                    'betfair_data': bf_event
                })
                used_bf_indices.add(bf_idx)
                break

            # Check flipped orientation (both teams must match)
            if poly_home_lower == bf_away_lower and poly_away_lower == bf_home_lower:
                matched.append({
                    'polymarket_event_id': poly_id,
                    'betfair_event_id': bf_event.get('id') or bf_event.get('event_id') or '',
                    'polymarket_home': poly_home,
                    'polymarket_away': poly_away,
                    'betfair_home': bf_home,
                    'betfair_away': bf_away,
                    'home_fuzzy': 100,
                    'away_fuzzy': 100,
                    'flipped': True,
                    'polymarket_data': poly_event,
                    'betfair_data': bf_event
                })
                used_bf_indices.add(bf_idx)
                break

    # Pass 2: Fuzzy matching on unmatched events
    for poly_event in polymarket_data:
        if not poly_event:
            continue

        poly_id = poly_event.get('event_id')

        # Skip if already matched
        if any(m['polymarket_event_id'] == poly_id for m in matched):
            continue

        poly_time_str = poly_event.get('end_date')
        poly_home = poly_event.get('home_team')
        poly_away = poly_event.get('away_team')

        # Skip malformed events
        if not (poly_id and poly_time_str and poly_home and poly_away):
            continue

        # Parse Polymarket timestamp
        try:
            poly_ts = convert_string_timestamp(poly_time_str)
        except:
            continue

        poly_home_lower = poly_home.lower()
        poly_away_lower = poly_away.lower()

        best_match = None
        best_bf_idx = -1
        best_min_score = -1
        best_avg_score = -1
        best_flipped = False
        best_home_score = 0
        best_away_score = 0

        # Find best fuzzy match
        for bf_idx, bf_event in enumerate(ref_data):
            if bf_idx in used_bf_indices or not bf_event:
                continue

            # Parse Betfair timestamp
            bf_time_str = bf_event.get('start_time') or bf_event.get('openDate') or bf_event.get('matchTime')
            if not bf_time_str:
                continue

            try:
                bf_ts = convert_string_timestamp(bf_time_str)
            except:
                continue

            # Exact timestamp match required
            if poly_ts != bf_ts:
                continue

            # Extract Betfair team names
            bf_matchup = bf_event.get('matchup')
            if not bf_matchup or len(bf_matchup) != 2 or not bf_matchup[0] or not bf_matchup[1]:
                continue

            bf_home = bf_matchup[0]
            bf_away = bf_matchup[1]
            bf_home_lower = bf_home.lower()
            bf_away_lower = bf_away.lower()

            # Calculate fuzzy scores for direct orientation
            direct_home = fuzz.ratio(poly_home_lower, bf_home_lower)
            direct_away = fuzz.ratio(poly_away_lower, bf_away_lower)

            # Substring containment can upgrade to 100
            if poly_home_lower in bf_home_lower or bf_home_lower in poly_home_lower:
                direct_home = 100
            if poly_away_lower in bf_away_lower or bf_away_lower in poly_away_lower:
                direct_away = 100

            # Check if direct is valid (both >= 80)
            if direct_home >= 80 and direct_away >= 80:
                min_score = min(direct_home, direct_away)
                avg_score = (direct_home + direct_away) / 2.0

                # Update best if this is better
                if (min_score > best_min_score or
                    (min_score == best_min_score and avg_score > best_avg_score)):
                    best_match = bf_event
                    best_bf_idx = bf_idx
                    best_min_score = min_score
                    best_avg_score = avg_score
                    best_flipped = False
                    best_home_score = direct_home
                    best_away_score = direct_away

            # Calculate fuzzy scores for flipped orientation
            flipped_home = fuzz.ratio(poly_home_lower, bf_away_lower)
            flipped_away = fuzz.ratio(poly_away_lower, bf_home_lower)

            # Substring containment can upgrade to 100
            if poly_home_lower in bf_away_lower or bf_away_lower in poly_home_lower:
                flipped_home = 100
            if poly_away_lower in bf_home_lower or bf_home_lower in poly_away_lower:
                flipped_away = 100

            # Check if flipped is valid (both >= 80)
            if flipped_home >= 80 and flipped_away >= 80:
                min_score = min(flipped_home, flipped_away)
                avg_score = (flipped_home + flipped_away) / 2.0

                # Update best if this is better
                if (min_score > best_min_score or
                    (min_score == best_min_score and avg_score > best_avg_score)):
                    best_match = bf_event
                    best_bf_idx = bf_idx
                    best_min_score = min_score
                    best_avg_score = avg_score
                    best_flipped = True
                    best_home_score = flipped_home
                    best_away_score = flipped_away

        # Add best match if found
        if best_match:
            bf_home = best_match['matchup'][0]
            bf_away = best_match['matchup'][1]

            matched.append({
                'polymarket_event_id': poly_id,
                'betfair_event_id': best_match.get('id') or best_match.get('event_id') or '',
                'polymarket_home': poly_home,
                'polymarket_away': poly_away,
                'betfair_home': bf_home,
                'betfair_away': bf_away,
                'home_fuzzy': int(best_home_score),
                'away_fuzzy': int(best_away_score),
                'flipped': best_flipped,
                'polymarket_data': poly_event,
                'betfair_data': best_match
            })
            used_bf_indices.add(best_bf_idx)

    return matched



def insert_to_database_polymarket(matched_event, league):
    """
    Write or update a matched Polymarket/Betfair event pair in polymarket_matches.

    Unpacks Polymarket 1X2 odds and Betfair odds from the matched event,
    applies home/away flip correction if needed, assembles the full odds JSON,
    then either updates an existing row or inserts a new one.

    Args:
        matched_event (dict): Single matched event from align_matches() with:
            - polymarket_event_id, betfair_event_id
            - polymarket_home, polymarket_away
            - betfair_home, betfair_away
            - home_fuzzy, away_fuzzy (stored as t1_polymarket_fuzzy, t2_polymarket_fuzzy)
            - flipped (bool): whether teams are in reversed order
            - polymarket_data: normalized Polymarket event dict
            - betfair_data: Betfair reference data dict
        league (str): Sport/league identifier for the match
    """
    try:
        conn = pymysql.connect(host='localhost', user='local', passwd='oeijifjwejfio', db=db_name)
        cur = conn.cursor()

        # Extract matched event identifiers
        poly_event_id = matched_event.get('polymarket_event_id')
        bf_event_id = matched_event.get('betfair_event_id')
        flipped = matched_event.get('flipped', False)
        home_fuzzy = matched_event.get('home_fuzzy', 0)
        away_fuzzy = matched_event.get('away_fuzzy', 0)

        # Extract Polymarket data
        poly_data = matched_event.get('polymarket_data', {})
        poly_home = matched_event.get('polymarket_home')
        poly_away = matched_event.get('polymarket_away')
        poly_1_odds = poly_data.get('decimal_odds_1', 0)
        poly_x_odds = poly_data.get('decimal_odds_x', 0)
        poly_2_odds = poly_data.get('decimal_odds_2', 0)

        # Extract Betfair data
        bf_data = matched_event.get('betfair_data', {})
        bf_home = matched_event.get('betfair_home')
        bf_away = matched_event.get('betfair_away')
        bf_timestamp = bf_data.get('timestamp', 0)

        # Extract Betfair back/lay odds (1X2 match result)
        bf_back_book = bf_data.get('back_book', [])
        bf_lay_book = bf_data.get('lay_book', [])

        bf_1_last_back_odds = 0
        bf_1_last_back_vol = 0
        bf_1_lowest_back_odds = 0
        bf_1_lowest_back_vol = 0
        bf_1_lay_odds = 0
        bf_1_lay_vol = 0

        bf_x_last_back_odds = 0
        bf_x_last_back_vol = 0
        bf_x_lowest_back_odds = 0
        bf_x_lowest_back_vol = 0
        bf_x_lay_odds = 0
        bf_x_lay_vol = 0

        bf_2_last_back_odds = 0
        bf_2_last_back_vol = 0
        bf_2_lowest_back_odds = 0
        bf_2_lowest_back_vol = 0
        bf_2_lay_odds = 0
        bf_2_lay_vol = 0

        # Parse Betfair back odds for 1X2
        for runner in bf_back_book:
            if runner[0] == bf_home:
                bf_1_last_back_odds = runner[1]
                bf_1_last_back_vol = runner[2]
                bf_1_lowest_back_odds = runner[3]
                bf_1_lowest_back_vol = runner[4]
            elif runner[0] == bf_away:
                bf_2_last_back_odds = runner[1]
                bf_2_last_back_vol = runner[2]
                bf_2_lowest_back_odds = runner[3]
                bf_2_lowest_back_vol = runner[4]
            else:
                bf_x_last_back_odds = runner[1]
                bf_x_last_back_vol = runner[2]
                bf_x_lowest_back_odds = runner[3]
                bf_x_lowest_back_vol = runner[4]

        # Parse Betfair lay odds for 1X2
        for runner in bf_lay_book:
            if runner[0] == bf_home:
                bf_1_lay_odds = runner[1]
                bf_1_lay_vol = runner[2]
            elif runner[0] == bf_away:
                bf_2_lay_odds = runner[1]
                bf_2_lay_vol = runner[2]
            else:
                bf_x_lay_odds = runner[1]
                bf_x_lay_vol = runner[2]

        # Handle flipped orientation
        poly_teamnames = [poly_home, poly_away]
        bf_teamnames = [bf_home, bf_away]

        if flipped:
            # Flip Polymarket side only (reorder to match Betfair reference orientation)
            temp = poly_1_odds
            poly_1_odds = poly_2_odds
            poly_2_odds = temp

            temp = poly_teamnames[0]
            poly_teamnames[0] = poly_teamnames[1]
            poly_teamnames[1] = temp

        # Build odds JSON (1X2 only for Polymarket)
        odds_json = {
            "polymarket_1_odds": poly_1_odds,
            "polymarket_x_odds": poly_x_odds,
            "polymarket_2_odds": poly_2_odds,
            "bf_1_odds": {
                "vwap": bf_data.get('vwaps', {}).get('1', 0),
                "last_back_price": bf_1_last_back_odds,
                "last_back_vol": bf_1_last_back_vol,
                "lowest_back_price": bf_1_lowest_back_odds,
                "lowest_back_vol": bf_1_lowest_back_vol,
                "lay_price": bf_1_lay_odds,
                "lay_vol": bf_1_lay_vol
            },
            "bf_x_odds": {
                "vwap": bf_data.get('vwaps', {}).get('X', 0),
                "last_back_price": bf_x_last_back_odds,
                "last_back_vol": bf_x_last_back_vol,
                "lowest_back_price": bf_x_lowest_back_odds,
                "lowest_back_vol": bf_x_lowest_back_vol,
                "lay_price": bf_x_lay_odds,
                "lay_vol": bf_x_lay_vol
            },
            "bf_2_odds": {
                "vwap": bf_data.get('vwaps', {}).get('2', 0),
                "last_back_price": bf_2_last_back_odds,
                "last_back_vol": bf_2_last_back_vol,
                "lowest_back_price": bf_2_lowest_back_odds,
                "lowest_back_vol": bf_2_lowest_back_vol,
                "lay_price": bf_2_lay_odds,
                "lay_vol": bf_2_lay_vol
            }
        }

        # Check for existing event
        cur.execute(
            "select * from polymarket_matches where polymarket_event_id=%s and betfair_event_id=%s",
            (poly_event_id, bf_event_id)
        )
        rows = cur.fetchall()

        if len(rows) > 0:
            # Update existing record
            cur.execute(
                "update polymarket_matches set timestamp=%s,polymarket_data=%s,t1_polymarket_fuzzy=%s,t2_polymarket_fuzzy=%s where polymarket_event_id=%s and betfair_event_id=%s",
                (bf_timestamp, json.dumps(odds_json), home_fuzzy, away_fuzzy, poly_event_id, bf_event_id)
            )
        else:
            # Insert new record
            cur.execute(
                "insert into polymarket_matches (timestamp,polymarket_event_id,betfair_event_id,team_1_polymarket,team_2_polymarket,team_1_betfair,team_2_betfair,polymarket_data,t1_polymarket_fuzzy,t2_polymarket_fuzzy,ignored,league) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (bf_timestamp, poly_event_id, bf_event_id, poly_teamnames[0], poly_teamnames[1], bf_teamnames[0], bf_teamnames[1], json.dumps(odds_json), home_fuzzy, away_fuzzy, 0, league)
            )

        conn.commit()
        conn.close()

    except Exception as e:
        print(f"Error inserting Polymarket match: {str(e)}")


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

