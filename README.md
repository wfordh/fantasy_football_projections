# fantasy_football_projections
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Background
This repository houses various tools I have created to aid me during the fantasy football season. I am currently in a [Sleeper league](https://www.sleeper.app), so development is focused there. Note that right now these are more tools built around decision making and using existing projections, not my own projections.

## Details
This repository is all in Python 3.9.1. It is formatted using [black](https://github.com/psf/black) and run using [pipenv](https://github.com/pypa/pipenv).

## Ideas/Scratchwork
- Change names of 'data' and 'projections' attributes and 'get_data' and 'convert_projections' methods to better reflect what they are meant to do
- What to do in the case of name collision across positions? If two players have same name, then only the last one will be presented in the converted projections
- Add `BaseProjections` class that can then be added onto for the specific websites
- Projection sources to add - could potentially do async/parallelized pulling of the projections?:
	- [fantasy rundown](https://fantasyrundown.com/weekly-football-rankings/)
	- [fftoday](https://www.fftoday.com/rankings/playerwkproj.php?&PosID=20)
	- [fantasydata](https://fantasydata.com/nfl/fantasy-football-weekly-projections): can do RoS with some work - check that, only shows top 10 over selected area and need premium to get more. Probably skip for now
	- [fantasysharks](https://www.fantasysharks.com/apps/Projections/SeasonProjections.php?pos=RB)
	- [fantasysp](https://www.fantasysp.com/projections/football/weekly/RB): only weekly and requires headers
	- [optimal DFS](https://optimaldfs.app/nfl/weekly-projections/flex): only weekly
- Re-factor code in `sleeper_waivers.py` so the business logic is more separate from the UI
- Add wins over expectation and season to date strength of schedule to `sleeper_expected_records.py`
- Lineup optimization and predicted matchup points with the projections
- Pull projections independently of waivers?
	- Save missing players so it's easier to know if there's a blind spot
- [Google search](https://www.google.com/search?q=fantasy+football+python&rlz=1C5CHFA_enUS873&oq=fantasy+football+python&aqs=chrome..69i57.3426j0j1&sourceid=chrome&ie=UTF-8) for python fantasy football tools

## Roadmap
1. typing for projection functions
2. documentation for projection functions
3. add isort and [pre-commit hooks](https://pre-commit.com/)
4. tests
5. fancy code coverage stuff
6. CBS projections need some private helper methods for checking inputs such as ytd/restofseason and constructing the URL
