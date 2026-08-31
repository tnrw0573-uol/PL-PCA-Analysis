import requests
import time
from pprint import pprint
import pandas as pd

base_url = "https://api.thestatsapi.com/api/football"
headers = {
    'Authorization': 'Bearer fapi_RiFdBS9odearwe8WgyoXfljk9mUo9G9I',
    'Content-Type': 'application/json'
}

#Check response and handle errors
def response_success(response):
    if response.status_code == 200:
        return True
    return False

#Find Premier League ID
def find_pl_id(base_url, headers):
    response = requests.get(f"{base_url}/competitions", headers=headers, params={'name': 'Premier League', 'country': 'England'})
    if response_success(response) == True:
        content = response.json()
        data = content['data']
        for league in data:
            if league['name'] == 'Premier League':
               league_id = league['id']
    return league_id 
league_id = find_pl_id(base_url, headers)


#Find 25/26 season ID
def find_season_id(base_url, headers):
    response = requests.get(f"{base_url}/competitions/{league_id}/seasons", headers=headers)
    if response_success(response) == True:
        content = response.json()
        data = content['data']
        for season in data:
            if season['name'] == 'Premier League 25/26':
                season_id = season['id']
    return season_id
season_id = find_season_id(base_url, headers)

#Find 25/26 Premier League teams 
team_ids = []
def find_teams(base_url, headers, teams):
    response = requests.get(f"{base_url}/competitions/{league_id}/seasons/{season_id}/standings", headers=headers)
    if response_success(response) == True:
        content = response.json()
        data = content['data']
        for team in data:
            team_id = team['team']['id']
            teams.append(team_id)
    return team_ids
team_ids = find_teams(base_url, headers, team_ids)

#Find player ids
player_ids=[]
def find_player_stats(base_url, headers):
    for team in team_ids:
        response = requests.get(f"{base_url}/teams/{team}/players", headers=headers)
        if response_success(response) == True:
            content = response.json()
            data = content['data']
            for player in data:
                player_ids.append({
                    'name': player['name'],
                    'id': player['id']
                })
    return player_ids
player_ids = find_player_stats(base_url, headers)

#Get player statistics
player_stats = []
def find_player_stats(base_url, headers):
    for player in player_ids:
        response = requests.get(f"{base_url}/players/{player['id']}/stats", headers=headers, params={'competition_id':league_id, 'season_id':season_id})
        if response_success(response) == True:
            content = response.json()
            data = content['data']
            if data['minutes_played'] >= 1000:
                nineties_played = data['minutes_played'] / 90
                player_stats.append({
                    'player_id': data['player_id'],
                    'name': player['name'],
                    'position': data['position'],
                    'goals': data['scoring']['goals'] / nineties_played,
                    'assists': data['scoring']['assists'] / nineties_played,
                    'goal_conversion_percentage': data['scoring']['goal_conversion_percentage'],
                    'big_chances_created': data['scoring']['big_chances_created'] / nineties_played,
                    'shots': data['shooting']['total_shots'] / nineties_played,
                    'shots_on_target': data['shooting']['shots_on_target'] / nineties_played,
                    'passes': data['passing']['total_passes'] / nineties_played,
                    'pass_accuracy': data['passing']['pass_accuracy'],
                    'key_passes': data['passing']['key_passes'] / nineties_played,
                    'cross_accuracy': data['passing']['accurate_crosses_percentage'],
                    'tackles': data['defending']['tackles'] / nineties_played,
                    'interceptions': data['defending']['interceptions'] / nineties_played,
                    'ground_duels_won_percentage': data['duels']['ground_duels_won_percentage'],
                    'successful_dribbles': data['duels']['successful_dribbles'] / nineties_played
                })
            #Time interval of 0.5s between requests to avoid exceeding rate limit
            time.sleep(0.5)
    return player_stats
player_stats = find_player_stats(base_url, headers)
pprint(player_stats)
df = pd.DataFrame(player_stats)
df.to_csv('player_stats.csv', index = False)