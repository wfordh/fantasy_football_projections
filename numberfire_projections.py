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

    def __init__(self, scoring_system, position=None):
        self.scoring_system = self._get_scoring_map(scoring_system)
        self.position = position #make these property functions?
        self.data = list()
        self.projections = dict()

    def get_data(self, url):
        # make this the default?
        # https://www.numberfire.com/nfl/fantasy/remaining-projections/
        r = requests.get(url)
        soup = BeautifulSoup(r.content, "html.parser")
        raw_data = (
            soup.find("main")
            .find("section", {"class": "grid__two-col--main grid--1-2"})
            .find(
                "div", {"class": "projection-wrap projection-rankings power-rankings"}
            )
        )

        player_header = (
            raw_data.find("table").find("thead").find_all("tr")[1].get_text().strip()
        )
        player_names = [
            td.find("span", {"class": "full"}).get_text()
            for td in raw_data.find("table").find("tbody").find_all("td")
        ]
        player_projections = [
            [td.get_text().strip() for td in tr.find_all("td")]
            for tr in raw_data.find_all("table")[1].find("tbody").find_all("tr")
        ]
        projection_headers = [
            th["title"]
            for th in raw_data.find_all("table")[1]
            .find("thead")
            .find_all("tr")[1]
            .find_all("th")
        ]

        # data_list = list()
        for idx, player in enumerate(player_names):
            player_dict = dict(zip(projection_headers, player_projections[idx]))
            player_dict[player_header] = player
            self.data.append(player_dict)

    def convert_projections(self):

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


"""
table = soup.find('main').find('section', {'class':"grid__two-col--main grid--1-2"}).find('div', {'class': 'projection-wrap projection-rankings power-rankings'})
player_header = table.find('table').find('thead').find_all('tr')[1].get_text().strip()
player_names = [td.find('span', {'class':'full'}).get_text() for td in table.find('table').find('tbody').find_all('td')]
player_projections = [[td.get_text().strip() for td in tr.find_all('td')] for tr in table.find_all('table')[1].find('tbody').find_all('tr')]
projection_headers = [th['title'] for th in table.find_all('table')[1].find('thead').find_all('tr')[1].find_all('th')]

# insert the player name into 0 index for player projection

"""

"""
CBS:
cbs_qb_url = 'https://www.cbssports.com/fantasy/football/stats/QB/2019/restofseason/projections/nonppr/'
cbs_qb_r = requests.get(cbs_qb_url)
cbs_qb_soup = BeautifulSoup(cbs_qb_r.content, 'html.parser')
cq_table = cbs_qb_soup.find('table', {'class': 'TableBase-table'})

# repeat for each player and figure out how to save
cbs_test_player = [tr.find_all('td') for tr in cq_table.find('tbody').find_all('tr')][1]

for i, elem in enumerate(cbs_test_player):
	if i==0:
		p_name = elem.find_all('a')[1].get_text()
		p_pos = elem.find('span', {'class':'CellPlayerName-position'}).get_text().strip()
	else:
		elem.get_text().strip()

cbs_headers = cq_table.find('thead').find_all('tr')[1].find_all('th')
for i, elem in enumerate(cbs_headers):
	if i==0:
		elem.find('a').get_text()
	else:
		elem.find('div', {'class':'Tablebase-tooltipInner'}).get_text().strip()

# get ytd stats by replacing 'restofseason/projections' with 'ytd/stats'
"""
