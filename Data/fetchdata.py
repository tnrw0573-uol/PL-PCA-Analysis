import requests
import time
from datetime import datetime
from pprint import pprint
import pandas as pd

base_url = "https://api.thestatsapi.com/api/football"
headers = {
    'Authorization': 'Bearer fapi_iHb8rAyu8VA6WOtqDGsp7tvxDXRZLCWo',
    'Content-Type': 'application/json'
}
current_year = datetime.now().year

def response_success(response):
    """
    Checks if the response was successful.   
    Args:
        response (requests.Response): The response given after calling the API.   
    Returns:
        bool: True if the response was successful, False otherwise.
    """
    if response.status_code == 200: #200 is the code for a successful response
        return True
    return False

#Find ID for each league
def find_league_ids(base_url, headers, countries, leagues):
    league_ids = []
    for country, league in zip(countries, leagues):
        response = requests.get(f"{base_url}/competitions", headers=headers, params={'name': f'{league}', 'country': f'{country}'})
        if response_success(response) == True:
            content = response.json()
            data = content['data']
        for result in data:
            if result['name'] == f'{league}':
               league_ids.append(result['id'])
    return league_ids

#Find 25/26 season IDs
def find_seasons_id(base_url, headers):
    season_ids = []
    for id in league_ids:
        response = requests.get(f"{base_url}/competitions/{id}/seasons", headers=headers)
        if response_success(response) == True:
            content = response.json()
            data = content['data']
            for season in data:
                if season['end_year'] == current_year:
                    season_ids.append(season['id'])
    return season_ids

#Find 25/26 Big 5 league teams 
def find_teams(base_url, headers, league_ids, season_ids):
    team_ids = []
    for league, season in zip(league_ids, season_ids):
        response = requests.get(f"{base_url}/competitions/{league}/seasons/{season}/standings", headers=headers)
        if response_success(response) == True:
            content = response.json()
            data = content['data']
            for team in data:
                team_ids.append({
                    'id': team['team']['id'],
                    'league_id': league,
                    'season_id': season
                })
    return team_ids

#Find player ids
def find_player_ids(base_url, headers, team_ids):
    player_ids = []
    for team in team_ids:
        response = requests.get(f"{base_url}/teams/{team['id']}/players", headers=headers)
        if response_success(response) == True:
            content = response.json()
            data = content['data']
            for player in data:
                player_ids.append({
                    'name': player['name'],
                    'id': player['id'],
                    'league_id': team['league_id'],
                    'season_id': team['season_id']
                })
    return player_ids

#Get player statistics
def find_player_stats(base_url, headers):
    player_stats = []
    for player in player_ids:
        response = requests.get(f"{base_url}/players/{player['id']}/stats", headers=headers, params={'competition_id':player['league_id'], 'season_id':player['season_id']})
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

if __name__ == "__main__":
    countries = ['England', 'Italy', 'Spain', 'Germany', 'France']
    leagues = ['Premier League', 'Serie A', 'LaLiga', 'Bundesliga', 'Ligue 1']
    league_ids = find_league_ids(base_url, headers, countries, leagues)
    season_ids = find_seasons_id(base_url, headers)
    team_ids = find_teams(base_url, headers, league_ids, season_ids)
    player_ids = find_player_ids(base_url, headers, team_ids)
    player_stats = find_player_stats(base_url, headers)
    pprint(player_stats)
    df = pd.DataFrame(player_stats)
    df.to_csv('Data/player_stats.csv', index = False)

