from random import *
import csv
import os
import pandas as pd
players = pd.read_csv('football.csv', header=None, dtype={0: str}).dropna().set_index(0).squeeze().to_dict()
#sortedplayers = sorted(players[11].items(), key=lambda x:x[1])
sortedplayers = sorted(players[11].items(), key=lambda kv: (kv[1], kv[0]))
for player in range(len(sortedplayers)):
	#print(player, players[11][player])
	print(sortedplayers)
	print()
	
