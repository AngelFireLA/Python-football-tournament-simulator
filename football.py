import random
import csv
import os
import pandas as pd
import math

season = 11

players = {}
# sortedplayers = sorted(players[1].items(), key=lambda kv: (kv[1], kv[0]))
# print(sortedplayers)



def initialize_database():
	global players
	players = pd.read_csv('football - Copy.csv', index_col=[1], header=None, dtype={0: str}).dropna().set_index(0).squeeze().to_dict()
	df_players = pd.read_csv('football - Copy.csv', index=False)
	# for player in players[season]:
	# 	print(player, players[season][player])

def pair_players():
	players.rename(columns = {'Unnamed: 0':''}, inplace = True)
	if not "Saison " + str(season) in players.columns:
		players.insert(len(csv_file.columns), "Saison " + str(season), 1, False)
	changeRating(season, "Timber", 89)
	player_list = []
	winners = []
	for player in players[season]:
		player_list.append(player)
	player_list_lenght = len(player_list)
	#print(player_list)
	for loop in range(int(math.log(player_list_lenght, 2))):
	    print( )
	    print("Il reste", len(player_list), "joueurs.")
	    print()
	    for pairs in range(int((len(player_list)+1)/2)):
		    player1 = random.choice(player_list)
		    player_list.remove(player1)
		    player2 = random.choice(player_list)
		    player_list.remove(player2)
		    print(player1, getPlayerRating(season, player1), "vs", player2, getPlayerRating(season, player2))
		    but1 = random.randint(0, int(getPlayerRating(season, player1)/10))
		    but2 = random.randint(0, int(getPlayerRating(season, player2)/10))
		    while but1 == but2:
		    	but1 = random.randint(0, int(getPlayerRating(season, player1)/10))
		    	but2 = random.randint(0, int(getPlayerRating(season, player2)/10))
		    input()
		    if but1 > but2:
			    winners.append(player1)
			    print("Winner :", player1, str(but1) + ":" + str(but2))
		    else:
			    winners.append(player2)
			    print("Winner :", player2, str(but2) + ":" + str(but1))
		    print()
	    for p in winners:
	    	player_list.append(p)
	    winners = []
	print()
	print("Winner :", player_list[0], getPlayerRating(season, player_list[0]))
	players.to_csv('football - Copy.csv', index=False)

def main():
	initialize_database()
	pair_players()


def getRating(season : int, name) -> int:
	return int(players[season][name])
	
def changePlayerRating(season : int, name, rating : int):
		players.loc[players[''] == 'name', "Saison " + season] = rating

main()


