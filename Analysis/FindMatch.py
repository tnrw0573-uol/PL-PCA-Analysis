import requests
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pprint import pprint 
from Data.fetchdata import response_success
from datetime import datetime
from Analysis.PCA import reduce_dataset
import pandas as pd
from scipy.spatial.distance import cdist

base_url = "https://api.thestatsapi.com/api/football"
headers = {
    'Authorization': 'Bearer fapi_iHb8rAyu8VA6WOtqDGsp7tvxDXRZLCWo',
    'Content-Type': 'application/json'
}
current_year = datetime.now().year

def find_player(player):
    player_id = None
    team_id = None
    name = None
    position = None
    response = requests.get(f"{base_url}/players", headers=headers, params={'search': f'{player}'})
    if response_success(response) == True:
        content = response.json()
        data = content['data']
        if len(data) != 0:
            player_id = data[0]['id']
            team_id = data[0]['current_team']['id']
            name = data[0]['name']
            position = data[0]['position']
    return player_id, team_id, name, position

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

while True:
    player = input("Enter player's full name: ").strip()
    if not player:
        print("Name cannot be empty.")
        continue
    
    player_id, team_id, name, position = find_player(player)
    if player_id is None:
        print("Player not found. Try again.")
        continue  
    break

while True:
    options = ['a', 's']
    option = input("Compare player to all players (enter 'a') or players with same position? (enter 's'): ")
    if option.lower() in options:
        break
    print(f'Invalid Input. Choose from {options}')

league_id = find_league(team_id)
season_id = find_season(league_id)
player_stats = []
player_stats = find_player_stats(season_id, player_id, league_id, name)

df = pd.read_csv('Data/player_stats.csv')
new_df, scaler, pca = reduce_dataset(option, df, 0.95)

player_data = pd.DataFrame(player_stats)
norm_player_data = scaler.transform(player_data.drop(['player_id', 'name', 'position'], axis = 1))
new_player_data = pca.transform(norm_player_data)
red_player_data = pd.DataFrame(data=new_player_data, columns=[f'PC{i+1}' for i in range(new_player_data.shape[1])])

distances = cdist(red_player_data, new_df.drop(['player_id', 'name', 'position'], axis = 1), 'euclidean')

player_info = [{
    'player_id': player_id,
    'name': name,
    'position': position
}]
player_info = pd.DataFrame(player_info)
player_row = pd.concat([player_info, red_player_data], axis = 1)

new_df = pd.concat([new_df, player_row]).reset_index(drop=True)
print(new_df)