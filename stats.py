import pandas as pd
import matplotlib.pyplot as plt
import os
import re

players_file = "players.csv"

# Assuming 'tournament.players_df' is your DataFrame with players as rows and seasons as columns
players_df = pd.read_csv(players_file)

# Transpose the DataFrame so that each player becomes a column
transposed_df = players_df.set_index(players_df.columns[0]).transpose()

# Creating a directory to save the plots if it doesn't already exist
output_dir = "player_ratings"
os.makedirs(output_dir, exist_ok=True)

# Iterate over each column (player) to plot their ratings over seasons
for player in transposed_df.columns:
    transposed_df[player].plot(title=f'Overall Rating Over Time for {player}')
    plt.xlabel('Season')
    plt.ylabel('ELO Rating')
    player_name = player.replace("/", " ")
    player_name = re.sub(r'\\', ' ', player_name)  # Clean up the player name for file saving

    # Save the figure
    plt.savefig(os.path.join(output_dir, f'{player_name}_elo_ratings.png'))
    plt.close()
