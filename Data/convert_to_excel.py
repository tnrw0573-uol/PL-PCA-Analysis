import pandas as pd

df = pd.read_csv('Data/player_stats.csv')
df = df.drop(['big_chances_missed', 'aerial_duels_won_percentage', 'successful_dribbles_percentage'], axis = 1)
df.to_excel('Data/player_stats.xlsx', index = False)