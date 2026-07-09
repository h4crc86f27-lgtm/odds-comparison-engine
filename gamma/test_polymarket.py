#!/usr/bin/env python3
"""
Polymarket soccer 1X2 upcoming event explorer.

Standalone utility to discover and analyze upcoming soccer 1X2 Match Odds events from Polymarket.
Focuses exclusively on three-way (1X2) outcomes: home win, draw, away win.
No database access. No engine integration. Safe for local testing.

Paginates events by tag_id=100350 (soccer tag) with limit=100 and offset until no more events.
Identifies events with exactly 3 markets: home win, draw, away win.
Filters out non-match market types and non-match market questions.
Includes only events with future endDate (kickoff time).
Sorts by endDate ascending (earliest first).
Uses bestAsk price to calculate decimal odds: decimal_odds = 1 / bestAsk.

Usage:
    python3 gamma/test_polymarket.py

Output:
    - Prints first 20 upcoming 1X2 events with full metadata
    - Prints event ID, endDate, home/away, market IDs, bestAsk prices, decimal odds
    - Saves sorted candidate list to gamma/polymarket_soccer_1x2_events.json
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
        default (float): Value to return on conversion failure (default 0.0)
        
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
    Deduplicates by event_id, keeping first complete record for each id.
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
            print(f"Querying offset={offset}: {url}")
            
            request = urllib.request.Request(
                url,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            
            with urllib.request.urlopen(request, timeout=30) as response:
                events = json.loads(response.read().decode('utf-8'))
            
            print(f"  → {len(events)} events returned")
            
            if not events:
                break
            
            raw_events.extend(events)
            
            # Continue pagination if we got a full batch
            if len(events) < limit:
                break
            
            offset += limit
        
        total_raw = len(raw_events)
        print(f"  → Total raw events fetched: {total_raw}")
        
        # Phase 2: Deduplicate by event_id, keeping first record
        seen_ids = set()
        unique_events = []
        duplicates_removed = 0
        
        for event in raw_events:
            if not isinstance(event, dict):
                continue
            
            event_id = event.get('id')
            if not event_id:
                continue
            
            if event_id in seen_ids:
                duplicates_removed += 1
                continue
            
            seen_ids.add(event_id)
            unique_events.append(event)
        
        total_unique = len(unique_events)
        print(f"  → Unique events after deduplication: {total_unique}")
        print(f"  → Duplicates removed: {duplicates_removed}")
        
        # Phase 3: Filter and identify 1X2 candidates
        candidates = []
        excluded_title = 0
        past_date = 0
        not_1x2 = 0
        
        for event in unique_events:
            title = event.get('title') or event.get('name') or ''
            
            # Check for excluded event titles
            if is_excluded_event_title(title):
                excluded_title += 1
                continue
            
            # Check if event is in the future
            if not is_future_event(event):
                past_date += 1
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
            else:
                not_1x2 += 1
        
        print(f"  → {len(candidates)} 1X2 candidates identified")
        print(f"  → {excluded_title} excluded (non-match titles)")
        print(f"  → {past_date} excluded (past events)")
        print(f"  → {not_1x2} excluded (not 1X2 structure)")
        
        # Sort by endDate ascending (soonest first)
        candidates.sort(key=lambda c: c.get('end_date', ''))
        print(f"  → Sorted by endDate ascending")
        
        return candidates
        
    except urllib.error.URLError as e:
        print(f"  ⚠ Network error: {e}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"  ⚠ Error: {e}", file=sys.stderr)
        return []


def normalize_1x2_candidate(candidate):
    """
    Convert candidate event to JSON-serializable format.
    
    Args:
        candidate (dict): Candidate event dict
        
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
    }


def print_soccer_1x2_events(candidates, limit=20):
    """
    Print soccer 1X2 candidate events with bestAsk and decimal odds.
    
    Args:
        candidates (list): List of candidate event dicts
        limit (int): Maximum events to print
    """
    print(f"\n{'='*100}")
    print(f"Soccer 1X2 Candidate Events (first {min(limit, len(candidates))} of {len(candidates)})")
    print(f"{'='*100}\n")
    
    for i, candidate in enumerate(candidates[:limit], 1):
        event_id = candidate.get('event_id', 'N/A')
        title = candidate.get('title', 'N/A')
        league, home, away = parse_event_title(title)
        markets = candidate.get('markets_1x2', {})
        end_date = candidate.get('end_date', 'N/A')
        
        m1 = markets.get('1', {})
        mx = markets.get('X', {})
        m2 = markets.get('2', {})
        
        ask_1, odds_1 = extract_best_ask_and_odds(m1)
        ask_x, odds_x = extract_best_ask_and_odds(mx)
        ask_2, odds_2 = extract_best_ask_and_odds(m2)
        
        print(f"{i:2d}. Event ID:      {event_id}")
        print(f"    EndDate:        {end_date}")
        print(f"    {home:20s} vs {away}")
        
        print(f"    Market 1 (Home):  {m1.get('id', 'N/A')}")
        print(f"      BestAsk: {ask_1}  Odds: {odds_1:.4f}" if odds_1 else f"      BestAsk: {ask_1}  Odds: None")
        
        print(f"    Market X (Draw): {mx.get('id', 'N/A')}")
        print(f"      BestAsk: {ask_x}  Odds: {odds_x:.4f}" if odds_x else f"      BestAsk: {ask_x}  Odds: None")
        
        print(f"    Market 2 (Away): {m2.get('id', 'N/A')}")
        print(f"      BestAsk: {ask_2}  Odds: {odds_2:.4f}" if odds_2 else f"      BestAsk: {ask_2}  Odds: None")
        
        print()
    
    if len(candidates) > limit:
        print(f"... and {len(candidates) - limit} more")
    
    print(f"{'='*100}\n")


def save_raw_json(data, filepath):
    """
    Save data to JSON file with LF line endings.
    
    Args:
        data (list or dict): Data to save
        filepath (str): Path to output file
        
    Raises:
        Exception: On file write error
    """
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✓ JSON saved to {filepath}")
    except IOError as e:
        raise Exception(f"File write error: {e}") from e


def main():
    """Main exploration workflow."""
    print("Polymarket Soccer 1X2 Upcoming Event Explorer")
    print("=" * 100)
    print("Fetching soccer events and identifying 1X2 match odds...\n")
    
    try:
        # Fetch soccer events with pagination
        candidates = fetch_soccer_1x2_events()
        
        if not candidates:
            print("No 1X2 candidate events found")
            return 1
        
        print()
        
        # Print first 20 candidates
        print_soccer_1x2_events(candidates, limit=20)
        
        # Normalize candidates for JSON output
        normalized = [normalize_1x2_candidate(c) for c in candidates]
        
        # Final deduplication of normalized output by event_id
        seen_event_ids = set()
        unique_normalized = []
        for item in normalized:
            event_id = item.get('event_id')
            if event_id not in seen_event_ids:
                seen_event_ids.add(event_id)
                unique_normalized.append(item)
        
        # Save to JSON
        output_path = "gamma/polymarket_soccer_1x2_events.json"
        save_raw_json(unique_normalized, output_path)
        
        # Print summary
        print(f"{'='*100}")
        print("SUMMARY")
        print(f"{'='*100}")
        print(f"Total 1X2 candidate events: {len(candidates)}")
        print(f"Unique events in JSON output: {len(unique_normalized)}")
        print(f"Saved to: {output_path}")
        print(f"{'='*100}\n")
        
        print(f"✓ Discovery complete")
        return 0
        
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
