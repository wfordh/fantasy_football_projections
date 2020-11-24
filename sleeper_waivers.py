import argparse
import json
import pprint
import os
from halo import Halo
from sleeper_wrapper import Players, League
from tqdm import tqdm, trange
from numberfire_projections import numberfireProjections
from utils import clean_name

parser = argparse.ArgumentParser()
parser.add_argument("-d", "--dry_run", type=bool, required=True)
parser.add_argument("-p", "--positions", required=False)


def main():
    league_id = os.environ.get("SLEEPER_LEAGUE_ID", None)
    user_id = os.environ.get("SLEEPER_USER_ID", None)

    args = parser.parse_args()
    command_args = dict(vars(args))
    is_dry_run = command_args.pop("dry_run", None)
    keep_positions = ("QB", "RB", "WR", "TE", "D/ST")  # make CLI arg. D/ST??

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

    own_team = [team for team in league_rosters if team["owner_id"] == user_id].pop()
    keep_players = {
        p_id: p_data
        for p_id, p_data in all_players.items()
        if p_data["position"] in keep_positions
    }
    # save keep_players for testing
    with open("./data/sleeper_players_keep.json", "w") as outfile:
        json.dump(keep_players, outfile)
    # ID free agents by comparing keep_players to rosters
    # currently rostered_players is just IDs while FA is all of the player data
    rostered_players = [player for team in league_rosters for player in team["players"]]
    free_agents = {
        p_id: p_data
        for p_id, p_data in keep_players.items()
        if p_id not in rostered_players
    }
    # pull projections
    nfp = numberfireProjections("half_ppr")

    with Halo("Pulling Numberfire Projections", spinner="dots") as spinner:
        nfp.get_data("flex")
        nfp.convert_projections()
        spinner.succeed()

    nf_cleaned_names = {clean_name(x):x for x in nf_proj.keys()}
    # add projections in to rosters for comparisons
    for p_id, p_data in free_agents.items():
        if p_data["search_full_name"] in nf_cleaned_names.keys():
            p_data["numberfire_projections"] = nfp.projections[nf_cleaned_names[p_data["search_full_name"]]]
        else:
            p_data["numberfire_projections"] = 0

    


if __name__ == "__main__":
    main()
