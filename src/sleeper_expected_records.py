"""Pulls expected standings and RoS strength of schedule.

more to come
"""

import argparse
import os
import pprint
from operator import add
from sleeper_wrapper import League
from tqdm import tqdm, trange

# may try to make this automatic somehow
parser = argparse.ArgumentParser()
parser.add_argument("-w", "--week", help="The current week", required=True, type=int)
# not sure this is necessary...
parser.add_argument(
    "-s",
    "--score_type",
    help="Score type.",
    required=True,
    type=str,
    default="half_ppr",
    options=["standard", "half_ppr", "ppr"],
)


def main():
    pp = pprint.PrettyPrinter()
    args = parser.parse_args()
    command_args = dict(vars(args))
    current_week = command_args.pop("week", None)
    league_id = os.environ.get("SLEEPER_LEAGUE_ID", "")
    league = League(league_id)

    rosters = league.get_rosters()
    roster_id_map = league.map_rosterid_to_ownerid(rosters)

    users = league.get_users()
    users_dict = league.map_users_to_team_name(users)

    score_type = command_args.pop("score_type", None)
    expected_wins = dict.fromkeys([roster["roster_id"] for roster in rosters], 0)
    teams_faced = dict.fromkeys([roster["roster_id"] for roster in rosters])
    # need to track teams faced - why? see oppo win% to date, both real and expected?

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

    num_matchups = (current_week - 1) * 11
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

    pp.pprint(
        sorted(
            [
                (team_info["team_name"], team_info["win_pct"])
                for team_id, team_info in team_exp_records.items()
            ],
            key=lambda tup: tup[1],
            reverse=True,
        )
    )

    # team: list of opponents remaining
    remaining_opponents = dict.fromkeys([roster["roster_id"] for roster in rosters])
    for week in trange(current_week, 14, desc="Getting future weeks"):
        weekly_matchups = league.get_matchups(week)
        team_matchups = {
            roster["roster_id"]: roster["matchup_id"] for roster in weekly_matchups
        }
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

    # combine SoS dict and remaining opponents dict?
    remaining_sos = dict()
    for team, opponents in remaining_opponents.items():
        sos = sum([team_exp_records[oppo]["win_pct"] for oppo in opponents]) / len(
            opponents
        )
        remaining_sos[team_exp_records[team]["team_name"]] = round(sos, 3)

    # sort?
    pp.pprint(remaining_sos)


if __name__ == "__main__":
    main()
