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

# order = client.create_order(symbol= 'DOGEUSDT', side= 'BUY', type= 'MARKET', quantity= 100)
pr(client.get_all_orders(symbol = 'DOGEUSDT'))
# df = get_history(symbol = "DOGEUSDT", interval = "1h", start = str(baghdad_time_last_night), end = str(baghdad_time))

# while True:
#     # initialize and start the WebSocket
#     twm.start()
#     twm.start_symbol_miniticker_socket(callback = stream_data, symbol = "BTCUSDT")
#     sleep(5)
#     twm.stop()

{
    'symbol': 'DOGEUSDT', 
    'orderId': 3763678, 
    'orderListId': -1, 
    'clientOrderId': 'x-HNA2TXFJf2361752f4838f1a251aa', 
    'transactTime': 1738662437733, 
    'price': '0.00000000', 
    'origQty': '100.00000000', 
    'executedQty': '100.00000000', 
    'origQuoteOrderQty': '0.00000000', 
    'cummulativeQuoteQty': '26.40900000', 
    'status': 'FILLED', 
    'timeInForce': 'GTC', 
    'type': 'MARKET', 
    'side': 'BUY', 
    'workingTime': 1738662437733, 
    'fills': [
        {
            'price': '0.26409000', 
            'qty': '100.00000000', 
            'commission': '0.00000000', 
            'commissionAsset': 'DOGE', 
            'tradeId': 1155386
            }
        ], 
    'selfTradePreventionMode': 'EXPIRE_MAKER'
}