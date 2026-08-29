import pandas as pd

df = pd.read_csv('Data/player_stats.csv')
df.to_excel('Data/player_stats.xlsx', index = False)