import requests
from bs4 import BeautifulSoup


class nf_projections:
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
    position_types = ["QB", "RB", "WR", "TE", "flex", "all"]

    def __init__(self, scoring_system):
        self.scoring_system = self._get_scoring_map(scoring_system)
        # self.position = position #make these property functions?
        self.data = list()
        self.projections = dict()
        self.base_url = "https://www.numberfire.com/nfl/fantasy/remaining-projections/"

    def make_url(self, position):
        if position == "RB/WR":
            return self.base_url + "rbwr"
        return self.base_url + position.lower()

    def get_data(self, position):
        url = self.make_url(position)
        raw_data = self.scrape_data(url)

        player_header = self.get_player_header(raw_data)
        player_names = self.get_player_names(raw_data)
        player_projections = self.get_player_projections(raw_data)
        projection_headers = self.get_projection_headers(raw_data)

        # data_list = list()
        # for idx, player in enumerate(player_names):
        #     player_dict = dict(zip(projection_headers, player_projections[idx]))
        #     player_dict[player_header] = player
        #     self.data.append(player_dict)

        self.data = [
            dict(
                zip(projection_headers, player_projections[idx]),
                **{player_header, player}
            )
            for idx, player in enumerate(player_names)
        ]

    @staticmethod
    def scrape_data(url):
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
    def get_player_header(data):
        return data.find("table").find("thead").find_all("tr")[1].get_text().strip()

    @staticmethod
    def get_player_names(data):
        return [
            td.find("span", {"class": "full"}).get_text()
            for td in data.find("table").find("tbody").find_all("td")
        ]

    @staticmethod
    def get_player_projections(data):
        return [
            [td.get_text().strip() for td in tr.find_all("td")]
            for tr in data.find_all("table")[1].find("tbody").find_all("tr")
        ]

    @staticmethod
    def get_projection_headers(data):
        return [
            th["title"]
            for th in data.find_all("table")[1]
            .find("thead")
            .find_all("tr")[1]
            .find_all("th")
        ]

    def convert_projections(self):
        ## how to deal with non-QB scoring? try to avoid deep indentation
        ## modularize the scoring calculations and turn this into a list comp?
        for row in self.data:
            player = row["Player"]
            proj_points = (
                self.scoring_system["pass_yds"] * float(row["Passing Yards"])
                + self.scoring_system["pass_td"] * float(row["Passing Touchdowns"])
                + self.scoring_system["int"] * float(row["Interceptions Thrown"])
                + self.scoring_system["rush_yds"] * float(row["Rushing Yards"])
                + self.scoring_system["rec_yds"] * float(row["Receiving Yards"])
                + self.scoring_system["rec"] * float(row["Receptions"])
                + self.scoring_system["rush_td"] * float(row["Rushing Touchdowns"])
                + self.scoring_system["rec_td"] * float(row["Receiving Touchdowns"])
            )
            self.projections[player] = round(proj_points, 2)

    def _get_scoring_map(self, scoring_system):
        if scoring_system not in self.scoring_map:
            raise Exception("System not in scoring map")
        return self.scoring_map[scoring_system]
