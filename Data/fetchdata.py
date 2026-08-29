import requests
from pprint import pprint

url = "https://api.football-data.org/v4/competitions/PL/teams"
headers = {
    'X-Auth-Token': 'REMOVED',
    'Content-Type': 'application/json'
}

all_data = {}
for season in ['2023', '2024', '2025']:
    params = {'season': season}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        all_data[season] = data
    else:
        print(f"Request failed with status code {response.status_code}")

pprint(all_data['2025'])