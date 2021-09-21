from pathlib import Path
import requests
from bs4 import BeautifulSoup
from time import sleep


class nflProjections:
    """docstring for nflProjections"""

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
            "fumble": -2,
            "two_pt_conv": 2,
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
        },
        "standard": {},
    }

    pure_positions = ["QB", "RB", "WR", "TE"]
    position_types = ["QB", "RB", "WR", "TE", "RB/WR", "flex", "all"]
    position_map = {"QB": 1, "RB": 2, "WR": 3, "TE": 4}
    reverse_position_map = {1: "QB", 2: "RB", 3: "WR", 4: "TE"}

    def __init__(self, scoring_system):
        self.scoring_system = self._get_scoring_map(scoring_system)
        self.data = list()
        self.projections = dict()
        self.base_url = "https://fantasy.nfl.com/research/projections"
        self.params = None  # for now

    def construct_params(self, week, position, offset):
        self.params = {
            "statWeek": week,
            "position": position,
            "statCategory": "projectedStats",
            "statType": "weekProjectedStats",
            "statSeason": 2021,
            "offset": offset,  # works as 25n + 1 where n is page num starting at 0
        }

    # if scoring is full PPR, can just grab the projected points
    # otherwise must get individual stats and convert into projections

    def get_player_projections(self, player, position):
        stats = dict()
        stats["pass_yds"] = player.find("td", "stat_5").text
        stats["pass_td"] = player.find("td", "stat_6").text
        stats["int"] = player.find("td", "stat_7").text
        stats["rush_yds"] = player.find("td", "stat_14").text
        stats["rush_td"] = player.find("td", "stat_15").text
        stats["rec"] = player.find("td", "stat_20").text
        stats["rec_yds"] = player.find("td", "stat_21").text
        stats["rec_td"] = player.find("td", "stat_22").text
        stats["fumble"] = player.find("td", "stat_30").text
        stats["two_pt_conv"] = player.find("td", "stat_32").text
        # if doing this, don't need if statements above?
        stats = {k: (float(v) if v != "-" else 0) for k, v in stats.items()}
        return stats

    def get_data(self, soup, position):
        player_results = list()
        player_rows = soup.find("tbody").find_all("tr")
        sleep(0.8)
        for player in player_rows:
            name = player.find("a", "playerCard")
            try:
                team = player.find("em").text.split(" - ")[1]
            except (IndexError, AttributeError):
                team = None
            # how is position getting here?
            stats = self.get_player_projections(player, position)
            if all([name, stats]):
                # not sure I want to structure this as list of lists, but doing it for testing
                player_results.append(
                    # [name.text, team, self.params["statWeek"], stats]
                    {
                        "player": name.text,
                        "team": team,
                        "position": position,
                        "week": self.params["statWeek"],
                        "player_data": stats,
                    }
                )
        return player_results

    # run through players on first 2 pages for QB, 3 for RB / TE, 4 for WR
    # roll up players for all weeks
    def compile_data(self, positions):
        if type(positions) != list:
            positions = [positions]
        # add logging for this
        # need to programmatically do week somehow...argparse? new sleeper api call?
        week = 2
        for week_num in range(week, 19):
            # go thru all the weeks
            for position in positions:
                # go thru all requested positions

                # set this somewhere else? dynamically for position?
                num_offsets = 2
                for offset in range(num_offsets):
                    # go thru all the offsets...remember, 25*n + 1
                    self.construct_params(
                        week_num, self.position_map[position], 25 * offset + 1
                    )
                    resp = requests.get(self.base_url, params=self.params)
                    soup = BeautifulSoup(resp.content, "html.parser")
                    self.data.extend(self.get_data(soup, position))

    def convert_projections(self):
        for row in self.data:
            player = row["player"]
            player_posn = row["position"]
            if player_posn == "QB":
                week_proj_pts = self.calc_qb_projections(row["player_data"])
            else:
                week_proj_pts = self.calc_skill_projections(row["player_data"])
            if player in self.projections.keys():
                self.projections[player] += week_proj_pts
            else:
                self.projections[player] = week_proj_pts

        for player, proj_pts in self.projections.items():
            self.projections[player] = round(proj_pts, 2)

    def calc_qb_projections(self, player_data):
        return (
            self.scoring_system["pass_yds"] * float(player_data["pass_yds"])
            + self.scoring_system["pass_td"] * float(player_data["pass_td"])
            + self.scoring_system["int"] * float(player_data["int"])
            + self.scoring_system["rush_yds"] * float(player_data["rush_yds"])
            + self.scoring_system["rush_td"] * float(player_data["rush_td"])
            + self.scoring_system["fumble"] * float(player_data["fumble"])
            + self.scoring_system["two_pt_conv"] * float(player_data["two_pt_conv"])
        )

    def calc_skill_projections(self, player_data):
        return (
            self.scoring_system["rush_yds"] * float(player_data["rush_yds"])
            + self.scoring_system["rec_yds"] * float(player_data["rec_yds"])
            + self.scoring_system["rec"] * float(player_data["rec"])
            + self.scoring_system["rush_td"] * float(player_data["rush_td"])
            + self.scoring_system["rec_td"] * float(player_data["rec_td"])
            + self.scoring_system["fumble"] * float(player_data["fumble"])
            + self.scoring_system["two_pt_conv"] * float(player_data["two_pt_conv"])
        )

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
