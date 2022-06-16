"""
Clean raw data
"""
import pandas as pd

# + tags=["parameters"]
upstream = ['raw']
product = None
# -

# +
df = pd.read_csv(upstream['clean-1']['data'])
df['race'] = df.race.str.strip()
# -

# +
df.to_csv(str(product['data']), index=False)
# -
