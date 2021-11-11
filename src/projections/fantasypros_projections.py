import requests
import chompjs
from bs4 import BeautifulSoup

class fantasyprosProjctions:
    
    pure_positions = ["QB", "RB", "WR", "TE"]

    def __init__(self, scoring_system):
        self.scoring_system = self._get_scoring_map(scoring_system)
        self.data = list()
        self.projections = dict()
        self.base_url = "https://fantasypros.com/nfl/rankings"

   def construct_url(self, position):
        return f"{self.base_url}/ros-{self.scoring_system}-{position.lower()}.php"

    def get_data(self, soup, position):
        scripts = soup.find_all("script")
        ecrData = None
        for script in scripts:
            if script.string is not None and "ecrData" in script.string:
                ecrData = script.string
                break
        player_dict = chompjs.parse_js_object(ecrData)
        # pull out only necessary things, returning the raw data for now 
        return player_dict

    def compile_data(self, positions):
        if positions == "flex":
            positions = ["RB", "WR", "TE"]
        elif positions == "all":
            positions = ["QB", "RB", "WR", "TE"]

 
        for position in positions:
            resp = requests.get(self.construct_url(position))
            soup = BeautifulSoup(resp.content, 'html.parser')
            self.data.extend(self.get_data(soup, position))

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
