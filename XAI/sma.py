from client import Client, get_client
from binance.enums import *
import pandas as pd
import pandas_ta
import time
from _utils.const import meme_coins

# Binance API keys (replace with your own keys)
api_key = 'your_api_key'
api_secret = 'your_api_secret'

# Initialize Binance client
# client = Client(api_key, api_secret)
client = get_client(testnet=True)

# Configuration
symbol = 'BTCUSDT'  # Trading pair
quantity = 0.001  # Amount to trade (adjust based on your USDT value)
interval = Client.KLINE_INTERVAL_1MINUTE

def fetch_klines(symbol, interval, limit=100):
    klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
    df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['close'] = df['close'].astype(float)
    return df

def get_signal(df):
    # Using Simple Moving Averages for signals
    sma_short = pandas_ta.sma(df['close'], length=5)
    sma_long = pandas_ta.sma(df['close'], length=20)
    
    if sma_short.iloc[-1] > sma_long.iloc[-1] and sma_short.iloc[-2] <= sma_long.iloc[-2]:
        return 'BUY'
    elif sma_short.iloc[-1] < sma_long.iloc[-1] and sma_short.iloc[-2] >= sma_long.iloc[-2]:
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
        for symbol in meme_coins:
            df = fetch_klines(symbol, interval)
            signal = get_signal(df)
            
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