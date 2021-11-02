import requests
from bs4 import BeautifulSoup

class fantasyprosProjctions:
    
    def __init__(self, scoring_system):
        self.scoring_system = self._get_scoringn_map(scoring_system)
        self.data = list()
        self.projectionsn = dict()
        self.base_url = "https://fantasypros.com/nfl/rankings"

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

    def compile_data(self, position):
        for position in positions:
            resp = requests.get(f"{self.base_url}/ros-{self.scoring_sytem}-{position.lower()}.php" 
            soup = BeautifulSoup(resp.content, 'html.parser')
            self.data.extend(self.get_data(soup, position))
