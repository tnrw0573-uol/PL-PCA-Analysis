import requests
from pprint import pprint

base_url = "https://api.thestatsapi.com/api/football"
headers = {
    'Authorization': 'Bearer REMOVED',
    'Content-Type': 'application/json'
}

#Check response and handle errors
def response_success(response):
    if response.status_code == 200:
        print("Successful response.")
        return True
    else:
        print(f"Response unsuccessful with status code {response.status_code}")
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
players=[]
def find_player_stats(base_url, headers):
    for team in team_ids:
        response = requests.get(f"{base_url}/teams/{team}/players", headers=headers)
        if response_success(response) == True:
            content = response.json()
            data = content['data']
            for player in data:
                players.append({
                    'name': player['name'],
                    'id': player['id']
                })
    return players
players = find_player_stats(base_url, headers)
pprint(players)
