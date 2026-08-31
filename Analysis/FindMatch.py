import requests
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pprint import pprint 
from Data.fetchdata import response_success

base_url = "https://api.thestatsapi.com/api/football"
headers = {
    'Authorization': 'Bearer fapi_iHb8rAyu8VA6WOtqDGsp7tvxDXRZLCWo',
    'Content-Type': 'application/json'
}

def find_player(player):
    response = requests.get(f"{base_url}/players", headers=headers, params={'search': f'{player}'})
    if response_success(response) == True:
        content = response.json()
        data = content['data']
        player_id = data[0]['id']
        team_id = data[0]['current_team']['id']
    return player_id, team_id

player = input("Enter player's full name: ")
player_id, team_id = find_player(player)
print(player_id)
print(team_id)