import requests
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pprint import pprint 
from Data.fetchdata import response_success, find_teams, find_league_ids, find_season_ids
from datetime import datetime
from Analysis.PCA import reduce_dataset
import pandas as pd
from scipy.spatial.distance import cdist
import numpy as np
import streamlit as st

#Base URL used for every API call. A path to an endpoint is added for every request
base_url = "https://api.thestatsapi.com/api/football"

"""
headers(dict): HTTP request headers that are sent with each API call. 
    - Authorization (str): The key needed to authenticate with the server.
    - Content-Type (str): The content the server is to parse the response in.
"""
headers = {
    'Authorization': f'Bearer {st.secrets['API_KEY']}',
    'Content-Type': 'application/json'
}
current_year = datetime.now().year

#Construct a list of every Big 5 league team and their ID, league and season ID for the relevant season.
countries = ['England', 'Italy', 'Spain', 'Germany', 'France']
leagues = ['Premier League', 'Serie A', 'LaLiga', 'Bundesliga', 'Ligue 1']
league_ids = find_league_ids(countries, leagues)
season_ids = find_season_ids(league_ids)
teams = find_teams(league_ids, season_ids)

def find_player(player, teams):
    """Finds the player the user wants.
    Args:
        player (str): The player's name inputted by the user.
        teams (list[dict]): A list of every team with their ID, league and season.
    Returns:
        player_id (str): The player's ID.
        team_id (str): The player's team ID.
        name (str): The player's name, with diacritics, hyphens etc.
        position (str): The player's position
    """
    #Search for the player
    response = requests.get(f"{base_url}/players", headers=headers, params={'search': f'{player}'})
    if response_success(response) != True: #if response fails
        return None, None, None, None

    content = response.json()
    data = content['data']

    # Filter to only players currently at a Big 5 league club
    team_ids = [t['id'] for t in teams]
    data = [p for p in data if p.get('current_team') and p['current_team']['id'] in team_ids]

    #Return None if player isn't found
    if len(data) == 0:
        return {'id': None}

    if len(data) == 1:
        chosen = data[0]
    #If there are multiple players with the same name, present the user with an option to choose their intended choice
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

    #Return the info of the user chosen player
    return chosen

def find_player_league_season(team_id, teams):
    """Finds the player's league and the league's relevant season.
    Args:
        team_id (str): The player's team ID.
        teams (list[dict]): A list of every team with their ID, league and season.
    Returns:
        league_id (str): The player's league's ID.
        season_id (str): The league's season ID for the relevant season.
    """
    league_id = []
    season_id = []
    #Search for the player's team
    for team in teams:
        if team['id'] == team_id:
            league_id.append(team['league_id'])
            season_id.append(team['season_id'])
    return league_id, season_id

def find_player_stats(season_id, player_id, league_id, name, player_stats):
    """
    Finds the player's stats for the relevant season.
    Args:
        season_id (str): The league's season ID for the relevant season.
        player_id (str): The player's ID.
        league_id (str): The player's league ID.
        name (str): The player's name.
    """
    #Search for the stats
    response = requests.get(f"{base_url}/players/{player_id}/stats", headers=headers, params={
        'season_id': f'{season_id[0]}',
        'competition_id': f'{league_id[0]}'})
    if response_success(response) == True:
        content = response.json()
        data = content['data']
        nineties_played = data['minutes_played'] / 90 #Just like for other players in the dataframe, account for per 90 stats
        #Construct list of player, player's information and player's stats 
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
            'aerial_duels_won': data['duels']['aerial_duels_won'] / nineties_played,
            'aerial_duels_won_percentage': data['duels']['aerial_duels_won_percentage'],
            'successful_dribbles': data['duels']['successful_dribbles'] / nineties_played,
            'successful_dribbles_percentage': data['duels']['successful_dribbles_percentage']
        })
    return player_stats

if __name__ == "__main__":
    continuing = True
    while continuing:
        #Get player name and validate
        while True:
            print("IMPORTANT: Player that have recently switched between leagues are unavailable.")
            player = input("Enter player's full name: ").strip()
            if not player: #If user doesn't enter anything
                print("Name cannot be empty.")
                continue
            #Find player info
            chosen = find_player(player, teams)
            #If player not found, print a message and prompt the user again
            if chosen['id'] is None: 
                print("Player not found. Try again.")
                continue  
            break

        while True:
            options = ['a', 's']
            option = input("Compare player to all players (enter 'a') or players with same position? (enter 's'): ")
            #If user enters an invalid option, prompt the user again
            if option.lower() in options:
                break
            print(f'Invalid input. Choose from {options}')

        player_id = chosen['id']
        team_id = chosen['current_team']['id']
        name = chosen['name']
        position = chosen['position']
        #Find player's season
        league_id, season_id = find_player_league_season(team_id, teams)
        #Get player stats for last season
        player_stats = []
        player_stats = find_player_stats(season_id, player_id, league_id, name, player_stats)

        #Load dataset
        df = pd.read_csv('Data/player_stats.csv')
        #Reduce dataset: Compress the stats down to fewer components that explain 95% of the variance
        if option == 's': #if player chose to compare player to those of the same position
            new_df, scaler, pca = reduce_dataset(position, df, 0.95)
        else: #if player chose to compare player to every other player
            new_df, scaler, pca = reduce_dataset(option, df, 0.95)

        #Make player's stats have the same features as the other players
        player_data = pd.DataFrame(player_stats).reindex(columns=df.columns)
        #Normalise and transform the player's data with the same scaler and pca as the dataset
        norm_player_data = scaler.transform(player_data.drop(['player_id', 'name', 'position'], axis = 1)) #omit non-numeric stats
        new_player_data = pca.transform(norm_player_data)
        red_player_data = pd.DataFrame(data=new_player_data, columns=[f'PC{i+1}' for i in range(new_player_data.shape[1])])

        #Calculate cosine distance between player and every other player
        distances = cdist(red_player_data, new_df.drop(['player_id', 'name', 'position'], axis = 1), 'cosine')
        #Transpose and make a column of the distances ready to add to the dataset
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

        #Show top 10 closest matches  
        counter = 1
        for index, row in sorted_df.iterrows():
            if row['name'] != name: #Avoid showing the same player as the one inputted 
                print(f"{counter}. {row['name']}")
                counter += 1
                if counter > 10:
                    break

        #Give user option to enter new player
        cont_option = input("Enter another player? (Enter 'y' for yes): ")
        if cont_option.lower() != "y":
            break #Quit
