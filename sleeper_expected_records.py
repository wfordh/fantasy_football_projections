import os
import pprint
from operator import add
from sleeper_wrapper import League
from tqdm import tqdm, trange


def main():
    pp = pprint.PrettyPrinter()
    current_week = 10
    league_id = os.environ.get("SLEEPER_LEAGUE_ID", "")
    league = League(league_id)

    # League.get_scoreboards(rosters, matchups, users, score_type, week)
    rosters = league.get_rosters()
    roster_id_map = league.map_rosterid_to_ownerid(rosters)

    users = league.get_users()
    users_dict = league.map_users_to_team_name(users)

    score_type = "pts_half_ppr"
    expected_wins = dict.fromkeys([roster["roster_id"] for roster in rosters], 0)
    teams_faced = dict.fromkeys([roster["roster_id"] for roster in rosters])
    # need to track teams faced - why? see oppo win% to date, both real and expected?

    for week in trange(1, current_week):
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
    for roster_id, wins in tqdm(expected_wins.items()):
        owner_id = roster_id_map[roster_id]
        team_name = users_dict[owner_id]
        losses = num_matchups - wins
        win_pct = round(wins / num_matchups, 3)
        team_exp_records[team_name] = {
            "wins": wins,
            "losses": losses,
            "win_pct": win_pct,
            "roster_id": roster_id
        }

    pp.pprint(
        sorted(
            [(team, stats["win_pct"]) for team, stats in team_exp_records.items()],
            key=lambda tup: tup[1],
            reverse=True,
        )
    )

    # how to structure this data?
    # team: list of opponents remaining
    remaining_opponents = dict.fromkeys([roster["roster_id"] for roster in rosters], list())
    for week in trange(current_week, 14):
        # need roster_id and matchup_id for forward looking
        # get matchups
        weekly_matchups = league.get_matchups(week)
        # reformat into matchup id: team 1, team 2
        head_to_head_matchups = dict.fromkeys(set([m["matchup_id"] for m in weekly_matchups]))
        for matchup in weekly_matchups:
            matchup_id = matchup["matchup_id"]
            head_to_head_matchups[matchup_id].append(matchup["roster_id"])




if __name__ == "__main__":
    main()
