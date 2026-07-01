import os
import csv
import shutil
import re
from jinja2 import Environment, FileSystemLoader
import matplotlib.pyplot as plt
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
OUTPUT_DIR = os.path.join(BASE_DIR, 'docs')
IMAGE_SRC = os.path.join(BASE_DIR, 'static', 'images')
IMAGE_DST = os.path.join(OUTPUT_DIR, 'static', 'images')

os.makedirs(IMAGE_DST, exist_ok=True)


def read_logs_from_csv(filename):
    logs = {}
    try:
        with open(filename, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                log_entry = row[0]
                player_name = log_entry.split()[0]
                logs.setdefault(player_name, []).append(log_entry)
    except Exception as e:
        print(f"Error reading {filename}: {e}")
    return logs


def read_picks_from_csv(filename):
    picks = {}
    headers = []
    try:
        with open(filename, 'r') as file:
            reader = csv.reader(file)
            headers = next(reader)
            for row in reader:
                picks[row[0]] = row[1:]
    except Exception as e:
        print(f"Error reading {filename}: {e}")
    return headers, picks


def read_winners_from_csv(filename):
    with open(filename, 'r') as file:
        reader = csv.reader(file)
        data = list(reader)

    hoh_winners = [x for x in data[0][1:] if x]
    veto_winners = [x for x in data[1][1:] if x]

    other_comp_winners_raw = [x for x in data[3][1:] if x]
    evictions = [x for x in data[4][1:] if x]

    off_block_raw = [x for x in data[2][1:] if x]
    off_block = {}
    for i in range(0, len(off_block_raw), 2):
        week = int(off_block_raw[i])
        players = off_block_raw[i + 1].split(',')
        off_block.setdefault(week, []).extend(players)

    other_comp_winners = {}
    for i in range(0, len(other_comp_winners_raw), 2):
        week = int(other_comp_winners_raw[i])
        winners = other_comp_winners_raw[i + 1].split(',')
        other_comp_winners.setdefault(week, []).extend(winners)

    buy_back_raw = [x for x in data[5][1:] if x]
    buy_back = {}
    for i in range(0, len(buy_back_raw), 2):
        week = int(buy_back_raw[i])
        winners = buy_back_raw[i + 1].split(',')
        buy_back.setdefault(week, []).extend(winners)

    americas_favorite = data[6][1]

    return hoh_winners, veto_winners, off_block, other_comp_winners, evictions, buy_back, americas_favorite


def read_points_from_csv(filename):
    headers = []
    points = []
    try:
        with open(filename, 'r') as file:
            reader = csv.reader(file)
            headers = next(reader)
            points = list(reader)
    except Exception as e:
        print(f"Error reading {filename}: {e}")
    return headers, points


def points_rows_to_scores(points_data):
    weekly_scores = {}
    total_scores = {}
    for row in points_data:
        if len(row) < 3:
            continue
        player = row[0]
        try:
            total_scores[player] = float(row[1])
            weekly_scores[player] = [float(value) for value in row[2:]]
        except ValueError:
            continue
    return weekly_scores, total_scores


def calc_points(hoh_winners, veto_winners, off_block, other_comp_winners, evictions, americas_favorite, buy_back, picks):
    weekly_scores = {player: [0] * (len(hoh_winners) + 1) for player in picks}
    total_scores = {player: 0 for player in picks}
    points_log = []
    number_of_players = 17 # change if number of players is different than last season

    def log_points(player, points, reason, week):
        action = "gained" if points >= 0 else "lost"
        points_log.append([f"{player} {action} {abs(points)} points because {reason} during week {week+1}."])

    for player in picks:
        for idx, winner in enumerate(hoh_winners):
            for ranking, pick in enumerate(picks[player]):
                if pick == winner:
                    points = 10 - ranking
                    weekly_scores[player][idx] += points
                    log_points(player, points, f"{pick} won HOH", idx)

        for idx, winner in enumerate(veto_winners):
            for ranking, pick in enumerate(picks[player]):
                if pick == winner:
                    points = 10 - ranking
                    weekly_scores[player][idx] += points
                    log_points(player, points, f"{pick} won Veto", idx)

        for week, players in off_block.items():
            for off_block_player in players:
                for ranking, pick in enumerate(picks[player]):
                    if pick == off_block_player:
                        points = 7.5 - (ranking * 0.75)
                        weekly_scores[player][week] += points
                        log_points(player, points, f"{pick} got off the block", week)

        for week, winners in other_comp_winners.items():
            for winner in winners:
                for ranking, pick in enumerate(picks[player]):
                    if pick == winner:
                        points = 5 - (ranking * 0.5)
                        weekly_scores[player][week] += points
                        log_points(player, points, f"{pick} won another competition", week)

        for week, winners in buy_back.items():
            for winner in winners:
                for ranking, pick in enumerate(picks[player]):
                    if pick == winner:
                        points = 10 - ranking
                        weekly_scores[player][week] += points
                        log_points(player, points, f"{pick} won buy back", week)

        if len(evictions) == number_of_players + len(buy_back):
            if picks[player] == evictions[::-1]:
                points = 100
                weekly_scores[player][-1] += points
                log_points(player, points, "perfect prediction of evictions", len(hoh_winners))
            if picks[player][0] == americas_favorite:
                weekly_scores[player][-1] += 75
            elif picks[player][1] == americas_favorite:
                weekly_scores[player][-1] += 50
            elif picks[player][2] == americas_favorite:
                weekly_scores[player][-1] += 25
            elif picks[player][-1] == americas_favorite:
                weekly_scores[player][-1] -= 50
            elif picks[player][-2] == americas_favorite:
                weekly_scores[player][-1] -= 25
            elif picks[player][-3] == americas_favorite:
                weekly_scores[player][-1] -= 10

            final_week_index = len(hoh_winners)

            season_winner = evictions[-1]
            if picks[player][0] == season_winner:
                points = 100
                weekly_scores[player][-1] += points
                log_points(player, points, f"{season_winner} won the season and you ranked them first", final_week_index)
            elif picks[player][1] == season_winner:
                points = 75
                weekly_scores[player][-1] += points
                log_points(player, points, f"{season_winner} won the season and you ranked them second", final_week_index)
            elif picks[player][2] == season_winner:
                points = 50
                weekly_scores[player][-1] += points
                log_points(player, points, f"{season_winner} won the season and you ranked them third", final_week_index)
            elif picks[player][-1] == season_winner:
                points = -75
                weekly_scores[player][-1] += points
                log_points(player, points, f"{season_winner} won the season but you ranked them last", final_week_index)
            elif picks[player][-2] == season_winner:
                points = -50
                weekly_scores[player][-1] += points
                log_points(player, points, f"{season_winner} won the season but you ranked them second to last", final_week_index)
            elif picks[player][-3] == season_winner:
                points = -25
                weekly_scores[player][-1] += points
                log_points(player, points, f"{season_winner} won the season but you ranked them third to last", final_week_index)

            runner_up = evictions[-2]
            if picks[player][0] == runner_up:
                points = 75
                weekly_scores[player][-1] += points
                log_points(player, points, f"{runner_up} finished runner-up and you ranked them first", final_week_index)
            elif picks[player][1] == runner_up:
                points = 50
                weekly_scores[player][-1] += points
                log_points(player, points, f"{runner_up} finished runner-up and you ranked them second", final_week_index)
            elif picks[player][2] == runner_up:
                points = 25
                weekly_scores[player][-1] += points
                log_points(player, points, f"{runner_up} finished runner-up and you ranked them third", final_week_index)
            elif picks[player][-1] == runner_up:
                points = -50
                weekly_scores[player][-1] += points
                log_points(player, points, f"{runner_up} finished runner-up but you ranked them last", final_week_index)
            elif picks[player][-2] == runner_up:
                points = -25
                weekly_scores[player][-1] += points
                log_points(player, points, f"{runner_up} finished runner-up but you ranked them second to last", final_week_index)
            elif picks[player][-3] == runner_up:
                points = -10
                weekly_scores[player][-1] += points
                log_points(player, points, f"{runner_up} finished runner-up but you ranked them third to last", final_week_index)

            third_place = evictions[-3]
            if picks[player][0] == third_place:
                points = 50
                weekly_scores[player][-1] += points
                log_points(player, points, f"{third_place} finished third and you ranked them first", final_week_index)
            elif picks[player][1] == third_place:
                points = 25
                weekly_scores[player][-1] += points
                log_points(player, points, f"{third_place} finished third and you ranked them second", final_week_index)
            elif picks[player][2] == third_place:
                points = 10
                weekly_scores[player][-1] += points
                log_points(player, points, f"{third_place} finished third and you ranked them third", final_week_index)
            elif picks[player][-1] == third_place:
                points = -25
                weekly_scores[player][-1] += points
                log_points(player, points, f"{third_place} finished third but you ranked them last", final_week_index)
            elif picks[player][-2] == third_place:
                points = -10
                weekly_scores[player][-1] += points
                log_points(player, points, f"{third_place} finished third but you ranked them second to last", final_week_index)
            elif picks[player][-3] == third_place:
                points = -5
                weekly_scores[player][-1] += points
                log_points(player, points, f"{third_place} finished third but you ranked them third to last", final_week_index)


    for player in weekly_scores:
        total_scores[player] = sum(weekly_scores[player])

    with open(os.path.join(DATA_DIR, 'log.csv'), 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(points_log)

    with open(os.path.join(DATA_DIR, 'points.csv'), 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Player', 'Total Points'] + [f'Week {i+1}' for i in range(len(weekly_scores[next(iter(weekly_scores))]))])
        for player, scores in weekly_scores.items():
            writer.writerow([player, sum(scores)] + scores)

    return weekly_scores, total_scores


def plot_total_scores(total_scores):
    sorted_scores = {k: v for k, v in sorted(total_scores.items(), key=lambda x: x[1], reverse=True)}
    plt.figure(figsize=(14, 8))
    plt.bar(sorted_scores.keys(), sorted_scores.values(), color='blue')
    average_score = np.mean(list(sorted_scores.values()))
    plt.axhline(y=average_score, color='r', linestyle='-', label=f'Average Score: {average_score:.2f}')
    plt.axhline(y=0, color='black', linestyle='-')
    plt.xlabel('Players')
    plt.ylabel('Total Points')
    plt.title('Total Points per Player')
    plt.legend()
    plt.xticks(rotation=45)
    plt.savefig(os.path.join(IMAGE_SRC, 'total_scores.png'), bbox_inches='tight')
    plt.close()


def plot_scores_over_time(weekly_scores):
    plt.figure(figsize=(14, 8))
    players = list(weekly_scores.keys())
    for player in players:
        cumulative_score = np.cumsum(weekly_scores[player])
        plt.plot(cumulative_score, label=player)
    weekly_averages = np.mean([weekly_scores[player] for player in players], axis=0)
    cumulative_average = np.cumsum(weekly_averages)
    plt.plot(cumulative_average, label='Average', color='black', linestyle='--')
    plt.xlabel('Week')
    plt.ylabel('Cumulative Points')
    plt.legend()
    plt.title('Cumulative Points over Time per Player')
    plt.savefig(os.path.join(IMAGE_SRC, 'cumulative_scores.png'))
    plt.close()


def read_raw_data_from_csv(filename):
    data = []
    try:
        with open(filename, 'r') as file:
            reader = csv.reader(file)
            data = list(reader)
    except Exception as e:
        print(f"Error reading {filename}: {e}")
    return data


def format_points(value):
    if float(value).is_integer():
        return str(int(value))
    return f'{value:.2f}'.rstrip('0').rstrip('.')


def build_player_chart_data(weekly_scores, total_scores):
    sorted_players = sorted(total_scores.items(), key=lambda x: x[1], reverse=True)
    leaders_total = sorted_players[0][1] if sorted_players else 0
    players = []
    for rank, (player, total) in enumerate(sorted_players, start=1):
        weekly = [float(score) for score in weekly_scores[player]]
        cumulative = np.cumsum(weekly).tolist()
        players.append({
            'rank': rank,
            'name': player,
            'total': float(total),
            'totalLabel': format_points(float(total)),
            'weekly': weekly,
            'cumulative': [float(score) for score in cumulative],
            'lastWeek': weekly[-1] if weekly else 0,
            'bestWeek': max(weekly) if weekly else 0,
            'gap': float(leaders_total - total),
        })
    return players


def build_summary(player_chart_data):
    if not player_chart_data:
        return {
            'leader': 'TBD',
            'leaderPoints': '0',
            'playerCount': 0,
            'weeksScored': 0,
            'averageScore': '0',
            'highestWeekPlayer': 'TBD',
            'highestWeekPoints': '0',
        }

    total_points = [player['total'] for player in player_chart_data]
    highest_week_player = max(player_chart_data, key=lambda player: player['bestWeek'])
    return {
        'leader': player_chart_data[0]['name'],
        'leaderPoints': player_chart_data[0]['totalLabel'],
        'playerCount': len(player_chart_data),
        'weeksScored': len(player_chart_data[0]['weekly']),
        'averageScore': format_points(float(np.mean(total_points))),
        'highestWeekPlayer': highest_week_player['name'],
        'highestWeekPoints': format_points(float(highest_week_player['bestWeek'])),
    }


def points_by_rank(contestant_count, formula):
    return [float(formula(rank, contestant_count)) for rank in range(contestant_count)]


def final_bonus_points(rank, contestant_count, positive, negative):
    if rank < len(positive):
        return positive[rank]
    reverse_index = contestant_count - 1 - rank
    if reverse_index < len(negative):
        return negative[reverse_index]
    return 0


def build_contestant_events(hoh_winners, veto_winners, off_block, other_comp_winners,
                            evictions, buy_back, americas_favorite, contestant_count,
                            week_count):
    events = []

    def add_event(contestant, week, reason, rank_points):
        if not contestant or week < 0 or week >= week_count:
            return
        events.append({
            'contestant': contestant,
            'week': week,
            'reason': reason,
            'pointsByRank': rank_points,
        })

    for week, winner in enumerate(hoh_winners):
        add_event(winner, week, 'HOH win', points_by_rank(contestant_count, lambda rank, _count: 10 - rank))

    for week, winner in enumerate(veto_winners):
        add_event(winner, week, 'Veto win', points_by_rank(contestant_count, lambda rank, _count: 10 - rank))

    for week, contestants in off_block.items():
        for contestant in contestants:
            add_event(contestant, week, 'Got off the block', points_by_rank(contestant_count, lambda rank, _count: 7.5 - (rank * 0.75)))

    for week, contestants in other_comp_winners.items():
        for contestant in contestants:
            add_event(contestant, week, 'Other competition win', points_by_rank(contestant_count, lambda rank, _count: 5 - (rank * 0.5)))

    for week, contestants in buy_back.items():
        for contestant in contestants:
            add_event(contestant, week, 'Buy back', points_by_rank(contestant_count, lambda rank, _count: 10 - rank))

    season_complete = len(evictions) >= contestant_count
    final_week = min(max(len(hoh_winners), 0), max(week_count - 1, 0))
    if season_complete and week_count:
        if americas_favorite:
            add_event(
                americas_favorite,
                final_week,
                "America's Favorite",
                points_by_rank(contestant_count, lambda rank, count: final_bonus_points(rank, count, [75, 50, 25], [-50, -25, -10])),
            )

        placements = [
            (evictions[-1] if len(evictions) >= 1 else '', 'Season winner', [100, 75, 50], [-75, -50, -25]),
            (evictions[-2] if len(evictions) >= 2 else '', 'Runner-up', [75, 50, 25], [-50, -25, -10]),
            (evictions[-3] if len(evictions) >= 3 else '', 'Third place', [50, 25, 10], [-25, -10, -5]),
        ]
        for contestant, reason, positive, negative in placements:
            add_event(
                contestant,
                final_week,
                reason,
                points_by_rank(contestant_count, lambda rank, count, p=positive, n=negative: final_bonus_points(rank, count, p, n)),
            )

    return events


def build_contestant_breakdown(picks, hoh_winners, veto_winners, off_block,
                               other_comp_winners, evictions, buy_back,
                               americas_favorite, week_count):
    contestants = sorted({contestant for player_picks in picks.values() for contestant in player_picks if contestant})
    contestant_count = max([len(player_picks) for player_picks in picks.values()], default=len(contestants))
    if not contestants or not week_count:
        return []

    events = build_contestant_events(
        hoh_winners,
        veto_winners,
        off_block,
        other_comp_winners,
        evictions,
        buy_back,
        americas_favorite,
        contestant_count,
        week_count,
    )
    events_by_contestant = {}
    for event in events:
        events_by_contestant.setdefault(event['contestant'], []).append(event)

    rank_by_player = {
        player: {contestant: rank for rank, contestant in enumerate(player_picks)}
        for player, player_picks in picks.items()
    }

    breakdown = []
    for contestant in contestants:
        actual_weekly = [0.0] * week_count
        weekly_by_rank = [[0.0] * week_count for _ in range(contestant_count)]
        event_summaries = []
        for event in events_by_contestant.get(contestant, []):
            week = event['week']
            for rank, value in enumerate(event['pointsByRank']):
                weekly_by_rank[rank][week] += value
            for player_rankings in rank_by_player.values():
                rank = player_rankings.get(contestant)
                if rank is not None and rank < len(event['pointsByRank']):
                    actual_weekly[week] += event['pointsByRank'][rank]
            event_summaries.append({
                'week': week,
                'reason': event['reason'],
                'firstRankPoints': event['pointsByRank'][0] if event['pointsByRank'] else 0,
            })

        actual_cumulative = np.cumsum(actual_weekly).tolist()
        breakdown.append({
            'name': contestant,
            'actualWeekly': [float(value) for value in actual_weekly],
            'actualCumulative': [float(value) for value in actual_cumulative],
            'actualTotal': float(sum(actual_weekly)),
            'weeklyByRank': weekly_by_rank,
            'events': event_summaries,
        })

    return sorted(breakdown, key=lambda item: item['actualTotal'], reverse=True)


def build_blank_season():
    return {
        'id': 'current',
        'label': 'Big Brother 28',
        'status': 'No current-season scoring data has been added yet.',
        'isArchive': False,
        'isEmpty': True,
        'playerChartData': [],
        'weekLabels': [],
        'summary': build_summary([]),
        'picksHeaders': ['name'],
        'picksData': [],
        'pointsHeaders': ['Player', 'Total Points'],
        'pointsData': [],
        'winnersHeaders': ['Category'],
        'winnersData': [],
        'logs': {},
        'playerNames': [],
        'contestants': [],
    }


def build_season(season_id, label, picks_file, winners_file, points_file, log_file=None, status='Archived season'):
    picks_headers, picks = read_picks_from_csv(picks_file)
    points_headers, points_data = read_points_from_csv(points_file)
    weekly_scores, total_scores = points_rows_to_scores(points_data)
    winners_raw = read_raw_data_from_csv(winners_file)
    hoh, veto, off_block, other_comp, evictions, buy_back, fav = read_winners_from_csv(winners_file)

    week_count = len(next(iter(weekly_scores.values()), [])) if weekly_scores else 0
    week_labels = [f'Week {i+1}' for i in range(week_count)]
    winners_headers = ['Category'] + [f'Week {i+1}' for i in range(max((len(row) for row in winners_raw), default=1) - 1)]
    winners_data = [[row[0]] + row[1:] for row in winners_raw]
    logs = read_logs_from_csv(log_file) if log_file and os.path.exists(log_file) else {}
    player_chart_data = build_player_chart_data(weekly_scores, total_scores)

    return {
        'id': season_id,
        'label': label,
        'status': status,
        'isArchive': True,
        'isEmpty': not bool(player_chart_data),
        'playerChartData': player_chart_data,
        'weekLabels': week_labels,
        'summary': build_summary(player_chart_data),
        'picksHeaders': picks_headers,
        'picksData': read_raw_data_from_csv(picks_file)[1:],
        'pointsHeaders': points_headers,
        'pointsData': points_data,
        'winnersHeaders': winners_headers,
        'winnersData': winners_data,
        'logs': logs,
        'playerNames': list(logs.keys()),
        'contestants': build_contestant_breakdown(picks, hoh, veto, off_block, other_comp, evictions, buy_back, fav, week_count),
    }


def discover_archive_seasons():
    seasons = [
        build_season(
            'previous',
            'Big Brother 27',
            os.path.join(DATA_DIR, 'picks.csv'),
            os.path.join(DATA_DIR, 'winners.csv'),
            os.path.join(DATA_DIR, 'points.csv'),
            os.path.join(DATA_DIR, 'log.csv'),
            'Most recent completed draft season',
        )
    ]

    archive_dir = os.path.join(DATA_DIR, 'archived_data')
    if os.path.isdir(archive_dir):
        for filename in sorted(os.listdir(archive_dir)):
            match = re.match(r'points_(.+)\.csv$', filename)
            if not match:
                continue
            suffix = match.group(1)
            picks_file = os.path.join(archive_dir, f'picks_{suffix}.csv')
            winners_file = os.path.join(archive_dir, f'winners_{suffix}.csv')
            points_file = os.path.join(archive_dir, filename)
            if os.path.exists(picks_file) and os.path.exists(winners_file):
                seasons.append(build_season(
                    f'archive-{suffix}',
                    f'Big Brother {suffix}',
                    picks_file,
                    winners_file,
                    points_file,
                    None,
                    f'Archived season {suffix}',
                ))
    return seasons


def find_file(*names):
    for name in names:
        path = os.path.join(DATA_DIR, name)
        if os.path.exists(path):
            return path
    raise FileNotFoundError(f'None of {names} found in {DATA_DIR}')


def main():
    current_season = build_blank_season()
    archive_seasons = discover_archive_seasons()
    seasons = [current_season] + archive_seasons

    if archive_seasons:
        latest_archive = archive_seasons[0]
        latest_weekly_scores = {
            player['name']: player['weekly']
            for player in latest_archive['playerChartData']
        }
        latest_total_scores = {
            player['name']: player['total']
            for player in latest_archive['playerChartData']
        }
        if latest_weekly_scores and latest_total_scores:
            plot_total_scores(latest_total_scores)
            plot_scores_over_time(latest_weekly_scores)
            shutil.copy(os.path.join(IMAGE_SRC, 'total_scores.png'), os.path.join(IMAGE_DST, 'total_scores.png'))
            shutil.copy(os.path.join(IMAGE_SRC, 'cumulative_scores.png'), os.path.join(IMAGE_DST, 'cumulative_scores.png'))

    env = Environment(loader=FileSystemLoader(os.path.join(BASE_DIR, 'templates')))
    template = env.get_template('index.html')
    html = template.render(
        total_scores_img='static/images/total_scores.png',
        cumulative_scores_img='static/images/cumulative_scores.png',
        picks_headers=current_season['picksHeaders'],
        picks_data=current_season['picksData'],
        points_headers=current_season['pointsHeaders'],
        points_data=current_season['pointsData'],
        winners_headers=current_season['winnersHeaders'],
        winners_data=current_season['winnersData'],
        leaderboard=[],
        logs=current_season['logs'],
        player_names=current_season['playerNames'],
        player_chart_data=current_season['playerChartData'],
        week_labels=current_season['weekLabels'],
        summary=current_season['summary'],
        seasons=seasons,
        archive_seasons=archive_seasons,
        active_season_id=current_season['id'],
    )

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(os.path.join(OUTPUT_DIR, 'index.html'), 'w') as f:
        f.write(html)


if __name__ == '__main__':
    main()
