from datetime import datetime  # Import datetime module
from binance.client import Client
import pandas as pd
import time
import ta  # Technical Analysis Library
from XAI.BinanceKeys import test_api_key, test_secret_key
from XAI.symbols import SYMBOLS

from XAI.utils import format_quantity

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

# -------------------------------
# GLOBAL PARAMETERS & SETTINGS
# -------------------------------

# ================================
# Global Constants and Settings
# ================================
RSI_BUY_THRESHOLD = 40.0     # Lower threshold to trigger buys
RSI_SELL_THRESHOLD = 60.0    # Upper threshold to trigger sells
MACD_CONFIRMATION = True     # Require MACD condition?
TRADE_USDT_AMOUNT = 100.0      # USDT amount used per trade (adjust as desired)
TOLERANCE_FACTOR = 0.1       # Fraction of grid spacing used as tolerance


DURATION_MINUTES = 1200        # Run duration in minutes (change as needed)

# ================================
# Helper Functions
# ================================


def calculate_grid_levels(support, resistance, levels=5):
    """
    Divide the range between support and resistance into grid levels.
    Returns:
      - grid_levels: list of grid levels (from low to high)
      - grid_spacing: distance between adjacent levels
    """
    grid_spacing = (resistance - support) / (levels + 1)
    grid_levels = [support + grid_spacing * (i + 1) for i in range(levels)]
    return grid_levels, grid_spacing


def place_order(symbol, side, quantity):
    """
    Place a simulated market order. (Replace this simulation with actual
    Binance API calls when you are live.)
    """
    try:
        formatted_quantity = format_quantity(client, symbol, quantity)
        print(
            f"Placing {side} order for {symbol} for quantity {formatted_quantity:.6f}")
        # Uncomment below for live trading:
        if side == 'BUY':
            order = client.order_market_buy(
                symbol=symbol, quantity=formatted_quantity)
        else:
            order = client.order_market_sell(
                symbol=symbol, quantity=formatted_quantity)
        return order
        # return True  # Simulate a successful order
    except Exception as e:
        print(f"Error placing order for {symbol}: {e}")
        return None


def get_current_price(symbol):
    """
    Get the current market price for a given symbol.
    """
    try:
        return float(client.get_symbol_ticker(symbol=symbol)['price'])
    except Exception as e:
        print(f"Error fetching current price for {symbol}: {e}")
        return None


def get_weekly_support_resistance(symbol):
    """
    Fetch one week of 1-hour klines and calculate:
      - Support: the minimum of the lows
      - Resistance: the maximum of the highs
    """
    try:
        klines = client.get_historical_klines(
            symbol, Client.KLINE_INTERVAL_1HOUR, "7 days ago UTC")
        df = pd.DataFrame(klines, columns=[
            'open_time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'qav', 'num_trades', 'taker_base_vol', 'taker_quote_vol', 'ignore'
        ])
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        support = df['low'].min()
        resistance = df['high'].max()
        return support, resistance
    except Exception as e:
        print(f"Error fetching weekly data for {symbol}: {e}")
        return None, None


def get_technical_indicators(symbol, interval="15m", lookback="1 day ago UTC"):
    """
    Retrieve recent klines and compute technical indicators:
      - RSI (14-period)
      - MACD and its signal line
      - Bollinger Bands (upper and lower)
      - 50-period Simple Moving Average (SMA50)
    """
    try:
        klines = client.get_historical_klines(symbol, interval, lookback)
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'qav', 'num_trades', 'taker_base_vol', 'taker_quote_vol', 'ignore'
        ])
        df['close'] = df['close'].astype(float)
        df['volume'] = df['volume'].astype(float)

        # RSI (14-period)
        rsi = ta.momentum.RSIIndicator(df['close'], window=14).rsi().iloc[-1]

        # MACD and Signal
        macd_series = ta.trend.MACD(df['close'])
        macd = macd_series.macd().iloc[-1]
        macd_signal = macd_series.macd_signal().iloc[-1]

        # Bollinger Bands (20-period, 2 std dev)
        bb_indicator = ta.volatility.BollingerBands(
            df['close'], window=20, window_dev=2)
        bb_lower = bb_indicator.bollinger_lband().iloc[-1]
        bb_upper = bb_indicator.bollinger_hband().iloc[-1]

        # 50-period Simple Moving Average
        sma50 = df['close'].rolling(window=50).mean().iloc[-1]

        return rsi, macd, macd_signal, bb_lower, bb_upper, sma50
    except Exception as e:
        print(f"Error calculating indicators for {symbol}: {e}")
        return None, None, None, None, None, None

# ================================
# Trading Bot Main Function
# ================================


def get_usdt_balance():
    """
    Fetch the current USDT balance from the Binance Testnet account.
    """
    try:
        account_info = client.get_account(recvWindow=5000)
        for asset in account_info['balances']:
            if asset['asset'] == 'USDT':
                return float(asset['free'])
        return 0.0
    except Exception as e:
        print(f"Error fetching USDT balance: {e}")
        return 0.0


def monitor_profits(interval_minutes=5):
    """
    Monitor and print the current USDT balance and profits every 5 minutes.
    """
    print("Starting profit monitor...")
    initial_balance = get_usdt_balance()
    print(f"Initial USDT Balance: {initial_balance:.8f}")

    while True:
        try:
            current_balance = get_usdt_balance()
            profit = current_balance - initial_balance
            print(f"\n=== Profit Report ===")
            print(f"Current USDT Balance: {current_balance:.8f}")
            print(f"Profit/Loss: {profit:.8f} USDT")
            # Add timestamp here
            print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            print("=====================")
        except Exception as e:
            print(f"Error generating profit report: {e}")

        time.sleep(interval_minutes * 60)  # Wait for the specified interval


def run_trading_bot(duration_minutes=DURATION_MINUTES):
    """
    Run the trading bot for a fixed duration (in minutes). For each symbol:
      1. Calculate weekly support/resistance and build grid levels.
      2. In a loop until the duration expires, check the current price and technical indicators.
      3. If the price is near a grid level and one or more additional technical signals (RSI, Bollinger Bands, SMA50)
         indicate an entry, place a BUY order.
      4. For any open position, if the price reaches the target sell level and sell signals are met,
         place a SELL order.
      5. At the end of the session, report the total profit.
    """
    start_time = time.time()
    end_time = start_time + duration_minutes * 60

    # Track open positions and closed trades per symbol
    open_positions = {symbol: [] for symbol in SYMBOLS}
    closed_trades = []

    # Initialize grid levels for each symbol
    symbol_grids = {}
    for symbol in SYMBOLS:
        support, resistance = get_weekly_support_resistance(symbol)
        if support is None or resistance is None:
            continue
        grid_levels, grid_spacing = calculate_grid_levels(support, resistance)
        tolerance = grid_spacing * TOLERANCE_FACTOR
        symbol_grids[symbol] = {
            "support": support,
            "resistance": resistance,
            "grid_levels": grid_levels,
            "grid_spacing": grid_spacing,
            "tolerance": tolerance
        }
        print(f"{symbol} >> Support: {support:.8f}, Resistance: {resistance:.8f}")
        print(f"Grid levels: {grid_levels}\n")

    # Main trading loop
    while time.time() < end_time:
        for symbol in SYMBOLS:
            try:
                if symbol not in symbol_grids:
                    continue
                grid_info = symbol_grids[symbol]
                current_price = get_current_price(symbol)
                if current_price is None:
                    continue
                print(f"{symbol} >> Current Price: {current_price:.8f}")

                # Get technical indicators
                rsi, macd, macd_signal, bb_lower, bb_upper, sma50 = get_technical_indicators(
                    symbol)
                if rsi is None:
                    continue
                print(f"{symbol} >> RSI: {rsi:.2f} | MACD: {macd:.8f} | Signal: {macd_signal:.8f} | "
                      f"BB Lower: {bb_lower:.8f} | BB Upper: {bb_upper:.8f} | SMA50: {sma50:.8f}")

                # ---------------
                # BUY LOGIC
                # ---------------
                for i, level in enumerate(grid_info["grid_levels"]):
                    already_bought = any(
                        pos.get("grid_index") == i for pos in open_positions[symbol])
                    if already_bought:
                        continue
                    if current_price <= level + grid_info["tolerance"]:
                        # Determine buy signal using multiple conditions:
                        buy_signal = False
                        if rsi < RSI_BUY_THRESHOLD:
                            print(
                                f"{symbol} >> Buy signal: RSI ({rsi:.2f}) below threshold ({RSI_BUY_THRESHOLD}).")
                            buy_signal = True
                        if current_price < bb_lower:
                            print(
                                f"{symbol} >> Buy signal: Price ({current_price:.8f}) below Bollinger Lower ({bb_lower:.8f}).")
                            buy_signal = True
                        if current_price < sma50:
                            print(
                                f"{symbol} >> Buy signal: Price ({current_price:.8f}) below SMA50 ({sma50:.8f}).")
                            buy_signal = True
                        # Enforce MACD condition if enabled
                        if MACD_CONFIRMATION and not (macd > macd_signal):
                            print(
                                f"{symbol} >> MACD condition not met for BUY (MACD: {macd:.8f} <= Signal: {macd_signal:.8f}).")
                            buy_signal = False

                        if buy_signal:
                            quantity = TRADE_USDT_AMOUNT / current_price
                            order = place_order(symbol, 'BUY', quantity)
                            if order:
                                target_sell = (grid_info["grid_levels"][i + 1]
                                               if i + 1 < len(grid_info["grid_levels"])
                                               else grid_info["resistance"])
                                open_positions[symbol].append({
                                    "grid_index": i,
                                    "buy_price": current_price,
                                    "quantity": quantity,
                                    "target_sell": target_sell
                                })
                                print(
                                    f"{symbol} >> BUY order executed at {current_price:.8f} for quantity {quantity:.6f}.")

                # ---------------
                # SELL LOGIC
                # ---------------
                for pos in open_positions[symbol][:]:
                    if current_price >= pos["target_sell"] - grid_info["tolerance"]:
                        sell_signal = False
                        if rsi > RSI_SELL_THRESHOLD:
                            print(
                                f"{symbol} >> Sell signal: RSI ({rsi:.2f}) above threshold ({RSI_SELL_THRESHOLD}).")
                            sell_signal = True
                        if current_price > bb_upper:
                            print(
                                f"{symbol} >> Sell signal: Price ({current_price:.8f}) above Bollinger Upper ({bb_upper:.8f}).")
                            sell_signal = True
                        if current_price > sma50:
                            print(
                                f"{symbol} >> Sell signal: Price ({current_price:.8f}) above SMA50 ({sma50:.8f}).")
                            sell_signal = True
                        # Enforce MACD condition for selling
                        if MACD_CONFIRMATION and not (macd < macd_signal):
                            print(
                                f"{symbol} >> MACD condition not met for SELL (MACD: {macd:.8f} >= Signal: {macd_signal:.8f}).")
                            sell_signal = False

                        if sell_signal:
                            order = place_order(
                                symbol, 'SELL', pos["quantity"])
                            if order:
                                profit = (current_price -
                                          pos["buy_price"]) * pos["quantity"]
                                closed_trades.append({
                                    "symbol": symbol,
                                    "buy_price": pos["buy_price"],
                                    "sell_price": current_price,
                                    "quantity": pos["quantity"],
                                    "profit": profit
                                })
                                open_positions[symbol].remove(pos)
                                print(
                                    f"{symbol} >> SELL order executed at {current_price:.8f}; Profit: {profit:.8f} USDT")
            except Exception as e:
                print(f"Error processing {symbol}: {e}")

        time.sleep(15)  # Pause between loops

    # Session complete – summarize results
    total_profit = sum(trade["profit"] for trade in closed_trades)
    print("\n=== Trading session completed ===")
    print(f"Total closed trades: {len(closed_trades)}")
    print(
        f"Total profit over {duration_minutes} minutes: {total_profit:.8f} USDT")
    return total_profit, closed_trades


# ================================
# Run the Bot
# ================================
if __name__ == "__main__":
    # monitor_profits()
    run_trading_bot(duration_minutes=DURATION_MINUTES)
