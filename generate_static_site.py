import os
import csv
import shutil
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


def calc_points(hoh_winners, veto_winners, off_block, other_comp_winners, evictions, americas_favorite, buy_back, picks):
    weekly_scores = {player: [0] * (len(hoh_winners) + 1) for player in picks}
    total_scores = {player: 0 for player in picks}
    points_log = []

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

        if len(evictions) == 16 + len(buy_back):
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

    for player in weekly_scores:
        total_scores[player] = sum(weekly_scores[player])

    with open(os.path.join(DATA_DIR, 'test_log.csv'), 'w', newline='') as file:
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


def find_file(*names):
    for name in names:
        path = os.path.join(DATA_DIR, name)
        if os.path.exists(path):
            return path
    raise FileNotFoundError(f'None of {names} found in {DATA_DIR}')


def main():
    picks_file = find_file('picks.csv', 'picks_26.csv', 'test_picks.csv')
    winners_file = find_file('winners.csv', 'winners_26.csv', 'test_winners.csv')
    points_file = find_file('points.csv', 'points_26.csv', 'test_points.csv')
    log_file = find_file('log.csv', 'test_log.csv')

    picks_headers, picks = read_picks_from_csv(picks_file)
    hoh, veto, off_block, other_comp, evictions, buy_back, fav = read_winners_from_csv(winners_file)
    weekly_scores, total_scores = calc_points(hoh, veto, off_block, other_comp, evictions, fav, buy_back, picks)

    plot_total_scores(total_scores)
    plot_scores_over_time(weekly_scores)

    shutil.copy(os.path.join(IMAGE_SRC, 'total_scores.png'), os.path.join(IMAGE_DST, 'total_scores.png'))
    shutil.copy(os.path.join(IMAGE_SRC, 'cumulative_scores.png'), os.path.join(IMAGE_DST, 'cumulative_scores.png'))

    picks_data = read_raw_data_from_csv(picks_file)
    points_headers, points_data = read_points_from_csv(points_file)
    winners_raw = read_raw_data_from_csv(winners_file)

    num_weeks = len(winners_raw[0]) - 1
    winners_headers = ['Category'] + [f'Week {i+1}' for i in range(num_weeks)]
    winners_data = [[row[0]] + row[1:] for row in winners_raw]

    logs = read_logs_from_csv(log_file)
    player_names = list(logs.keys())
    leaderboard = sorted(total_scores.items(), key=lambda x: x[1], reverse=True)

    env = Environment(loader=FileSystemLoader(os.path.join(BASE_DIR, 'templates')))
    template = env.get_template('index.html')
    html = template.render(
        total_scores_img='static/images/total_scores.png',
        cumulative_scores_img='static/images/cumulative_scores.png',
        picks_headers=picks_headers,
        picks_data=picks_data,
        points_headers=points_headers,
        points_data=points_data,
        winners_headers=winners_headers,
        winners_data=winners_data,
        leaderboard=leaderboard,
        logs=logs,
        player_names=player_names
    )

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(os.path.join(OUTPUT_DIR, 'index.html'), 'w') as f:
        f.write(html)


if __name__ == '__main__':
    main()
