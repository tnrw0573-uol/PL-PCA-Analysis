import streamlit as st
import requests
from Data.fetchdata import response_success, find_teams, find_league_ids
from datetime import datetime
from Analysis.PCA import reduce_dataset
import pandas as pd
from scipy.spatial.distance import cdist
import numpy as np

base_url = "https://api.thestatsapi.com/api/football"
headers = {
    'Authorization': f"Bearer {st.secrets['API_KEY']}",
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

    return data


def resolve_choice(data, chosen_label):
    labels = [f"{p['name']} - {p['current_team']['name']} - {p['position']}" for p in data]
    chosen = data[labels.index(chosen_label)]
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


@st.cache_data(ttl=3600)
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


@st.cache_data(ttl=1800)
def find_player_stats(season_id, player_id, league_id, name):
    player_stats = []
    response = requests.get(f"{base_url}/players/{player_id}/stats", headers=headers, params={
        'season_id': f'{season_id[0]}',
        'competition_id': f'{league_id[0]}'})
    if response_success(response) == True:
        content = response.json()
        data = content['data']
        nineties_played = data['minutes_played'] / 90
        if nineties_played == 0:
            return player_stats
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


@st.cache_data(ttl=3600)
def get_league_ids():
    return find_league_ids(base_url, headers, countries, leagues)


@st.cache_data(ttl=3600)
def get_teams(league_ids, season_ids):
    return find_teams(base_url, headers, league_ids, season_ids)


@st.cache_data
def load_data():
    return pd.read_csv('Data/player_stats.csv')


countries = ['England', 'Italy', 'Spain', 'Germany', 'France']
leagues = ['Premier League', 'Serie A', 'LaLiga', 'Bundesliga', 'Ligue 1']
league_ids = get_league_ids()
season_ids = find_season(league_ids)
teams = get_teams(league_ids, season_ids)


# ---------- App starts here ----------
st.title("Big 5 League Player Similarity Finder")

st.warning("IMPORTANT: Players that have recently joined/left clubs in the Big 5 leagues are unavailable.")

df = load_data()

# session_state keeps track of an in-progress search across reruns, so the
# "multiple players found" dropdown doesn't get wiped out on selection
if 'candidates' not in st.session_state:
    st.session_state.candidates = None
if 'search_name' not in st.session_state:
    st.session_state.search_name = None

player = st.text_input("Enter player's full name:")

option = st.radio(
    "Compare player to all players (enter 'a') or players with same position? (enter 's'):",
    ['a', 's']
)

if st.button("Find similar players") and player.strip():
    data = find_player(player.strip(), teams)
    if data is None:
        st.error("Player not found.")
        st.session_state.candidates = None
    else:
        st.session_state.candidates = data
        st.session_state.search_name = player.strip()

# If the search matched more than one player, ask which one before continuing
chosen = None
if st.session_state.candidates is not None:
    data = st.session_state.candidates
    if len(data) == 1:
        chosen = data[0]
    else:
        st.write("Multiple players found:")
        labels = [f"{p['name']} - {p['current_team']['name']} - {p['position']}" for p in data]
        selected_label = st.selectbox("Choose the correct player:", labels)
        if st.button("Confirm player"):
            chosen = data[labels.index(selected_label)]

if chosen is not None:
    player_id = chosen['id']
    team_id = chosen['current_team']['id']
    name = chosen['name']
    position = chosen['position']

    league_id, season_id = find_league_and_season(team_id, teams)
    player_stats = find_player_stats(season_id, player_id, league_id, name)

    if not player_stats:
        st.error("Player recently left a club.")
    else:
        if option == 's':
            new_df, scaler, pca = reduce_dataset(position, df, 0.95)
        else:
            new_df, scaler, pca = reduce_dataset(option, df, 0.95)

        player_data = pd.DataFrame(player_stats)
        feature_cols = df.drop(['player_id', 'name', 'position'], axis=1).columns
        norm_player_data = scaler.transform(player_data[feature_cols])
        new_player_data = pca.transform(norm_player_data)
        red_player_data = pd.DataFrame(data=new_player_data, columns=[f'PC{i+1}' for i in range(new_player_data.shape[1])])

        distances = cdist(red_player_data, new_df.drop(['player_id', 'name', 'position'], axis=1), 'euclidean')
        distances = np.transpose(distances)
        distances = pd.DataFrame(data=distances, columns=['Distance'])

        player_info = [{
            'player_id': player_id,
            'name': name,
            'position': position
        }]
        player_info = pd.DataFrame(player_info)
        player_row = pd.concat([player_info, red_player_data], axis=1)
        new_df = pd.concat([new_df, player_row]).reset_index(drop=True)

        new_df = pd.concat([new_df, distances], axis=1)
        sorted_df = new_df.sort_values(by='Distance')

        st.subheader(f"Players most similar to {name}")
        counter = 1
        for index, row in sorted_df.iterrows():
            if row['player_id'] != player_id:
                st.write(f"{counter}. {row['name']}")
                counter += 1
                if counter > 10:
                    break
