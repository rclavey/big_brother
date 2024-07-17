import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

# Read the CSV file
file_path = '/Users/richie/Documents/git_hub/big_brother/big_brother/data/test_points.csv'
data = pd.read_csv(file_path)

# Remove the 'name' column for analysis
contestant_columns = data.columns[1:]

# Prepare a dictionary to store descriptive statistics
descriptive_stats = {}

# Calculate descriptive statistics for each contestant
for contestant in contestant_columns:
    ranks = data[contestant]
    mean_rank = np.mean(ranks)
    median_rank = np.median(ranks)
    mode_rank = stats.mode(ranks)[0][0]
    std_dev_rank = np.std(ranks)
    range_rank = np.ptp(ranks)
    outliers = ranks[(np.abs(stats.zscore(ranks)) > 3)]
    
    descriptive_stats[contestant] = {
        'Mean': mean_rank,
        'Median': median_rank,
        'Mode': mode_rank,
        'Standard Deviation': std_dev_rank,
        'Range': range_rank,
        'Outliers': outliers.tolist()
    }

# Generate average list
average_list = data[contestant_columns].mean().sort_values().index.tolist()
average_list_with_scores = data[contestant_columns].mean().sort_values().tolist()

# Write the statistics and lists to a text file
with open('descriptive_stats.txt', 'w') as file:
    for contestant, stats in descriptive_stats.items():
        file.write(f"{contestant}:\n")
        file.write(f"  Mean Placement: {stats['Mean']}\n")
        file.write(f"  Median Placement: {stats['Median']}\n")
        file.write(f"  Mode Placement: {stats['Mode']}\n")
        file.write(f"  Standard Deviation: {stats['Standard Deviation']}\n")
        file.write(f"  Range: {stats['Range']}\n")
        file.write(f"  Outliers: {stats['Outliers']}\n")
        file.write("\n")
    
    file.write("Average List:\n")
    file.write(", ".join(average_list) + "\n\n")
    
    file.write("Average List with Scores:\n")
    for name, score in zip(average_list, average_list_with_scores):
        file.write(f"{name}: {score}\n")
    
# Plot graphs for each contestant
for contestant in contestant_columns:
    ranks = data[contestant]
    plt.figure(figsize=(10, 6))
    plt.hist(ranks, bins=np.arange(1, 19)-0.5, edgecolor='black')
    plt.title(f'Distribution of Rankings for {contestant}')
    plt.xlabel('Rank')
    plt.ylabel('Frequency')
    plt.xticks(np.arange(1, 18))
    plt.grid(axis='y')
    plt.savefig(f'{contestant}_rank_distribution.png')
    plt.close()

print("Descriptive statistics and graphs have been saved.")
