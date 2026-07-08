from flask import Flask, render_template, request
import csv
import matplotlib.pyplot as plt
import os
import numpy as np

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

# Define paths
base_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(base_dir, 'data')
images_dir = os.path.join(base_dir, 'static', 'images')
current_season_token = 'bb28'
picks_file = os.path.join(data_dir, f'picks_{current_season_token}.csv')
winners_file = os.path.join(data_dir, f'winners_{current_season_token}.csv')
points_file = os.path.join(data_dir, f'points_{current_season_token}.csv')
log_file = os.path.join(data_dir, f'log_{current_season_token}.csv')

# Ensure directories exist
os.makedirs(images_dir, exist_ok=True)


def read_logs_from_csv(filename):
    logs = {}
    try:
        with open(filename, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                if not row or not row[0].strip():
                    continue
                log_entry = row[0]
                player_name = log_entry.split()[0]  # Extract the player's name
                if player_name not in logs:
                    logs[player_name] = []
                logs[player_name].append(log_entry)
        print(f"Loaded logs from {filename}: {logs}")
    except Exception as e:
        print(f"Error reading {filename}: {e}")
    return logs

# Read picks from CSV file
def read_picks_from_csv(filename):
    picks = {}
    headers = []
    try:
        with open(filename, 'r') as file:
            reader = csv.reader(file)
            headers = next(reader)
            for row in reader:
                if not row or not row[0].strip():
                    continue
                picks[row[0]] = row[1:]
        print(f"Loaded picks from {filename}: {picks}")
    except Exception as e:
        print(f"Error reading {filename}: {e}")
    return headers, picks

def read_winners_from_csv(filename):
    with open(filename, 'r') as file:
        reader = csv.reader(file)
        data = list(reader)

    def row_values(index):
        if index >= len(data):
            return []
        return [x.strip() for x in data[index][1:] if x.strip()]

    def parse_week_pairs(values):
        parsed = {}
        for i in range(0, len(values) - 1, 2):
            try:
                week = int(values[i])
            except ValueError:
                continue
            winners = [winner.strip() for winner in values[i + 1].split(',') if winner.strip()]
            parsed.setdefault(week, []).extend(winners)
        return parsed

    hoh_winners = row_values(0)
    veto_winners = row_values(1)
    off_block_raw = row_values(2)
    off_block = parse_week_pairs(off_block_raw)
    if not off_block and off_block_raw:
        off_block = {week: [player] for week, player in enumerate(off_block_raw)}
    other_comp_winners = parse_week_pairs(row_values(3))
    evictions = row_values(4)
    buy_back = parse_week_pairs(row_values(5))
    americas_favorite_values = row_values(6)
    americas_favorite = americas_favorite_values[0] if americas_favorite_values else ''
    
    return hoh_winners, veto_winners, off_block, other_comp_winners, evictions, buy_back, americas_favorite

# Read points from CSV file
def read_points_from_csv(filename):
    headers = []
    points = []
    try:
        with open(filename, 'r') as file:
            reader = csv.reader(file)
            headers = next(reader)
            points = [row for row in reader if row]
        print(f"Loaded points from {filename}: {points}")
    except Exception as e:
        print(f"Error reading {filename}: {e}")
    return headers, points

# Calculate points
def calc_points(hoh_winners, veto_winners, off_block, other_comp_winners, evictions, americas_favorite, buy_back, picks):
    weekly_scores = {player: [0] * (len(hoh_winners) + 1) for player in picks.keys()}
    total_scores = {player: 0 for player in picks.keys()}
    points_log = []
    number_of_players = 17 # change if number of players is different than last season

    def log_points(player, points, reason, week):
        action = "gained" if points >= 0 else "lost"
        points_log.append([f"{player} {action} {abs(points)} points because {reason} during week {week+1}."])

    for player in picks:
        for index_of_winner in range(len(hoh_winners)):
            for ranking in range(len(picks[player])):
                if picks[player][ranking] == hoh_winners[index_of_winner]:
                    points = 10 - ranking
                    weekly_scores[player][index_of_winner] += points
                    log_points(player, points, f"{picks[player][ranking]} won HOH", index_of_winner)

        for index_of_winner in range(len(veto_winners)):
            for ranking in range(len(picks[player])):
                if picks[player][ranking] == veto_winners[index_of_winner]:
                    points = 10 - ranking
                    weekly_scores[player][index_of_winner] += points
                    log_points(player, points, f"{picks[player][ranking]} won Veto", index_of_winner)

                for week, players in off_block.items():
                    if not isinstance(players, list):
                        players = [players]
                    for off_block_player in players:
                        for ranking in range(len(picks[player])):
                            if picks[player][ranking] == off_block_player:
                                points = 7.5 - (ranking * 0.75)
                                weekly_scores[player][week] += points
                                log_points(player, points, f"{picks[player][ranking]} got off the block", week)
        
        for week, winners in other_comp_winners.items():
            if not isinstance(winners, list):
                winners = [winners]
            for winner in winners:
                for ranking in range(len(picks[player])):
                    if picks[player][ranking] == winner:
                        points = 5 - (ranking * 0.5)
                        weekly_scores[player][week] += points
                        log_points(player, points, f"{picks[player][ranking]} won another competition", week)

        for week, winner in buy_back.items():
            for ranking in range(len(picks[player])):
                if picks[player][ranking] == winner:
                    points = 10 - ranking
                    weekly_scores[player][week] += points
                    log_points(player, points, f"{picks[player][ranking]} won buy back", week)

        if len(evictions) == number_of_players + len(buy_back):
            if picks[player] == evictions[::-1]:
                points = 100
                weekly_scores[player][-1] += points
                log_points(player, points, "perfect prediction of evictions", len(hoh_winners))
            if picks[player][0] == americas_favorite:
                points = 75
                weekly_scores[player][-1] += points
                log_points(player, points, f"{picks[player][0]} was America's Favorite", len(hoh_winners))
            elif picks[player][1] == americas_favorite:
                points = 50
                weekly_scores[player][-1] += points
                log_points(player, points, f"{picks[player][1]} was America's Favorite", len(hoh_winners))
            elif picks[player][2] == americas_favorite:
                points = 25
                weekly_scores[player][-1] += points
                log_points(player, points, f"{picks[player][2]} was America's Favorite", len(hoh_winners))
            elif picks[player][-1] == americas_favorite:
                points = -50
                weekly_scores[player][-1] += points
                log_points(player, points, f"{picks[player][-1]} was America's Favorite", len(hoh_winners))
            elif picks[player][-2] == americas_favorite:
                points = -25
                weekly_scores[player][-1] += points
                log_points(player, points, f"{picks[player][-2]} was America's Favorite", len(hoh_winners))
            elif picks[player][-3] == americas_favorite:
                points = -10
                weekly_scores[player][-1] += points
                log_points(player, points, f"{picks[player][-3]} was America's Favorite", len(hoh_winners))
            if picks[player][0] == evictions[-1]:
                points = 100
                weekly_scores[player][-1] += points
                log_points(player, points, f"{picks[player][0]} won the game", len(hoh_winners))
            elif picks[player][1] == evictions[-1]:
                points = 75
                weekly_scores[player][-1] += points
                log_points(player, points, f"{picks[player][1]} won the game", len(hoh_winners))
            elif picks[player][2] == evictions[-1]:
                points = 50
                weekly_scores[player][-1] += points
                log_points(player, points, f"{picks[player][2]} won the game", len(hoh_winners))
            elif picks[player][-1] == evictions[-1]:
                points = -75
                weekly_scores[player][-1] += points
                log_points(player, points, f"{picks[player][-1]} won the game", len(hoh_winners))
            elif picks[player][-2] == evictions[-1]:
                points = -50
                weekly_scores[player][-1] += points
                log_points(player, points, f"{picks[player][-2]} won the game", len(hoh_winners))
            elif picks[player][-3] == evictions[-1]:
                points = -25
                weekly_scores[player][-1] += points
                log_points(player, points, f"{picks[player][-3]} won the game", len(hoh_winners))
            if picks[player][0] == evictions[-2]:
                points = 75
                weekly_scores[player][-1] += points
                log_points(player, points, f"{picks[player][0]} was evicted second last", len(hoh_winners))
            elif picks[player][1] == evictions[-2]:
                points = 50
                weekly_scores[player][-1] += points
                log_points(player, points, f"{picks[player][1]} was evicted second last", len(hoh_winners))
            elif picks[player][2] == evictions[-2]:
                points = 25
                weekly_scores[player][-1] += points
                log_points(player, points, f"{picks[player][2]} was evicted second last", len(hoh_winners))
            elif picks[player][-1] == evictions[-2]:
                points = -50
                weekly_scores[player][-1] += points
                log_points(player, points, f"{picks[player][-1]} was evicted second last", len(hoh_winners))
            elif picks[player][-2] == evictions[-2]:
                points = -25
                weekly_scores[player][-1] += points
                log_points(player, points, f"{picks[player][-2]} was evicted second last", len(hoh_winners))
            elif picks[player][-3] == evictions[-2]:
                points = -10
                weekly_scores[player][-1] += points
                log_points(player, points, f"{picks[player][-3]} was evicted second last", len(hoh_winners))
            if picks[player][0] == evictions[-3]:
                points = 50
                weekly_scores[player][-1] += points
                log_points(player, points, f"{picks[player][0]} was evicted third last", len(hoh_winners))
            elif picks[player][1] == evictions[-3]:
                points = 25
                weekly_scores[player][-1] += points
                log_points(player, points, f"{picks[player][1]} was evicted third last", len(hoh_winners))
            elif picks[player][2] == evictions[-3]:
                points = 10
                weekly_scores[player][-1] += points
                log_points(player, points, f"{picks[player][2]} was evicted third last", len(hoh_winners))
            elif picks[player][-1] == evictions[-3]:
                points = -25
                weekly_scores[player][-1] += points
                log_points(player, points, f"{picks[player][-1]} was evicted third last", len(hoh_winners))
            elif picks[player][-2] == evictions[-3]:
                points = -10
                weekly_scores[player][-1] += points
                log_points(player, points, f"{picks[player][-2]} was evicted third last", len(hoh_winners))
            elif picks[player][-3] == evictions[-3]:
                points = -5
                weekly_scores[player][-1] += points
                log_points(player, points, f"{picks[player][-3]} was evicted third last", len(hoh_winners))

        total_scores[player] = sum(weekly_scores[player])

    print(f"Calculated weekly_scores: {weekly_scores}")
    print(f"Calculated total_scores: {total_scores}")

    # Save points log to CSV
    with open(log_file, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(points_log)

    # Save updated points to CSV
    with open(points_file, 'w', newline='') as file:
        writer = csv.writer(file)
        # Write the header row
        week_count = len(next(iter(weekly_scores.values()))) if weekly_scores else 0
        writer.writerow(['Player', 'Total Points'] + ['Week ' + str(i + 1) for i in range(week_count)])
        # Write each player's total and weekly points
        for player, scores in weekly_scores.items():
            total_points = sum(scores)
            writer.writerow([player, total_points] + scores)


    return weekly_scores, total_scores

# Plot total scores
def plot_total_scores(total_scores):
    sorted_scores = {k: v for k, v in sorted(total_scores.items(), key=lambda item: item[1], reverse=True)}
    plt.figure(figsize=(14, 8))  # Increase size
    plt.bar(sorted_scores.keys(), sorted_scores.values(), color='blue')
    average_score = np.mean(list(sorted_scores.values()))
    plt.axhline(y=average_score, color='r', linestyle='-', label=f'Average Score: {average_score:.2f}')
    plt.axhline(y=0, color='black', linestyle='-')
    plt.xlabel('Players')
    plt.ylabel('Total Points')
    plt.title('Total Points per Player')
    plt.legend()
    plt.xticks(rotation=45)
    plt.savefig(os.path.join(images_dir, 'total_scores.png'), bbox_inches='tight')
    plt.close()

# Plot scores over time
def plot_scores_over_time(weekly_scores):
    plt.figure(figsize=(14, 8))  # Increase size
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
    plt.savefig(os.path.join(images_dir, 'cumulative_scores.png'))
    plt.close()

# Load data
picks_headers, picks = read_picks_from_csv(picks_file)
hoh_winners, veto_winners, off_block, other_comp_winners, evictions, buy_back, americas_favorite = read_winners_from_csv(winners_file)

# Calculate points
weekly_scores, total_scores = calc_points(hoh_winners, veto_winners, off_block, other_comp_winners, evictions, americas_favorite, buy_back, picks)

# Generate graphs
if total_scores and weekly_scores:
    plot_total_scores(total_scores)
    plot_scores_over_time(weekly_scores)

# Read raw data for display
def read_raw_data_from_csv(filename):
    data = []
    try:
        with open(filename, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                data.append(row)
    except Exception as e:
        print(f"Error reading {filename}: {e}")
    return data

picks_data = read_raw_data_from_csv(picks_file)
points_headers, points_data = read_points_from_csv(points_file)
winners_data_str = read_raw_data_from_csv(winners_file)

@app.route('/', methods=['GET'])
def index():
    total_scores_img = os.path.join('static', 'images', 'total_scores.png')
    cumulative_scores_img = os.path.join('static', 'images', 'cumulative_scores.png')
    leaderboard = sorted(total_scores.items(), key=lambda x: x[1], reverse=True)
    logs = read_logs_from_csv(log_file)  # Read the logs from the CSV file
    player_names = list(logs.keys())  # Get the player names from the logs dictionary
    return render_template('index.html', total_scores_img=total_scores_img,
                           cumulative_scores_img=cumulative_scores_img,
                           leaderboard=leaderboard,
                           picks_headers=picks_headers,
                           picks_data=picks_data,
                           points_headers=points_headers,
                           points_data=points_data,
                           winners_data=winners_data_str,
                           logs=logs,
                           player_names=player_names)  # Pass the player names and logs to the template

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
