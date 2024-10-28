import json

import nfl_data_py as nfl # type: ignore
from datetime import datetime, timedelta

year = 2024
week = 0
debug = False
discarded = False
refresh_cache = False
print_result = True
use_cache = False
no_secondary = False
print_rank = True

min_score = 37
min_ot_score = 35
max_final_differential = 15

preferred_teams = []
preferred_team_bonus = 1

preferred_min_score = 50
preferred_max_final_differential = 7
preferred_max_Q4_differential = 4
preferred_min_lead_changes = 2
preferred_Q4_scores = 4
big_score_bonus = 60
really_close_bonus = 3

min_preferred_rank = 5
min_rank = 3
ot_bonus = 1

team_names = {
    'ARI': 'Cardinals',
    'ATL': 'Falcons',
    'BAL': 'Ravens',
    'BUF': 'Bills',
    'CAR': 'Panthers',
    'CHI': 'Bears',
    'CIN': 'Bengals',
    'CLE': 'Browns',
    'DAL': 'Cowboys',
    'DEN': 'Broncos',
    'DET': 'Lions',
    'GB': 'Packers',
    'HOU': 'Texans',
    'IND': 'Colts',
    'JAX': 'Jaguars',
    'KC': 'Chiefs',
    'LV': 'Raiders',
    'LAC': 'Chargers',
    'LA': 'Rams',
    'MIA': 'Dolphins',
    'MIN': 'Vikings',
    'NE': 'Patriots',
    'NO': 'Saints',
    'NYG': 'Giants',
    'NYJ': 'Jets',
    'PIT': 'Steelers',
    'PHI': 'Eagles',
    'SF': '49ers',
    'SEA': 'Seahawks',
    'TB': 'Buccaneers',
    'TEN': 'Titans',
    'WAS': 'Commanders',
}

if __name__ == '__main__':
    if refresh_cache:
        nfl.cache_pbp([year], True, '/Users/nils/proj')

    cols = [
        'game_id',
        'qtr',
        'home_team',
        'away_team',
        'week',
        'play_type',
        'start_time',
        'sp',
        'total_home_score',
        'total_away_score',
        'home_score',
        'away_score',
        'game_seconds_remaining',
        'game_half'
    ]
    ydf = nfl.import_pbp_data([year], cols, False, False, use_cache, "", True)

    if week > 0:
        filter_ = (ydf['sp'] == 1.0) & (ydf['play_type'] != 'extra_point') & (ydf['week'] == week)
    else:
        filter_ = (ydf['sp'] == 1.0) & (ydf['play_type'] != 'extra_point')

    wdf = ydf[filter_]

    game_ids = wdf['game_id'].unique()

    gamedf = {}
    gamestats = {}

    print("Considered games")
    for game_id in game_ids:
        game = wdf[wdf['game_id'] == game_id]
        print(game_id)
        gamestats[game_id] = {
            'kickoff': 0,
            'week': 0,
            'final_score': '0 - 0',
            'total_score': 0,
            'overtime': False,
            'lead_changes': 0,
            'Q4_weighted_differential': 0,
            'Q4_scores': 0,
            'final_differential': 0,
            'biggest_spread': 0,
            'rank': 0,
            'preferred_team_home': False,
            'preferred_team_away': False
        }

        last_differential = 0
        last_time = 3600.0
        tw = 0.0
        twq4 = 0.0

        for (ndx, score) in game.iterrows():
            gamestats[game_id]['kickoff'] = datetime.strptime(score['start_time'], '%m/%d/%y, %H:%M:%S')
            gamestats[game_id]['week'] = score['week']

            gamestats[game_id]['final_score'] = str(score['home_score']) + ' - ' + str(score['away_score'])
            gamestats[game_id]['total_score'] = score['home_score'] + score['away_score']

            spread = abs(score['total_home_score'] - score['total_away_score'])
            gamestats[game_id]['biggest_spread'] = max(gamestats[game_id]['biggest_spread'], spread)

            if (score['home_team'] in preferred_teams):
                gamestats[game_id]['preferred_team_home'] = True

            if (score['away_team'] in preferred_teams):
                gamestats[game_id]['preferred_team_away'] = True

            if score['game_half'] != 'Overtime':
                time_span = last_time - score['game_seconds_remaining']
                last_time = score['game_seconds_remaining']
                weight = time_span/3600.0
                tw += weight
                differential = int(score['total_home_score'] - score['total_away_score'])
                if differential == 0:
                    gamestats[game_id]['lead_changes'] += 1
                if (differential > 0) & (last_differential <= 0):
                    gamestats[game_id]['lead_changes'] += 1
                if (differential < 0) & (last_differential >= 0):
                    gamestats[game_id]['lead_changes'] += 1
                last_differential = differential

                if score['qtr'] == 4.0:
                    twq4 += weight
                    gamestats[game_id]['Q4_weighted_differential'] += (abs(last_differential) * weight)
                    gamestats[game_id]['Q4_scores'] += 1
            else:
                gamestats[game_id]['overtime'] = True

        if twq4 > 0.0:
            gamestats[game_id]['Q4_weighted_differential'] /= twq4
        else:
            gamestats[game_id]['Q4_weighted_differential'] = 100.0

        gamestats[game_id]['final_differential'] = abs(score['home_score'] - score['away_score'])

    print()

    watch_list = []

    scheds = nfl.import_schedules([year])
    friendly_names = {}
    all_games = {}
    for (ndx, sd) in scheds.iterrows():
        friendly_names[sd['game_id']] = f"{sd['away_team']} @ {sd['home_team']} - {sd['gameday']} {sd['weekday']}, {sd['gametime']}"
        all_games[sd['game_id']] = {
            'away_team':sd['away_team'],
            'home_team': sd['home_team'],
            'week': sd['week'],
            'gametime': datetime.strptime(f"{sd['gameday']} {sd['gametime']}", '%Y-%m-%d %H:%M') - timedelta(hours=3),
            'status': 'no_data'
        }

    discarded_score = []
    discarded_final_differential = []

    for (game_id) in gamestats:
        gs = gamestats[game_id]

        if gs['overtime']:
            if debug:
                print(f"{game_id} included shortcut: overtime and total_score ({gs['total_score']}) >= min_ot_score ({min_ot_score})")
                print(gs)
                print()
            watch_list.append(game_id)
            continue

        if gs['total_score'] < min_score:
            if debug:
                print(f"{game_id} discarded: total_score ({gs['total_score']}) < min_score ({min_score})")
                print(gs)
                print()
            discarded_score.append(game_id)
            all_games[game_id]['status'] = 'discarded_score'
            continue

        if gs['final_differential'] > max_final_differential:
            if debug:
                print(f"{game_id} discarded: final_differential ({gs['final_differential']}) > max_final_differential ({max_final_differential})")
                print(gs)
                print()
            discarded_final_differential.append(game_id)
            all_games[game_id]['status'] = 'discarded_differential'
            continue

        watch_list.append(game_id)

    preferred_watch = {}
    secondary_watch = {}

    for game_id in watch_list:
        gs = gamestats[game_id]
        rank = 0
        if gs['overtime']:
            rank += ot_bonus

        if gs['total_score'] >= preferred_min_score:
            rank += 1

        if gs['total_score'] >= big_score_bonus:
            rank += 1

        if gs['final_differential'] <= preferred_max_final_differential:
            rank += 1

        if gs['final_differential'] <= really_close_bonus:
            rank += 1

        if gs['Q4_weighted_differential'] <= preferred_max_Q4_differential:
            rank += 1

        if gs['lead_changes'] >= preferred_min_lead_changes:
            rank += 1

        if gs['Q4_scores'] >= preferred_Q4_scores:
            rank += 1

        if gs['preferred_team_home']:
            rank += preferred_team_bonus

        if gs['preferred_team_away']:
            rank += preferred_team_bonus

        gs['rank'] = rank

        if rank >= min_preferred_rank:
            preferred_watch[game_id] = rank
            all_games[game_id]['status'] = 'preferred'
        elif rank >= min_rank:
            if no_secondary:
                preferred_watch[game_id] = rank
                all_games[game_id]['status'] = 'preferred'
            else:
                secondary_watch[game_id] = rank
                all_games[game_id]['status'] = 'secondary'
        else:
            all_games[game_id]['status'] = 'discarded_rank'
            if debug:
                print(f"{game_id} discarded: rank ({rank}) < min_rank ({min_rank})")
                print(gs)
                print()

    import operator
    preferred_watch = sorted(preferred_watch.items(), key=operator.itemgetter(1), reverse=True)
    secondary_watch = sorted(secondary_watch.items(), key=operator.itemgetter(1), reverse=True)

    if discarded:
        print("\nDISCARDED SCORE\n")
        for game_id in discarded_score:
            print(game_id)
            print(gamestats[game_id])
            print()
        print()

    if discarded:
        print("DISCARDED FINAL DIFFERENTIAL\n")
        for game_id in discarded_final_differential:
            print(game_id)
            print(gamestats[game_id])
            print()
        print()

    if print_result:
        print("\nPREFERRED")

        for (game_id, rank) in preferred_watch:
            if print_rank:
                print(f"{friendly_names[game_id]}, rank ({rank})")
            else:
                print(friendly_names[game_id])
            if debug:
                print(gamestats[game_id])
                game = wdf[wdf['game_id'] == game_id]
                print(game.to_string())
                print()

        print()

        print("SECONDARY")
        for (game_id, rank) in secondary_watch:
            if print_rank:
                print(f"{friendly_names[game_id]}, rank ({rank})")
            else:
                print(friendly_names[game_id])
            if debug:
                print(gamestats[game_id])
                game = wdf[wdf['game_id'] == game_id]
                print(game.to_string())
                print()

    all_games = sorted(all_games.items(), key=lambda x: x[1]['gametime'])
    broadcast_map = {}

    final_ouput = {'year': year, 'current_week': 0, 'weeks': []}
    current_week = None
    current_day = None
    latest_week = None

    for (game_id, game_obj) in all_games:
        broadcast_map[game_id] = '';

        day = game_obj['gametime'].strftime("%A, %B %d")
        time = game_obj['gametime'].strftime("%I:%M %p").strip('0')


        if current_week != game_obj['week']:
            current_week = game_obj['week']
            final_ouput['weeks'].append({"week": current_week, 'days': []})

        if current_day != day:
            current_day = day
            final_ouput['weeks'][-1]['days'].append({'day':current_day, 'games': []})

        if (game_obj['status'] != 'no_data') & (latest_week != game_obj['week']):
            latest_week = game_obj['week']

        final_ouput['weeks'][-1]['days'][-1]['games'].append({'home_team': game_obj['home_team'], 'away_team': game_obj['away_team'], 'game_time': time, 'status': game_obj['status'],
                                                              'home_team_name': team_names[game_obj['home_team']], 'away_team_name': team_names[game_obj['away_team']], 'game_key': game_id})

    final_ouput['current_week'] = latest_week

    f = open("content/games.json", "w")
    f.write(json.dumps(final_ouput, indent=4))
    f.close()
    #f = open("content/broadcast_map.json", "w")
    #f.write(json.dumps(broadcast_map, indent=4))
    f.close()
