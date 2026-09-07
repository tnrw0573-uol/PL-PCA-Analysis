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

def reduce_dataset(option, df, n_components=2):
    """
    Reduces the dataset through PCA.
    Args:
        option (str): The players the user wants his chosen player to be compared against.
        df (DataFrame): The dataset of all players and their stats.
        n_components (int): The number of components to reduce the dataset to. If not specified when called, the default is 2.
    Returns:
        new_df (DataFrame): The reduced dataset.
        scaler (StandardScaler): The scaler object used to standardize every stat.
        pca (PCA): PCA object.
    """
    #if player wants position-specific comparison, only use players with that position
    if option != 'a':
        df = df[df['position'] == option.upper()].reset_index(drop=True)

    #Standardize the data 
    scaler = StandardScaler()
    norm_df = scaler.fit_transform(df.drop(['player_id', 'name', 'position'], axis = 1)) #Drop non-numeric columns

    #Reduce dataset
    pca = PCA(n_components)
    data = pca.fit_transform(norm_df)
    #If this file is being ran directly, the dataset is reduced to 2 principal components
    #Calculate the proportion of the variance those 2 components account for
    if __name__ == "__main__":
        print("Explained variance ratio:", pca.explained_variance_ratio_)
        print("Total explained variance:", pca.explained_variance_ratio_.sum())
    #Make a new, reduced dataset
    reduced_df = pd.DataFrame(data=data, columns=[f'PC{i+1}' for i in range(data.shape[1])])
    #Recombine non-numeric columns with the reduced dataset
    new_df = pd.concat([df[['player_id']], df[['name']], df[['position']], reduced_df], axis = 1)
    return new_df, scaler, pca

def plot_scatter(figure, condition):
    """
    Plots a scatter plot.
    Args:
        figure (Figure): A Figure object. 
        condition (bool): The condition that must be met for a player to be plotted.
    """
    figure.add_trace(go.Scatter(
                #Check if player meets the condition and plot if he does
                x=new_df.loc[condition, 'PC1'], 
                y=new_df.loc[condition, 'PC2'],
                mode='markers',
                marker=dict(size=8),
                text=new_df.loc[condition, 'name'], 
                hovertemplate='<b>%{text}</b><extra></extra>'
            ))

if __name__ == "__main__": #If file is being ran directly
    valid_options = ['a', 'g', 'd', 'm', 'f']
    while True:
        #Ask user for what positions they want analysis on
        option = input("For what positions do you want PCA analysis? Enter 'a' for all, 'g' for goalkeepers, 'd' for defenders, 'm' for midfielders and 'f' for forwards: ")
        option = option.lower()
        #Validate
        if option in valid_options:
            break
        else:
            print(f"Only valid inputs are {valid_options}")

    if option == "a": #All players
        #Get reduced dataset
        new_df, scaler, pca = reduce_dataset(option, df)
        fig = go.Figure()
        #Get all positions
        positions = list(set(new_df['position']))
        colors = ['red', 'green', 'blue', 'yellow']
        for position, color in zip(positions, colors): #Associate nth position with nth color
            #Plot the player if their position is the position being searched for
            cond = new_df['position'] == position
            fig.add_trace(go.Scatter(
                            x=new_df.loc[cond, 'PC1'],
                            y=new_df.loc[cond, 'PC2'],
                            mode='markers',
                            marker=dict(color=color, size=8),
                            name = f'{position}',
                            text=new_df.loc[cond, 'name'], 
                            hovertemplate='<b>%{text}</b><extra></extra>'
                        ))
        fig.update_layout(
            title='PCA Visualization on all Big 5 League Players',
            xaxis_title='Principal Component 1',
            yaxis_title='Principal Component 2'
        )
        fig.show()
        fig.write_html('Plots/PCA_all.html')

    elif option == "g": #Goalkeepers
        #Reduce dataset
        new_df, scaler, pca = reduce_dataset(option, df)
        fig = go.Figure()
        cond = new_df['position'] == "G" #Plot a player only if they are a goalkeeper
        plot_scatter(fig, cond)
        fig.update_layout(
                title='PCA Visualization on all Big 5 Goalkeepers',
                xaxis_title='Principal Component 1',
                yaxis_title='Principal Component 2'
            )
        fig.show()
        fig.write_html('Plots/PCA_gk.html')

    elif option == "d": #Defenders
        #Reduce dataset
        new_df, scaler, pca = reduce_dataset(option, df)
        fig = go.Figure()
        cond = new_df['position'] == "D" #Plot a player only if they are a defender
        plot_scatter(fig, cond)
        fig.update_layout(
                title='PCA Visualization on all Big 5 Defenders',
                xaxis_title='Principal Component 1',
                yaxis_title='Principal Component 2'
            )
        fig.show()
        fig.write_html('Plots/PCA_df.html')

    elif option == "m": #Midfielders
        #Reduce dataset
        new_df, scaler, pca = reduce_dataset(option, df)
        fig = go.Figure()
        cond = new_df['position'] == "M" #Plot a player only if they are a midfielder
        plot_scatter(fig, cond)
        fig.update_layout(
                title='PCA Visualization on all Big 5 Midfielders',
                xaxis_title='Principal Component 1',
                yaxis_title='Principal Component 2'
            )
        fig.show()
        fig.write_html('Plots/PCA_mf.html')

    elif option == "f": #Forwards
        #Reduce dataset
        new_df, scaler, pca = reduce_dataset(option, df)
        fig = go.Figure()
        cond = new_df['position'] == "F" #Plot a player only if they are a forward
        plot_scatter(fig, cond)
        fig.update_layout(
                title='PCA Visualization on all Big 5 Forwards',
                xaxis_title='Principal Component 1',
                yaxis_title='Principal Component 2'
            )
        fig.show()
        fig.write_html('Plots/PCA_fw.html')