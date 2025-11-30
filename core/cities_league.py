# -*- coding: utf-8 -*-
"""
دوري المدن - Cities League
Team-based H2H league where each team has 3 managers
Special rules:
- Triple Captain counts as 2x (not 3x)
- Bench Boost is ignored (only 11 players count)
"""

import requests
import os
from datetime import datetime
import time

# Configuration
CITIES_H2H_LEAGUE_ID = 1011575
TIMEOUT = 15

# Team definitions: team_name -> list of FPL entry IDs
TEAMS_FPL_IDS = {
    "بوسليم": [102255, 170629, 50261],
    "اوجلة": [423562, 49250, 99910],
    "البازة": [116175, 4005689, 2486966],
    "طرميسة": [701092, 199211, 2098119],
    "درنه": [191337, 4696003, 2601894],
    "ترهونة": [1941402, 2940600, 179958],
    "غريان": [7928, 6889159, 110964],
    "الهضبة": [3530273, 2911452, 1128265],
    "بنغازي": [372479, 568897, 3279877],
    "حي 9 يونيو": [7934485, 1651522, 5259149],
    "الخمس": [1301966, 4168085, 8041861],
    "المحجوب": [2780336, 746231, 1841364],
    "طرابلس": [2841954, 974668, 554016],
    "الفرناج": [129548, 1200849, 1163868],
    "مصراتة": [2501532, 255116, 346814],
    "زليتن": [4795379, 1298141, 3371889],
    "الزاوية": [3507158, 851661, 2811004],
    "القطرون": [3142905, 1760648, 43105],
    "جالو": [5026431, 117063, 97707],
    "سوق الجمعة": [46435, 57593, 4701548],
}

# Reverse lookup: entry_id -> team_name
ENTRY_TO_TEAM = {}
for team_name, ids in TEAMS_FPL_IDS.items():
    for entry_id in ids:
        ENTRY_TO_TEAM[entry_id] = team_name

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

def get_cities_league_data():
    """Fetch all data for Cities League"""
    global _cache
    
    now = time.time()
    
    # Return cached data if valid
    if _cache['data'] and (now - _cache['timestamp']) < _cache['ttl']:
        return _cache['data']
    
    try:
        cookies = get_cookies()
        
        # 1) Get bootstrap data
        bootstrap = fetch_json("https://fantasy.premierleague.com/api/bootstrap-static/", cookies)
        if not bootstrap:
            raise RuntimeError("Failed to fetch bootstrap data")
        
        events = bootstrap["events"]
        current_gw = next((e["id"] for e in events if e.get("is_current")), None)
        if not current_gw:
            finished = [e for e in events if e.get("finished")]
            current_gw = max(finished, key=lambda e: e["id"])["id"] if finished else 1
        
        # Player info
        player_info = {
            p["id"]: {
                "name": p["web_name"],
                "team": p["team"],
                "position": p["element_type"],
            } for p in bootstrap["elements"]
        }
        
        # 2) Get live data
        live_data = fetch_json(f"https://fantasy.premierleague.com/api/event/{current_gw}/live/", cookies)
        if not live_data:
            raise RuntimeError("Failed to fetch live data")
        
        live_elements = {
            e['id']: {
                'total_points': e['stats']['total_points'],
                'minutes': e['stats']['minutes'],
            } for e in live_data['elements']
        }
        
        # 3) Get fixtures to check team status
        fixtures = fetch_json(f"https://fantasy.premierleague.com/api/fixtures/?event={current_gw}", cookies) or []
        
        # Build team fixture status
        team_fixture_done = {}
        for fix in fixtures:
            finished = fix.get('finished') or fix.get('finished_provisional')
            started = fix.get('started', False)
            postponed = fix.get('kickoff_time') is None
            done = finished or postponed or started
            team_fixture_done[fix['team_h']] = done
            team_fixture_done[fix['team_a']] = done
        
        # 4) Get H2H league standings
        league_data = fetch_json(f"https://fantasy.premierleague.com/api/leagues-h2h/{CITIES_H2H_LEAGUE_ID}/standings/", cookies)
        if not league_data:
            raise RuntimeError("Failed to fetch league standings")
        
        h2h_standings = league_data.get('standings', {}).get('results', [])
        
        # 5) Get current GW matches
        matches_data = fetch_json(f"https://fantasy.premierleague.com/api/leagues-h2h-matches/league/{CITIES_H2H_LEAGUE_ID}/?event={current_gw}", cookies)
        matches = matches_data.get('results', []) if matches_data else []
        
        # 6) Calculate live points for each manager
        def calculate_manager_points(entry_id):
            """Calculate live points for a single manager with special rules"""
            picks_data = fetch_json(f"https://fantasy.premierleague.com/api/entry/{entry_id}/event/{current_gw}/picks/", cookies)
            if not picks_data:
                return 0, '-', 0
            
            picks = picks_data.get('picks', [])
            chip = picks_data.get('active_chip')
            hits = picks_data.get('entry_history', {}).get('event_transfers_cost', 0)
            
            # Find captain
            captain_id = next((p['element'] for p in picks if p.get('is_captain')), None)
            captain_name = player_info.get(captain_id, {}).get('name', '-') if captain_id else '-'
            
            # Calculate points for starting 11 only (ignore bench boost)
            total_points = 0
            for i, pick in enumerate(picks[:11]):  # Only first 11
                pid = pick['element']
                pts = live_elements.get(pid, {}).get('total_points', 0)
                
                # Captain gets 2x (TC is treated as regular captain - 2x not 3x)
                if pick.get('is_captain'):
                    cap_minutes = live_elements.get(pid, {}).get('minutes', 0)
                    cap_team = player_info.get(pid, {}).get('team')
                    cap_played = cap_minutes > 0
                    cap_done = team_fixture_done.get(cap_team, False)
                    
                    if cap_played:
                        pts *= 2  # Always 2x, even with TC
                    elif cap_done:
                        pts = 0  # Captain didn't play and game is done
                    # else: multiplier stays 1 (game not started)
                    
                elif pick.get('is_vice_captain'):
                    # Check if captain didn't play
                    cap_id = next((p['element'] for p in picks if p.get('is_captain')), None)
                    if cap_id:
                        cap_minutes = live_elements.get(cap_id, {}).get('minutes', 0)
                        cap_team = player_info.get(cap_id, {}).get('team')
                        cap_done = team_fixture_done.get(cap_team, False)
                        
                        if cap_minutes == 0 and cap_done:
                            # VC becomes captain with 2x
                            vc_minutes = live_elements.get(pid, {}).get('minutes', 0)
                            if vc_minutes > 0:
                                pts *= 2
                
                total_points += pts
            
            # Auto-subs calculation
            sub_points = calculate_auto_subs(picks, live_elements, player_info, team_fixture_done)
            
            return total_points + sub_points - hits, captain_name, hits
        
        def calculate_auto_subs(picks, live_elements, player_info, team_fixture_done):
            """Calculate auto-sub points"""
            def pos_of(eid):
                return player_info.get(eid, {}).get('position', 0)
            
            def formation_ok(d, m, f, g):
                return (g == 1 and 3 <= d <= 5 and 2 <= m <= 5 and 1 <= f <= 3)
            
            def team_done(eid):
                team_id = player_info.get(eid, {}).get('team')
                return team_fixture_done.get(team_id, False)
            
            starters = picks[:11]
            bench = picks[11:]
            
            d = sum(1 for p in starters if pos_of(p['element']) == 2)
            m = sum(1 for p in starters if pos_of(p['element']) == 3)
            f = sum(1 for p in starters if pos_of(p['element']) == 4)
            g = sum(1 for p in starters if pos_of(p['element']) == 1)
            
            non_playing_starters = [
                p for p in starters
                if live_elements.get(p['element'], {}).get('minutes', 0) == 0
                and team_done(p['element'])
            ]
            
            used_bench = set()
            sub_points = 0
            
            for starter in non_playing_starters:
                s_id = starter['element']
                s_pos = pos_of(s_id)
                
                for b in bench:
                    b_id = b['element']
                    if b_id in used_bench:
                        continue
                    
                    b_pos = pos_of(b_id)
                    b_min = live_elements.get(b_id, {}).get('minutes', 0)
                    b_played = b_min > 0
                    b_done = team_done(b_id)
                    
                    # GK <-> GK only
                    if (s_pos == 1 and b_pos != 1) or (s_pos != 1 and b_pos == 1):
                        continue
                    
                    if not b_played:
                        if not b_done:
                            used_bench.add(b_id)
                            break
                        continue
                    
                    # Check formation
                    d2, m2, f2, g2 = d, m, f, g
                    if s_pos == 2: d2 -= 1
                    elif s_pos == 3: m2 -= 1
                    elif s_pos == 4: f2 -= 1
                    elif s_pos == 1: g2 -= 1
                    
                    if b_pos == 2: d2 += 1
                    elif b_pos == 3: m2 += 1
                    elif b_pos == 4: f2 += 1
                    elif b_pos == 1: g2 += 1
                    
                    if not formation_ok(d2, m2, f2, g2):
                        continue
                    
                    sub_points += live_elements[b_id]['total_points']
                    used_bench.add(b_id)
                    d, m, f, g = d2, m2, f2, g2
                    break
            
            return sub_points
        
        # 7) Calculate team points
        team_live_points = {}
        team_captains = {}
        
        for team_name, entry_ids in TEAMS_FPL_IDS.items():
            total_pts = 0
            captains = []
            for entry_id in entry_ids:
                pts, cap_name, _ = calculate_manager_points(entry_id)
                total_pts += pts
                captains.append(cap_name)
            team_live_points[team_name] = total_pts
            team_captains[team_name] = captains
        
        # 8) Build H2H match results
        h2h_matches = []
        for match in matches:
            entry_1 = match.get('entry_1_entry')
            entry_2 = match.get('entry_2_entry')
            
            team_1 = ENTRY_TO_TEAM.get(entry_1)
            team_2 = ENTRY_TO_TEAM.get(entry_2)
            
            if team_1 and team_2:
                pts_1 = team_live_points.get(team_1, 0)
                pts_2 = team_live_points.get(team_2, 0)
                
                h2h_matches.append({
                    'team_1': team_1,
                    'team_2': team_2,
                    'points_1': pts_1,
                    'points_2': pts_2,
                    'captains_1': team_captains.get(team_1, []),
                    'captains_2': team_captains.get(team_2, []),
                })
        
        # 9) Build standings with live points
        # Map entry_id to H2H league points
        entry_league_points = {}
        for entry in h2h_standings:
            entry_league_points[entry['entry']] = entry.get('total', 0)
        
        # Calculate team league points (sum of all managers' H2H points)
        team_standings = []
        for team_name, entry_ids in TEAMS_FPL_IDS.items():
            league_pts = 0
            for eid in entry_ids:
                league_pts += entry_league_points.get(eid, 0)
            
            team_standings.append({
                'team_name': team_name,
                'league_points': league_pts,
                'live_gw_points': team_live_points.get(team_name, 0),
                'captains': team_captains.get(team_name, []),
            })
        
        # Sort by league points
        team_standings.sort(key=lambda x: (-x['league_points'], -x['live_gw_points']))
        
        # Add ranks
        for i, team in enumerate(team_standings, 1):
            team['rank'] = i
        
        # Check if live
        is_live = any(f.get('started') and not f.get('finished_provisional') for f in fixtures)
        
        result = {
            'standings': team_standings,
            'matches': h2h_matches,
            'gameweek': current_gw,
            'total_teams': len(TEAMS_FPL_IDS),
            'is_live': is_live,
            'last_updated': datetime.now().strftime('%H:%M')
        }
        
        _cache['data'] = result
        _cache['timestamp'] = now
        
        return result
        
    except Exception as e:
        print(f"Error fetching Cities League data: {e}")
        if _cache['data']:
            return _cache['data']
        return {
            'standings': [],
            'matches': [],
            'gameweek': None,
            'total_teams': 0,
            'is_live': False,
            'error': str(e)
        }
