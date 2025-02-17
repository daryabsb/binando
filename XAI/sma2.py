from binance.client import Client
from binance.enums import *
import talib
import numpy as np
import time

# Binance API keys (replace with your own keys)
api_key = 'your_api_key'
api_secret = 'your_api_secret'

# Initialize Binance client
client = Client(api_key, api_secret)

# Configuration
symbol = 'BTCUSDT'  # Trading pair
quantity = 0.001  # Amount to trade (adjust based on your USDT value)
interval = Client.KLINE_INTERVAL_1MINUTE

def fetch_klines(symbol, interval, limit=100):
    klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
    return np.array(klines, dtype=float)

def get_signal(klines):
    # Using simple moving averages for signals
    close = klines[:, 4]
    sma_short = talib.SMA(close, timeperiod=5)
    sma_long = talib.SMA(close, timeperiod=20)
    
    if sma_short[-1] > sma_long[-1] and sma_short[-2] <= sma_long[-2]:
        return 'BUY'
    elif sma_short[-1] < sma_long[-1] and sma_short[-2] >= sma_long[-2]:
        return 'SELL'
    return 'HOLD'

def execute_trade(symbol, side, quantity):
    try:
        order = client.create_order(
            symbol=symbol,
            side=side,
            type=ORDER_TYPE_MARKET,
            quantity=quantity
        )
        print(f"Executed {side} order for {symbol}")
        return order
    except Exception as e:
        print(f"An error occurred - {e}")
        return None

def main():
    while True:
        klines = fetch_klines(symbol, interval)
        signal = get_signal(klines)
        
        if signal == 'BUY':
            execute_trade(symbol, SIDE_BUY, quantity)
            print("BUY Signal logged")
        elif signal == 'SELL':
            execute_trade(symbol, SIDE_SELL, quantity)
            print("SELL Signal logged")
        else:
            print("HOLD Signal logged")
        
        time.sleep(60)  # Wait for one minute before next check

if __name__ == "__main__":
    main()