import json
from halo import Halo
from cbs_projections import cbsProjections
from numberfire_projections import numberfireProjections
from utils import clean_name, merge_projections

def main():
	# make these CLI args?
	scoring = "half_ppr"
	positions = "flex"
	stat_period = "ros"

	nfp = numberfireProjections("half_ppr")
	cbs = cbsProjections("half_ppr", season=2020)

	with Halo(text="Pulling projections", spinner="dots") as spinner:
		nfp.get_data(positions)
		cbs.get_data(positions, stat_period)
		spinner.succeed()

	nfp.convert_projections()
	cbs.convert_projections()

	combined_proj = merge_projections(cbs.projections, nfp.projections)
	with open("./data/combined_projections_test.json", "w") as outfile:
		json.dump(combined_proj, outfile)

if __name__ == '__main__':
	main()
