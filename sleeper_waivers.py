
import argparse
import json
import pprint
import os
from sleeper_wrapper import Players, League
from tqdm import tqdm, trange

parser = argparse.ArgumentParser()
parser.add_argument("-d", "--dry_run", type=bool, required=True)

def main():
	league_id = os.environ.get("SLEEPER_LEAGUE_ID", "")
	user_id = os.environ.get("SLEEPER_USER_ID", "")
	is_dry_run = False

	league = League(league_id)
	players = Players()

	league_rosters = league.get_rosters()
	if is_dry_run:
		all_players = players.get_all_players()
		with open("./data/sleeper_players_current.json", "w") as outfile:
			json.dump(all_players, outfile)
	else:
		with open("./data/sleeper_players_current.json", "r") as infile:
			all_players = json.load(infile)

	own_team = [team for team in league_rosters if team["owner_id"]==user_id].pop()



if __name__ == '__main__':
	main()