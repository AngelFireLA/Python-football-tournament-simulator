from random import *
import csv
import os
import pandas as pd

season = 1

players = {}
# sortedplayers = sorted(players[1].items(), key=lambda kv: (kv[1], kv[0]))
# print(sortedplayers)



def initialize_database():
	global players
	players = pd.read_csv('football.csv', header=None, dtype={0: str}).dropna().set_index(0).squeeze().to_dict()
	# for player in players[season]:
	# 	print(player, players[season][player])

def pair_players():
	player_list = []
	for player in players[season]:
		player_list.append(player)
	player_list_lenght = len(player_list)+1
	#print(player_list)
	for pairs in range(int(player_list_lenght/2)):
		player1 = player_list[randint(0, len(player_list)-1)]
		player_list.remove(player1)
		player2 = player_list[randint(0, len(player_list)-1)]
		player_list.remove(player2)
		print(player1, "vs", player2)
		if randint(0, 10) >= randint(0, 10):
			player_list.append(player1)
		else:
			player_list.append(player2)
	print()
	for pairs in range(int(player_list_lenght / 4)):
		player1 = player_list[randint(0, len(player_list) - 1)]
		player_list.remove(player1)
		player2 = player_list[randint(0, len(player_list) - 1)]
		player_list.remove(player2)
		print(player1, "vs", player2)
		if randint(0, 10) >= randint(0, 10):
			player_list.append(player1)
		else:
			player_list.append(player2)
	print()
	for pairs in range(int(player_list_lenght / 8)):
		player1 = player_list[randint(0, len(player_list) - 1)]
		player_list.remove(player1)
		player2 = player_list[randint(0, len(player_list) - 1)]
		player_list.remove(player2)
		print(player1, "vs", player2)
		if randint(0, 10) >= randint(0, 10):
			player_list.append(player1)
		else:
			player_list.append(player2)
	print()
	for pairs in range(int(player_list_lenght / 16)):
		player1 = player_list[randint(0, len(player_list) - 1)]
		player_list.remove(player1)
		player2 = player_list[randint(0, len(player_list) - 1)]
		player_list.remove(player2)
		print(player1, "vs", player2)
		if randint(0, 10) >= randint(0, 10):
			player_list.append(player1)
		else:
			player_list.append(player2)
	print()
	for pairs in range(int(player_list_lenght / 32)):
		player1 = player_list[randint(0, len(player_list) - 1)]
		player_list.remove(player1)
		player2 = player_list[randint(0, len(player_list) - 1)]
		player_list.remove(player2)
		print(player1, "vs", player2)
		if randint(0, 10) >= randint(0, 10):
			player_list.append(player1)
		else:
			player_list.append(player2)
	print(player_list)

def main():
	initialize_database()
	pair_players()


def getPlayerRating(season : int, name) -> int:
	return int(players[season][name])

main()


