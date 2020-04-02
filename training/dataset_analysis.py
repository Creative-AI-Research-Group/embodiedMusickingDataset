"""looks at the dataset to analyse hotspots heat maps and statitsical corrolations between features."
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# print(sns.__version__)
# print(np.__version__)
# print(pd.__version__)
# import sys
# print(sys.version)
# print(sklearn.__version__)

df = pd.read_csv('data/raw_phase1_dataset.csv', header=None)
col_name = ['id', 'limb', 'x', 'y', 'z', 'freq', 'amp']
df.columns = col_name

# apply filter function
# A) just the features we want
df.filter(['x', 'y', 'z', 'freq', 'amp'])
# all rows with amp values great er than 0 (i.e. has a sound)
df = df[df['amp'] > 0]

# choose only the feature for study
col_study = ['x', 'y', 'z', 'freq', 'amp']
print (df[col_study].describe())

# Correlation Analysis and Feature Selection
# initial plot of all selection features
sns.pairplot(df[col_study], height=1.5)
plt.show()

# reduce dp to 2
pd.options.display.float_format = '{:,.2f}'.format
# instigate corrolation analysis and plot heatmap
df[col_study].corr()
plt.figure(figsize=(12,8))
sns.heatmap(df[col_study].corr(), annot=True, fmt=".2f")
plt.show()

