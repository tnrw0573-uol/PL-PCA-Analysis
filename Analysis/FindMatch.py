import requests
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pprint import pprint 
from Data.fetchdata import response_success, find_teams, find_league_ids
from datetime import datetime
from Analysis.PCA import reduce_dataset
import pandas as pd
from scipy.spatial.distance import cdist
import numpy as np

base_url = "https://api.thestatsapi.com/api/football"
headers = {
    'Authorization': 'Bearer fapi_iHb8rAyu8VA6WOtqDGsp7tvxDXRZLCWo',
    'Content-Type': 'application/json'
}
current_year = datetime.now().year

def find_player(player, teams):
    response = requests.get(f"{base_url}/players", headers=headers, params={'search': f'{player}'})
    if response_success(response) != True:
        return None, None, None, None

    content = response.json()
    data = content['data']

    # Filter to only players currently at a Big 5 league club
    team_ids = [t['id'] for t in teams]
    data = [p for p in data if p.get('current_team') and p['current_team']['id'] in team_ids]

    if len(data) == 0:
        return None, None, None, None

    if len(data) == 1:
        chosen = data[0]
    else:
        print("\nMultiple players found:")
        for i, p in enumerate(data):
            team_name = p['current_team']['name'] if p.get('current_team') else 'Unknown'
            print(f"{i+1}. {p['name']} - {team_name} - {p['position']}")

        while True:
            choice = input(f"Enter the number of the correct player (1-{len(data)}): ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(data):
                chosen = data[int(choice) - 1]
                break
            print("Invalid choice. Try again.")

    player_id = chosen['id']
    team_id = chosen['current_team']['id']
    name = chosen['name']
    position = chosen['position']
    return player_id, team_id, name, position

def find_league_and_season(team_id, teams):
    league_id = []
    season_id = []
    for team in teams:
        if team['id'] == team_id:
            league_id.append(team['league_id'])
            season_id.append(team['season_id'])
    return league_id, season_id

def find_season(league_ids):
    season_ids = []
    for league in league_ids:
        response = requests.get(f"{base_url}/competitions/{league}/seasons", headers=headers)
        if response_success(response) == True:
            content = response.json()
            data = content['data']
            for season in data:
                if season['end_year'] == current_year:
                    season_ids.append(season['id'])
    return season_ids

def find_player_stats(season_id, player_id, league_id, name):
    response = requests.get(f"{base_url}/players/{player_id}/stats", headers=headers, params={
        'season_id': f'{season_id[0]}',
        'competition_id': f'{league_id[0]}'})
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

countries = ['England', 'Italy', 'Spain', 'Germany', 'France']
leagues = ['Premier League', 'Serie A', 'LaLiga', 'Bundesliga', 'Ligue 1']
league_ids = find_league_ids(base_url, headers, countries, leagues)
season_ids = find_season(league_ids)
teams = find_teams(base_url, headers, league_ids, season_ids)

continuing = True
while continuing:
    #Get player name and validate
    while True:
        print("IMPORTANT: Player that have recently switched between leagues are unavailable.")
        player = input("Enter player's full name: ").strip()
        if not player:
            print("Name cannot be empty.")
            continue

        player_id, team_id, name, position = find_player(player, teams)
        if player_id is None:
            print("Player not found. Try again.")
            continue  
        break
    #Get option, wanted distance and validate
    while True:
        options = ['a', 's']
        option = input("Compare player to all players (enter 'a') or players with same position? (enter 's'): ")
        if option.lower() in options:
            break
        print(f'Invalid input. Choose from {options}')
    
    #Find player's league
    league_id, season_id = find_league_and_season(team_id, teams)
    #Get player stats for last season
    player_stats = []
    player_stats = find_player_stats(season_id, player_id, league_id, name)

    #Load dataset
    df = pd.read_csv('Data/player_stats.csv')
    #Reduce dataset
    if option == 's':
        new_df, scaler, pca = reduce_dataset(position, df, 0.95)
    else:
        new_df, scaler, pca = reduce_dataset(option, df, 0.95)

    #Normalize and transform player's data using the same scaler and pca as the dataset
    player_data = pd.DataFrame(player_stats)
    norm_player_data = scaler.transform(player_data.drop(['player_id', 'name', 'position'], axis = 1))
    new_player_data = pca.transform(norm_player_data)
    red_player_data = pd.DataFrame(data=new_player_data, columns=[f'PC{i+1}' for i in range(new_player_data.shape[1])])

    #Calculate distance between player and the others
    distances = cdist(red_player_data, new_df.drop(['player_id', 'name', 'position'], axis = 1), 'cosine')
    #Transpose to make a column
    distances = np.transpose(distances)
    distances = pd.DataFrame(data=distances, columns=['Distance'])

    #Add player to the dataset
    player_info = [{
        'player_id': player_id,
        'name': name,
        'position': position
    }]
    player_info = pd.DataFrame(player_info)
    player_row = pd.concat([player_info, red_player_data], axis = 1)
    new_df = pd.concat([new_df, player_row]).reset_index(drop=True)

    #Add distance column to dataset
    new_df = pd.concat([new_df, distances], axis = 1)
    #Sort by distance (ascending)
    sorted_df = new_df.sort_values(by='Distance')

    counter = 1
    for index, row in sorted_df.iterrows():
        if row['name'] != name:
            print(f"{counter}. {row['name']}")
            counter += 1
            if counter > 20:
                break

    #Give user option to enter new player
    cont_option = input("Enter another player? (y/n): ")
    if cont_option.lower() == "n":
        break
