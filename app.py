import streamlit as st
import pandas as pd
from scipy.spatial.distance import cdist
import numpy as np
from pprint import pprint
from datetime import datetime
import os

from Data.fetchdata import response_success, find_teams, find_league_ids, find_season_ids
from Analysis.FindMatch import find_player, find_player_league_season, find_player_stats
from Analysis.PCA import reduce_dataset

base_url = "https://api.thestatsapi.com/api/football"
headers = {
    'Authorization': f"Bearer {os.environ['STATS_API_KEY']}",
    'Content-Type': 'application/json'
}
current_year = datetime.now().year

@st.cache_data(ttl=3600)
def get_data():
    #Load dataset
    df = pd.read_csv('Data/player_stats.csv')
    #Get every Big 5 League team, their league and relevant season
    countries = ['England', 'Italy', 'Spain', 'Germany', 'France']
    leagues = ['Premier League', 'Serie A', 'LaLiga', 'Bundesliga', 'Ligue 1']
    league_ids = find_league_ids(countries, leagues)
    season_ids = find_season_ids(league_ids)
    teams = find_teams(league_ids, season_ids)
    return df, teams

df, teams = get_data()

if 'candidates' not in st.session_state:
    st.session_state.candidates = None
if 'search_name' not in st.session_state:
    st.session_state.search_name = None

st.title("Big 5 Leagues Player Similarity Finder")
st.warning("IMPORTANT: Player that have recently switched between leagues are unavailable.")
#Ask user for player
player = st.text_input("Enter player's full name:")
option = st.radio("Compare player to all players or players with the same position?", ['All', 'Same'])






