"""
Clean raw data
"""

import pandas as pd

# + tags=["parameters"]
upstream = ["raw"]
product = None
# -

# +
df = pd.read_csv(upstream["raw"]["data"])
df["sex"] = df.sex.str.strip()
# -

# +
df.to_csv(str(product["data"]), index=False)
# -
