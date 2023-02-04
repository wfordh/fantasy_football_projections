"""Pulls expected standings and RoS strength of schedule.

more to come
"""

import argparse
import logging
import os
from operator import add
from pprint import pformat

import requests
from sleeper_wrapper import League, User
from tqdm import tqdm, trange

parser = argparse.ArgumentParser()
parser.add_argument(
    "-a",
    "--all_user_leagues",
    help="Pull all of a user's leagues?",
    type=str,
    default="yes",
    choices=["yes", "no"],
)

# is there a way to turn all of this into a class?
# a subclass of the wrapper's "League" class??
# a dataclass?

# can get weeks in season dynamically from the league object
# league["settings"]["playoff_week_start"]
WEEKS_IN_SEASON = 15

logging.basicConfig(level=logging.INFO)


class LeagueV2(League):
    """docstring for LeagueV2"""

    def __init__(self, league_id):
        super().__init__(self)
        self.roster_id_map = self._get_roster_id_map()

    def _get_roster_id_map(self) -> dict:
        """ """
        rosters = self.get_rosters()
        roster_id_map = self.map_rosterid_to_ownerid(rosters)
        return roster_id_map


def get_user_leagues(all_leagues: list[League], nfl_state: dict) -> list[League]:
    """"""
    if all_leagues:
        user_id = os.environ.get("SLEEPER_USER_ID", "")
        season = nfl_state.pop("season", None)
        user = User(user_id)
        leagues = user.get_all_leagues("nfl", season)
        leagues = [League(league["league_id"]) for league in leagues]
        return leagues
    league_id = os.environ.get("SLEEPER_LEAGUE_ID", "")
    return [League(league_id)]


def get_nfl_state() -> dict:
    """"""
    return requests.get("https://api.sleeper.app/v1/state/nfl").json()


def get_roster_id_map(league: League) -> dict:
    """ """
    rosters = league.get_rosters()
    roster_id_map = league.map_rosterid_to_ownerid(rosters)
    return roster_id_map


def calc_expected_wins(league: League, current_week: int, roster_id_map: dict) -> dict:
    """ """
    # need some docs here, especially for how expected_wins happens
    # and why it's structured that way
    expected_wins = dict.fromkeys(list(roster_id_map), 0)
    for week in trange(1, current_week, desc="Getting past weeks"):
        weekly_matchups = league.get_matchups(week)
        weekly_points = sorted(
            [(team["roster_id"], team["points"]) for team in weekly_matchups],
            key=lambda tup: tup[1],
        )
        expected_wins = {
            team: add(expected_wins[team], wins)
            for team, wins in [(team[0], idx) for idx, team in enumerate(weekly_points)]
        }
    return expected_wins


def calc_team_expected_record(
    league: League, expected_wins: dict, roster_id_map: dict, num_matchups: int
) -> dict:
    """ """
    # hmm need the num_matchups too, so would need current week / nfl state too
    users = league.get_users()
    users_dict = league.map_users_to_team_name(users)
    team_exp_records = dict()
    for roster_id, wins in tqdm(expected_wins.items(), desc="Expected records"):
        owner_id = roster_id_map[roster_id]
        team_name = users_dict[owner_id]
        losses = num_matchups - wins
        win_pct = round(wins / num_matchups, 3)
        team_exp_records[roster_id] = {
            "wins": wins,
            "losses": losses,
            "win_pct": win_pct,
            "team_name": team_name,
        }
    return team_exp_records


def get_remaining_opponents(
    league: League, roster_id_map: dict, current_week: int
) -> dict:
    """ """
    remaining_opponents = dict.fromkeys(list(roster_id_map))
    for week in trange(current_week, WEEKS_IN_SEASON, desc="Getting future weeks"):
        weekly_matchups = league.get_matchups(week)
        team_matchups = {
            roster["roster_id"]: roster["matchup_id"] for roster in weekly_matchups
        }
        # at least FUNCTIONS here and next for loop
        # ADD SOME DOCSTRINGS CUS IDK WHAT IS HAPPENING HERE
        matchup_dict = dict()
        for team, matchup in team_matchups.items():
            if matchup in matchup_dict:
                matchup_dict[matchup].append(team)
            else:
                matchup_dict[matchup] = [team]

        for matchup, teams in matchup_dict.items():
            if remaining_opponents[teams[0]]:
                remaining_opponents[teams[0]].append(teams[1])
            else:
                remaining_opponents[teams[0]] = [teams[1]]
            if remaining_opponents[teams[1]]:
                remaining_opponents[teams[1]].append(teams[0])
            else:
                remaining_opponents[teams[1]] = [teams[0]]

    return remaining_opponents


def calc_remaining_sos(remaining_opponents: dict, team_exp_records: dict) -> dict:
    """ """
    remaining_sos = dict()
    for team, opponents in remaining_opponents.items():
        sos = sum([team_exp_records[oppo]["win_pct"] for oppo in opponents]) / len(
            opponents
        )
        remaining_sos[team_exp_records[team]["team_name"]] = round(sos, 3)
    return remaining_sos


def main():
    args = parser.parse_args()
    command_args = dict(vars(args))

    all_leagues = True if command_args.pop("all_user_leagues") == "yes" else False
    nfl_state = get_nfl_state()
    # not sure how ironclad this logic is
    if nfl_state["season_type"] != "post":
        current_week = nfl_state.pop("week", None)
    else:
        current_week = 18

    leagues = get_user_leagues(all_leagues, nfl_state)
    for league in leagues:
        logging.info(pformat(f"Getting info for {league.get_league()['name']}"))

        roster_id_map = get_roster_id_map(league)

        teams_faced = dict.fromkeys(list(roster_id_map))
        # need to track teams faced to see oppo win% to date, real and expected?
        # not currently using it though

        expected_wins = calc_expected_wins(league, current_week, roster_id_map)

        # num_teams - 1 because you don't play yourself
        num_teams = league.get_league()["total_rosters"]
        # have this and some other things in a dataclass to track "state"?
        num_matchups = (current_week - 1) * (num_teams - 1)
        team_exp_records = calc_team_expected_record(
            league, expected_wins, roster_id_map, num_matchups
        )

        # probably want to figure out a better way for this, too
        # if don't need team_exp_records later, should I keep name and win_pct
        # when calculating team_exp_records?
        logging.info(
            pformat(
                sorted(
                    [
                        (team_info["team_name"], team_info["win_pct"])
                        for team_id, team_info in team_exp_records.items()
                    ],
                    key=lambda tup: tup[1],
                    reverse=True,
                )
            )
        )

        # skip if we're in the fantasy playoffs
        if current_week < WEEKS_IN_SEASON:
            remaining_opponents = get_remaining_opponents(
                league, roster_id_map, current_week
            )
            remaining_sos = calc_remaining_sos(remaining_opponents, team_exp_records)

            # sort?
            logging.info(pformat(remaining_sos))


if __name__ == "__main__":
    main()
