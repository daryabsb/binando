from binance.client import Client
from BinanceKeys import api_key, secret_key
import time
import pandas as pd

client = Client(api_key, secret_key, tld='com')


# Get Binance server time and adjust
server_time = client.get_server_time()['serverTime']
system_time = int(time.time() * 1000)
time_offset = server_time - system_time

# Set the timestamp offset manually
client.timestamp_offset = time_offset

account = client.get_account(recvWindow=5000)

# print(client.ping())

# for asset in account['balances']:
#     if float(asset['free']) > 0 or float(asset['locked']) > 0:
#         print(f"asset: {asset['asset']}, free: {asset['free']}, locked: {asset['locked']}")

# print(account['updateTime'])
# print(pd.to_datetime(account['updateTime'], unit='ms'))

# print(account['balances'])
# df = pd.DataFrame(account['balances'])
# print(df.loc[df['free'].astype(float) > 0])


# print(client.get_asset_balance(asset='DOGE'))
# print(client.get_asset_balance(asset='TRUMP'))

# snap = client.get_account_snapshot(type='SPOT', recvWindow=5000)
# print(pd.json_normalize(snap['snapshotVos']))
# get current prices for all pairs
timestamp = client._get_earliest_valid_timestamp(symbol = "BTCUSDT", interval = "1d")
bars = client.get_historical_klines(symbol = "BTCUSDT",
                                    interval = "1d", start_str = timestamp, limit = 1000)

df = pd.DataFrame(bars)
df["Date"] = pd.to_datetime(df.iloc[:,0], unit = "ms")
df.columns = ["Open Time", "Open", "High", "Low", "Close",
              "Volume", "Clos Time", "Quote Asset Volume", 
              "Number of Trades", "Taker Buy Base Asset Volume",
              "Taker Buy Quote Asset Volume", "Ignore", "Date" ]
df = df[["Date", "Open", "High", "Low", "Close", "Volume"]].copy()

df.set_index("Date", inplace = True)


def pr(command):
    print(command)


for column in df.columns:
    df[column] = pd.to_numeric(df[column], errors = "coerce")
    
pr(df) # current price for one symbol





{
    'code': 200, 'msg': '', 
    'snapshotVos': [
        {
            'type': 'spot', 'updateTime': 1737849599000, 
            'data': {
                'totalAssetOfBtc': '0.0021029', 
                'balances': [
                    {'asset': 'DOGE', 'free': '142.6250199', 'locked': '0'}, 
                    {'asset': 'LDANIME', 'free': '175.77017972', 'locked': '0'}, 
                    {'asset': 'TRUMP', 'free': '4.57935605', 'locked': '0'}, 
                    {'asset': 'USDT', 'free': '37.57119794', 'locked': '0'}
                        ]
                    }
        }, 
        {
            'type': 'spot', 'updateTime': 1737935999000, 
            'data': {
                'totalAssetOfBtc': '0.00184712',
                'balances': [
                    {'asset': 'DOGE', 'free': '142.6250199', 'locked': '0'}, 
                    {'asset': 'LDANIME', 'free': '175.77017972', 'locked': '0'}, 
                    {'asset': 'STPT', 'free': '412.16352815', 'locked': '0'}, 
                    {'asset': 'TRUMP', 'free': '3.07935605', 'locked': '0'}, 
                    {'asset': 'USDT', 'free': '17.57119794', 'locked': '0'}
                        ]
                    }
        }, 
        {
            'type': 'spot', 'updateTime': 1738022399000, 
            'data': {
                'totalAssetOfBtc': '0.00183376', 
                'balances': [
                    {'asset': 'ACH', 'free': '947.40425753', 'locked': '0'},
                    {'asset': 'DOGE', 'free': '142.6250199', 'locked': '0'},
                    {'asset': 'LDANIME', 'free': '175.77017972', 'locked': '0'}, 
                    {'asset': 'TRUMP', 'free': '3.07935605', 'locked': '0'}, 
                    {'asset': 'USDT', 'free': '17.57119794', 'locked': '0'}
                        ]
                    }
        }, 
        {
            'type': 'spot', 'updateTime': 1738108799000, 
            'data': {
                'totalAssetOfBtc': '0.00184375', 
                'balances': [
                    {'asset': 'ANIME', 'free': '0.03815255', 'locked': '0'}, 
                    {'asset': 'DOGE', 'free': '281.97395088', 'locked': '0'}, 
                    {'asset': 'TRUMP', 'free': '1.07935605', 'locked': '0'}, 
                    {'asset': 'USDT', 'free': '67.30914031', 'locked': '0'}
                        ]
                    }
        }, 
        {
            'type': 'spot', 'updateTime': 1738195199000, 
            'data': {
                'totalAssetOfBtc': '0.00184813', 
                'balances': [
                    {'asset': 'ANIME', 'free': '0.03815255', 'locked': '0'}, 
                    {'asset': 'DEXE', 'free': '2', 'locked': '0'}, 
                    {'asset': 'DOGE', 'free': '281.97395088', 'locked': '0'}, 
                    {'asset': 'TRUMP', 'free': '1.07935605', 'locked': '0'}, 
                    {'asset': 'USDT', 'free': '38.6796161', 'locked': '0'}
                        ]
                    }
        }, 
        {
            'type': 'spot', 'updateTime': 1738281599000, 
            'data': {
                'totalAssetOfBtc': '0.00193049', 
                'balances': [
                    {'asset': 'ANIME', 'free': '0.03815255', 'locked': '0'}, 
                    {'asset': 'DEXE', 'free': '2', 'locked': '0'}, 
                    {'asset': 'DOGE', 'free': '281.97395088', 'locked': '0'}, 
                    {'asset': 'TRUMP', 'free': '1.07935605', 'locked': '0'}, 
                    {'asset': 'USDT', 'free': '38.6796161', 'locked': '0'}
                        ]
                    }
        }, 
        {
            'type': 'spot', 'updateTime': 1738367999000, 
            'data': {
                'totalAssetOfBtc': '0.00195706', 
                'balances': [
                    {'asset': 'ANIME', 'free': '0.03815255', 'locked': '0'}, 
                    {'asset': 'DEXE', 'free': '2', 'locked': '0'}, 
                    {'asset': 'DOGE', 'free': '312.51362523', 'locked': '0'}, 
                    {'asset': 'TRUMP', 'free': '1.07935605', 'locked': '0'}, 
                    {'asset': 'USDT', 'free': '28.6796161', 'locked': '0'}
                        ]
                    }
        }
    ]
}