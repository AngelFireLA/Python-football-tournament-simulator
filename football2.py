import random
import time
import tkinter as tk

import pandas as pd

root = tk.Tk()
root.state('zoomed')

width = root.winfo_screenwidth()
height = root.winfo_screenheight()

season = 2

players = {}
goals_scored = {}
scored = {}
conceded = {}
goal_difference = {}
groups = {}
groups_calendar = {}
groups_standings = {}
free_index_groups = 0
qualified = []
df_players = None
df_players_goals = None
eliminated_groups = []


def initialize_database():
    global players
    global df_players
    global df_players_goals
    global goals_scored
    players = \
        pd.read_csv('football23(1).csv', header=None, dtype={0: str}).dropna().set_index(0).squeeze().to_dict()[
            season+1]

    players.pop('names')
    goals_scored = \
        pd.read_csv('football23(1)- goals.csv', header=None, dtype={0: str}).dropna().set_index(0).squeeze().to_dict()[
            season]

    df_players = pd.read_csv('football23(1).csv')
    df_players_goals = pd.read_csv('football23(1)- goals.csv')
    if not "Saison "+ str(season+1) in df_players.columns:
        df_players.insert(len(df_players.columns), "Saison "+ str(season+1), 1, False)
    if not "Saison "+ str(season+1) in df_players_goals.columns:
        df_players_goals.insert(len(df_players_goals.columns), "Saison "+ str(season+1), 1, False)


def getPlayerRating(name):
    return int(float(players[name]))


def getPlayerGoals(name):
    return int(float(goals_scored[name]))


def changeRating(season: int, name, rating: int):
    # if rating < 50:
    #     rating = 50
    # elif rating > 99:
    #     rating = 99
    df_players.loc[df_players['names'] == name, "Saison " + str(season)] = int(rating)


def changeGoals(season: int, name, goals: int):
    df_players_goals.loc[df_players_goals['names'] == name, "Saison " + str(season)] = goals

def gen_groups():
    global groups, groups_standings, free_index_groups
    player_names = []
    for i in players.keys():
        player_names.append(i)
    groups = {}
    for group in range(8):
        group = []
        for i in range(4):
            player = random.choice(player_names)
            group.append(player)
            player_names.remove(player)

        groups[free_index_groups] = group
        free_index_groups += 1
    groups_standings = {}
    for group in groups:
        group_name = group
        groups_standings[group_name] = {}
    for group_name in groups_standings:
        for player_name in groups[group_name]:
            groups_standings[group_name][player_name] = {'name': player_name, 'points': 0, 'goal_diff': 0}


def calendar_for_groups():
    global groups_calendar
    groups_calendar = []
    for k, group in groups.items():
        group_calendar = []
        while len(group_calendar) < 6:
            p1 = random.choice(group)
            p2 = random.choice(group)
            if p1 != p2 and (p1, p2) not in group_calendar and (p2, p1) not in group_calendar:
                group_calendar.append((p1, p2))
        groups_calendar.append(group_calendar)

group_match_results = [""] * 8
knockout_results = [""] * 4
eliminated_knockouts = []
for i in range(4):
    eliminated_knockouts.append([])
# Add a variable to keep track of the current group index
current_group_index = 0
knockout_index = 0
kc_meaning = {0: 8, 1: 4, 2: 2, 3: 1}
knockouts_ratings = {0: 0, 1: 1, 2: 2, 3: 3, 4:3}

def simulate_match(p1, p2, draw=True, is_group_match=False, group_number=-1):
    global conceded
    global scored
    global goal_difference
    global group_match_results
    but1, but2 = simulate_score(getPlayerRating(p1), getPlayerRating(p2))
    if but1 > but2:
        winner = p1
        loser = p2
    elif but1 < but2:
        winner = p2
        loser = p1
    else:
        if draw:
            winner = "draw"
            loser = (p1, p2)
        else:
            while but1 == but2:
                but1, but2 = simulate_score(getPlayerRating(p1), getPlayerRating(p2))
                if but1 > but2:
                    winner = p1
                    loser = p2
                elif but2 > but1:
                    winner = p2
                    loser = p1
    if p1 in scored:
        scored[p1] += but1
    else:
        scored[p1] = but1

    if p2 in scored:
        scored[p2] += but2
    else:
        scored[p2] = but2

    if p1 in conceded:
        conceded[p1] += but2
    else:
        conceded[p1] = but2

    if p2 in conceded:
        conceded[p2] += but1
    else:
        conceded[p2] = but1

    if p1 in goal_difference:
        goal_difference[p1] += but1
        goal_difference[p1] -= but2
    else:
        goal_difference[p1] = but1
        goal_difference[p1] -= but2

    if p2 in goal_difference:
        goal_difference[p2] += but2
        goal_difference[p2] -= but1
    else:
        goal_difference[p2] = but2
        goal_difference[p2] -= but1
    if is_group_match:
        group_match_results[group_number] += f'{p1} {but1} - {but2} {p2} : Winner is {winner}\n'
    else:
        knockout_results[knockout_index] += f'{p1} {but1} - {but2} {p2} : Winner is {winner}\n'
    #print(f'{p1} {but1} - {but2} {p2} : Winner is {winner}')
    return winner, loser


import numpy as np


def simulate_score(rating_team_a, rating_team_b):
    rating_team_a = max(min(rating_team_a, 99), 50)
    rating_team_b = max(min(rating_team_b, 99), 50)
    # Base lambda for an average team rating (set in the middle of the rating scale, around 75)
    base_lambda = 1.5

    # Adjust lambda based on team ratings
    # The lambda for each team starts from the base and is adjusted by their rating difference from the average
    lambda_a = base_lambda * (rating_team_a / 75)
    lambda_b = base_lambda * (rating_team_b / 75)

    # Adjust further based on the difference in ratings between the teams
    # The idea is to slightly increase the scoring rate of the stronger team and decrease for the weaker team
    rating_difference = rating_team_a - rating_team_b
    lambda_a_adjustment = rating_difference * 0.01  # 0.01 is a factor to adjust the influence
    lambda_b_adjustment = -lambda_a_adjustment  # Opposite adjustment for the other team

    lambda_a += lambda_a_adjustment
    lambda_b += lambda_b_adjustment

    # Ensure lambda values are positive
    lambda_a = max(0, lambda_a)
    lambda_b = max(0, lambda_b)

    # Generate match score using Poisson distribution for each team
    score_team_a = np.random.poisson(lambda_a)
    score_team_b = np.random.poisson(lambda_b)

    return score_team_a, score_team_b

def simulate_groups():
    global groups_standings, groups_calendar
    for i, group in groups.items():
        # print()
        for match in groups_calendar[i]:
            #print(f'{match[0]} VS {match[1]}')
            results = simulate_match(match[0], match[1], is_group_match=True, group_number=i)
            # print(groups_standings[i][results[0]], groups_standings[i][results[0]]['points'])
            if results[0] == "draw":
                groups_standings[i][results[1][0]]['points'] += 1
                groups_standings[i][results[1][1]]['points'] += 1
            else:
                groups_standings[i][results[0]]['points'] += 3

        for player in group:
            groups_standings[i][player]['goal_diff'] = scored[player] - conceded[player]
        #print(group_match_results[i])
    groups_standings = sort_groups(groups_standings)


# def generate_match_score(team_a_rating, team_b_rating):
#     def score_from_rating(rating):
#         weights = [2, 3, 5, 10, 7, 4, 1]
#         scores = [0, 1, 2, 3, 4, 5, 6]
#         adj_rating = (rating - 50) / 40
#         score_prob = [max(min(x*(1 - adj_rating) + x*adj_rating, 10), 1) for x in weights]
#         return random.choices(scores, weights=score_prob, k=1)[0]
#
#     team_a_score = score_from_rating(team_a_rating)
#     team_b_score = score_from_rating(team_b_rating)
#     return team_a_score, team_b_score


def sort_groups(standings):
    for group in standings.values():
        sorted_group = sorted(group.values(), key=lambda x: (-x['points'], -x['goal_diff']))
        group.clear()
        for team in sorted_group:
            group[team['name']] = team
    return standings


def show_groups_results():
    global qualified
    group_results_list = []
    for k, group in groups_standings.items():
        group_results = ""
        g_players = []
        g_players_names = []
        g_clean_names = []
        group_results += "Groupe " + str(k) + " :\n#  Nom                  Ovr J  Dif  Pts\n"
        for player in group:
            g_players.append(player)
            g_player_name = player
            while len(g_player_name) < 20:
                g_player_name += ' '
            g_players_names.append(g_player_name)
            g_clean_names.append(player)
        for i in range(0, 4):
            if group[g_players[i]]['goal_diff'] >= 0:
                group[g_players[i]]['goal_diff'] = '+' + str(group[g_players[i]]['goal_diff'])
        group_results += f"1. {g_players_names[0]} {getPlayerRating(g_clean_names[0])}  3  {group[g_players[0]]['goal_diff']}   {group[g_players[0]]['points']}"
        group_results += f"\n2. {g_players_names[1]} {getPlayerRating(g_clean_names[1])}  3  {group[g_players[1]]['goal_diff']}   {group[g_players[1]]['points']}"
        group_results += f"\n3. {g_players_names[2]} {getPlayerRating(g_clean_names[2])}  3  {group[g_players[2]]['goal_diff']}   {group[g_players[2]]['points']}"
        group_results += f"\n4. {g_players_names[3]} {getPlayerRating(g_clean_names[3])}  3  {group[g_players[3]]['goal_diff']}   {group[g_players[3]]['points']}"
        qualified.append(g_clean_names[0])
        qualified.append(g_clean_names[1])
        eliminated_groups.append(g_clean_names[2])
        eliminated_groups.append(g_clean_names[3])
        group_results_list.append(group_results)

    return group_results_list


def gen_knockouts(brackets_num):
    global brackets, qualified
    player_names = []
    # print(qualified)
    for i in qualified:
        player_names.append(i)
    brackets = []
    for bracket in range(brackets_num):
        bracket = []
        for i in range(2):
            player = random.choice(player_names)
            bracket.append(player)
            player_names.remove(player)
        brackets.append(bracket)


def simulate_knockouts():
    global knockout_results
    global qualified, knockout_results, eliminated_knockouts
    qualified = []
    knockout_results = [""] * 4
    for bracket in brackets:
        results = simulate_match(bracket[0], bracket[1], False)
        eliminated_knockouts[knockout_index].append(results[1])
        qualified.append(results[0])
    # print()
    # print('qualified : ' + str(qualified))
    # print()


def complete_simulation():
    global goals_scored, df_players_goals, knockout_index, season, groups, groups_calendar, groups_standings, free_index_groups, qualified, eliminated_groups, eliminated_knockouts, knockout_results, knockouts_ratings, scored, conceded, goal_difference, players, df_players, qualified, eliminated_groups, eliminated_knockouts, knockout_results, knockouts_season, group_match_results, current_group_index, knockout_index, kc_meaning, knockouts_ratings, scored, conceded, goal_difference, players, df_players, qualified, eliminated_groups, eliminated_knockouts, knockout_results, knockouts_ratings, players_changed

    #print("SAISON", season)
    players_changed = []
    group_match_results = [""] * 8
    knockout_results = [""] * 4
    eliminated_knockouts = []
    for i in range(4):
        eliminated_knockouts.append([])
    # Add a variable to keep track of the current group index
    current_group_index = 0
    knockout_index = 0
    kc_meaning = {0: 8, 1: 4, 2: 2, 3: 1}
    knockouts_ratings = {0: 0, 1: 1, 2: 2, 3: 3, 4: 3}
    scored = {}
    conceded = {}
    goal_difference = {}
    players = {}
    scored = {}
    conceded = {}
    goal_difference = {}
    groups = {}
    goals_scored = {}
    groups_calendar = {}
    groups_standings = {}
    free_index_groups = 0
    qualified = []
    df_players = None
    df_players_goals = None
    eliminated_groups = []


    qualified = []
    initialize_database()
    gen_groups()
    calendar_for_groups()
    simulate_groups()
    show_groups_results()
    gen_knockouts(8)
    simulate_knockouts()
    knockout_index += 1
    gen_knockouts(4)
    simulate_knockouts()
    knockout_index += 1
    gen_knockouts(2)
    simulate_knockouts()
    knockout_index += 1
    gen_knockouts(1)
    simulate_knockouts()
    knockout_index += 1
    scored = {k: v for k, v in sorted(scored.items(), key=lambda item: item[1], reverse=True)}
    conceded = {k: v for k, v in sorted(conceded.items(), key=lambda item: item[1], reverse=False)}
    goal_difference = {k: v for k, v in sorted(goal_difference.items(), key=lambda item: item[1], reverse=True)}
    # print('Top Scorers :')
    # for i in range(3):
    #     print(f'{i + 1}. {list(scored.items())[i]}')
    # print('Less Conceded :')
    # for i in range(3):
    #     print(f'{i + 1}. {list(conceded.items())[i]}')
    # print('Best Goal Difference :')
    # for i in range(3):
    #     print(f'{i + 1}. {list(goal_difference.items())[i]}')

    for player, goals in scored.items():
        #print(player, getPlayerGoals(player) + goals)
        changeGoals(season, player, getPlayerGoals(player) + goals)

    df_players_goals.to_csv('football23(1)- goals.csv', index=False)

    for player in eliminated_groups:
        changeRating(season + 1, player, getPlayerRating(player) - 1)
        players_changed.append(player)
    for h in range(len(eliminated_knockouts)):
        stage = eliminated_knockouts[h]
        if not knockouts_ratings[h] == 0:
            for player in stage:
                changeRating(season + 1, player, getPlayerRating(player) + knockouts_ratings[h])
                players_changed.append(player)
    #print(f"winner is {qualified[0]}")
    changeRating(season + 1, qualified[0], getPlayerRating(qualified[0]) + 3)
    players_changed.append(qualified[0])
    o = 0
    while list(scored.items())[o][0] in players_changed:
        if o + 1 < len(list(scored.items())):
            o += 1
    changeRating(season + 1, list(scored.items())[o][0], getPlayerRating(list(scored.items())[o][0]) + 1)

    players_changed.append(list(scored.items())[o][0])
    o = 0
    while list(conceded.items())[o][0] in players_changed:
        o += 1
    changeRating(season + 1, list(conceded.items())[o][0], getPlayerRating(list(conceded.items())[o][0]) + 1)
    players_changed.append(list(conceded.items())[o][0])
    stage = eliminated_knockouts[0]
    for player in stage:
        if player not in players_changed:
            changeRating(season + 1, player, getPlayerRating(player))
            players_changed.append(player)
    df_players.to_csv('football23(1).csv', index=False)
    season+=1


def start_button():
    global current_group_index, groups_results

    initialize_database()
    gen_groups()
    calendar_for_groups()
    simulate_groups()

    groups_results = show_groups_results()

    # We start showing the first group in the list
    current_group_index = 0
    label.config(text=groups_results[current_group_index])
    label2.config(text=group_match_results[current_group_index], padx=250, pady=50)
    startButton.destroy()
    knockout_buttons[knockout_index].place(x=width / 2, y=height / 2, anchor=tk.CENTER)


def show_next_group():
    global current_group_index, groups_results, label, label2

    # Increments the current group index
    current_group_index += 1

    # Reset to the first group when it reaches the end
    if current_group_index >= len(groups_results):
        current_group_index = 0

    # Update the group label with the next group_result
    label.config(text=groups_results[current_group_index])
    label2.config(text=group_match_results[current_group_index])


def kc_button_def():
    nextButton.place_forget()
    nextButton.place(x=width / 2, y=height / 1.35, anchor=tk.CENTER)
    label2.grid_forget()
    knockout_buttons[knockout_index].destroy()
    gen_knockouts(kc_meaning[knockout_index])
    knockouts_results = ""
    for match in brackets:
        knockouts_results += f"{match[0]} {getPlayerRating(match[0])} vs {getPlayerRating(match[1])} {match[1]}\n"
    label.config(text=knockouts_results)
    nextButton.config(command=lambda: sim_knockouts_button())


def sim_knockouts_button():
    global label2, knockout_index
    global scored, conceded, goal_difference
    simulate_knockouts()
    label2.config(text=knockout_results[knockout_index])
    label2.grid(row=0, column=5)
    knockout_index += 1
    nextButton.place_forget()
    if knockout_index == 4:
        scored = {k: v for k, v in sorted(scored.items(), key=lambda item: item[1], reverse=True)}
        conceded = {k: v for k, v in sorted(conceded.items(), key=lambda item: item[1], reverse=False)}
        goal_difference = {k: v for k, v in sorted(goal_difference.items(), key=lambda item: item[1], reverse=True)}
        players_changed = []
        # print('Top Scorers :')
        # for i in range(3):
        #     print(f'{i + 1}. {list(scored.items())[i]}')
        # print('Less Conceded :')
        # for i in range(3):
        #     print(f'{i + 1}. {list(conceded.items())[i]}')
        # print('Best Goal Difference :')
        # for i in range(3):
        #     print(f'{i + 1}. {list(goal_difference.items())[i]}')
        for player in eliminated_groups:
            changeRating(season + 1 , player, getPlayerRating(player)-1)
            players_changed.append(player)
        for h in range(len(eliminated_knockouts)):
            stage = eliminated_knockouts[h]
            if not knockouts_ratings[h] == 0:
                for player in stage:
                    changeRating(season + 1, player, getPlayerRating(player) + knockouts_ratings[h])
                    players_changed.append(player)
        #print(f"winner is {qualified[0]}")
        changeRating(season+1, qualified[0], getPlayerRating(qualified[0])+3)
        players_changed.append(qualified[0])
        o = 0
        while list(scored.items())[o][0] in players_changed:
            if o+1 < len(list(scored.items())):
                o += 1
        changeRating(season + 1, list(scored.items())[o][0], getPlayerRating(list(scored.items())[o][0]) + 1)

        players_changed.append(list(scored.items())[o][0])
        o = 0
        while list(conceded.items())[o][0] in players_changed:
            o += 1
        changeRating(season + 1, list(conceded.items())[o][0], getPlayerRating(list(conceded.items())[o][0]) + 1)
        players_changed.append(list(conceded.items())[o][0])
        stage = eliminated_knockouts[0]
        for player in stage:
            if player not in players_changed:
                changeRating(season + 1, player, getPlayerRating(player) + 0)
                players_changed.append(player)

    try:
        knockout_buttons[knockout_index].place(x=width / 2, y=height / 2, anchor=tk.CENTER)
    except IndexError:
        print('Finished')


label = tk.Label(root, justify='left', font=("Courier New", 20))
label.grid(row=0, column=0)

label2 = tk.Label(root, justify='left', font=("Courier New", 18))
label2.grid(row=0, column=5)


# Bind the Start button to the start_button function
startButton = tk.Button(root, text="Start", font=("Times", int(width / 40), "bold"), fg="black")
startButton.place(x=width / 2, y=height / 2, anchor=tk.CENTER)
startButton.config(command=lambda: start_button())

# Create a Next Button and bind it to the show_next_group function
nextButton = tk.Button(root, text="Next", font=("Times", int(width / 40), "bold"), fg="black")
nextButton.place(x=width / 2, y=height / 1.35, anchor=tk.CENTER)
nextButton.config(command=lambda: show_next_group())

knockout_buttons = []

for i in range(4):
    kc_button = tk.Button(root, text=f"Knockouts {1 + i}", font=("Times", int(width / 40), "bold"), fg="black")
    kc_button.config(command=lambda: kc_button_def())
    knockout_buttons.append(kc_button)

import cProfile
import pstats


# with cProfile.Profile() as pr:
#     complete_simulation()
#
# stats = pstats.Stats(pr)
# stats.sort_stats(pstats.SortKey.TIME)
# stats.print_stats()

for i in range(1000):
    start_time = time.time()
    complete_simulation()
    print(i, time.time()-start_time)

# complete_simulation()
#root.mainloop()
