# -*- coding: utf-8 -*-
"""
The 100 League - Simple Standings (No Live Calculation)
Uses official FPL standings - fast and memory efficient
"""

import requests
import os
from datetime import datetime

# Configuration
THE100_LEAGUE_ID = 8921
TIMEOUT = 15

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

def get_the100_standings(league_id=THE100_LEAGUE_ID):
    """Fetch official FPL standings - simple and fast"""
    global _cache
    
    import time
    now = time.time()
    
    # Return cached data if valid
    if _cache['data'] and (now - _cache['timestamp']) < _cache['ttl']:
        return _cache['data']
    
    try:
        cookies = get_cookies()
        
        # 1) Get current gameweek
        bootstrap = fetch_json("https://fantasy.premierleague.com/api/bootstrap-static/", cookies)
        if not bootstrap:
            raise RuntimeError("Failed to fetch bootstrap data")
        
        events = bootstrap["events"]
        current_gw = next((e["id"] for e in events if e.get("is_current")), None)
        if not current_gw:
            finished = [e for e in events if e.get("finished")]
            current_gw = max(finished, key=lambda e: e["id"])["id"] if finished else 1
        
        # Check if any games are live
        fixtures = fetch_json(f"https://fantasy.premierleague.com/api/fixtures/?event={current_gw}", cookies) or []
        is_live = any(f.get('started') and not f.get('finished_provisional') for f in fixtures)
        
        # 2) Fetch standings (paginated)
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
        
        # 3) Build simple standings list
        final_rows = []
        for row in standings:
            current_rank = row.get('rank', 0)
            last_rank = row.get('last_rank') or current_rank
            rank_change = last_rank - current_rank
            
            final_rows.append({
                'live_rank': current_rank,
                'manager_name': row.get('player_name', ''),
                'team_name': row.get('entry_name', ''),
                'live_total': row.get('total', 0),
                'live_gw_points': row.get('event_total', 0),
                'rank_change': rank_change,
                'entry_id': row.get('entry'),
                # No captain/chip - would require 1000+ API calls
                'captain': '-',
                'chip': '-',
                'chip_raw': None
            })
        
        result = {
            'standings': final_rows,
            'gameweek': current_gw,
            'total_managers': len(final_rows),
            'is_live': is_live,
            'qualification_cutoff': 100,
            'last_updated': datetime.now().strftime('%H:%M'),
            'is_official': True  # Flag to show this is official, not live calculated
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
