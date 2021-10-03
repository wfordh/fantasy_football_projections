import json
from halo import Halo
from projections.cbs_projections import cbsProjections
from projections.numberfire_projections import numberfireProjections
from projections.nfl_projections import nflProjections
from utils import clean_name, merge_projections
from typing import Union, List

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
		if cbs_player["position"] == nfp_player["position"] and cbs_player["position"] == nfl_player["position"] and cbs_player["team"] == nfp_player["team"] and cbs_player["team"] == nfl_player["team"]:
			combined_proj[player]["avg_proj_pts"] = (cbs_player["proj_pts"] + nfp_player["proj_pts"] + nfl_player["proj_pts"]) / 3
		else:
			players_not_all_sources.append(player)

	with open("./data/combined_projections_test.json", "w") as outfile:
		json.dump(combined_proj, outfile)

	return combined_proj

