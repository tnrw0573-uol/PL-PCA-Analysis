import requests
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pprint import pprint 
from Data.fetchdata import response_success
from datetime import datetime

base_url = "https://api.thestatsapi.com/api/football"
headers = {
    'Authorization': 'Bearer fapi_iHb8rAyu8VA6WOtqDGsp7tvxDXRZLCWo',
    'Content-Type': 'application/json'
}
current_year = datetime.now().year

def find_player(player):
    response = requests.get(f"{base_url}/players", headers=headers, params={'search': f'{player}'})
    if response_success(response) == True:
        content = response.json()
        data = content['data']
        player_id = data[0]['id']
        team_id = data[0]['current_team']['id']
        name = data[0]['name']
    return player_id, team_id, name

def find_league(team_id):
    response = requests.get(f"{base_url}/teams/{team_id}", headers=headers)
    if response_success(response) == True:
        content = response.json()
        data = content['data']
        league_id = data['primary_competition']['id']
    return league_id

def find_season(league_id):
    response = requests.get(f"{base_url}/competitions/{league_id}/seasons", headers=headers)
    if response_success(response) == True:
        content = response.json()
        data = content['data']
        for season in data:
            if season['end_year'] == current_year:
                season_id = season['id']
    return season_id 

def find_player_stats(season_id, player_id, league_id, name):
    response = requests.get(f"{base_url}/players/{player_id}/stats", headers=headers, params={
        'season_id': f'{season_id}',
        'competition_id': f'{league_id}'})
    if response_success(response) == True:
        content = response.json()
        data = content['data']
        nineties_played = data['minutes_played'] / 90
        player_stats.append({
            'player_id': data['player_id'],
            'name': name,
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
    return player_stats

player = input("Enter player's full name: ")
player_id, team_id, name = find_player(player)
league_id = find_league(team_id)
season_id = find_season(league_id)
player_stats = []
player_stats = find_player_stats(season_id, player_id, league_id, name)