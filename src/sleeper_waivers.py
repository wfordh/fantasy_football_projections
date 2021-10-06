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
from utils.utils import combine_projections

# add help descriptions
parser = argparse.ArgumentParser()
parser.add_argument(
    "-d",
    "--dry_run",
    type=bool,
    required=True,
    help="True if you want to re-pull players from Sleeper",
)
parser.add_argument(
    "-p",
    "--positions",
    required=False,
    nargs="+",
    help="List of positions to pull. Space separated and no quotes.",
)


def main():
    with Halo("Setting up script details.", spinner="dots") as spinner:
        league_id = os.environ.get("SLEEPER_LEAGUE_ID", None)
        user_id = os.environ.get("SLEEPER_USER_ID", None)

        args = parser.parse_args()
        command_args = dict(vars(args))
        is_dry_run = command_args.pop("dry_run", None)
        keep_positions = tuple(command_args.pop("positions", None).pop().split(","))
        if keep_positions == ("all",):
            keep_positions = ["QB", "RB", "WR", "TE"]
        elif keep_positions == ("flex",):
            keep_positions = [ "RB", "WR", "TE"]
        spinner.succeed()

    Halo(
        f"Included positions are {', '.join(keep_positions)}", spinner="dots"
    ).succeed()
    league = League(league_id)
    players = Players()

    league_rosters = league.get_rosters()
    # shouldn't this be if not is_dry_run?
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
    with Halo("Separating players into rostered and FAs.", spinner="dots") as spinner:
        free_agents = {
            p_id: p_data
            for p_id, p_data in keep_players.items()
            if p_id not in rostered_player_ids and p_data["team"] is not None
        }
        rostered_players = {
            p_id: p_data
            for p_id, p_data in keep_players.items()
            if p_id in rostered_player_ids
        }
        spinner.succeed()

    with Halo("Pulling projections", spinner="dots") as spinner:
        combined_proj = combine_projections(keep_positions)
        spinner.succeed()

    cleaned_names = combined_proj.keys()
    # add projections in to rosters
    for p_id, p_data in free_agents.items():
        # workaround for players who aren't in all 3
        # if p_data["search_full_name"] in cleaned_names:
        try:
            p_data["projections"] = combined_proj[p_data["search_full_name"]][
                "avg_proj_pts"
            ]

        # else:
        except KeyError:
            p_data["projections"] = 0

    for p_id, p_data in rostered_players.items():
        # if p_data["search_full_name"] in cleaned_names:
        try:
            p_data["projections"] = combined_proj[p_data["search_full_name"]][
                "avg_proj_pts"
            ]
        # else:
        except KeyError:
            p_data["projections"] = 0
    Halo("Added projections to FAs and rostered players.", spinner="dots").succeed()

    # comparison
    own_roster = {
        p_id: p_data for p_id, p_data in rostered_players.items() if p_id in own_players
    }
    waiver_players = dict()
    for p_id, p_data in own_roster.items():
        if p_data["status"] == "Injured Reserve":
            continue
        waiver_dict = {
            "drop_proj": p_data["projections"],
            "players_to_add": list(),
        }
        # don't look at FA if projection is 0
        if p_data["projections"] == 0:
            continue
        for fa_id, fa_data in free_agents.items():
            if (fa_data["projections"] > 0.95 * p_data["projections"]) and (
                fa_data["position"] == p_data["position"]
            ):
                fa_dict = {
                    "waiver_player": fa_data["search_full_name"],
                    "waiver_proj": fa_data["projections"],
                }
                waiver_dict["players_to_add"].append(fa_dict)
        waiver_players[p_data["search_full_name"]] = waiver_dict
    Halo(
        "Compared FA projections to your roster. Returning players with better projections.",
        spinner="dots",
    ).succeed()

    pp = pprint.PrettyPrinter()
    pp.pprint(waiver_players)


if __name__ == "__main__":
    main()
