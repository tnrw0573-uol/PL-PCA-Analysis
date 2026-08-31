import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt

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

#Plot
plt.clf() #Prevent new figure from being created
positions = list(set(new_df['position']))
colors = ['r', 'g', 'b', 'y']
for position, color in zip(positions, colors):
    cond = new_df['position'] == position
    plt.scatter(new_df.loc[cond, 'PC1'], new_df.loc[cond, 'PC2'], c=color, s=50)
plt.legend(positions, title="Position", loc='best')
plt.xlabel('Principal Component 1')
plt.ylabel('Principal Component 2')
plt.title("PCA on Premier League Players")
plt.savefig('Analysis/PL_PCA_scatter.png')
plt.show()