import re
import requests
import os
import sleeper_wrapper as sleeper
from tqdm import tqdm


def clean_name(player_name):
    name_suffixes = ("jr", "sr", "ii", "iii", "iv", "v")
    player_name = re.sub(r"([.'])", "", player_name.lower())
    player_name = (
        player_name.rsplit(maxsplit=1)[0]
        if player_name.endswith(name_suffixes)
        else player_name
    )
    return re.sub(r"([ ])", "", player_name)


def merge_projections(cbs_proj, nf_proj):
    # what exactly is the cbs_proj and nf_proj?
    # maybe use keyword args and list of projections?
    # final struct:
    # key: player name and/or id
    # position: position
    # website 1: proj 1
    # website 2: proj 2
    nf_cleaned_names = {clean_name(x): x for x in nf_proj.keys()}
    cbs_cleaned_names = {clean_name(x): x for x in cbs_proj.keys()}

    # now want {clean_name: {"cbs": name, "nf": name}}
    cleaned_names = set(nf_cleaned_names).union(cbs_cleaned_names)
    combined_proj = dict()
    missing_names = {"cbs_names": [], "nf_names": []}
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

    print(missing_names)

    return combined_proj


def sleeper_add_projections():
    pass
