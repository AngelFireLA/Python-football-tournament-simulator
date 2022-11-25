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
	global df_players
	players = pd.read_csv('football - Copy.csv', index_col=[1], header=None, dtype={0: str}).dropna().set_index(0).squeeze().to_dict()
	df_players = pd.read_csv('football - Copy.csv')
	# for player in players[season]:
	# 	print(player, players[season][player])

def pair_players():
	df_players.rename(columns = {'Unnamed: 0':''}, inplace = True)
	if not "Saison " + str(season) in df_players.columns:
		df_players.insert(len(df_players.columns), "Saison " + str(season), 1, False)
	changeRating(season, "Timber", 89)
	player_list = []
	winners = []
	losers = []
	for player in players[season]:
		player_list.append(player)
	player_list_lenght = len(player_list)
	rounds = int(math.log(player_list_lenght, 2))
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
		    if but1 > but2:
			    winners.append(player1)
			    losers.append(player2)
			    print("Winner :", player1, str(but1) + ":" + str(but2))
		    else:
			    winners.append(player2)
			    losers.append(player1)
			    print("Winner :", player2, str(but2) + ":" + str(but1))
		    
		    print()
	    for p in winners:
	    	player_list.append(p)
	    winners = []
	    for l in losers:
                if rounds == 6:
                        if loop == 0:
                                changeRating(season+1, l, getPlayerRating(season, name)-2)
                        elif loop == 1:
                                changeRating(season+1, l, getPlayerRating(season, name)-1)
                        elif loop == 2:
                                changeRating(season+1, l, getPlayerRating(season, name))
                        elif loop == 3:
                                changeRating(season+1, l, getPlayerRating(season, name)+1)
                        elif loop == 4:
                                changeRating(season+1, l, getPlayerRating(season, name)+3)
                        elif loop == 5:
                                changeRating(season+1, l, getPlayerRating(season, name)+5)
                        
                if rounds == 5 and loop==0:
                        changeRating(season+1, l, getPlayerRating(season, name)-2)
	print()
	print("Winner :", player_list[0], getPlayerRating(season, player_list[0]))
	df_players.to_csv('football - Copy.csv', index=False)

def main():
	initialize_database()
	pair_players()


def getPlayerRating(season : int, name) -> int:
	return int(players[season][name])
	
def changeRating(season : int, name, rating : int):
        df_players.loc[df_players[''] == name, "Saison " + str(season)] = rating

main()


