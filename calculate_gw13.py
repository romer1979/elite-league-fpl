#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Calculate GW13 standings for team leagues
Run this locally and copy the output to the league files

Usage: python3 calculate_gw13.py
"""

import requests
import json

TIMEOUT = 15

# Your FPL cookies - update these!
COOKIES = {
    'sessionid': '.eJxVy8sKwjAQheF3yVpK0slkGnfuBQvFdchlQsRSirGr4rub7nR5-M6_C-e3d3Fb5Zd7JHEWWg-STA_i9EvBxycvh69zXufukG683pvVabpd2vwPiq-lva0BDRisIsZkjAWTWSlMUcoUiXXikFX2IXuK_UBRNidCVIxAVoL4fAH7WjMU:1qdKWX:gscU4n3NXCVKZVKm-TyQDyAFAvERsssnflInEj63Bxw',
    'csrftoken': 'bdkplQaYzsHYN6FZOM8u1BNVZtbLixic'
}

def fetch_json(url):
    try:
        r = requests.get(url, cookies=COOKIES, timeout=TIMEOUT)
        if r.status_code == 200:
            return r.json()
        print(f"Error {r.status_code} for {url}")
        return None
    except Exception as e:
        print(f"Fetch error: {e}")
        return None

# ============================================
# LEAGUE CONFIGURATIONS
# ============================================

LEAGUES = {
    'cities': {
        'id': 1011575,
        'gw12': {
            "جالو": 33, "طرميسة": 24, "غريان": 24, "اوجلة": 21, "حي 9 يونيو": 19,
            "ترهونة": 19, "الهضبة": 19, "المحجوب": 18, "القطرون": 18, "بنغازي": 18,
            "طرابلس": 18, "درنه": 18, "بوسليم": 16, "الخمس": 16, "البازة": 15,
            "زليتن": 15, "الفرناج": 15, "الزاوية": 13, "سوق الجمعة": 9, "مصراتة": 9,
        },
        'teams': {
            "بوسليم": [102255, 170629, 50261], "اوجلة": [423562, 49250, 99910],
            "البازة": [116175, 4005689, 2486966], "طرميسة": [701092, 199211, 2098119],
            "درنه": [191337, 4696003, 2601894], "ترهونة": [1941402, 2940600, 179958],
            "غريان": [7928, 6889159, 110964], "الهضبة": [3530273, 2911452, 1128265],
            "بنغازي": [372479, 568897, 3279877], "حي 9 يونيو": [7934485, 1651522, 5259149],
            "الخمس": [1301966, 4168085, 8041861], "المحجوب": [2780336, 746231, 1841364],
            "طرابلس": [2841954, 974668, 554016], "الفرناج": [129548, 1200849, 1163868],
            "مصراتة": [2501532, 255116, 346814], "زليتن": [4795379, 1298141, 3371889],
            "الزاوية": [3507158, 851661, 2811004], "القطرون": [3142905, 1760648, 43105],
            "جالو": [5026431, 117063, 97707], "سوق الجمعة": [46435, 57593, 4701548],
        }
    },
    'libyan': {
        'id': 1231867,
        'gw12': {
            "الأخضر": 28, "يفرن": 27, "الصقور": 24, "المستقبل": 24, "الظهرة": 24,
            "العروبة": 24, "الشط": 22, "النصر": 21, "الجزيرة": 21, "الصداقة": 18,
            "الأولمبي": 18, "الملعب": 18, "النصر زليتن": 15, "الأفريقي درنة": 15,
            "الإخاء": 12, "المدينة": 12, "دارنس": 9, "الأهلي طرابلس": 9, "الشرارة": 9, "السويحلي": 9,
        },
        'teams': {
            "السويحلي": [90627, 4314045, 6904125], "الأفريقي درنة": [73166, 48803, 157909],
            "المدينة": [1801960, 1616108, 3708101], "النصر زليتن": [2864, 32014, 1138535],
            "دارنس": [2042169, 79249, 6918866], "الشرارة": [4474659, 4665498, 1382702],
            "العروبة": [2429965, 104498, 2155970], "الصقور": [7161174, 6656930, 6698684],
            "الإخاء": [168059, 1282550, 3049220], "الأهلي طرابلس": [1011498, 5765498, 1018875],
            "النصر": [139498, 2440757, 1304043], "الشط": [8027734, 189473, 31498],
            "يفرن": [8102498, 2486232, 6905498], "الأخضر": [47498, 93498, 2899498],
            "الصداقة": [161498, 3216498, 5626498], "الملعب": [3312498, 4315498, 76498],
            "الجزيرة": [2988586, 92498, 41498], "الظهرة": [7598, 4614103, 1050498],
            "الأولمبي": [24498, 2434498, 4656498], "المستقبل": [6498, 1040498, 3389498],
        }
    },
    'arab': {
        'id': 1015271,
        'gw12': {
            "العربي القطري": 28, "العين": 27, "القوة الجوية": 24, "الفتح السعودي": 24,
            "نيوم": 24, "اتحاد العاصمة": 22, "المريخ": 19, "النصر السعودي": 18,
            "النجم الساحلي": 18, "الترجي": 18, "الجزيرة الإماراتي": 16, "الأهلي المصري": 15,
            "الأفريقي": 15, "الاتحاد السعودي": 15, "الوداد": 15, "الرجاء": 15,
            "شبيبة القبائل": 12, "الهلال السعودي": 12, "أربيل": 9, "الهلال السوداني": 9,
        },
        'teams': {
            "الهلال السعودي": [1879543, 88452, 98572], "أربيل": [41808, 670218, 4848368],
            "الجزيرة الإماراتي": [1573546, 5636647, 2634904], "شبيبة القبائل": [1202069, 3270139, 320850],
            "الهلال السوداني": [209410, 378164, 2117536], "المريخ": [5766070, 2401629, 2119541],
            "الرجاء": [1137498, 3303498, 1572498], "النجم الساحلي": [6168498, 99498, 6082498],
            "الأفريقي": [2296498, 4146498, 1070498], "اتحاد العاصمة": [2115498, 2163498, 1065498],
            "الترجي": [6376498, 6364498, 6430498], "الوداد": [6332498, 1109498, 1085498],
            "الأهلي المصري": [5933498, 5930498, 5893498], "القوة الجوية": [5660498, 5700498, 5651498],
            "العين": [5569498, 5590498, 5555498], "نيوم": [5540498, 5471498, 5415498],
            "الفتح السعودي": [5352498, 5361498, 5332498], "الاتحاد السعودي": [5216498, 5219498, 5232498],
            "النصر السعودي": [5276498, 5280498, 5246498], "العربي القطري": [5127498, 5157498, 5109498],
        }
    }
}


def calculate_gw13_standings(league_name, config):
    """Calculate GW13 standings for a league"""
    print(f"\n{'='*60}")
    print(f"Calculating GW13 standings for {league_name.upper()}")
    print(f"{'='*60}")
    
    # Build entry_to_team lookup
    entry_to_team = {}
    for team_name, ids in config['teams'].items():
        for entry_id in ids:
            entry_to_team[entry_id] = team_name
    
    # Fetch GW13 live data
    print("Fetching GW13 live data...")
    live_data = fetch_json("https://fantasy.premierleague.com/api/event/13/live/")
    if not live_data:
        print("ERROR: Could not fetch live data")
        return None
    
    live_elements = {elem['id']: elem['stats']['total_points'] for elem in live_data['elements']}
    
    # Calculate team GW points
    print("Calculating team points...")
    team_gw_points = {}
    
    for team_name, entry_ids in config['teams'].items():
        total_pts = 0
        for entry_id in entry_ids:
            picks_data = fetch_json(f"https://fantasy.premierleague.com/api/entry/{entry_id}/event/13/picks/")
            if picks_data:
                picks = picks_data.get('picks', [])[:11]
                manager_pts = 0
                for pick in picks:
                    pts = live_elements.get(pick['element'], 0)
                    mult = pick.get('multiplier', 1)
                    if mult == 3:  # TC = 2x in team leagues
                        mult = 2
                    manager_pts += pts * mult
                manager_pts -= picks_data.get('entry_history', {}).get('event_transfers_cost', 0)
                total_pts += manager_pts
        team_gw_points[team_name] = total_pts
    
    # Fetch H2H matches
    print("Fetching H2H matches...")
    matches_data = fetch_json(f"https://fantasy.premierleague.com/api/leagues-h2h-matches/league/{config['id']}/?event=13")
    
    # Determine results
    match_results = {}
    processed = set()
    
    if matches_data:
        for match in matches_data.get('results', []):
            entry_1 = match.get('entry_1_entry')
            entry_2 = match.get('entry_2_entry')
            
            if not entry_1 or not entry_2:
                continue
            
            team_1 = entry_to_team.get(entry_1)
            team_2 = entry_to_team.get(entry_2)
            
            if not team_1 or not team_2 or team_1 == team_2 or team_1 in processed:
                continue
            
            pts_1 = team_gw_points.get(team_1, 0)
            pts_2 = team_gw_points.get(team_2, 0)
            
            if pts_1 > pts_2:
                match_results[team_1] = 'W'
                match_results[team_2] = 'L'
                print(f"  {team_1} ({pts_1}) vs {team_2} ({pts_2}) -> {team_1} WINS")
            elif pts_2 > pts_1:
                match_results[team_1] = 'L'
                match_results[team_2] = 'W'
                print(f"  {team_1} ({pts_1}) vs {team_2} ({pts_2}) -> {team_2} WINS")
            else:
                match_results[team_1] = 'D'
                match_results[team_2] = 'D'
                print(f"  {team_1} ({pts_1}) vs {team_2} ({pts_2}) -> DRAW")
            
            processed.add(team_1)
            processed.add(team_2)
    
    # Calculate final standings
    gw13 = {}
    for team_name in config['teams'].keys():
        base = config['gw12'].get(team_name, 0)
        result = match_results.get(team_name, '')
        added = 3 if result == 'W' else (1 if result == 'D' else 0)
        gw13[team_name] = base + added
    
    return gw13


def main():
    print("="*60)
    print("GW13 STANDINGS CALCULATOR")
    print("="*60)
    
    all_standings = {}
    
    for league_name, config in LEAGUES.items():
        standings = calculate_gw13_standings(league_name, config)
        if standings:
            all_standings[league_name] = standings
    
    # Print results in Python dict format for easy copy-paste
    print("\n" + "="*60)
    print("COPY THE FOLLOWING TO YOUR LEAGUE FILES:")
    print("="*60)
    
    for league_name, standings in all_standings.items():
        print(f"\n# {league_name.upper()} LEAGUE - GW13 Standings")
        print("13: {")
        for team, pts in sorted(standings.items(), key=lambda x: -x[1]):
            print(f'    "{team}": {pts},')
        print("},")


if __name__ == '__main__':
    main()
