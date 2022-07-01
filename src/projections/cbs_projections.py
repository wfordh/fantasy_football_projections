import csv
import random
from pathlib import Path
from time import sleep
from typing import Dict, List

import requests
from bs4 import BeautifulSoup


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

    def __init__(self, scoring_system: str, season: int = 2021) -> None:
        self.scoring_system = self._get_scoring_map(scoring_system)
        # self._position = position
        self.data = list()
        self.projections = dict()
        # have this default to current somehow?
        self.season = season if type(season) == str else str(season)
        self.base_url = "https://www.cbssports.com/fantasy/football/stats/"

    def _check_position(self, position: str) -> None:
        """Private method to check if the provided position is allowed.
        
        Args:
            position: A string representing the position to check.
        
        Raises:
            ValueError: An invalid position was provided.
        """
        if position not in self.position_types:
            raise ValueError(
                f"Invalid position type ({position}). Must be in: {', '.join(self.position_types)}"
            )

    def _convert_position_list(self, positions: List[str]) -> List[str]:
        sort_posns = sorted(positions)
        converted_posns = None
        # no rb/wr group for CBS
        if sort_posns == ["RB", "TE", "WR"]:
            converted_posns = "flex"
        elif sort_posns == ["QB", "RB", "TE", "WR"]:
            converted_posns = "all"
        else:
            converted_posns = positions
        return converted_posns

    def get_data(self, position: str, stat_type: str) -> None:
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

        if len(position) > 1:
            [self._check_position(posn) for posn in position]
            # reset positions as list to their relevant strings
            position = self._convert_position_list(position)
        else:
            position = position[0]
            self._check_position(position)

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
            positions = ["RB", "WR", "TE"]
            for p in positions:
                sleep(random.uniform(0.7, 1.2))
                position_url = self.construct_url(self.season, stat_url, p, score_type)
                self.data.extend(self.scrape_data(position_url))
        elif type(position) != str and len(position) > 1:
            # for gathering data for combos such as RB, TE
            for p in position:
                sleep(random.uniform(0.7, 1.2))
                position_url = self.construct_url(self.season, stat_url, p, score_type)
                self.data.extend(self.scrape_data(position_url))
        else:
            position_url = self.construct_url(
                self.season, stat_url, position, score_type
            )
            self.data = self.scrape_data(position_url)

    def construct_url(
        self, season: int, stat_type: str, position: str, score_type: str
    ) -> str:
        # make this the default?
        # https://www.cbssports.com/fantasy/football/stats/RB-WR-TE/2019/restofseason/projections/nonppr/
        # allow QB, RB, WR, TE, and flex (=RB/WR/TE)
        return self.base_url + position + f"/{season}/" + stat_type + score_type

    @staticmethod
    def scrape_data(url: str) -> List[Dict]:
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
                    player_cbs_id = elem.find("a")["href"].rsplit("/", maxsplit=3)[1]
                else:
                    player_data.append(elem.get_text().strip())
            player_dict = dict(zip(cbs_headers, player_data))
            player_dict["Position"] = player_pos
            player_dict["team"] = player_team
            player_dict["cbs_id"] = player_cbs_id
            projection_list.append(player_dict)

        return projection_list

    def convert_projections(self) -> None:

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
                try:
                    proj_points = (
                        self.scoring_system["rush_yds"] * float(row["Rushing Yards"])
                        + self.scoring_system["rec_yds"] * float(row["Receiving Yards"])
                        + self.scoring_system["rec"] * float(row["Receptions"])
                        + self.scoring_system["rush_td"]
                        * float(row["Rushing Touchdowns"])
                        + self.scoring_system["rec_td"]
                        * float(row["Receiving Touchdowns"])
                        + self.scoring_system["fumbles"] * float(row["Fumbles Lost"])
                    )
                except KeyError:
                    # workaround until I think of something better for Gio Ricci...listed as FB but on TE page
                    proj_points = (
                        self.scoring_system["rec_yds"] * float(row["Receiving Yards"])
                        + self.scoring_system["rec"] * float(row["Receptions"])
                        + self.scoring_system["rec_td"]
                        * float(row["Receiving Touchdowns"])
                        + self.scoring_system["fumbles"] * float(row["Fumbles Lost"])
                    )

            self.projections[player] = {
                "team": row["team"],
                "position": row["Position"],
                "proj_pts": round(proj_points, 2),
                "cbs_id": row["cbs_id"],
            }

    def save_projections(self, file_path: str) -> None:
        # will need to update now that data structure of projections has changed
        data_folder = Path.cwd() / "data"
        full_path = data_folder / file_path
        with open(full_path, "w") as outfile:
            field_names = self.data[0].keys()
            dict_writer = csv.DictWriter(outfile, field_names)
            dict_writer.writeheader()
            dict_writer.writerows(self.data)

    def load_projections(self, file_path: str) -> None:
        data_folder = Path.cwd() / "data"
        full_path = data_folder / file_path
        with open(full_path, "r") as infile:
            reader = csv.DictReader(infile)
            for row in reader:
                self.data.append(row)

    def _get_scoring_map(self, scoring_system: str) -> Dict:
        if scoring_system not in self.scoring_map:
            raise Exception("System not in scoring map")
        return self.scoring_map[scoring_system]
