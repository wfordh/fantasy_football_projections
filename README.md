# fantasy_football_projections

## Background
This repository houses various tools I have created to aid me during the fantasy football season. I am currently in a [Sleeper league](https://www.sleeper.app), so development is focused there. Note that right now these are more tools built around decision making and using existing projections, not my own projections.

## Details
This repository is all in Python 3.6.9. It is formatted using [black](https://github.com/psf/black) and run using [pipenv](https://github.com/pypa/pipenv).

## Ideas/Scratchwork
- Change names of 'data' and 'projections' attributes and 'get_data' and 'convert_projections' methods to better reflect what they are meant to do
- What to do in the case of name collision across positions? If two players have same name, then only the last one will be presented in the converted projections
- Update folder structure for project
- Projection sources to add - could potentially do async/parallelized pulling of the projections?:
	- [fantasy rundown](https://fantasyrundown.com/weekly-football-rankings/)
	- [nfl's own projections](https://fantasy.nfl.com/research/projections?position=O&sort=projectedPts&statCategory=projectedStats&statSeason=2020&statType=weekProjectedStats&statWeek=13) - [stack overflow post](https://stackoverflow.com/questions/51785640/scraping-nfl-com-fantasy-football-projections-using-python/51790517)
	- [fftoday](https://www.fftoday.com/rankings/playerwkproj.php?&PosID=20)
	- [fantasydata](https://fantasydata.com/nfl/fantasy-football-weekly-projections): can do RoS with some work
	- [fantasysharks](https://www.fantasysharks.com/apps/Projections/SeasonProjections.php?pos=RB)
	- [fantasysp](https://www.fantasysp.com/projections/football/weekly/RB): only weekly and requires headers
- Re-factor code in `sleeper_waivers.py` so the business logic is more separate from the UI
- Add wins over expectation and season to date strength of schedule to `sleeper_expected_records.py`
