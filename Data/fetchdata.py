import requests
import time
from datetime import datetime
from pprint import pprint
import pandas as pd
import os

#Base URL for the API endpoints, requests are made by appending a path to this
base_url = "https://api.thestatsapi.com/api/football"

"""
headers(dict): HTTP request headers that are sent with each API call. 
    - Authorization (str): The key needed to authenticate with the server.
    - Content-Type (str): The content the server is to parse the response in.
"""
headers = {
    'Authorization': f'Bearer {os.environ['STATS_API_KEY']}',
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

def find_league_ids(countries, leagues):
    """
    Finds a league's ID.
    Args:
        countries (list): A list of the countries each league is based in.
        leagues (list): A list of each league.
    Returns:
        league_ids (list): A list of every league's ID.
    """
    league_ids = []
    #Associate the nth country with the nth league
    for country, league in zip(countries, leagues):
        #Search for the league
        response = requests.get(f"{base_url}/competitions", headers=headers, params={'name': f'{league}', 'country': f'{country}'})
        if response_success(response) == True:
            content = response.json()
            data = content['data']
        for result in data:
            if result['name'] == f'{league}':
               league_ids.append(result['id'])
    return league_ids

def find_seasons_id(league_ids):
    """
    Finds the ID of each league's last season. If a league is at least halfway done, it finds the ID of the current season.
    Args:
        league_ids (list): A list of each league's ID.
    Returns:
        season_ids (list): A list of each league's last season (or current season if at least halfway done).
    """
    season_ids = []
    for id in league_ids:
        #Get each league's seasons
        response = requests.get(f"{base_url}/competitions/{id}/seasons", headers=headers)
        if response_success(response) == True:
            content = response.json()
            data = content['data']
            #Search for the last/current season
            for season in data:
                if season['end_year'] == current_year: #The Big 5 leagues are usually from August-May
                    season_ids.append(season['id'])
    return season_ids

def find_teams(league_ids, season_ids):
    """
    Finds every team that played in the relevant season of the Big 5 leagues.
    Args:
        league_ids (list): A list of each league's ID.
        season_ids (list): A list of the relevant season's ID for each league.
    Returns:
        team_ids (list[dict]): A list consisting of each team's ID, league and the season.
    """
    team_ids = []
    #Associate the nth league ID with the nth season ID
    for league, season in zip(league_ids, season_ids):
        #Find the league standings for that season
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

def find_player_ids(team_ids):
    """
    Finds every player in the Big 5 leagues.
    Args:
        team_ids (list[dict]): A list of every Big 5 league team, their league and the season they played in.
    Returns:
        players (list[dict]): A list of every player consisting of their name, id, team and season.
    """
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

def find_player_stats(players):
    """
    Finds the stats for every player.
    Args:
        players (list[dict]): The list consiting of every Big 5 league player and their information.
    Returns:
        player_stats (list[dict]): A list consisting of a player's id, name, position and their relevant stats.
    """
    player_stats = []
    for player in players:
        #Find the player's stats for the relevant season
        response = requests.get(f"{base_url}/players/{player['id']}/stats", headers=headers, params={'competition_id':player['league_id'], 'season_id':player['season_id']})
        if response_success(response) == True:
            content = response.json()
            data = content['data']
            #Filter by minutes played. If a player has played less than 1000 minutes it is not a big enough sample size
            if data['minutes_played'] >= 1000:
                #Account for per 90 stats only so stats aren't biased towards players who have simply played more than others
                nineties_played = data['minutes_played'] / 90
                raw_stats = {
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
                    'aerial_duels_won': data['duels']['aerial_duels_won'] / nineties_played,
                    'aerial_duels_won_percentage': data['duels']['aerial_duels_won_percentage'],
                    'total_duels_won': data['duels']['total_duels_won'] / nineties_played,
                    'total_duels_won_percentage': data['duels']['total_duels_won_percentage'],
                    'successful_dribbles': data['duels']['successful_dribbles'] / nineties_played,
                    'succesful_dribbles_percentage': data['duels']['successful_dribbles_percentage']
                }
                #Leave out any stats that are null
                player_stats.append({key : value for key, value in raw_stats.items() if value is not None})
            #Time interval of 0.5s between requests to avoid exceeding rate limit
            time.sleep(0.5)
    return player_stats

if __name__ == "__main__":
    countries = ['England', 'Italy', 'Spain', 'Germany', 'France']
    leagues = ['Premier League', 'Serie A', 'LaLiga', 'Bundesliga', 'Ligue 1']
    league_ids = find_league_ids(countries, leagues)
    season_ids = find_seasons_id(league_ids)
    team_ids = find_teams(league_ids, season_ids)
    players = find_player_ids(team_ids)
    player_stats = find_player_stats(players)
    pprint(player_stats)
    #Convert player stats to dataframe and export as a csv file
    df = pd.DataFrame(player_stats)
    df.to_csv('Data/player_stats.csv', index = False)

