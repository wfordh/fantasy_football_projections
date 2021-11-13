import requests
import chompjs
from bs4 import BeautifulSoup


class fantasyprosProjections:

    pure_positions = ["QB", "RB", "WR", "TE"]

    scoring_map = {
        "half_ppr": "half-point-ppr",
    }

    def __init__(self, scoring_system):
        self.scoring_system = self._get_scoring_map(scoring_system)
        self.projections = dict()
        self.base_url = "https://fantasypros.com/nfl/rankings"

    def construct_url(self, position):
        return f"{self.base_url}/ros-{self.scoring_system}-{position.lower()}.php"

    def get_projections(self, soup):
        scripts = soup.find_all("script")
        ecrData = None
        for script in scripts:
            if script.string is not None and "ecrData" in script.string:
                ecr_data = script.string
                break
        players = chompjs.parse_js_object(ecr_data).get("players", None)
        keep_fields = ["player_name", "player_position_id", "player_team_id", "r2p_pts"]
        # pull out only necessary things, returning the raw data for now
        for player in players:
            self.projections[player["player_name"]] = {
                "position": player["player_position_id"],
                "team": player["player_team_id"],
                "proj_pts": player["r2p_pts"],
            }

    def compile_data(self, positions):
        print(positions)
        if type(positions) == str:
            if positions == "flex":
                positions = ["RB", "WR", "TE"]
            elif positions == "all":
                positions = ["QB", "RB", "WR", "TE"]
            else:
                positions = [positions]
        else:
            pass

        print(positions)

        for position in positions:
            resp = requests.get(self.construct_url(position))
            print(self.construct_url(position))
            soup = BeautifulSoup(resp.content, "html.parser")
            self.get_projections(soup)

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

    def _wrangle_positions(self, positions):
        # not sure this is necessary. or pull the code above down into here
        if type(positions) in [tuple, list] and len(positions) == 1:
            positions = positions[0]
        if positions == "flex":
            positions = ["RB", "WR", "TE"]
        if positions == "all":
            positions = self.pure_positions
        if type(positions) not in [list, tuple]:
            positions = [positions]
