import requests
import json
import os
from operator import add

espn_swid = os.environ.get("ESPN_SWID_COOKIE", " ")
espn_s2 = os.environ.get("ESPN_S2_COOKIE", " ")
# eventually the league ID will be a CLI supplied argument or something similar
espn_ff_league_id = os.environ.get("ESPN_FF_LEAGUE_ID", " ")

cookies = {"SWID": espn_swid, "espn_s2": espn_s2}
url = f"https://fantasy.espn.com/apis/v3/games/ffl/seasons/2019/segments/0/leagues/{espn_ff_league_id}"
params = {"view": "mMatchup"}  # or whatever

# big ups here: https://stmorse.github.io/journal/espn-fantasy-v3.html

schedule_resp = requests.get(url, params=params, cookies=cookies)
schedule = r.json()["schedule"]
## get weekly results
teams_exp_record = dict.fromkeys(team_mapping.keys(), 0)
for week_num in range(1, current_week + 1):
    weekly_points = sorted(
        [
            (game[team]["teamId"], game[team]["totalPoints"])
            for team in ["home", "away"]
            for game in filter(
                lambda matchup: matchup["matchupPeriodId"] == week_num, schedule
            )
        ],
        key=lambda tup: tup[1],
    )
    teams_exp_record = {
        team: add(teams_exp_record[team], wins)
        for team, wins in [(team[0], idx) for idx, team in enumerate(weekly_points)]
    }


###################
###  Team Info  ###
###################
params = {"view": "mTeams"}
team_resp = requests.get(url, params=params, cookies=cookies)

teams_info = team_resp.json()["teams"]
team_mapping = {
    team["id"]: (team["location"] + " " + team["nickname"]) for team in teams_info
}
team_records = {
    team["id"]: (team["record"]["overall"]["wins"], team["record"]["overall"]["losses"])
    for team in teams_info
}

###################
### League Week ###
###################

params = {"view": "mSchedule"}
league_schedule_resp = requests.get(url, params=params, cookies=cookies)
league_schedule = league_schedule_resp.json()
current_week = league_schedule["status"]["currentMatchupPeriod"]
