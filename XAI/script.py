from binance.client import Client
from binance import ThreadedWebsocketManager
import pandas as pd
from XAI.BinanceKeys import api_key, secret_key
import time
from time import sleep
from datetime import datetime, timedelta
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
timestamp = client._get_earliest_valid_timestamp(
    symbol="BTCUSDT", interval="1d")
bars = client.get_historical_klines(symbol="BTCUSDT",
                                    interval="1d", start_str=timestamp, limit=1000)

df = pd.DataFrame(bars)
df["Date"] = pd.to_datetime(df.iloc[:, 0], unit="ms")
df.columns = ["Open Time", "Open", "High", "Low", "Close",
              "Volume", "Clos Time", "Quote Asset Volume",
              "Number of Trades", "Taker Buy Base Asset Volume",
              "Taker Buy Quote Asset Volume", "Ignore", "Date"]

df = df[["Date", "Open", "High", "Low", "Close", "Volume"]].copy()

df.set_index("Date", inplace=True)

# valid intervals - 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M


def get_history(symbol, interval, start, end=None):
    bars = client.get_historical_klines(symbol=symbol, interval=interval,
                                        start_str=start, end_str=end, limit=1000)
    df = pd.DataFrame(bars)
    df["Date"] = pd.to_datetime(df.iloc[:, 0], unit="ms")
    df.columns = ["Open Time", "Open", "High", "Low", "Close", "Volume",
                  "Clos Time", "Quote Asset Volume", "Number of Trades",
                  "Taker Buy Base Asset Volume", "Taker Buy Quote Asset Volume", "Ignore", "Date"]
    df = df[["Date", "Open", "High", "Low", "Close", "Volume"]].copy()
    df.set_index("Date", inplace=True)
    for column in df.columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    return df


def pr(command):
    print(command)


# for column in df.columns:
#     df[column] = pd.to_numeric(df[column], errors = "coerce")

# df = get_history(symbol = "BTCUSDT", interval = "1d", start = timestamp)

# pr(df) # current price for one symbol
now = datetime.utcnow()
baghdad_time = now + timedelta(hours=3)
baghdad_time_last_night = baghdad_time - timedelta(hours=13)

df = get_history(symbol="DOGEUSDT", interval="1h", start=str(
    baghdad_time_last_night), end=str(baghdad_time))


def stream_data(msg):
    print(msg)


def stream_candles(msg):
    ''' define how to process incoming WebSocket messages '''
    # extract the required items from msg
    event_time = pd.to_datetime(msg["E"], unit="ms")
    start_time = pd.to_datetime(msg["k"]["t"], unit="ms")
    first = float(msg["k"]["o"])
    high = float(msg["k"]["h"])
    low = float(msg["k"]["l"])
    close = float(msg["k"]["c"])
    volume = float(msg["k"]["v"])
    complete = msg["k"]["x"]

    # print out
    print("Time: {} | Price: {}".format(event_time, close))

    # feed df (add new bar / update latest bar)
    df.loc[start_time] = [first, high, low, close, volume, complete]


# pr(baghdad_time) # current price for one symbol
# pr(baghdad_time_last_night) # current price for one symbol
# pr(df) # current price for one symbol
{'e': '24hrMiniTicker', 'E': 1738579230921, 's': 'DOGEUSDT', 'c':
 '0.25808000', 'o': '0.29872000', 'h': '0.30165000', 'l': '0.20178000', 'v': '7391014564.00000000', 'q': '1870145086.53592000'}
twm = ThreadedWebsocketManager()
{
    'e': '24hrMiniTicker',
    'E': 1738502987558,
    's': 'DOGEUSDT',
    'c': '0.29401000',
    'o': '0.32444000',
    'h': '0.32447000',
    'l': '0.28848000',
    'v': '1718375686.00000000',
    'q': '523393611.91487000'
}

{
    'e': 'kline',
    'E': 1738579434020,
    's': 'BTCUSDT',
    'k': {
        't': 1738579380000,
        'T': 1738579439999,
        's': 'BTCUSDT',
        'i': '1m',
        'f': 4511674996,
        'L': 4511679783,
        'o': '95239.15000000',
        'c': '95284.32000000',
        'h': '95339.31000000',
        'l': '95239.15000000',
        'v': '29.69850000',
        'n': 4788,
        'x': False,
        'q': '2830608.39831130',
        'V': '4.05544000',
        'Q': '386475.11794980',
        'B': '0'
    }
}

# df = pd.DataFrame(columns = ["Open", "High", "Low", "Close", "Volume", "Complete"])

# stop = True

# if stop is True:
#     twm.start()
#     # twm.start_symbol_miniticker_socket(callback = stream_data, symbol = "DOGEUSDT")
#     twm.start_kline_socket(callback = stream_candles, symbol = "BTCUSDT", interval = "1m")
#     sleep(20)
#     stop = False
# else:
#     twm.stop()

order = client.create_test_order(
    symbol="DOGEUSDT", side="BUY", type="MARKET", quantity=10)

pr(f'order: {order}')

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
