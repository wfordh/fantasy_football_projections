"""Script for pulling projections and comparing FAs to my roster.

get_user_leagues and get_nfl_state repeated over two files...
"""

import argparse
import json
import logging
import os
from pprint import pformat

from halo import Halo
from sleeper_wrapper import League, Players
from tqdm import tqdm

from utils.utils import combine_projections

# add help descriptions
parser = argparse.ArgumentParser()
parser.add_argument(
    "--pull_players",
    action=argparse.BooleanOptionalAction,
    required=True,
    help="--pull_players if you want to re-pull players from Sleeper. --no-pull_players if you do not.",
)
parser.add_argument(
    "-p",
    "--positions",
    required=False,
    nargs="+",
    help="List of positions to pull. Comma separated and no quotes.",
)
parser.add_argument(
    "-a",
    "--all_user_leagues",
    help="Pull all of a user's leagues?",
    type=str,
    default="yes",
    choices=["yes", "no"],
)

logging.basicConfig(level=logging.INFO)


def get_user_leagues(all_leagues: list[League], nfl_state: dict) -> list[League]:
    """"""
    if all_leagues:
        user_id = os.environ.get("SLEEPER_USER_ID", "")
        season = nfl_state.pop("season", None)
        user = User(user_id)
        leagues = user.get_all_leagues("nfl", season)
        leagues = [League(league["league_id"]) for league in leagues]
        return leagues
    league_id = os.environ.get("SLEEPER_LEAGUE_ID", "")
    return [League(league_id)]


def get_nfl_state() -> dict:
    """"""
    return requests.get("https://api.sleeper.app/v1/state/nfl").json()


def get_sleeper_players(pull_players: bool, players: Players) -> dict:
    # check the date or season type? if preseason, pull the players?
    # or check the date of the saved file? some way to make it dynamic
    # probably need to investigate some of the possible values for the season / league status
    if pull_players:
        all_players = players.get_all_players()
        with open("./data/sleeper_players_current.json", "w") as outfile:
            json.dump(all_players, outfile)
    else:
        with open("./data/sleeper_players_current.json", "r") as infile:
            all_players = json.load(infile)

    return all_players


def get_own_players(league_rosters: list[dict]) -> dict:
    user_id = os.environ.get(
        "SLEEPER_USER_ID", ""
    )  # turn this into an global var? now calling twice
    own_team = [team for team in league_rosters if team["owner_id"] == user_id].pop()
    return own_team["players"]


def add_projections_to_keep_players(keep_players: dict, combined_proj) -> dict:
    for p_id, p_data in keep_players.items():
        try:
            p_data["projections"] = combined_proj[p_data["search_full_name"]][
                "avg_proj_pts"
            ]
        except KeyError:
            p_data["projections"] = 0

    return keep_players


def get_waiver_options(
    own_roster: dict, free_agents: dict, threshold: float = 0.95
) -> dict:
    # possible to group by position to make it cleaner?
    waiver_players = dict()
    for p_id, p_data in own_roster.items():
        # ignore if on IR or projection is 0 -- player is likely a "stash"
        if p_data["status"] == "Injured Reserve" or p_data["projections"] == 0:
            continue
        waiver_dict = {
            "drop_proj": p_data["projections"],
            "players_to_add": list(),
        }
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

    return waiver_players


def main():
    with Halo("Setting up script details.", spinner="dots") as spinner:
        # add a setup FUNCTION?
        args = parser.parse_args()
        command_args = dict(vars(args))
        pull_players = command_args.pop("pull_players", None)
        all_leagues = True if command_args.pop("all_user_leagues") == "yes" else False
        leagues = get_user_leagues(all_leagues, nfl_state)

        # better way to do this?
        keep_positions = tuple(command_args.pop("positions", None).pop().split(","))
        if keep_positions == ("all",):
            keep_positions = ["QB", "RB", "WR", "TE"]
        elif keep_positions == ("flex",):
            keep_positions = ["RB", "WR", "TE"]
        spinner.succeed()

    Halo(
        f"Included positions are {', '.join(keep_positions)}", spinner="dots"
    ).succeed()
    players = Players()

    for league in leagues:
        league_rosters = league.get_rosters()

        all_players = get_sleeper_players(pull_players, players)

        own_players = get_own_players(league_rosters)

        with Halo("Pulling projections", spinner="dots") as spinner:
            combined_proj = combine_projections(keep_positions)
            spinner.succeed()

        # issue #5 in the repo? move this to when pulling the players?
        keep_players = {
            p_id: p_data
            for p_id, p_data in all_players.items()
            if p_data["position"] in keep_positions
        }

        keep_players = add_projections_to_keep_players(keep_players, combined_proj)
        Halo("Added projections to players.", spinner="dots").succeed()
        # save keep_players for testing
        ## how necessary is this?
        with open("./data/sleeper_players_keep.json", "w") as outfile:
            json.dump(keep_players, outfile)
        # ID free agents by comparing keep_players to rosters
        ## could this be done with the league.get_free_agents() and .get_rosters() functions?
        rostered_player_ids = [
            player for team in league_rosters for player in team["players"]
        ]
        with Halo(
            "Separating players into rostered and FAs.", spinner="dots"
        ) as spinner:
            # need some comments here for free_agents. why p_data["team"] logic? avoid real life free agents?
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

        # comparison
        own_roster = {
            p_id: p_data
            for p_id, p_data in rostered_players.items()
            if p_id in own_players
        }

        with Halo(
            "Compared FA projections to your roster. Returning players with better projections.",
            spinner="dots",
        ) as spinner:
            waiver_players = get_waiver_options(own_roster, free_agents)
            spinner.succeed()

        logging.info(pformat(waiver_players))


if __name__ == "__main__":
    main()
