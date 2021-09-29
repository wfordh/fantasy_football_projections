import requests
from bs4 import BeautifulSoup
from pathlib import Path
import csv
from time import sleep
import random


class cbsProjections:
	# fill out rest and make aliases for 'half' and 'full'
	scoring_map = {
		"half_ppr": {
			"pass_yds": 0.04,
			"pass_td": 4,
			"int": -2,
			"rush_yds": 0.1,
			"rec_yds": 0.1,
			"rec": 0.5,
			"rush_td": 6,
			"rec_td": 6,
			"fumbles": -2,
		},
		"ppr": {
			"pass_yds": 0.04,
			"pass_td": 4,
			"int": -2,
			"rush_yds": 0.1,
			"rec_yds": 0.1,
			"rec": 1,
			"rush_td": 6,
			"rec_td": 6,
			"fumbles": -2,
		},
		"standard": {},
	}
	pure_positions = ["QB", "RB", "WR", "TE"]
	position_types = ["QB", "RB", "WR", "TE", "flex", "all"]
	stat_types = ["ytd", "restofseason", "projections", "ros"]

	def __init__(self, scoring_system, season=2019):
		self.scoring_system = self._get_scoring_map(scoring_system)
		# self._position = position
		self.data = list()
		self.projections = dict()
		# have this default to current somehow?
		self.season = season if type(season) == str else str(season)
		self.base_url = "https://www.cbssports.com/fantasy/football/stats/"

	def get_data(self, position, stat_type):
		# combo of construct_url and scrape_data
		# needs to handle "all" position type calls
		if len(self.data) > 0:
			raise Exception(
				"Data has already been pulled. Please re-instantiate to pull again."
			)

		if stat_type not in self.stat_types:
			raise ValueError(
				f"Invalid stat type. Must be in {', '.join(self.stat_types)}"
			)

		if stat_type == "ytd":
			stat_url = "ytd/stats/"
		else:
			stat_url = "restofseason/projections/"

		if position not in self.position_types:
			raise ValueError(
				f"Invalid position type. Must be in: {', '.join(self.position_types)}"
			)

		if self.scoring_system == "ppr":
			score_type = self.scoring_system
		else:
			score_type = "nonppr"

		if position == "all":
			for p in self.pure_positions:
				sleep(random.uniform(1, 2))
				position_url = self.construct_url(self.season, stat_url, p, score_type)
				self.data.extend(self.scrape_data(position_url))
		elif position == "flex":
			position = "RB-WR-TE"
			position_url = self.construct_url(
				self.season, stat_url, position, score_type
			)
			self.data.extend(self.scrape_data(position_url))
		else:
			position_url = self.construct_url(
				self.season, stat_url, position, score_type
			)
			self.data = self.scrape_data(position_url)

	def construct_url(self, season, stat_type, position, score_type):
		# make this the default?
		# https://www.cbssports.com/fantasy/football/stats/RB-WR-TE/2019/restofseason/projections/nonppr/
		# allow QB, RB, WR, TE, and flex (=RB/WR/TE)
		return self.base_url + position + f"/{season}/" + stat_type + score_type

	@staticmethod
	def scrape_data(url):
		r = requests.get(url)
		soup = BeautifulSoup(r.content, "html.parser")

		raw_data = soup.find("table", {"class": "TableBase-table"})

		table_headers = raw_data.find("thead").find_all("tr")[1].find_all("th")
		cbs_headers = list()
		for i, elem in enumerate(table_headers):
			if i == 0:
				cbs_headers.append(elem.find("a").get_text().strip())
			else:
				cbs_headers.append(
					elem.find("div", {"class": "Tablebase-tooltipInner"})
					.get_text()
					.strip()
				)

		player_projections = [
			tr.find_all("td") for tr in raw_data.find("tbody").find_all("tr")
		]
		projection_list = list()

		for player in player_projections:
			player_data = list()
			for idx, elem in enumerate(player):
				if idx == 0:
					player_data.append(elem.find_all("a")[1].get_text())
					player_pos = (
						elem.find("span", {"class": "CellPlayerName-position"})
						.get_text()
						.strip()
					)
					player_team = (
						elem.find("span", {"class": "CellPlayerName-team"})
						.get_text()
						.strip()
					)
				else:
					player_data.append(elem.get_text().strip())
			player_dict = dict(zip(cbs_headers, player_data))
			player_dict["Position"] = player_pos
			player_dict["team"] = player_team
			projection_list.append(player_dict)

		return projection_list

	def convert_projections(self):

		for row in self.data:
			player = row["Player"]
			if row["Position"] == "QB":
				proj_points = (
					self.scoring_system["pass_yds"] * float(row["Passing Yards"])
					+ self.scoring_system["pass_td"] * float(row["Touchdowns Passes"])
					+ self.scoring_system["int"] * float(row["Interceptions Thrown"])
					+ self.scoring_system["rush_yds"] * float(row["Rushing Yards"])
					+ self.scoring_system["rush_td"] * float(row["Rushing Touchdowns"])
					+ self.scoring_system["fumbles"] * float(row["Fumbles Lost"])
				)
			elif row["Position"] == "TE":
				proj_points = (
					self.scoring_system["rec_yds"] * float(row["Receiving Yards"])
					+ self.scoring_system["rec"] * float(row["Receptions"])
					+ self.scoring_system["rec_td"] * float(row["Receiving Touchdowns"])
					+ self.scoring_system["fumbles"] * float(row["Fumbles Lost"])
				)
			else:
				proj_points = (
					self.scoring_system["rush_yds"] * float(row["Rushing Yards"])
					+ self.scoring_system["rec_yds"] * float(row["Receiving Yards"])
					+ self.scoring_system["rec"] * float(row["Receptions"])
					+ self.scoring_system["rush_td"] * float(row["Rushing Touchdowns"])
					+ self.scoring_system["rec_td"] * float(row["Receiving Touchdowns"])
					+ self.scoring_system["fumbles"] * float(row["Fumbles Lost"])
				)
			self.projections[player] = round(proj_points, 2)

	def save_projections(self, file_path):
		data_folder = Path.cwd() / "data"
		full_path = data_folder / file_path
		with open(full_path, "w") as outfile:
			field_names = self.data[0].keys()
			dict_writer = csv.DictWriter(outfile, field_names)
			dict_writer.writeheader()
			dict_writer.writerows(self.data)

	def load_projections(self, file_path):
		data_folder = Path.cwd() / "data"
		full_path = data_folder / file_path
		with open(full_path, "r") as infile:
			reader = csv.DictReader(infile)
			for row in reader:
				self.data.append(row)

	def _get_scoring_map(self, scoring_system):
		if scoring_system not in self.scoring_map:
			raise Exception("System not in scoring map")
		return self.scoring_map[scoring_system]
