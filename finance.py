import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from utils import pr
start = "2022-01-01"
end = "2022-01-31"

# symbol = ["BA", "MSFT", "^DJI", "EURUSD=X", "GC=F", "BTC-USD"]
symbol = ["RELIANCE.NS"]
df = yf.download(symbol, start=start, end=end)

# df.loc[:, ("Close", "BA")]

# df = df.swaplevel(axis="columns").sort_index(axis="columns")

close = df.Close.copy()
# close.dropna().plot(figsize=(15, 8), fontsize=13)
# plt.legend(fontsize=13)
# plt.show()
# pr(close.describe())
# close.BA.div(close.iloc[0,0]).mul(100)
norm = close.dropna().div(close.iloc[0,0]).mul(100)
pr(df)
