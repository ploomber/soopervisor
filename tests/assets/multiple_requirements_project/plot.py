"""
Generate plot
"""
import pandas as pd

# + tags=["parameters"]
upstream = ['clean-2']
product = None
# -

# +
df = pd.read_csv(upstream['clean-2']['data'])
grouped = df.groupby('sex')[['age', 'hours-per-week']].mean()
grouped.columns = ['Mean age', 'Mean hours per week worked']
grouped.head()
# -

# +
# some plotting code...
# -
