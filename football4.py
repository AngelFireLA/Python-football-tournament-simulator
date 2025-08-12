import os
import random
import shutil
import time
import itertools  # For itertools.accumulate
import bisect  # For bisect.bisect_right for efficient weighted random choice

import numpy as np  # Retained as it was in original imports, though not directly used in score logic
import pandas as pd

# --- Constants for dynamic score generation based on rating difference ---
_BASE_SCORES_DOMAIN = [0, 1, 2, 3, 4, 5, 6]  # The possible scores
_BASE_WEIGHTS = [2, 3, 5, 10, 7, 4, 1]  # Original base weights for _BASE_SCORES_DOMAIN

# Determine the "average" or "peak" score from the base weights for deviation calculation
# This is the score that corresponds to the highest base weight (10 for score 3)
_AVG_SCORE = _BASE_SCORES_DOMAIN[_BASE_WEIGHTS.index(max(_BASE_WEIGHTS))]  # Score 3
# How much each score deviates from the average score (e.g., 0 goals is -3 from avg of 3)
_SCORE_VALUE_DEVIATIONS = [s - _AVG_SCORE for s in _BASE_SCORES_DOMAIN]
# Example: scores 0,1,2,3,4,5,6 -> deviations -3,-2,-1,0,1,2,3

# Normalization factor for rating difference. This controls how a rating difference
# translates into an "adjustment unit" for the weights.
# A difference of 40 points will create an 'effective_adj' of 1.0 (similar to original 'adj_rating').
_RATING_DIFF_NORMALIZATION_FACTOR = 50.0

# Clipping the 'effective_adj' factor to prevent excessively skewed probabilities.
# This prevents extremely large/small rating differences from creating unrealistically
# high or low probabilities. A difference beyond 200 points (5 * 40) will have the same max impact.
_MAX_EFFECTIVE_ADJUSTMENT = 5.0
_MIN_EFFECTIVE_ADJUSTMENT = -5.0

# Factor to apply to score deviations when adjusting weights.
# A smaller value means rating difference has less impact on the score distribution.
# Tune this value (e.g., 0.1 to 0.5) to control how much rating difference affects goal scoring.
_SCORE_IMPACT_FACTOR = 0.1

# Weight clipping to ensure valid and reasonable probabilities for score selection.
# All final weights will be between 1 and 10, as implied by your original code's clipping.
_MIN_WEIGHT_VALUE = 1.0
_MAX_WEIGHT_VALUE = 10.0


def _get_adjusted_weights_for_player(rating_diff_for_player):
    """
    Calculates dynamic score weights for a player based on their strength relative to the opponent.
    `rating_diff_for_player` is (this_player_rating - opponent_rating).

    A positive `rating_diff_for_player` (player is stronger) will shift the distribution
    towards higher scores for this player.
    A negative `rating_diff_for_player` (player is weaker) will shift the distribution
    towards lower scores for this player.
    """
    # Scale the rating difference to get an 'effective adjustment' factor.
    # This factor determines how much the score distribution shifts.
    effective_adj = rating_diff_for_player / _RATING_DIFF_NORMALIZATION_FACTOR

    # Clamp the effective adjustment to prevent probabilities from becoming too extreme.
    effective_adj = max(min(effective_adj, _MAX_EFFECTIVE_ADJUSTMENT), _MIN_EFFECTIVE_ADJUSTMENT)

    adjusted_weights = []
    for i, base_w in enumerate(_BASE_WEIGHTS):
        # Adjust each base weight:
        # If `effective_adj` is positive (stronger player):
        #   - Scores > _AVG_SCORE (positive deviation) get their weights increased.
        #   - Scores < _AVG_SCORE (negative deviation) get their weights decreased.
        # This shifts the distribution towards higher scores.
        # If `effective_adj` is negative (weaker player):
        #   - Scores > _AVG_SCORE get decreased weights.
        #   - Scores < _AVG_SCORE get increased weights.
        # This shifts the distribution towards lower scores.
        new_w = base_w + _SCORE_VALUE_DEVIATIONS[i] * effective_adj * _SCORE_IMPACT_FACTOR

        # Apply clipping to ensure all weights are positive and within reasonable bounds.
        clipped_w = max(min(new_w, _MAX_WEIGHT_VALUE), _MIN_WEIGHT_VALUE)
        adjusted_weights.append(clipped_w)

    return adjusted_weights


def _get_single_score_from_weights(weights_list):
    """Generates a single score based on a provided list of dynamic weights."""
    # Precompute cumulative sums for efficient weighted random choice
    cum_weights = list(itertools.accumulate(weights_list))
    total_weight = cum_weights[-1]

    # Generate a random number scaled by total weight
    r = random.random() * total_weight

    # Use binary search (bisect_right) to find the index corresponding to the random number
    idx = bisect.bisect_right(cum_weights, r)

    return _BASE_SCORES_DOMAIN[idx]


def simulate_match(rating_of_player_a, rating_of_player_b, limit_ratings_in_practise=False,
                   limit_ratings_in_file=False):
    """
    Simulates a single match where scores depend on the rating difference between players.
    """
    # Apply rating limits if 'limit_ratings_in_practise' is true (before calculating difference).
    # Note: 'limit_ratings_in_file' is used when updating ratings in the file, not here.
    if limit_ratings_in_practise:  # and not limit_ratings_in_file: (original code had this, but it makes no sense here)
        rating_of_player_a = max(min(rating_of_player_a, 99), 50)
        rating_of_player_b = max(min(rating_of_player_b, 99), 50)

    # Calculate the rating difference from player A's perspective.
    # This difference drives how many goals A is likely to score.
    rating_diff_A_vs_B = rating_of_player_a - rating_of_player_b

    # Get the dynamically adjusted weights for player A's goal scoring.
    weights_for_A_goals = _get_adjusted_weights_for_player(rating_diff_A_vs_B)

    # Get the dynamically adjusted weights for player B's goal scoring.
    # From B's perspective, the rating difference is the inverse of A's.
    weights_for_B_goals = _get_adjusted_weights_for_player(-rating_diff_A_vs_B)

    # Generate scores for each player based on their respective dynamic weights.
    score_A = _get_single_score_from_weights(weights_for_A_goals)
    score_B = _get_single_score_from_weights(weights_for_B_goals)

    return score_A, score_B


# Removed the global `score_probabilities` dictionary and its population logic
# as it's no longer used and was the source of the "bug" and performance overhead.


# --- Remaining Tournament class and Main script (optimized from previous iteration) ---

def load_season_data(season, df):
    season_col = f"Saison {season}"
    if season_col in df.columns:
        return df.set_index(df.columns[0])[season_col].to_dict()
    return {}


def update_season_data_in_memory(df, modified_data, new_season):
    """ Update the DataFrame in memory with new season data, without exporting to CSV. """
    season_col = f"Saison {new_season}"
    df[season_col] = df[df.columns[0]].map(modified_data)


def create_rating_changes_dict(numbers):
    sorted_numbers = sorted(numbers)
    offset = 1
    mid = len(sorted_numbers) // 2 + offset
    return {num: mid - i for i, num in enumerate(sorted_numbers)}


class Tournament:
    def __init__(self, players_file, goals_file, current_season, players_per_group=4, number_of_encounters_per_match=2,
                 players_qualified_per_group=2, limit_ratings_in_practise=False, limit_ratings_in_file=False):
        self.players_df = pd.read_csv(players_file)
        self.goals_df = pd.read_csv(goals_file)
        self.current_season = current_season
        self.current_players_data = load_season_data(current_season, self.players_df)
        self.current_goals_data = load_season_data(current_season, self.goals_df)
        if not self.current_players_data: raise IndexError(
            f"Players data for season {current_season} doesn't exist yet")
        if not self.current_goals_data: raise IndexError(f"Goals data for season {current_season} doesn't exist yet")

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
        current_round_val = self.rounds
        round_keys = []
        while current_round_val > 0:
            round_keys.append(current_round_val)
            if current_round_val == 1: break
            current_round_val //= 2
        self.rankings_per_round = {r: [] for r in round_keys}

        self.players_ranking = {player: None for player in self.participants}
        self.current_round = self.rounds

        self.scored_goals = {player: 0 for player in self.participants}
        self.conceded_goals = {player: 0 for player in self.participants}
        self.remaining_players = list(self.participants)

    def run_tournament(self, players_per_group, number_of_encounters):
        self.generate_groups(players_per_group)
        self.generate_group_calendar(number_of_encounters)
        self.simulate_groups()

        knockout_stage_keys = sorted([r for r in self.rankings_per_round if r < self.rounds and r > 1], reverse=True)

        for round_val in knockout_stage_keys:
            self.current_round = round_val
            round_matches = self.generate_knockout_matches()
            self.simulate_knockout_round(round_matches)

        self.current_round = 1
        if len(self.remaining_players) == 1:
            self.eliminate_player(self.remaining_players[0])
        elif not self.remaining_players and len(self.participants) == 1:
            self.eliminate_player(self.participants[0])
        elif len(self.remaining_players) > 1:  # Fallback for unexpected remaining players
            if self.remaining_players:
                self.eliminate_player(self.remaining_players[0])

        self.update_rating()
        self.update_goals()

    def generate_knockout_matches(self):
        random.shuffle(self.remaining_players)
        # Assuming number of players is always even for knockouts or handled upstream
        if len(self.remaining_players) % 2 != 0 and self.remaining_players:
            pass

        matches = list(zip(self.remaining_players[::2], self.remaining_players[1::2]))
        return matches

    def simulate_knockout_round(self, round_matches):
        winners = []
        for p1, p2 in round_matches:
            rating1 = self.current_players_data[p1]
            rating2 = self.current_players_data[p2]

            results = simulate_match(rating1, rating2, self.limit_ratings_in_practise, self.limit_ratings_in_file)
            while results[0] == results[1]:  # Re-simulate ties
                results = simulate_match(rating1, rating2, self.limit_ratings_in_practise, self.limit_ratings_in_file)

            self.update_stats(p1, p2, results)
            if results[0] > results[1]:
                self.eliminate_player(p2)
                winners.append(p1)
            else:
                self.eliminate_player(p1)
                winners.append(p2)
        self.remaining_players = winners

    def update_rating(self):
        rating_changes_dict = create_rating_changes_dict(list(self.rankings_per_round.keys()))

        #rating_changes_dict[1] += 1

        for player in self.participants:
            player_rank = self.players_ranking[player]
            if player_rank is not None and player_rank in rating_changes_dict:
                self.current_players_data[player] += rating_changes_dict[player_rank]
                if self.limit_ratings_in_file:
                    self.current_players_data[player] = max(min(self.current_players_data[player], 99), 50)

    def eliminate_player(self, player):
        self.players_ranking[player] = self.current_round
        if self.current_round in self.rankings_per_round:
            self.rankings_per_round[self.current_round].append(player)

    def update_goals(self):
        for player in self.participants:
            self.current_goals_data[player] += self.scored_goals[player]

    def update_stats(self, player1, player2, scores):
        self.scored_goals[player1] += scores[0]
        self.scored_goals[player2] += scores[1]
        self.conceded_goals[player1] += scores[1]
        self.conceded_goals[player2] += scores[0]

    def generate_groups(self, players_per_group):
        if not self.remaining_players:
            self.groups = []
            return
        if len(self.remaining_players) % players_per_group != 0:
            raise ValueError(
                f"Number of players ({len(self.remaining_players)}) must be divisible by players per group ({players_per_group})")

        groups_list = []
        for i in range(0, len(self.remaining_players), players_per_group):
            groups_list.append(self.remaining_players[i:i + players_per_group])
        self.groups = groups_list

    def generate_group_calendar(self, number_of_encounters):
        group_calendar_list = []
        if not self.groups:
            self.group_calendar = []
            return

        for group in self.groups:
            matches = []
            for i, p1 in enumerate(group):
                for p2 in group[i + 1:]:
                    matches.append((p1, p2))

            repeated_matches = matches * number_of_encounters
            random.shuffle(repeated_matches)
            group_calendar_list.append(repeated_matches)
        self.group_calendar = group_calendar_list

    def simulate_groups(self):
        qualified_from_all_groups = []
        if not self.groups:
            self.remaining_players = []
            return

        for group_idx, group_members in enumerate(self.groups):
            group_match_schedule = self.group_calendar[group_idx]
            standings = {member: {'points': 0, 'goals_scored': 0, 'goals_conceded': 0} for member in group_members}

            for p1, p2 in group_match_schedule:
                rating1 = self.current_players_data[p1]
                rating2 = self.current_players_data[p2]
                scores = simulate_match(rating1, rating2, self.limit_ratings_in_practise, self.limit_ratings_in_file)

                self.update_stats(p1, p2, scores)

                if scores[0] == scores[1]:
                    standings[p1]['points'] += 1
                    standings[p2]['points'] += 1
                elif scores[0] > scores[1]:
                    standings[p1]['points'] += 3
                else:
                    standings[p2]['points'] += 3

                standings[p1]['goals_scored'] += scores[0]
                standings[p1]['goals_conceded'] += scores[1]
                standings[p2]['goals_scored'] += scores[1]
                standings[p2]['goals_conceded'] += scores[0]

            players_ranked_in_group = sorted(
                group_members,
                key=lambda x_player: (
                    standings[x_player]['points'],
                    standings[x_player]['goals_scored'] - standings[x_player]['goals_conceded'],
                    standings[x_player]['goals_scored'],
                    random.random()  # Random tiebreaker
                ),
                reverse=True
            )

            qualified_this_group = players_ranked_in_group[:self.players_qualified_per_group]
            qualified_from_all_groups.extend(qualified_this_group)

            for player_to_eliminate in players_ranked_in_group[self.players_qualified_per_group:]:
                self.eliminate_player(player_to_eliminate)

        self.remaining_players = qualified_from_all_groups


if __name__ == '__main__':  # Standard practice to encapsulate main execution
    players_file = "players.csv"
    goals_file = "goals.csv"

    # Reset player and goals data CSVs for a clean run
    if os.path.exists(players_file):
        os.remove(players_file)
    shutil.copyfile("players - clean.csv", players_file)

    if os.path.exists(goals_file):
        os.remove(goals_file)
    shutil.copyfile("goals - clean.csv", goals_file)

    # Initialize the tournament simulator
    tournament_simulator = Tournament(players_file, goals_file, 0,
                                      limit_ratings_in_practise=True,
                                      limit_ratings_in_file=True,
                                      players_per_group=4,
                                      number_of_encounters_per_match=2,
                                      players_qualified_per_group=2)

    # Cache player name Series for efficient mapping of new season data
    player_names_map_series = tournament_simulator.players_df[tournament_simulator.players_df.columns[0]].copy()
    goals_player_names_map_series = tournament_simulator.goals_df[tournament_simulator.goals_df.columns[0]].copy()

    # Dictionaries to accumulate new season data before a single DataFrame concatenation
    new_players_season_data_dict = {}
    new_goals_season_data_dict = {}

    start_time = time.time()
    num_seasons_to_simulate = 10000

    for i in range(num_seasons_to_simulate):
        tournament_simulator.start_tournament()
        tournament_simulator.run_tournament(players_per_group=4, number_of_encounters=2)

        tournament_simulator.current_season += 1
        new_season_column_name = f"Saison {tournament_simulator.current_season}"

        # Map current player/goal data (which are dicts) to the cached player name Series
        # to create a pandas Series for the new season's column.
        new_players_season_data_dict[new_season_column_name] = player_names_map_series.map(
            tournament_simulator.current_players_data)
        new_goals_season_data_dict[new_season_column_name] = goals_player_names_map_series.map(
            tournament_simulator.current_goals_data)

    # Create DataFrames from the collected season data (after the loop)
    # This is much faster than concatenating DataFrames inside the loop.
    if new_players_season_data_dict:
        players_new_seasons_df = pd.DataFrame(new_players_season_data_dict)
        tournament_simulator.players_df = pd.concat([tournament_simulator.players_df, players_new_seasons_df], axis=1)

    if new_goals_season_data_dict:
        goals_new_seasons_df = pd.DataFrame(new_goals_season_data_dict)
        tournament_simulator.goals_df = pd.concat([tournament_simulator.goals_df, goals_new_seasons_df], axis=1)

    # Export the final updated DataFrames to CSV files
    tournament_simulator.players_df.to_csv(players_file, index=False)
    tournament_simulator.goals_df.to_csv(goals_file, index=False)

    end_time = time.time()
    print(f"Simulated {num_seasons_to_simulate} seasons in {end_time - start_time:.2f} seconds.")