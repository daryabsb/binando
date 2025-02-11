import time
from binance.client import Client
from BinanceKeys import test_api_key, test_secret_key, api_key, secret_key

def get_client(testnet=False):
    API_KEY = test_api_key if testnet else api_key
    API_SECRET = test_secret_key if testnet else secret_key
    client = Client(API_KEY, API_SECRET, tld='com', testnet=testnet)

    # Get Binance server time and adjust
    server_time = client.get_server_time()['serverTime']
    system_time = int(time.time() * 1000)
    time_offset = server_time - system_time

    # Set the timestamp offset manually
    client.timestamp_offset = time_offset
    return client