import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import plotly.graph_objects as go

#Read stats CSV 
try:
    df = pd.read_csv('Data/player_stats.csv')
    print("CSV read successfully.")
except FileNotFoundError:
    print("CSV not found.")
except Exception as e:
    print(f"Error: {e}")

#Normalize data
norm_df = StandardScaler().fit_transform(df.drop(['player_id', 'name', 'position'], axis = 1))

#Reduce dataset
pca = PCA(n_components=2)
data = pca.fit_transform(norm_df)
reduced_df = pd.DataFrame(data=data, columns=['PC1', 'PC2'])
new_df = pd.concat([df[['player_id']], df[['name']], df[['position']], reduced_df], axis = 1)

def plot_scatter(figure, condition):
    figure.add_trace(go.Scatter(
                x=new_df.loc[condition, 'PC1'],
                y=new_df.loc[condition, 'PC2'],
                mode='markers',
                marker=dict(size=8),
                text=new_df.loc[condition, 'name'], 
                hovertemplate='<b>%{text}</b><extra></extra>'
            ))

#Get user input and validate
valid_options = ['a', 'g', 'd', 'm', 'f']
while True:
    option = input("For what positions do you want PCA analysis? Enter 'a' for all, 'd' for defenders, 'm' for midfielders and 'f' for forwards: ")
    if option in valid_options:
        break
    else:
        print(f"Only valid inputs are {valid_options}")

if option.lower() == "a":
    #Plot for all players
    fig = go.Figure()
    positions = list(set(new_df['position']))
    colors = ['red', 'green', 'blue', 'yellow']
    for position, color in zip(positions, colors):
        cond = new_df['position'] == position
        plot_scatter(fig, cond)
        fig.add_trace(go.Scatter(
            name = f"{position}",
            marker=dict(color=color, size=8),
        ))
    fig.update_layout(
        title='PCA Visualization on all Premier League Players',
        xaxis_title='Principal Component 1',
        yaxis_title='Principal Component 2'
    )
    fig.show()

elif option == "g":
    #Plot for goalkeepers
    fig = go.Figure()
    cond = new_df['position'] == "G"
    plot_scatter(fig, cond)
    fig.update_layout(
            title='PCA Visualization on all Premier League Goalkeepers',
            xaxis_title='Principal Component 1',
            yaxis_title='Principal Component 2'
        )
    fig.show()

elif option == "d":
    #Plot for defenders
    fig = go.Figure()
    cond = new_df['position'] == "D"
    plot_scatter(fig, cond)
    fig.update_layout(
            title='PCA Visualization on all Premier League Defenders',
            xaxis_title='Principal Component 1',
            yaxis_title='Principal Component 2'
        )
    fig.show()

elif option == "m":
    #Plot for midfielders
    fig = go.Figure()
    cond = new_df['position'] == "M"
    plot_scatter(fig, cond)
    fig.update_layout(
            title='PCA Visualization on all Premier League Midfielders',
            xaxis_title='Principal Component 1',
            yaxis_title='Principal Component 2'
        )
    fig.show()

elif option == "f":
    #Plot for forwards
    fig = go.Figure()
    cond = new_df['position'] == "F"
    plot_scatter(fig, cond)
    fig.update_layout(
            title='PCA Visualization on all Premier League Forwards',
            xaxis_title='Principal Component 1',
            yaxis_title='Principal Component 2'
        )
    fig.show()