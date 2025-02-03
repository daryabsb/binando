from binance.client import Client
from binance import ThreadedWebsocketManager
import pandas as pd
from BinanceKeys import test_api_key, test_secret_key
import time
from utils import get_history, pr, stream_data, stream_candles
from time import sleep
from datetime import datetime, timedelta
# client = Client(api_key, secret_key, tld='com')
twm = ThreadedWebsocketManager()

now = datetime.utcnow()
baghdad_time = now + timedelta(hours = 3)
baghdad_time_last_night = baghdad_time - timedelta(hours = 13)


client = Client(test_api_key, test_secret_key, tld='com', testnet=True)


# Get Binance server time and adjust
server_time = client.get_server_time()['serverTime']
system_time = int(time.time() * 1000)
time_offset = server_time - system_time

# Set the timestamp offset manually
client.timestamp_offset = time_offset

account = client.get_account(recvWindow=5000)

# df = get_history(symbol = "DOGEUSDT", interval = "1h", start = str(baghdad_time_last_night), end = str(baghdad_time))

pr(account)