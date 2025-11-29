# -*- coding: utf-8 -*-
"""
League Statistics Module
Calculates various stats for the league
"""

import pandas as pd
from collections import Counter
from core.fpl_api import (
    get_bootstrap_data,
    get_current_gameweek,
    get_league_standings,
    get_league_matches,
    get_entry_picks,
    get_multiple_entry_picks,
    get_multiple_entry_history,
    get_live_data,
    get_fixtures,
    build_player_info,
    fetch_data,
    FPLApiError
)
from config import LEAGUE_ID, EXCLUDED_PLAYERS, get_chip_arabic


def calculate_live_points_for_entry(picks_data, live_elements_dict, player_info, fixtures):
    """
    Calculate live points for a single entry including auto-subs
    """
    picks = picks_data.get('picks', [])
    chip = picks_data.get('active_chip')
    cost = picks_data.get('entry_history', {}).get('event_transfers_cost', 0)
    
    if not picks or not live_elements_dict:
        return picks_data.get('entry_history', {}).get('points', 0)
    
    # Build team fixture status
    team_fixture_started = {}
    team_fixture_finished = {}
    for fixture in fixtures:
        started = fixture.get('started', False)
        finished = fixture.get('finished', False) or fixture.get('finished_provisional', False)
        team_fixture_started[fixture['team_h']] = team_fixture_started.get(fixture['team_h'], False) or started
        team_fixture_started[fixture['team_a']] = team_fixture_started.get(fixture['team_a'], False) or started
        team_fixture_finished[fixture['team_h']] = team_fixture_finished.get(fixture['team_h'], True) and finished
        team_fixture_finished[fixture['team_a']] = team_fixture_finished.get(fixture['team_a'], True) and finished
    
    def team_finished(team_id):
        return team_fixture_finished.get(team_id, False)
    
    # Get captain/vice info
    captain_id = next((p['element'] for p in picks if p.get('is_captain')), None)
    vice_id = next((p['element'] for p in picks if p.get('is_vice_captain')), None)
    
    # Calculate starting XI points
    if chip == 'bboost':
        starters = picks[:15]
    else:
        starters = picks[:11]
    
    bench = picks[11:] if chip != 'bboost' else []
    
    # Get live data
    def get_pts(pid):
        return live_elements_dict.get(pid, {}).get('total_points', 0)
    
    def get_mins(pid):
        return live_elements_dict.get(pid, {}).get('minutes', 0)
    
    # Calculate captain multiplier
    multiplier = 3 if chip == '3xc' else 2
    captain_played = get_mins(captain_id) > 0 if captain_id else False
    captain_team = player_info.get(captain_id, {}).get('team', 0) if captain_id else 0
    captain_team_finished = team_finished(captain_team)
    
    # Determine if vice-captain should get multiplier
    vice_gets_multiplier = False
    if captain_id and not captain_played and captain_team_finished:
        vice_gets_multiplier = True
    
    # Calculate base points from starters
    total = 0
    for pick in starters:
        pid = pick['element']
        pts = get_pts(pid)
        
        if pick.get('is_captain'):
            if captain_played:
                total += pts * multiplier
            elif captain_team_finished:
                total += 0  # Captain didn't play, team finished
            else:
                total += pts  # Captain hasn't played yet, team not finished
        elif pick.get('is_vice_captain') and vice_gets_multiplier:
            total += pts * multiplier
        else:
            total += pts
    
    # Auto-subs (only if not bench boost)
    if chip != 'bboost' and bench:
        # Find non-playing starters
        xi_ids = [p['element'] for p in picks[:11]]
        used_bench = set()
        
        for pick in picks[:11]:
            pid = pick['element']
            mins = get_mins(pid)
            pteam = player_info.get(pid, {}).get('team', 0)
            
            # Check if player didn't play and team finished
            if mins == 0 and team_finished(pteam):
                # Find eligible bench player
                for bench_pick in bench:
                    bid = bench_pick['element']
                    if bid in used_bench:
                        continue
                    
                    bmins = get_mins(bid)
                    bteam = player_info.get(bid, {}).get('team', 0)
                    
                    # Skip if bench player also didn't play and team finished
                    if bmins == 0 and team_finished(bteam):
                        continue
                    
                    # GK can only replace GK
                    spos = player_info.get(pid, {}).get('position', 0)
                    bpos = player_info.get(bid, {}).get('position', 0)
                    
                    if spos == 1 and bpos != 1:
                        continue
                    if spos != 1 and bpos == 1:
                        continue
                    
                    # Valid sub found
                    total += get_pts(bid)
                    used_bench.add(bid)
                    break
    
    # Subtract transfer cost
    total -= cost
    
    return total


def get_manager_history(league_id=None):
    """
    Get historical data (points and ranks) for all managers across all gameweeks
    Uses parallel fetching for much faster loading
    """
    if league_id is None:
        league_id = LEAGUE_ID
    
    try:
        bootstrap_data = get_bootstrap_data()
        gw_info = get_current_gameweek(bootstrap_data)
        current_gw = gw_info['id']
        
        league_data = get_league_standings(league_id)
        teams = league_data['standings']['results']
        
        # Collect entry IDs
        entry_ids = []
        entry_to_name = {}
        for team in teams:
            player_name = team.get('player_name')
            if player_name in EXCLUDED_PLAYERS:
                continue
            entry_id = team.get('entry')
            entry_ids.append(entry_id)
            entry_to_name[entry_id] = player_name
        
        # PARALLEL FETCH all histories
        all_histories = {}
        try:
            all_histories = get_multiple_entry_history(entry_ids)
        except Exception as e:
            print(f"Error fetching histories: {e}")
        
        managers = []
        points_data = {}
        ranks_data = {}
        
        for entry_id, player_name in entry_to_name.items():
            team = next((t for t in teams if t.get('entry') == entry_id), {})
            managers.append({
                'name': player_name,
                'entry_id': entry_id,
                'team_name': team.get('entry_name', '')
            })
            
            points_data[player_name] = {}
            ranks_data[player_name] = {}
            
            history_data = all_histories.get(entry_id, {})
            
            if history_data:
                for gw_history in history_data.get('current', []):
                    gw = gw_history.get('event')
                    
                    # Points (minus transfer cost)
                    points = gw_history.get('points', 0)
                    transfer_cost = gw_history.get('event_transfers_cost', 0)
                    net_points = points - transfer_cost
                    
                    # Overall rank
                    overall_rank = gw_history.get('overall_rank', 0)
                    
                    points_data[player_name][gw] = net_points
                    ranks_data[player_name][gw] = overall_rank
            else:
                # Fallback: set None for all gameweeks
                for gw in range(1, current_gw + 1):
                    points_data[player_name][gw] = None
                    ranks_data[player_name][gw] = None
        
        return {
            'success': True,
            'current_gw': current_gw,
            'managers': managers,
            'points_data': points_data,
            'ranks_data': ranks_data,
            'gameweeks': list(range(1, current_gw + 1))
        }
        
    except FPLApiError as e:
        return {
            'success': False,
            'error': str(e)
        }


def get_league_stats(league_id=None, gameweek=None):
    """
    Get comprehensive league statistics - OPTIMIZED with parallel fetching
    Uses LIVE points when gameweek is in progress
    """
    if league_id is None:
        league_id = LEAGUE_ID
    
    try:
        # Initialize data
        bootstrap_data = get_bootstrap_data()
        player_info = build_player_info(bootstrap_data)
        elements = bootstrap_data.get('elements', [])
        
        # Get current gameweek info
        gw_info = get_current_gameweek(bootstrap_data)
        current_gw = gameweek or gw_info['id']
        
        # Check if gameweek is live (started but not finished)
        is_live = gw_info.get('is_current', False) and not gw_info.get('finished', False)
        fixtures_started = False
        
        # Get live data if gameweek is live
        live_elements_dict = {}
        fixtures = []
        
        if is_live:
            try:
                # Check if any fixtures have started
                fixtures = get_fixtures(current_gw)
                fixtures_started = any(f.get('started', False) for f in fixtures)
                
                if fixtures_started:
                    # Fetch live data
                    live_data = get_live_data(current_gw)
                    live_elements_dict = {
                        e['id']: {
                            'total_points': e['stats'].get('total_points', 0),
                            'minutes': e['stats'].get('minutes', 0),
                            'bonus': e['stats'].get('bonus', 0)
                        }
                        for e in live_data.get('elements', [])
                    }
            except Exception as e:
                print(f"Error fetching live data: {e}")
                is_live = False
        
        use_live_points = is_live and fixtures_started and live_elements_dict
        
        # Get league data
        league_data = get_league_standings(league_id)
        league_name = league_data.get('league', {}).get('name', 'Elite League')
        teams = league_data['standings']['results']
        
        # Collect entry IDs
        entry_ids = []
        entry_to_name = {}
        for team in teams:
            player_name = team.get('player_name')
            if player_name in EXCLUDED_PLAYERS:
                continue
            entry_id = team.get('entry')
            entry_ids.append(entry_id)
            entry_to_name[entry_id] = player_name
        
        # PARALLEL FETCH all picks data at once
        all_picks_data = {}
        try:
            all_picks_data = get_multiple_entry_picks(entry_ids, current_gw)
        except Exception as e:
            print(f"Error fetching picks for stats: {e}")
        
        # Initialize collectors
        captains = []
        chips_used = []
        gw_points = []
        player_ownership = Counter()
        manager_points = {}
        all_ranks = []
        
        for entry_id, player_name in entry_to_name.items():
            picks_data = all_picks_data.get(entry_id)
            if not picks_data:
                continue
            
            picks = picks_data.get('picks', [])
            entry_history = picks_data.get('entry_history', {})
            chip = picks_data.get('active_chip')
            
            # GW Points - USE LIVE POINTS if available
            if use_live_points:
                points = calculate_live_points_for_entry(picks_data, live_elements_dict, player_info, fixtures)
            else:
                points = entry_history.get('points', 0)
            
            gw_points.append(points)
            manager_points[player_name] = points
            
            # Overall rank (keep from API - this is always accurate)
            overall_rank = entry_history.get('overall_rank', 0)
            if overall_rank and overall_rank > 0:
                all_ranks.append({
                    'manager': player_name,
                    'rank': overall_rank
                })
            
            # Captain
            captain_id = next((p['element'] for p in picks if p.get('is_captain')), None)
            if captain_id:
                captain_name = player_info.get(captain_id, {}).get('name', 'Unknown')
                captains.append({
                    'manager': player_name,
                    'captain_id': captain_id,
                    'captain_name': captain_name
                })
            
            # Chips
            if chip:
                chips_used.append({
                    'manager': player_name,
                    'entry_id': entry_id,
                    'chip': chip,
                    'chip_ar': get_chip_arabic(chip)
                })
            
            # Effective Ownership
            if chip == 'bboost':
                players_to_count = picks[:15]
            else:
                players_to_count = picks[:11]
            
            for pick in players_to_count:
                element_id = pick['element']
                
                if pick.get('is_captain'):
                    if chip == '3xc':
                        player_ownership[element_id] += 3
                    else:
                        player_ownership[element_id] += 2
                else:
                    player_ownership[element_id] += 1
        
        # Calculate captain stats
        captain_counts = Counter([c['captain_name'] for c in captains])
        captain_stats = [
            {'name': name, 'count': count}
            for name, count in captain_counts.most_common()
        ]
        
        # Calculate GW points stats
        if gw_points:
            n = len(gw_points)
            min_points = min(gw_points)
            max_points = max(gw_points)
            
            # Find managers with min/max points
            min_managers = [name for name, pts in manager_points.items() if pts == min_points]
            max_managers = [name for name, pts in manager_points.items() if pts == max_points]
            
            # Find best and worst overall ranks
            best_rank = None
            best_rank_managers = []
            worst_rank = None
            worst_rank_managers = []
            
            if all_ranks:
                all_ranks_sorted = sorted(all_ranks, key=lambda x: x['rank'])
                best_rank = all_ranks_sorted[0]['rank']
                worst_rank = all_ranks_sorted[-1]['rank']
                best_rank_managers = [r['manager'] for r in all_ranks if r['rank'] == best_rank]
                worst_rank_managers = [r['manager'] for r in all_ranks if r['rank'] == worst_rank]
            
            # Calculate lucky and unlucky managers from H2H matches
            lucky_manager = None
            lucky_points = float('inf')
            unlucky_manager = None
            unlucky_points = 0
            
            try:
                matches = get_league_matches(league_id, current_gw)['results']
                
                for match in matches:
                    entry_1 = match['entry_1_entry']
                    entry_2 = match['entry_2_entry']
                    
                    # Get manager names
                    team_1_info = next((t for t in teams if t['entry'] == entry_1), None)
                    team_2_info = next((t for t in teams if t['entry'] == entry_2), None)
                    
                    if not team_1_info or not team_2_info:
                        continue
                    
                    name_1 = team_1_info['player_name']
                    name_2 = team_2_info['player_name']
                    
                    if name_1 in EXCLUDED_PLAYERS or name_2 in EXCLUDED_PLAYERS:
                        continue
                    
                    # Use live points from manager_points dict if available
                    pts_1 = manager_points.get(name_1, match.get('entry_1_points', 0))
                    pts_2 = manager_points.get(name_2, match.get('entry_2_points', 0))
                    
                    # Skip draws
                    if pts_1 == pts_2:
                        continue
                    
                    # Determine winner and loser
                    if pts_1 > pts_2:
                        winner_name, winner_pts = name_1, pts_1
                        loser_name, loser_pts = name_2, pts_2
                    else:
                        winner_name, winner_pts = name_2, pts_2
                        loser_name, loser_pts = name_1, pts_1
                    
                    # Lucky: winner with lowest points
                    if winner_pts < lucky_points:
                        lucky_points = winner_pts
                        lucky_manager = winner_name
                    
                    # Unlucky: loser with highest points
                    if loser_pts > unlucky_points:
                        unlucky_points = loser_pts
                        unlucky_manager = loser_name
                        
            except:
                pass
            
            points_stats = {
                'min': min_points,
                'min_managers': min_managers,
                'max': max_points,
                'max_managers': max_managers,
                'avg': round(sum(gw_points) / n, 1),
                'total_managers': n,
                'best_rank': best_rank,
                'best_rank_managers': best_rank_managers,
                'worst_rank': worst_rank,
                'worst_rank_managers': worst_rank_managers,
                'lucky_manager': lucky_manager,
                'lucky_points': lucky_points if lucky_manager else None,
                'unlucky_manager': unlucky_manager,
                'unlucky_points': unlucky_points if unlucky_manager else None
            }
        else:
            points_stats = {
                'min': 0, 'min_managers': [],
                'max': 0, 'max_managers': [],
                'avg': 0, 'total_managers': 0,
                'best_rank': None, 'best_rank_managers': [],
                'worst_rank': None, 'worst_rank_managers': [],
                'lucky_manager': None, 'lucky_points': None,
                'unlucky_manager': None, 'unlucky_points': None
            }
        
        # Calculate effective ownership (top 15)
        # Percentage is count / 36 * 100
        effective_ownership = []
        
        for element_id, count in player_ownership.most_common(15):
            player = player_info.get(element_id, {})
            player_element = next((p for p in elements if p['id'] == element_id), {})
            team_id = player.get('team', 0)
            team_name = ''
            for t in bootstrap_data.get('teams', []):
                if t['id'] == team_id:
                    team_name = t['short_name']
                    break
            
            # Percentage based on 36 managers
            percentage = round((count / 36) * 100, 1)
            
            effective_ownership.append({
                'name': player.get('name', 'Unknown'),
                'team': team_name,
                'count': count,
                'percentage': percentage
            })
        
        return {
            'success': True,
            'gameweek': current_gw,
            'gw_info': gw_info,
            'league_name': league_name,
            'is_live': use_live_points,
            'captain_stats': captain_stats,
            'chips_used': chips_used,
            'points_stats': points_stats,
            'effective_ownership': effective_ownership,
            'total_managers': len([t for t in teams if t.get('player_name') not in EXCLUDED_PLAYERS])
        }
        
    except FPLApiError as e:
        return {
            'success': False,
            'error': str(e)
        }
