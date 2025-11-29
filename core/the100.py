# -*- coding: utf-8 -*-
"""
The 100 League - Standings with Captain/Chip
Fetches official standings + picks for top managers
"""

import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from datetime import datetime
import time

# Configuration
THE100_LEAGUE_ID = 8921
TIMEOUT = 15
MAX_PICKS_FETCH = 150  # Fetch picks only for top 150 (memory safe)
MAX_WORKERS = 8

# Last season winner - auto-qualifies regardless of position
WINNER_ENTRY_ID = 49250

# Simple cache
_cache = {
    'data': None,
    'timestamp': 0,
    'ttl': 120  # Cache for 2 minutes
}

def get_cookies():
    return {
        'sessionid': os.environ.get('FPL_SESSION_ID', ''),
        'csrftoken': os.environ.get('FPL_CSRF_TOKEN', '')
    }

def fetch_json(url, cookies=None):
    """Simple fetch with timeout"""
    try:
        r = requests.get(url, cookies=cookies, timeout=TIMEOUT)
        if r.status_code == 200:
            return r.json()
        return None
    except Exception as e:
        print(f"Fetch error: {e}")
        return None

def get_chip_display(chip):
    """Get chip emoji"""
    chips = {
        'wildcard': '🃏',
        'freehit': '🎯',
        'bboost': '📈',
        '3xc': '👑',
        'manager': '🧠'
    }
    return chips.get(chip, '-')

def fetch_picks(entry_id, gw, cookies):
    """Fetch picks for a manager"""
    url = f"https://fantasy.premierleague.com/api/entry/{entry_id}/event/{gw}/picks/"
    return entry_id, fetch_json(url, cookies)

def get_the100_standings(league_id=THE100_LEAGUE_ID):
    """Fetch standings with captain/chip for top managers"""
    global _cache
    
    now = time.time()
    
    # Return cached data if valid
    if _cache['data'] and (now - _cache['timestamp']) < _cache['ttl']:
        return _cache['data']
    
    try:
        cookies = get_cookies()
        
        # 1) Get bootstrap data (player names for captain)
        bootstrap = fetch_json("https://fantasy.premierleague.com/api/bootstrap-static/", cookies)
        if not bootstrap:
            raise RuntimeError("Failed to fetch bootstrap data")
        
        events = bootstrap["events"]
        current_gw = next((e["id"] for e in events if e.get("is_current")), None)
        if not current_gw:
            finished = [e for e in events if e.get("finished")]
            current_gw = max(finished, key=lambda e: e["id"])["id"] if finished else 1
        
        # Player ID to name mapping
        player_names = {p["id"]: p["web_name"] for p in bootstrap["elements"]}
        
        # 2) Fetch all standings (paginated)
        standings = []
        page = 1
        while True:
            url = f"https://fantasy.premierleague.com/api/leagues-classic/{league_id}/standings/?page_standings={page}"
            data = fetch_json(url, cookies)
            if not data:
                break
            
            block = data.get("standings", {})
            rows = block.get("results", [])
            standings.extend(rows)
            
            if not block.get("has_next"):
                break
            page += 1
        
        if not standings:
            raise RuntimeError("No standings found")
        
        # 3) Find winner's position
        winner_in_standings = None
        winner_rank = None
        for i, row in enumerate(standings):
            if row.get('entry') == WINNER_ENTRY_ID:
                winner_in_standings = row
                winner_rank = row.get('rank', i + 1)
                break
        
        # 4) Determine which managers to fetch picks for
        # Top 150 + winner (if outside top 150)
        entries_to_fetch = set()
        for i, row in enumerate(standings[:MAX_PICKS_FETCH]):
            entries_to_fetch.add(row.get('entry'))
        
        # Always include winner
        if WINNER_ENTRY_ID not in entries_to_fetch:
            entries_to_fetch.add(WINNER_ENTRY_ID)
        
        # 5) Fetch picks concurrently
        picks_dict = {}
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {
                executor.submit(fetch_picks, entry_id, current_gw, cookies): entry_id 
                for entry_id in entries_to_fetch
            }
            for future in as_completed(futures):
                try:
                    entry_id, picks_data = future.result()
                    if picks_data:
                        picks_dict[entry_id] = picks_data
                except Exception:
                    pass
        
        # 6) Build standings list
        final_rows = []
        for row in standings:
            entry_id = row.get('entry')
            current_rank = row.get('rank', 0)
            last_rank = row.get('last_rank') or current_rank
            rank_change = last_rank - current_rank
            
            # Get captain and chip from picks
            captain_name = '-'
            chip_display = '-'
            chip_raw = None
            
            if entry_id in picks_dict:
                picks_data = picks_dict[entry_id]
                picks = picks_data.get('picks', [])
                chip_raw = picks_data.get('active_chip')
                chip_display = get_chip_display(chip_raw)
                
                # Find captain
                cap_id = next((p['element'] for p in picks if p.get('is_captain')), None)
                if cap_id and cap_id in player_names:
                    captain_name = player_names[cap_id]
            
            # Check if this is the winner (auto-qualifier)
            is_winner = (entry_id == WINNER_ENTRY_ID)
            
            final_rows.append({
                'live_rank': current_rank,
                'manager_name': row.get('player_name', ''),
                'team_name': row.get('entry_name', ''),
                'live_total': row.get('total', 0),
                'live_gw_points': row.get('event_total', 0),
                'rank_change': rank_change,
                'entry_id': entry_id,
                'captain': captain_name,
                'chip': chip_display,
                'chip_raw': chip_raw,
                'is_winner': is_winner
            })
        
        # 7) Calculate qualification cutoff
        # If winner is outside top 100, only 99 others qualify
        if winner_rank and winner_rank > 100:
            qualification_cutoff = 99
        else:
            qualification_cutoff = 100
        
        result = {
            'standings': final_rows,
            'gameweek': current_gw,
            'total_managers': len(final_rows),
            'is_live': False,
            'qualification_cutoff': qualification_cutoff,
            'winner_entry_id': WINNER_ENTRY_ID,
            'winner_rank': winner_rank,
            'last_updated': datetime.now().strftime('%H:%M')
        }
        
        # Cache the result
        _cache['data'] = result
        _cache['timestamp'] = now
        
        return result
        
    except Exception as e:
        print(f"Error fetching The 100 standings: {e}")
        # Return cached data if available
        if _cache['data']:
            return _cache['data']
        return {
            'standings': [],
            'gameweek': None,
            'total_managers': 0,
            'is_live': False,
            'qualification_cutoff': 100,
            'error': str(e)
        }
