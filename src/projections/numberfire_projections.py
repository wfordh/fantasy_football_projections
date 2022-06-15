import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from pathlib import Path
import csv
from itertools import chain
from time import sleep
import random
import re
from typing import Dict, List, Union


class numberfireProjections:
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

    # fuzzymatch for when players not entered correctly? would that be necessary
    # in a flask app? or just CLI?
    # how far does your projection need to outpace the other side in a X for 1 trade
    # where X > 1
    pure_positions = ["QB", "RB", "WR", "TE"]
    position_types = ["QB", "RB", "WR", "TE", "RB/WR", "flex", "all"]

    def __init__(self, scoring_system: str) -> None:
        self.scoring_system = self._get_scoring_map(scoring_system)
        # self.position = position #make these property functions?
        self.data = list()
        self.projections = dict()
        self.base_url = "https://www.numberfire.com/nfl/fantasy/remaining-projections/"

    def construct_url(self, position: str) -> str:
        if position == "RB/WR":
            return self.base_url + "rbwr"
        return self.base_url + position.lower()

    def _check_position(self, position: str) -> None:
        if position not in self.position_types:
            raise ValueError(
                f"Invalid position type ({position}). Must be in: {', '.join(self.position_types)}"
            )

    def _convert_position_list(self, positions: List) -> Union[str, List]:
        sort_posns = sorted(positions)
        converted_posns = None
        if sort_posns == ["RB", "WR"]:
            converted_posns = "RB/WR"
        elif sort_posns == ["RB", "TE", "WR"]:
            converted_posns = "flex"
        elif sort_posns == ["QB", "RB", "TE", "WR"]:
            converted_posns = "all"
        else:
            converted_posns = positions
        return converted_posns

    def get_data(self, position: str) -> None:
        # get all positions in one grab
        if len(position) > 1:
            [self._check_position(posn) for posn in position]
            # reset positions as list to their relevant strings
            position = self._convert_position_list(position)
        else:
            position = position[0]
            self._check_position(position)

        if position == "all":
            self.data = list(
                chain.from_iterable(
                    [self.compile_data(pos) for pos in self.pure_positions]
                )
            )
        elif position == "flex":
            self.data = list(
                chain.from_iterable(
                    [self.compile_data(pos) for pos in ["rb", "wr", "te"]]
                )
            )
        elif position == "RB/WR":
            # unclear if I want this option
            # if so, remove the 'rb/wr' piece from construct_url
            self.data = list(
                chain.from_iterable([self.compile_data(pos) for pos in ["rb", "wr"]])
            )
        elif type(position) != str and len(position) > 1:
            self.data = list(
                chain.from_iterable([self.compile_data(pos) for pos in position])
            )
        else:
            self.data = self.compile_data(position)

    def compile_data(self, position: str) -> List[Dict]:
        sleep(random.uniform(1, 2))
        url = self.construct_url(position)
        raw_data = self.scrape_data(url)

        player_header = self.get_player_header(raw_data)
        player_names = self.get_player_names(raw_data)
        player_teams = self.get_player_teams(raw_data)
        player_projections = self.get_player_projections(raw_data)
        projection_headers = self.get_projection_headers(raw_data)
        player_data = zip(player_names, player_teams)

        return [
            dict(
                zip(projection_headers, player_projections[idx]),
                **{player_header: player[0]},
                **{"position": position.upper()},
                **{"team": player[1]},
            )
            for idx, player in enumerate(player_data)
        ]

    @staticmethod
    def scrape_data(url: str) -> Tag:
        # need the return type...something soupy
        r = requests.get(url)
        soup = BeautifulSoup(r.content, "html.parser")
        raw_data = (
            soup.find("main")
            .find("section", {"class": "grid__two-col--main grid--1-2"})
            .find(
                "div", {"class": "projection-wrap projection-rankings power-rankings"}
            )
        )

        return raw_data

    @staticmethod
    def get_player_header(data) -> str:
        return data.find("table").find("thead").find_all("tr")[1].get_text().strip()

    @staticmethod
    def get_player_names(data) -> List:
        return [
            td.find("span", {"class": "full"}).get_text()
            for td in data.find("table").find("tbody").find_all("td")
        ]

    @staticmethod
    def get_player_teams(data) -> List:
        raw_teams = [
            re.findall(r"[A-Z]+", td.a.next_sibling.strip())[1]
            for td in data.find("table").find("tbody").find_all("td")
        ]
        # dumb mapping to make LA -> LAR
        player_teams = list()
        for tm in raw_teams:
            if tm == "LA":
                player_teams.append("LAR")
            elif tm == "WSH":
                player_teams.append("WAS")
            else:
                player_teams.append(tm)
        return player_teams

    @staticmethod
    def get_player_projections(data) -> List:
        return [
            [td.get_text().strip() for td in tr.find_all("td")]
            for tr in data.find_all("table")[1].find("tbody").find_all("tr")
        ]

    @staticmethod
    def get_projection_headers(data) -> List:
        return [
            th["title"]
            for th in data.find_all("table")[1]
            .find("thead")
            .find_all("tr")[1]
            .find_all("th")
        ]

    def convert_projections(self) -> None:
        ## modularize the scoring calculations and turn this into a dict comp?
        for row in self.data:
            player = row["Player"]
            proj_points = (
                self.calc_qb_projections(row)
                if row["position"] == "QB"
                else self.calc_skill_projections(row)
            )
            self.projections[player] = {
                "team": row["team"],
                "position": row["position"],
                "proj_pts": round(proj_points, 2),
            }

    def calc_qb_projections(self, player_data) -> float:
        return (
            self.scoring_system["pass_yds"] * float(player_data["Passing Yards"])
            + self.scoring_system["pass_td"] * float(player_data["Passing Touchdowns"])
            + self.scoring_system["int"] * float(player_data["Interceptions Thrown"])
            + self.scoring_system["rush_yds"] * float(player_data["Rushing Yards"])
            + self.scoring_system["rush_td"] * float(player_data["Rushing Touchdowns"])
        )

    def calc_skill_projections(self, player_data) -> float:
        return (
            self.scoring_system["rush_yds"] * float(player_data["Rushing Yards"])
            + self.scoring_system["rec_yds"] * float(player_data["Receiving Yards"])
            + self.scoring_system["rec"] * float(player_data["Receptions"])
            + self.scoring_system["rush_td"] * float(player_data["Rushing Touchdowns"])
            + self.scoring_system["rec_td"] * float(player_data["Receiving Touchdowns"])
        )

    def save_projections(self, file_path: str) -> float:
        data_folder = Path.cwd() / "data"
        full_path = data_folder / file_path
        with open(full_path, "w") as outfile:
            field_names = self.data[0].keys()
            dict_writer = csv.DictWriter(outfile, field_names)
            dict_writer.writeheader()
            dict_writer.writerows(self.data)

    def load_projections(self, file_path: str) -> float:
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
