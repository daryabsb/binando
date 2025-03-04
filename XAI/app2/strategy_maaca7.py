from datetime import datetime  # Import datetime module
from binance.client import Client
import pandas as pd
import time
import ta  # Technical Analysis Library
from XAI.BinanceKeys import test_api_key, test_secret_key
from XAI.symbols import SYMBOLS
import math

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


# ==================================
# Global Constants and Settings
# ==================================
RSI_BUY_THRESHOLD = 40.0     # Buy if RSI is below this
RSI_SELL_THRESHOLD = 60.0    # Sell if RSI is above this
MACD_CONFIRMATION = True     # Require MACD > Signal for buy and vice versa for sell
TRADE_USDT_AMOUNT = 10.0      # USDT allocated per trade
TOLERANCE_FACTOR = 0.1       # Fraction of grid spacing used as tolerance

DURATION_MINUTES = 4000       # Bot run duration in minutes for this test
MAX_EXPOSURE_PER_SYMBOL = 100  # Maximum USDT to commit per symbol
GRID_LEVELS_COUNT = 5        # Number of grid levels
GRID_RECALC_INTERVAL = 30 * 60  # Recalculate grid every 30 minutes


# ==================================
# Helper Functions
# ==================================

def calculate_grid_levels(support, resistance, levels=GRID_LEVELS_COUNT):
    """
    Divide the range between support and resistance into grid levels.
    Returns:
      - grid_levels: list of grid levels (from low to high)
      - grid_spacing: spacing between levels
    """
    grid_spacing = (resistance - support) / (levels + 1)
    grid_levels = [support + grid_spacing * (i + 1) for i in range(levels)]
    return grid_levels, grid_spacing


def format_quantity(symbol, quantity):
    """
    Adjust the quantity to the allowed precision based on the symbol's LOT_SIZE filter.
    """
    try:
        info = client.get_symbol_info(symbol)
        if info is None:
            return quantity
        for f in info['filters']:
            if f['filterType'] == 'LOT_SIZE':
                step_size = float(f['stepSize'])
                decimals = int(round(-math.log10(step_size), 0))
                formatted_quantity = round(quantity, decimals)
                return formatted_quantity
        return quantity
    except Exception as e:
        print(f"Error formatting quantity for {symbol}: {e}")
        return quantity


def place_order(symbol, side, quantity):
    """
    Place a market order after formatting the quantity.
    Replace the simulated order with live API calls when ready.
    """
    try:
        formatted_quantity = format_quantity(symbol, quantity)
        print(
            f"Placing {side} order for {symbol} for quantity {formatted_quantity:.6f}")
        # Uncomment below for live trading:
        # if side == 'BUY':
        #     order = client.order_market_buy(symbol=symbol, quantity=formatted_quantity)
        # else:
        #     order = client.order_market_sell(symbol=symbol, quantity=formatted_quantity)
        # return order
        return True  # Simulate successful order placement
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
      - Support: minimum of lows
      - Resistance: maximum of highs
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


def zero_lag_ema(data, period=14):
    """Calculate Zero Lag Exponential Moving Average (ZLMA)"""
    ema1 = data.ewm(span=period, adjust=False).mean()
    ema2 = ema1.ewm(span=period, adjust=False).mean()
    zlma = 2 * ema1 - ema2  # Zero Lag EMA formula
    return zlma


def get_technical_indicators(symbol, interval="15m", lookback="1 day ago UTC"):
    """
    Retrieve recent klines and compute technical indicators:
      - RSI (14-period)
      - MACD and MACD signal
      - Bollinger Bands (20-period, 2 std dev)
      - SMA50 (50-period Simple Moving Average)
      - ZLMA (20-period Zero Lag Moving Average)
    """
    try:
        klines = client.get_historical_klines(symbol, interval, lookback)
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'qav', 'num_trades', 'taker_base_vol', 'taker_quote_vol', 'ignore'
        ])
        df['close'] = df['close'].astype(float)

        # RSI (Relative Strength Index)
        rsi = ta.momentum.RSIIndicator(df['close'], window=14).rsi().iloc[-1]

        # MACD (Moving Average Convergence Divergence)
        macd_series = ta.trend.MACD(df['close'])
        macd = macd_series.macd().iloc[-1]
        macd_signal = macd_series.macd_signal().iloc[-1]

        # Bollinger Bands
        bb_indicator = ta.volatility.BollingerBands(
            df['close'], window=20, window_dev=2)
        bb_lower = bb_indicator.bollinger_lband().iloc[-1]
        bb_upper = bb_indicator.bollinger_hband().iloc[-1]

        # SMA (Simple Moving Average)
        sma50 = df['close'].rolling(window=50).mean().iloc[-1]

        # ZLMA (Zero Lag Moving Average) Calculation
        ema1 = df['close'].ewm(span=20, adjust=False).mean()
        ema2 = ema1.ewm(span=20, adjust=False).mean()
        zlma = (2 * ema1 - ema2).iloc[-1]  # Final ZLMA value

        return rsi, macd, macd_signal, bb_lower, bb_upper, sma50, zlma
    except Exception as e:
        print(f"Error calculating indicators for {symbol}: {e}")
        return None, None, None, None, None, None, None


def get_total_exposure(open_positions, symbol):
    """
    Calculate the total USDT exposure for open positions for a given symbol.
    """
    return sum(pos["buy_price"] * pos["quantity"] for pos in open_positions[symbol])


def check_stop_loss(pos, current_price, stop_loss_pct=0.05):
    """
    Return True if the current price is more than stop_loss_pct below the entry.
    """
    if current_price < pos["buy_price"] * (1 - stop_loss_pct):
        return True
    return False


def recalc_grid_levels(symbol):
    """
    Recalculate grid levels for the symbol based on the latest weekly support/resistance.
    """
    support, resistance = get_weekly_support_resistance(symbol)
    if support is None or resistance is None:
        return None
    grid_levels, grid_spacing = calculate_grid_levels(support, resistance)
    tolerance = grid_spacing * TOLERANCE_FACTOR
    return {
        "support": support,
        "resistance": resistance,
        "grid_levels": grid_levels,
        "grid_spacing": grid_spacing,
        "tolerance": tolerance
    }


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


# Dictionary to track last grid recalculation time per symbol
last_grid_recalc = {}

# ==================================
# Trading Bot Main Function
# ==================================


def run_trading_bot(duration_minutes=DURATION_MINUTES):
    start_time = time.time()
    end_time = start_time + duration_minutes * 60

    # Track open positions and closed trades per symbol
    open_positions = {symbol: [] for symbol in SYMBOLS}
    closed_trades = []
    symbol_grids = {}
    last_grid_recalc = {}

    # Initial Grid Calculation
    for symbol in SYMBOLS:
        grid_info = recalc_grid_levels(symbol)
        if grid_info:
            symbol_grids[symbol] = grid_info
            last_grid_recalc[symbol] = time.time()
            print(
                f"{symbol} >> Grid initialized: Support {grid_info['support']:.8f}, Resistance {grid_info['resistance']:.8f}")

    # Main Trading Loop
    while time.time() < end_time:
        for symbol in SYMBOLS:
            try:
                now = time.time()

                # Recalculate grid if needed
                if now - last_grid_recalc.get(symbol, 0) > GRID_RECALC_INTERVAL:
                    new_grid = recalc_grid_levels(symbol)
                    if new_grid:
                        symbol_grids[symbol] = new_grid
                        last_grid_recalc[symbol] = now
                        print(f"{symbol} >> Grid recalculated.")

                if symbol not in symbol_grids:
                    continue

                # Get Current Price
                current_price = get_current_price(symbol)
                if current_price is None:
                    continue

                # Get Technical Indicators
                rsi, macd, macd_signal, bb_lower, bb_upper, sma50, zlma = get_technical_indicators(
                    symbol)
                if rsi is None:
                    continue

                print(f"{symbol} >> Price: {current_price:.8f} | RSI: {rsi:.2f} | MACD: {macd:.8f} | Signal: {macd_signal:.8f} | "
                      f"BB Lower: {bb_lower:.8f} | BB Upper: {bb_upper:.8f} | SMA50: {sma50:.8f} | ZLMA: {zlma:.8f}")

                # --------- BUY LOGIC ----------
                for i, level in enumerate(symbol_grids[symbol]["grid_levels"]):
                    if any(pos["grid_index"] == i for pos in open_positions[symbol]):
                        continue

                    if current_price <= level + symbol_grids[symbol]["tolerance"]:
                        if get_total_exposure(open_positions, symbol) + TRADE_USDT_AMOUNT > MAX_EXPOSURE_PER_SYMBOL:
                            continue

                        buy_signal = (
                            (rsi < RSI_BUY_THRESHOLD) or
                            (current_price < bb_lower) or
                            (current_price < sma50) or
                            (current_price < zlma)  # ZLMA Buy Confirmation
                        )

                        if MACD_CONFIRMATION and not (macd > macd_signal):
                            buy_signal = False  # MACD must confirm

                        if buy_signal:
                            quantity = TRADE_USDT_AMOUNT / current_price
                            order = place_order(symbol, 'BUY', quantity)
                            if order:
                                target_sell = symbol_grids[symbol]["grid_levels"][i + 1] if i + 1 < len(
                                    symbol_grids[symbol]["grid_levels"]) else symbol_grids[symbol]["resistance"]
                                open_positions[symbol].append(
                                    {"grid_index": i, "buy_price": current_price, "quantity": quantity, "target_sell": target_sell})
                                print(
                                    f"{symbol} >> BUY executed at {current_price:.8f} for {quantity:.6f}.")

                # --------- SELL LOGIC ----------
                for pos in open_positions[symbol][:]:
                    if check_stop_loss(pos, current_price, stop_loss_pct=0.05):
                        order = place_order(symbol, 'SELL', pos["quantity"])
                        if order:
                            profit = (current_price -
                                      pos["buy_price"]) * pos["quantity"]
                            closed_trades.append(
                                {"symbol": symbol, "buy_price": pos["buy_price"], "sell_price": current_price, "quantity": pos["quantity"], "profit": profit})
                            open_positions[symbol].remove(pos)
                            print(
                                f"{symbol} >> STOP-LOSS SELL at {current_price:.8f}; Profit: {profit:.8f} USDT")
                        continue

                    if current_price >= pos["target_sell"] - symbol_grids[symbol]["tolerance"]:
                        sell_signal = (
                            (rsi > RSI_SELL_THRESHOLD) or
                            (current_price > bb_upper) or
                            (current_price > sma50) or
                            (current_price > zlma)  # ZLMA Sell Confirmation
                        )

                        if MACD_CONFIRMATION and not (macd < macd_signal):
                            sell_signal = False  # MACD must confirm

                        if sell_signal:
                            order = place_order(
                                symbol, 'SELL', pos["quantity"])
                            if order:
                                profit = (current_price -
                                          pos["buy_price"]) * pos["quantity"]
                                closed_trades.append(
                                    {"symbol": symbol, "buy_price": pos["buy_price"], "sell_price": current_price, "quantity": pos["quantity"], "profit": profit})
                                open_positions[symbol].remove(pos)
                                print(
                                    f"{symbol} >> SELL executed at {current_price:.8f}; Profit: {profit:.8f} USDT")

            except Exception as e:
                print(f"Error processing {symbol}: {e}")

        time.sleep(15)

    print(
        f"Total Profit: {sum(trade['profit'] for trade in closed_trades):.8f} USDT")
    return closed_trades


# ================================
# Run the Bot
# ================================
if __name__ == "__main__":
    # monitor_profits()
    run_trading_bot(duration_minutes=DURATION_MINUTES)
