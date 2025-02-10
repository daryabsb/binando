from binance.client import Client
import math
import pandas as pd
import time
import ta  # Technical Analysis Library
from BinanceKeys import test_api_key, test_secret_key
from binance.enums import *
from symbols import SYMBOLS

API_KEY = test_api_key
API_SECRET = test_secret_key
# client = Client(API_KEY, API_SECRET)
client = Client(API_KEY, API_SECRET, tld='com', testnet=True)

# Get Binance server time and adjust
server_time = client.get_server_time()['serverTime']
system_time = int(time.time() * 1000)
time_offset = server_time - system_time

# Set the timestamp offset manually
client.timestamp_offset = time_offset


# List of meme coin symbols to trade
meme_coins = SYMBOLS

# Trade settings
TRADE_ALLOCATION_PERCENTAGE = 0.10  # 10% of total USDT balance
PRICE_CHANGE_THRESHOLD = 0.015  # 1.5% threshold for buy/sell
MINIMUM_TRADE_AMOUNT = 10  # Minimum order amount in USDT to cover fees


def get_usdt_balance():
    """Retrieve the available USDT balance."""
    balance = client.get_asset_balance(asset="USDT")
    return float(balance["free"])


def get_price(symbol):
    """Get the current price of a symbol."""
    ticker = client.get_symbol_ticker(symbol=symbol)
    return float(ticker["price"])


def get_previous_hour_price(symbol):
    """Get the price of a symbol one hour ago using historical klines."""
    klines = client.get_klines(
        symbol=symbol, interval=Client.KLINE_INTERVAL_1HOUR, limit=2)
    return float(klines[0][4])  # Closing price of the previous hour


def place_order(symbol, side, quantity):
    """Place a market order (buy/sell)."""
    try:
        order = client.order_market(
            symbol=symbol,
            side=side,
            quantity=quantity
        )
        print(f"✅ {side.upper()} Order placed for {symbol}: {quantity}")
    except Exception as e:
        print(f"❌ Error placing {side} order for {symbol}: {str(e)}")


def calculate_quantity(symbol, amount):
    """Calculate the quantity of a coin to buy/sell based on USDT amount."""
    price = get_price(symbol)
    quantity = amount / price
    # Rounds down to 3 decimal places
    return math.floor(quantity * 1000) / 1000


def execute_strategy():
    """Monitor and execute the trading strategy."""
    usdt_balance = get_usdt_balance()
    trade_amount = usdt_balance * TRADE_ALLOCATION_PERCENTAGE

    if trade_amount < MINIMUM_TRADE_AMOUNT:
        print("⚠️ Not enough USDT allocated for trading.")
        return

    for symbol in meme_coins:
        current_price = get_price(symbol)
        previous_price = get_previous_hour_price(symbol)

        price_change = (current_price - previous_price) / previous_price

        if price_change >= PRICE_CHANGE_THRESHOLD:  # Uptrend → SELL
            print(f"📈 {symbol} is UP {price_change:.2%}. Selling...")
            quantity = calculate_quantity(symbol, trade_amount)
            place_order(symbol, SIDE_SELL, quantity)

        elif price_change <= -PRICE_CHANGE_THRESHOLD:  # Downtrend → BUY
            print(f"📉 {symbol} is DOWN {price_change:.2%}. Buying...")
            quantity = calculate_quantity(symbol, trade_amount)
            place_order(symbol, SIDE_BUY, quantity)

        else:
            print(f"🔍 {symbol}: No trade (change: {price_change:.2%})")


# Run the strategy every hour
while True:
    execute_strategy()
    print("⏳ Waiting 1 hour before checking again...")
    time.sleep(3600)
