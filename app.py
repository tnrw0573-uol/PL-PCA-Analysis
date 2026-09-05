import streamlit as st
import pandas as pd
from scipy.spatial.distance import cdist
import numpy as np
from pprint import pprint
from datetime import datetime

from Data.fetchdata import find_teams, find_league_ids, find_season_ids
from Analysis.FindMatch import find_player, find_player_league_season, find_player_stats
from Analysis.PCA import reduce_dataset

base_url = "https://api.thestatsapi.com/api/football"
headers = {
    'Authorization': f"Bearer {st.secrets['STATS_API_KEY']}",
    'Content-Type': 'application/json'
}
current_year = datetime.now().year

@st.cache_data(ttl=3600)
def get_data():
    #Load dataset
    return pd.read_csv('Data/player_stats.csv')

@st.cache_data(ttl=3600)
def get_league_ids():
    return find_league_ids(countries, leagues)

@st.cache_data(ttl=3600)
def get_season_ids():
    return find_season_ids(league_ids)

@st.cache_data(ttl=3600)
def get_teams():
    return find_teams(league_ids, season_ids)

@st.cache_data(ttl=3600)
def get_player():
    return find_player(player, teams)

@st.cache_data(ttl=3600)
def get_player_league_season(team_id, teams):
    return find_player_league_season(team_id, teams)

@st.cache_data(ttl=3600)
def get_player_stats(season_id, player_id, league_id, name, player_stats):
    return find_player_stats(season_id, player_id, league_id, name, player_stats)

df = get_data()
#Get every Big 5 League team, their league and relevant season
countries = ['England', 'Italy', 'Spain', 'Germany', 'France']
leagues = ['Premier League', 'Serie A', 'LaLiga', 'Bundesliga', 'Ligue 1']
league_ids = get_league_ids()
season_ids = get_season_ids()
teams = get_teams()

if 'candidates' not in st.session_state:
    st.session_state.candidates = None
if 'search_name' not in st.session_state:
    st.session_state.search_name = None

st.title("Big 5 Leagues Player Similarity Finder")
st.warning("IMPORTANT: Player that have recently switched between leagues are unavailable.")
#Ask user for player
player = st.text_input("Enter player's full name:")
option = st.radio("Compare player to all players or players with the same position?", ['All', 'Same'])


if st.button("Find similar players") and player.strip():
    data = find_player(player.strip(), teams)
    if data['id'] is None:
        st.error("Player not found.")
        st.session_state.candidates = None
    else:
        st.session_state.candidates = data
        st.session_state.search_name = player.strip()
    
        player_id = data['id']
        team_id = data['current_team']['id']
        name = data['name']
        position = data['position']

        league_id, season_id = get_player_league_season(team_id, teams)
        player_stats = []
        player_stats = get_player_stats(season_id, player_id, league_id, name, player_stats)

        if not player_stats:
            st.error("Player recently left a club.")
        else:
            if option == 'Same':
                new_df, scaler, pca = reduce_dataset(position, df, 0.95)
            else:
                option = 'a'
                new_df, scaler, pca = reduce_dataset(option, df, 0.95)

            player_data = pd.DataFrame(player_stats).reindex(columns=df.columns)
            columns_with_nulls = player_data.columns[player_data.isna().any() == True].to_list()
            player_data = player_data.drop(columns = columns_with_nulls)
            feature_cols = df.drop(['player_id', 'name', 'position'], axis=1).columns
            norm_player_data = scaler.transform(player_data[feature_cols])
            new_player_data = pca.transform(norm_player_data)
            red_player_data = pd.DataFrame(data=new_player_data, columns=[f'PC{i+1}' for i in range(new_player_data.shape[1])])

            distances = cdist(red_player_data, new_df.drop(['player_id', 'name', 'position'], axis=1), 'cosine')
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