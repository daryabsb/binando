from binance.client import Client
import pandas as pd
import time
import ta  # Technical Analysis Library
# from BinanceKeys import test_api_key, test_secret_key


API_KEY = 'test_api_key'
API_SECRET = 'test_secret_key'
client = Client(API_KEY, API_SECRET)

# -------------------------------
# GLOBAL PARAMETERS & SETTINGS
# -------------------------------

# List of symbols you want to trade (e.g., meme coins/altcoins)
SYMBOLS = [
    "DOGEUSDT",
    "SHIBUSDT",
    "PEPEUSDT",
    "XRPUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "BERAUSDT",
    "BNBUSDT",
    "TRUMPUSDT",
    # Add more symbols as desired...
]

# Technical strategy parameters
BUY_PERCENT = 0.01       # Grid: Buy when price drops 1%
SELL_PERCENT = 0.015     # Grid: Sell when price is 1.5% above buy price
RSI_THRESHOLD = 30       # Only buy when RSI is below 30 (oversold)
SELL_RSI_THRESHOLD = 70  # Only sell when RSI is above 70 (overbought)
MACD_CONFIRMATION = True  # Only buy if MACD > MACD signal; sell if MACD < signal
VOLUME_THRESHOLD = 1.2   # Volume must be 20% above its 20-period moving average

# Wallet & allocation parameters
INITIAL_WALLET = 100.0          # Your total USDT wallet (set this manually)
MAX_SPEND_PERCENT = 0.25         # Use only 25% of your wallet on trades
ALLOWED_ALLOCATION = INITIAL_WALLET * \
    MAX_SPEND_PERCENT  # e.g., 250 USDT maximum allocated
TRADE_USDT_AMOUNT = 10.0         # Each trade will use 10 USDT

# Grid settings: how many levels per symbol
GRID_LEVELS = 5

# -------------------------------
# IN-MEMORY STATE TRACKING
# -------------------------------
# For each symbol we hold a grid with buy/sell levels.
grid = {}

# For each symbol we keep a list of open positions.
# Each position is a dictionary with: buy_price, quantity, USDT cost, and target sell_level.
open_positions = {}

# -------------------------------
# HELPER FUNCTIONS
# -------------------------------


def get_historical_data(symbol, interval="15m", lookback="1 hour ago UTC"):
    """
    Fetch recent klines (candlestick data) for indicator calculations.
    """
    try:
        klines = client.get_historical_klines(symbol, interval, lookback)
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'trades',
            'taker_base_volume', 'taker_quote_volume', 'ignore'
        ])
        df["close"] = df["close"].astype(float)
        df["volume"] = df["volume"].astype(float)
        return df
    except Exception as e:
        print(f"Error fetching historical data for {symbol}: {e}")
        return None


def calculate_indicators(symbol):
    """
    Calculate technical indicators (RSI, MACD, volume strength) for the given symbol.
    """
    df = get_historical_data(symbol)
    if df is None or df.empty:
        return None

    # Calculate RSI
    rsi_series = ta.momentum.RSIIndicator(df["close"], window=14).rsi()
    rsi = rsi_series.iloc[-1]

    # Calculate MACD and its signal line
    macd_indicator = ta.trend.MACD(df["close"])
    macd = macd_indicator.macd().iloc[-1]
    macd_signal = macd_indicator.macd_signal().iloc[-1]

    # Volume analysis: compare the last volume with the rolling 20-period average
    if len(df["volume"]) >= 20:
        volume_avg = df["volume"].rolling(window=20).mean().iloc[-1]
    else:
        volume_avg = df["volume"].mean()
    last_volume = df["volume"].iloc[-1]
    volume_strong = last_volume > (volume_avg * VOLUME_THRESHOLD)

    return {
        "rsi": rsi,
        "macd": macd,
        "macd_signal": macd_signal,
        "volume_strong": volume_strong
    }


def should_buy(symbol, current_price):
    """
    Returns True if the indicators support a buy.
    """
    indicators = calculate_indicators(symbol)
    if indicators is None:
        return False

    # Check oversold condition
    if indicators["rsi"] >= RSI_THRESHOLD:
        print(
            f"{symbol}: RSI {indicators['rsi']:.2f} is not below threshold {RSI_THRESHOLD}.")
        return False

    # Check for bullish MACD (if enabled)
    if MACD_CONFIRMATION and indicators["macd"] <= indicators["macd_signal"]:
        print(
            f"{symbol}: MACD {indicators['macd']:.4f} is not above signal {indicators['macd_signal']:.4f}.")
        return False

    # Check for strong volume
    if not indicators["volume_strong"]:
        print(f"{symbol}: Volume condition not met.")
        return False

    return True


def should_sell(symbol, current_price, buy_price):
    """
    Returns True if conditions are met to exit (sell) a position.
    """
    indicators = calculate_indicators(symbol)
    if indicators is None:
        return False

    # For selling, you might want to wait until the asset is overbought
    if indicators["rsi"] <= SELL_RSI_THRESHOLD:
        print(
            f"{symbol}: RSI {indicators['rsi']:.2f} is not above sell threshold {SELL_RSI_THRESHOLD}.")
        return False

    # Confirm a bearish MACD for selling (if enabled)
    if MACD_CONFIRMATION and indicators["macd"] >= indicators["macd_signal"]:
        print(
            f"{symbol}: MACD {indicators['macd']:.4f} is not below signal {indicators['macd_signal']:.4f} for selling.")
        return False

    # Ensure the price has moved at least the desired profit margin
    target_sell_price = buy_price * (1 + SELL_PERCENT)
    if current_price < target_sell_price:
        print(f"{symbol}: Current price {current_price:.4f} has not reached target sell price {target_sell_price:.4f}.")
        return False

    return True


def get_total_allocation():
    """
    Calculate the total USDT cost of open positions.
    """
    total = 0.0
    for symbol, positions in open_positions.items():
        for pos in positions:
            total += pos["usdt_cost"]
    return total


def initialize_grid():
    """
    For each symbol, set up grid levels for buy and sell orders.
    """
    for symbol in SYMBOLS:
        try:
            current_price = float(
                client.get_symbol_ticker(symbol=symbol)["price"])
            # Create a grid of buy levels (each level is 1% lower than the previous)
            buy_levels = [current_price * (1 - BUY_PERCENT * i)
                          for i in range(1, GRID_LEVELS + 1)]
            # For each buy level, define a target sell price 1.5% above the buy level
            sell_levels = [bp * (1 + SELL_PERCENT) for bp in buy_levels]
            grid[symbol] = {"buy_levels": buy_levels,
                            "sell_levels": sell_levels}
            open_positions[symbol] = []
            print(f"Initialized grid for {symbol}:")
            print(f"  Buy levels:  {buy_levels}")
            print(f"  Sell levels: {sell_levels}")
        except Exception as e:
            print(f"Error initializing grid for {symbol}: {e}")

# -------------------------------
# TRADING BOT MAIN LOOP
# -------------------------------


def trading_bot():
    """
    Main trading loop: For each symbol in the list, check if the current price has hit any grid level.
    If conditions are met (via RSI, MACD, and volume), then place a simulated buy order—
    provided that the total USDT allocated does not exceed the allowed allocation.

    Similarly, if a symbol’s current price reaches the target sell level for an open position and
    the exit conditions are met, then place a simulated sell order.
    """
    initialize_grid()
    while True:
        for symbol in SYMBOLS:
            try:
                current_price = float(
                    client.get_symbol_ticker(symbol=symbol)["price"])
                # print(f"\n{symbol}: Current Price: {current_price:.4f}")
                print(f"{symbol}: Current Price: {current_price:.12f}")

                # ---------------
                # BUY LOGIC:
                # ---------------
                # For each grid level that is still “open” (not yet executed)
                for i, buy_level in enumerate(grid[symbol]["buy_levels"]):
                    if buy_level is not None and current_price <= buy_level:
                        print(
                            f"{symbol}: Price {current_price:.4f} <= grid buy level {buy_level:.4f}")
                        if should_buy(symbol, current_price):
                            current_allocation = get_total_allocation()
                            if current_allocation + TRADE_USDT_AMOUNT <= ALLOWED_ALLOCATION:
                                quantity = TRADE_USDT_AMOUNT / current_price
                                # To actually trade, uncomment the API call below:
                                # client.order_market_buy(symbol=symbol, quantity=quantity)
                                print(
                                    f"Placing BUY order for {symbol} at {current_price:.4f} for {quantity:.6f} units (USDT {TRADE_USDT_AMOUNT}).")
                                # Record the open position (we track the USDT cost, buy price, and target sell level)
                                position = {
                                    "buy_price": current_price,
                                    "quantity": quantity,
                                    "usdt_cost": TRADE_USDT_AMOUNT,
                                    "sell_level": grid[symbol]["sell_levels"][i]
                                }
                                open_positions[symbol].append(position)
                                # Mark this grid level as executed (so we don’t trigger it again)
                                grid[symbol]["buy_levels"][i] = None
                            else:
                                print(
                                    f"Allocation limit reached for {symbol}. Current allocation: {current_allocation:.2f} USDT, Allowed: {ALLOWED_ALLOCATION:.2f} USDT.")

                # ---------------
                # SELL LOGIC:
                # ---------------
                # For each open position for this symbol, check if current price meets the sell condition.
                for pos in open_positions[symbol][:]:
                    if current_price >= pos["sell_level"]:
                        print(
                            f"{symbol}: Price {current_price:.4f} reached target sell level {pos['sell_level']:.4f} for position bought at {pos['buy_price']:.4f}.")
                        if should_sell(symbol, current_price, pos["buy_price"]):
                            # To actually trade, uncomment the API call below:
                            # client.order_market_sell(symbol=symbol, quantity=pos["quantity"])
                            print(
                                f"Placing SELL order for {symbol} at {current_price:.4f} for {pos['quantity']:.6f} units.")
                            open_positions[symbol].remove(pos)
                # ---------------------------------
                # (Optional) You can also implement stop-loss logic here.
                # ---------------------------------

            except Exception as e:
                print(f"Error in trading loop for {symbol}: {e}")
        # Wait a short time before checking all symbols again
        print(f"------------------------------")
        print(f"==============================")
        time.sleep(5)


if __name__ == "__main__":
    trading_bot()
