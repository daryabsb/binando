from decimal import Decimal, ROUND_DOWN
from binance.client import Client
import math
import pandas as pd
import time
import ta  # Technical Analysis Library
from XAI.BinanceKeys import test_api_key, test_secret_key, api_key, secret_key
from binance.enums import *
from XAI.symbols import SYMBOLS, MEME_COINS, get_percentage_options, get_history_options

API_KEY = api_key
API_SECRET = secret_key
# client = Client(API_KEY, API_SECRET)
# client = Client(API_KEY, API_SECRET, tld='com', testnet=True)
client = Client(API_KEY, API_SECRET, tld='com')

# Get Binance server time and adjust
server_time = client.get_server_time()['serverTime']
system_time = int(time.time() * 1000)
time_offset = server_time - system_time

# Set the timestamp offset manually
client.timestamp_offset = time_offset


# List of meme coin symbols to trade
meme_coins = MEME_COINS

# Trade settings
TRADE_ALLOCATION_PERCENTAGE = 1  # 0.10  # 10% of total USDT balance
MAX_TRADE_PERCENTAGE = Decimal(0.25)  # Max 25% of coin balance per trade

# PRICE_CHANGE_THRESHOLD = 0.015  # 1.5% threshold for buy/sell
PRICE_CHANGE_THRESHOLD = get_percentage_options(
    "5%")  # 1.5% threshold for buy/sell
MINIMUM_TRADE_AMOUNT = 5  # Minimum order amount in USDT to cover fees

# Store last trade price per symbol
LAST_TRADE = {}


def should_trade(symbol, current_price, trade_type, threshold):
    """
    Check if we should place a trade based on price movement and prevent repeated trades.
    """
    last_price = LAST_TRADE.get(symbol, None)

    if last_price is None:
        LAST_TRADE[symbol] = current_price  # Initialize tracking
        return True  # Allow first trade

    price_change = (current_price - last_price) / last_price

    if trade_type == "BUY" and price_change <= -threshold:
        LAST_TRADE[symbol] = current_price  # Update last trade price
        return True
    elif trade_type == "SELL" and price_change >= threshold:
        LAST_TRADE[symbol] = current_price  # Update last trade price
        return True

    return False  # No trade if conditions are not met


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
    selected_interval = get_history_options("1_day")
    klines = client.get_klines(
        symbol=symbol, interval=selected_interval, limit=2)
    return float(klines[0][4])  # Closing price of the previous hour


def get_step_size_and_min_qty(symbol):
    """Retrieve the step size and minimum quantity for a given symbol."""
    exchange_info = client.get_symbol_info(symbol)

    step_size = min_qty = None
    for f in exchange_info["filters"]:
        if f["filterType"] == "LOT_SIZE":
            step_size = Decimal(f["stepSize"])
            min_qty = Decimal(f["minQty"])

    return step_size, min_qty


def get_coin_balance(symbol):
    """Retrieve the available balance for a specific coin."""
    asset = symbol.replace("USDT", "")  # Extract asset name
    balance = client.get_asset_balance(asset=asset)
    return Decimal(balance["free"])


def calculate_quantity(symbol, amount):
    """Calculate the correct quantity based on Binance precision rules."""
    price = Decimal(get_price(symbol))
    step_size, min_qty = get_step_size_and_min_qty(symbol)

    if not step_size or not min_qty:
        print(f"⚠️ Error fetching step size or minQty for {symbol}.")
        return None

    available_balance = get_coin_balance(symbol)
    max_trade_amount = available_balance * MAX_TRADE_PERCENTAGE  # Limit trade size

    # Limit by max % balance
    raw_quantity = min(Decimal(amount) / price, max_trade_amount)
    quantity = (raw_quantity // step_size) * step_size  # Adjust to step size

    if quantity < min_qty:
        print(f"⚠️ {symbol} Order too small ({quantity} < {min_qty}), skipping.")
        return None

    return str(quantity)  # Convert to string to avoid precision issues


def place_order(symbol, side, quantity):
    """Place a market order (buy/sell) with balance validation."""
    if not quantity:
        return  # Skip order if quantity is None

    balance = client.get_asset_balance(asset=symbol.replace("USDT", ""))
    available_balance = Decimal(balance["free"])

    if side == SIDE_SELL and available_balance < Decimal(quantity):
        print(
            f"❌ Insufficient balance for {symbol} ({available_balance} < {quantity}).")
        return

    try:
        order = client.order_market(
            symbol=symbol, side=side, quantity=quantity)
        print(f"✅ {side.upper()} Order placed for {symbol}: {quantity}")
    except Exception as e:
        print(f"❌ Error placing {side} order for {symbol}: {str(e)}")


def execute_strategy():
    """Monitor and execute the trading strategy while preventing duplicate trades."""
    usdt_balance = get_usdt_balance()
    trade_amount = usdt_balance * TRADE_ALLOCATION_PERCENTAGE
    # Get available balance before selling

    if trade_amount < MINIMUM_TRADE_AMOUNT:
        print("⚠️ Not enough USDT allocated for trading.")
        return

    for symbol in meme_coins:
        coin_balance = get_coin_balance(symbol)

        current_price = get_price(symbol)
        previous_price = get_previous_hour_price(symbol)

        price_change = (current_price - previous_price) / previous_price

        if should_trade(symbol, current_price, "BUY", PRICE_CHANGE_THRESHOLD):  # Downtrend → BUY
            print(f"📉 {symbol} is DOWN {price_change:.2%}. Buying...")
            quantity = calculate_quantity(symbol, trade_amount)
            place_order(symbol, SIDE_BUY, quantity)

        elif should_trade(symbol, current_price, "SELL", PRICE_CHANGE_THRESHOLD):  # Uptrend → SELL
            if coin_balance == 0:
                print(
                    f"❌ Insufficient balance for {symbol}. Skipping sell order.")
                continue

            print(f"📈 {symbol} is UP {price_change:.2%}. Selling...")
            quantity = calculate_quantity(symbol, trade_amount)
            if quantity is None or Decimal(quantity) > coin_balance:
                continue

            place_order(symbol, SIDE_SELL, quantity)

        else:
            print(f"🔍 {symbol}: No trade (change: {price_change:.2%})")


# Run the strategy every hour
while True:
    execute_strategy()
    print("⏳ Waiting 1 hour before checking again...")
    time.sleep(3600)
