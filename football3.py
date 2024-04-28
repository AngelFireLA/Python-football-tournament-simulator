import os
import random
import shutil
import time
from math import ceil

import numpy as np
import pandas as pd


def load_season_data(season, df):
    season_col = f"Saison {season}"
    if season_col in df.columns:
        return df.set_index(df.columns[0])[season_col].to_dict()
    return {}


def update_season_data_in_memory(df, modified_data, new_season):
    """ Update the DataFrame in memory with new season data, without exporting to CSV. """
    season_col = f"Saison {new_season}"
    # Append new season data directly
    df[season_col] = df[df.columns[0]].map(modified_data)

def create_rating_changes_dict(numbers):
    """
    Returns a dict telling by how much a player's rating should change based on the round they reached
    :param numbers:
    :return:
    """
    sorted_numbers = sorted(numbers)
    offset = 1
    mid = len(sorted_numbers) // 2 + offset  # Adjust mid to be one step towards the start for zero
    return {num: mid - i for i, num in enumerate(sorted_numbers)}

def min(a, b):
    return a if a < b else b

def max(a, b):
    return a if a > b else b

score_probabilities = {}
for rating in range(-10000, 10000):  # Assuming ratings are clamped between 50 and 99
    adj_rating = (rating - 50) / 40
    weights = [2, 3, 5, 10, 7, 4, 1]
    score_prob = [max(min(x * (1 - adj_rating) + x * adj_rating, 10), 1) for x in weights]
    score_probabilities[rating] = score_prob

def simulate_match(rating_of_player_a, rating_of_player_b, limit_ratings_in_practise=False, limit_ratings_in_file=False):
    if limit_ratings_in_practise and not limit_ratings_in_file:
        rating_of_player_a = max(min(rating_of_player_a, 99), 50)
        rating_of_player_b = max(min(rating_of_player_b, 99), 50)
    scores = [0, 1, 2, 3, 4, 5, 6]
    return random.choices(scores, weights=score_probabilities[rating_of_player_a], k=1)[0], random.choices(scores, weights=score_probabilities[rating_of_player_b], k=1)[0]

class Tournament:

    def __init__(self, players_file, goals_file, current_season, players_per_group=4, number_of_encounters_per_match=2, players_qualified_per_group = 2, limit_ratings_in_practise=False, limit_ratings_in_file=False):

        self.players_df = pd.read_csv(players_file)
        self.goals_df = pd.read_csv(goals_file)
        self.current_season = current_season
        self.current_players_data = load_season_data(current_season, self.players_df)
        self.current_goals_data = load_season_data(current_season, self.goals_df)
        if not self.current_players_data: raise IndexError("Players data doesn't exist yet")
        if not self.current_goals_data: raise IndexError("Goals data doesn't exist yet")
        self.players_per_group = players_per_group
        self.number_of_encounters_per_match = number_of_encounters_per_match

        self.limit_ratings_in_practise = limit_ratings_in_practise
        self.limit_ratings_in_file = limit_ratings_in_file
        self.participants = None
        self.rounds = None
        self.rankings_per_round = None
        self.players_ranking = None
        self.current_round = None
        self.scored_goals = None
        self.conceded_goals = None
        self.remaining_players = None
        self.groups = None
        self.group_calendar = None
        self.players_qualified_per_group = players_qualified_per_group
        if players_qualified_per_group % 2 != 0: raise ValueError("Number of players qualified per group must be even")

    def start_tournament(self):
        self.participants = list(self.current_players_data.keys())
        if len(self.participants) % 2 != 0: raise ValueError("Number of participants must be even")

        self.rounds = len(self.participants)
        self.rankings_per_round = {self.rounds >> i: [] for i in range(self.rounds.bit_length()) if
                                   self.rounds >> i > 0}
        self.players_ranking = {player: None for player in self.participants}
        self.current_round = list(self.rankings_per_round.keys())[0]

        self.scored_goals = {player: 0 for player in self.participants}
        self.conceded_goals = {player: 0 for player in self.participants}

        self.remaining_players = list(self.participants)

    def run_tournament(self, players_per_group, number_of_encounters):
        self.generate_groups(players_per_group)
        self.generate_group_calendar(number_of_encounters)
        self.simulate_groups()
        #repeat simulating knockouts
        for round in list(self.rankings_per_round.keys())[1:-1]:
            self.current_round = round
            round_matches = self.generate_knockout_matches()
            self.simulate_knockout_round(round_matches)

        self.current_round = list(self.rankings_per_round.keys())[-1]
        self.eliminate_player(self.remaining_players[0])
        self.update_rating()
        self.update_goals()


    def generate_knockout_matches(self):
        random.shuffle(self.remaining_players)
        matches = list(zip(self.remaining_players[::2], self.remaining_players[1::2]))
        return matches

    # For instance, refactor simulate_knockout_round to use pre-fetched data
    def simulate_knockout_round(self, round_matches):
        # Pre-fetch ratings for all players
        ratings = {player: self.current_players_data[player] for player in self.remaining_players}

        self.remaining_players = []
        for match in round_matches:
            rating1 = ratings[match[0]]
            rating2 = ratings[match[1]]
            results = simulate_match(rating1, rating2, self.limit_ratings_in_practise, self.limit_ratings_in_file)
            while results[0] == results[1]:
                results = simulate_match(rating1, rating2, self.limit_ratings_in_practise, self.limit_ratings_in_file)
            self.update_stats(match[0], match[1], results)
            if results[0] > results[1]:
                self.eliminate_player(match[1])
                self.remaining_players.append(match[0])
            elif results[0] < results[1]:
                self.eliminate_player(match[0])
                self.remaining_players.append(match[1])

    def update_rating(self):
        rating_changes_dict = create_rating_changes_dict(list(self.rankings_per_round.keys()))
        rating_changes_dict[1]+=1

        # print(rating_changes_dict)
        # distribution = 0 #get's the amount of total points gained across a season for all players, optimally it's 0 or low
        # for k, v in rating_changes_dict.items():
        #     distribution += v*ceil(k/2)
        # print(distribution)


        rating_total = 0
        for player in self.participants:
            self.current_players_data[player] += rating_changes_dict[self.players_ranking[player]]
            if self.limit_ratings_in_file:
                self.current_players_data[player] = max(min(self.current_players_data[player], 99), 50)
            rating_total+=rating_changes_dict[self.players_ranking[player]]
        #print(rating_total)
    def eliminate_player(self, player):
        self.players_ranking[player] = self.current_round
        self.rankings_per_round[self.current_round].append(player)

    def update_goals(self):
        for player in self.participants:
            self.current_goals_data[player] += self.scored_goals[player]

    def update_stats(self, player1, player2, scores):
        # scores is [score1, score2]
        self.scored_goals[player1] += scores[0]
        self.scored_goals[player2] += scores[1]

        self.conceded_goals[player1] += scores[1]
        self.conceded_goals[player2] += scores[0]

    def generate_groups(self, players_per_group):
        if len(self.remaining_players) % players_per_group != 0:
            raise ValueError("Number of players must be divisible by players per group")
        groups = []
        for i in range(0, len(self.remaining_players), players_per_group):
            groups.append(self.remaining_players[i:i + players_per_group])
        self.groups = groups

    def generate_group_calendar(self, number_of_encounters):
        group_calendar = []
        for group in self.groups:
            matches = [(p1, p2) for i, p1 in enumerate(group) for p2 in group[i + 1:]]
            repeated_matches = matches * number_of_encounters
            random.shuffle(repeated_matches)
            group_calendar.append(repeated_matches)
        self.group_calendar = group_calendar

    def simulate_groups(self):
        """
        Simulates all group matches and ranks players based on points, goal difference, goals scored,
        and randomly if necessary.
        """
        self.remaining_players = []
        for group in self.groups:
            group_calendar = self.group_calendar[self.groups.index(group)]
            standings = {member: {'points': 0, 'goals_scored': 0, 'goals_conceded': 0} for member in group}
            for match in group_calendar:
                scores = simulate_match(self.current_players_data[match[0]], self.current_players_data[match[1]], self.limit_ratings_in_practise, self.limit_ratings_in_file)
                self.update_stats(match[0], match[1], scores)
                if scores[0] == scores[1]:
                    standings[match[0]]['points'] += 1
                    standings[match[1]]['points'] += 1
                elif scores[0] > scores[1]:
                    standings[match[0]]['points'] += 3
                else:
                    standings[match[1]]['points'] += 3

                # Update goals scored and conceded
                standings[match[0]]['goals_scored'] += scores[0]
                standings[match[0]]['goals_conceded'] += scores[1]
                standings[match[1]]['goals_scored'] += scores[1]
                standings[match[1]]['goals_conceded'] += scores[0]

            # Determine the ranking in the group based on the criteria
            players_ranked = sorted(
                standings.keys(),
                key=lambda x: (
                    standings[x]['points'],
                    standings[x]['goals_scored'] - standings[x]['goals_conceded'],  # Goal difference
                    standings[x]['goals_scored'],
                    random.random()  # Random tiebreaker
                ),
                reverse=True
            )

            players_qualified = players_ranked[:self.players_qualified_per_group]
            self.remaining_players.extend(players_qualified)

            # Eliminate other players
            for player in players_ranked[self.players_qualified_per_group:]:
                self.eliminate_player(player)

players_file = "test.csv"
goals_file = "test2.csv"

#reset test.csv and test2.csv
#delet test.csv
os.remove(players_file)
#copy football23(1).csv as test.csv
shutil.copyfile("football23(1).csv", players_file)

#repeat for football23(1)- goals - clean.csv
os.remove(goals_file)
shutil.copyfile("football23(1)- goals - clean.csv", goals_file)


# Create an instance with the data loaded
tournament = Tournament(players_file, goals_file, 2, limit_ratings_in_practise=False, limit_ratings_in_file=False)

# import cProfile
# import pstats
# with cProfile.Profile() as pr:
new_players_data = {}
new_goals_data = {}

# Inside the cProfile block, modify to accumulate data in dictionaries:
for i in range(100000):
    #print(i)
    tournament.start_tournament()
    tournament.run_tournament(4, 2)
    tournament.current_season += 1
    new_season_col = f"Saison {tournament.current_season}"
    new_players_data[new_season_col] = tournament.players_df[tournament.players_df.columns[0]].map(
        tournament.current_players_data)
    new_goals_data[new_season_col] = tournament.goals_df[tournament.goals_df.columns[0]].map(
        tournament.current_goals_data)

# Convert dictionaries to DataFrames and concatenate them to the original DataFrames
players_new_season_df = pd.DataFrame(new_players_data)
goals_new_season_df = pd.DataFrame(new_goals_data)

tournament.players_df = pd.concat([tournament.players_df, players_new_season_df], axis=1)
tournament.goals_df = pd.concat([tournament.goals_df, goals_new_season_df], axis=1)

# Export the updated DataFrames to CSV files outside of the loop
tournament.players_df.to_csv(players_file, index=False)
tournament.goals_df.to_csv(goals_file, index=False)

# stats = pstats.Stats(pr)
# stats.sort_stats(pstats.SortKey.TIME)
# stats.print_stats()

