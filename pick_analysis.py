import pandas as pd
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt

# Load the picks data
picks_file = '/Users/richie/Documents/git_hub/big_brother/big_brother/data/test_picks.csv'
picks_df = pd.read_csv(picks_file)

# Remove the first column (names)
picks_df = picks_df.drop(columns=['name'])

# Get the number of contestants
num_contestants = picks_df.shape[1]

# Initialize a dictionary to store the descriptive statistics
descriptive_stats = {}

# Initialize a list to store the average ranking for each contestant
average_list = []

# Function to detect outliers
def detect_outliers(data):
    z_scores = stats.zscore(data)
    return np.where(np.abs(z_scores) > 3)[0]  # Indices of outliers

# Flatten the DataFrame to get a list of all unique contestants
contestants = picks_df.values.flatten()
unique_contestants = pd.unique(contestants)

# Process the ranking for each contestant
for contestant in unique_contestants:
    ranks = []
    for index, row in picks_df.iterrows():
        if contestant in row.values:
            rank = num_contestants - row.values.tolist().index(contestant)
            ranks.append(rank)
    
    if len(ranks) == 0:
        continue
    
    mean_rank = np.mean(ranks)
    median_rank = np.median(ranks)
    mode_result = stats.mode(ranks)
    mode_rank = mode_result.mode[0] if isinstance(mode_result.mode, np.ndarray) and mode_result.mode.size > 0 else 'No mode'
    std_dev = np.std(ranks)
    range_rank = np.ptp(ranks)
    outliers = detect_outliers(ranks)
    num_outliers = len(outliers)

    descriptive_stats[contestant] = {
        'Mean': mean_rank,
        'Median': median_rank,
        'Mode': mode_rank,
        'Standard Deviation': std_dev,
        'Range': range_rank,
        'Outliers': num_outliers
    }

    # Add to average list
    average_list.append((contestant, mean_rank))

# Sort the average list by the average ranking
average_list.sort(key=lambda x: x[1])

# Write the results to a text file
with open('descriptive_statistics.txt', 'w') as file:
    for contestant, stats in descriptive_stats.items():
        file.write(f"{contestant}:\n")
        for stat, value in stats.items():
            file.write(f"  {stat}: {value}\n")
        file.write("\n")

    file.write("Average List:\n")
    for contestant, avg_rank in average_list:
        file.write(f"{contestant}: {avg_rank}\n")

# Plot the rankings
plt.figure(figsize=(10, 6))
for contestant in descriptive_stats.keys():
    ranks = []
    for index, row in picks_df.iterrows():
        if contestant in row.values:
            rank = num_contestants - row.values.tolist().index(contestant)
            ranks.append(rank)
    print(f"{contestant} got the following ranks:{ranks}")
    plt.plot(ranks, label=contestant)

plt.xlabel('Participants')
plt.ylabel('Rank')
plt.title('Ranking of Contestants')
plt.legend()
plt.savefig('rankings_plot.png')

