name_suffixes = ("ii", "iii", "iv", "v", "jr", "sr")


def clean_name(player_name):
    player_name = player_name.lower().replace(".", "").replace("'", "")
    name_suffixes = ("jr", "sr", "ii", "iii", "iv", "v")
    return (
        player_name.rsplit(maxsplit=1)[0]
        if player_name.endswith(name_suffixes)
        else player_name
    )

def merge_projections(cbs_proj, nf_proj):
	# what exactly is the cbs_proj and nf_proj?
	# maybe use keyword args and list of projections?
	# final struct:
	# key: player name and/or id
		# position: position
		# website 1: proj 1
		# website 2: proj 2
	nf_cleaned_names = {clean_name(x):x for x in nf_proj.keys()}
	cbs_cleaned_names = {clean_name(x):x for x in cbs_proj.keys()}

	# now want {clean_name: {"cbs": name, "nf": name}}
	cleaned_names = set(nf_cleaned_names).union(cbs_cleaned_names)
	combined_proj = dict.fromkeys(cleaned_names)
	for name in cleaned_names:
		combined_proj[name]["cbs_proj"] = cbs_proj[cbs_cleaned_names["name"]]
		combined_proj[name]["nf_proj"] = nf_proj[nf_cleaned_names["name"]]
		combined_proj[name]["position"] = nf_proj[nf_cleaned_names["position"]]


def get_sleeper_rosters():
	pass

def sleeper_add_projections():
	pass
