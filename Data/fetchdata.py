import requests
from pprint import pprint

url = "https://api.thestatsapi.com/api/football"
headers = {
    'Authorization': 'Bearer REMOVED',
    'Content-Type': 'application/json'
}
params = {
    'name': 'Premier League',
    'country': 'England'
}

#Find Premier League ID
response = requests.get(f"{url}/competitions", headers=headers, params=params)
if response.status_code == 200:
    content = response.json()
    data = content['data']
    for league in data:
        if league['name'] == 'Premier League':
            season_id = league['id']
            print(season_id)
else:
    print(f"Request failed with error code {response.status_code}.")