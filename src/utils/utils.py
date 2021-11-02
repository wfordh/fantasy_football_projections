import csv
import re
import requests
import os
import sleeper_wrapper as sleeper
from tqdm import tqdm
import pprint
import json
from halo import Halo
from projections.cbs_projections import cbsProjections
from projections.numberfire_projections import numberfireProjections
from projections.nfl_projections import nflProjections
from typing import Union, List


def clean_name(player_name):
    name_suffixes = ("jr", "sr", "ii", "iii", "iv", "v")
    player_name = re.sub(r"([.'])", "", player_name.lower())
    player_name = (
        player_name.rsplit(maxsplit=1)[0]
        if player_name.endswith(name_suffixes)
        else player_name
    )
    return re.sub(r"([ ]|-)", "", player_name)


# turn this into **kwargs or something once more projections are added?
def merge_projections(cbs_proj, nf_proj, nfl_proj):
    # what exactly is the cbs_proj and nf_proj?
    # maybe use keyword args and list of projections?
    # final struct:
    # key: player name and/or id
    # position: position
    # website 1: proj 1
    # website 2: proj 2
    nf_cleaned_names = {clean_name(x): x for x in nf_proj.keys()}
    cbs_cleaned_names = {clean_name(x): x for x in cbs_proj.keys()}
    nfl_cleaned_names = {clean_name(x): x for x in nfl_proj.keys()}

    # now want {clean_name: {"cbs": name, "nf": name}}
    cleaned_names = (
        set(nf_cleaned_names).union(cbs_cleaned_names).union(nfl_cleaned_names)
    )
    combined_proj = dict()
    missing_names = {"cbs_names": [], "nf_names": [], "nfl_names": []}

    for name in tqdm(cleaned_names):
        combined_proj[name] = dict()
        if name in cbs_cleaned_names.keys():
            combined_proj[name]["cbs_proj"] = cbs_proj[cbs_cleaned_names[name]]
        else:
            missing_names["cbs_names"].append(name)
        if name in nf_cleaned_names.keys():
            combined_proj[name]["nf_proj"] = nf_proj[nf_cleaned_names[name]]
            # not sure if this should be here or elsewhere
            # combined_proj[name]["position"] = nf_proj[nf_cleaned_names[name]]["position"]
        else:
            missing_names["nf_names"].append(name)
        if name in nfl_cleaned_names.keys():
            combined_proj[name]["nfl_proj"] = nfl_proj[nfl_cleaned_names[name]]
        else:
            missing_names["nfl_names"].append(name)

    # figure out what to do with missing names
    # pp = pprint.PrettyPrinter()
    # pp.pprint(missing_names)

    return combined_proj


def combine_projections(positions: Union[List, str], all_proj: bool = True):
    # make these CLI args?
    scoring = "half_ppr"
    # positions = "flex"
    stat_period = "ros"

    nfp = numberfireProjections("half_ppr")
    cbs = cbsProjections("half_ppr", season=2021)
    nfl = nflProjections("half_ppr")

    with Halo(text="Pulling projections", spinner="dots") as spinner:
        nfp.get_data(positions)
        cbs.get_data(positions, stat_period)
        nfl.compile_data(positions)
        spinner.succeed()

    nfp.convert_projections()
    cbs.convert_projections()
    nfl.convert_projections()

    combined_proj = merge_projections(cbs.projections, nfp.projections, nfl.projections)
    players_not_all_sources = list()
    for player, sources in combined_proj.items():
        if len(sources) != 3:
            continue
        cbs_player = sources["cbs_proj"]
        nfp_player = sources["nf_proj"]
        nfl_player = sources["nfl_proj"]

        # depending on positions and teams to be uniform right now
        if (
            cbs_player["position"] == nfp_player["position"]
            and cbs_player["position"] == nfl_player["position"]
            and cbs_player["team"] == nfp_player["team"]
            and cbs_player["team"] == nfl_player["team"]
        ):
            combined_proj[player]["avg_proj_pts"] = (
                cbs_player["proj_pts"] + nfp_player["proj_pts"] + nfl_player["proj_pts"]
            ) / 3
        else:
            players_not_all_sources.append(player)

    with open("./data/combined_projections_test.json", "w") as outfile:
        json.dump(combined_proj, outfile)

    with open(
        f"./data/combined_projections_missing_players_{'_'.join(positions)}.csv", "w"
    ) as outfile:
        player_writer = csv.writer(outfile)
        for player in players_not_all_sources:
            player_writer.writerow([player])

    return combined_proj


def sleeper_add_projections():
    pass


def get_league_team_names(league, names_as_keys: bool = False):
    users = league.get_users()
    team_name_dict = league.map_users_to_team_names(users)
    if names_as_keys:
        return {name: team_id for team_id, name in team_name_dict.items()}
    return team_name_dict
