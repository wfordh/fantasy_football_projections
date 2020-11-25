"""Script for pulling projections and comparing FAs to my roster.

more details to come
"""

import argparse
import json
import pprint
import os
from halo import Halo
from sleeper_wrapper import Players, League
from tqdm import tqdm, trange
from numberfire_projections import numberfireProjections
from utils import clean_name

# add help descriptions
parser = argparse.ArgumentParser()
parser.add_argument("-d", "--dry_run", type=bool, required=True)
parser.add_argument("-p", "--positions", required=False, nargs="+")


def main():
    league_id = os.environ.get("SLEEPER_LEAGUE_ID", None)
    user_id = os.environ.get("SLEEPER_USER_ID", None)

    args = parser.parse_args()
    command_args = dict(vars(args))
    is_dry_run = command_args.pop("dry_run", None)
    # log these?
    keep_positions = tuple(command_args.pop("positions", None))

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
    own_players = own_team["players"]
    keep_players = {
        p_id: p_data
        for p_id, p_data in all_players.items()
        if p_data["position"] in keep_positions
    }
    # save keep_players for testing
    with open("./data/sleeper_players_keep.json", "w") as outfile:
        json.dump(keep_players, outfile)
    # ID free agents by comparing keep_players to rosters
    rostered_player_ids = [
        player for team in league_rosters for player in team["players"]
    ]
    free_agents = {
        p_id: p_data
        for p_id, p_data in keep_players.items()
        if p_id not in rostered_player_ids
    }
    rostered_players = {
        p_id: p_data
        for p_id, p_data in keep_players.items()
        if p_id in rostered_player_ids
    }
    # pull projections
    nfp = numberfireProjections("half_ppr")

    with Halo("Pulling Numberfire Projections", spinner="dots") as spinner:
        nfp.get_data("flex")
        nfp.convert_projections()
        spinner.succeed()

    nf_cleaned_names = {clean_name(x): x for x in nfp.projections.keys()}
    # add projections in to rosters
    for p_id, p_data in free_agents.items():
        if p_data["search_full_name"] in nf_cleaned_names.keys():
            p_data["numberfire_projections"] = nfp.projections[
                nf_cleaned_names[p_data["search_full_name"]]
            ]
        else:
            p_data["numberfire_projections"] = 0

    for p_id, p_data in rostered_players.items():
        if p_data["search_full_name"] in nf_cleaned_names.keys():
            p_data["numberfire_projections"] = nfp.projections[
                nf_cleaned_names[p_data["search_full_name"]]
            ]
        else:
            p_data["numberfire_projections"] = 0

    # comparison
    own_roster = {
        p_id: p_data for p_id, p_data in rostered_players.items() if p_id in own_players
    }
    waiver_players = list()
    for p_id, p_data in own_roster.items():
        if p_data["status"] == "Injured Reserve":
            continue
        waiver_dict = {
            "drop_player": p_data["search_full_name"],
            "drop_proj": p_data["numberfire_projections"],
            "players_to_add": list(),
        }
        for fa_id, fa_data in free_agents.items():
            if (
                fa_data["numberfire_projections"] > p_data["numberfire_projections"]
            ) and (fa_data["position"] == p_data["position"]):
                fa_dict = {
                    "waiver_player": fa_data["search_full_name"],
                    "waiver_proj": fa_data["numberfire_projections"],
                }
                waiver_dict["players_to_add"].append(fa_dict)
        waiver_players.append(waiver_dict)

    pp = pprint.PrettyPrinter()
    pp.pprint(waiver_players)


if __name__ == "__main__":
    main()
