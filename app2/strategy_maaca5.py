from binance.client import Client
import pandas as pd
import time
import ta  # Technical Analysis Library
# from BinanceKeys import test_api_key, test_secret_key


API_KEY = 'test_api_key'
API_SECRET = 'test_secret_key'
# client = Client(API_KEY, API_SECRET)
client = Client(API_KEY, API_SECRET, tld='com', testnet=True)

# -------------------------------
# GLOBAL PARAMETERS & SETTINGS
# -------------------------------

# List of symbols to trade
SYMBOLS = [
    "DOGEUSDT",
    "SHIBUSDT",
    "PEPEUSDT",
    "XRPUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "BNBUSDT",
    "TRUMPUSDT",
    "BTCUSDT",
    "ENSUSDT",
    "MANTAUSDT",
    "TURBOUSDT",
    "ETCUSDT",
]

# Grid & technical parameters
GRID_LEVELS = 5              # Number of grid levels between support and resistance
TOLERANCE_FACTOR = 0.1       # Tolerance as a fraction of the grid spacing
TRADE_USDT_AMOUNT = 10.0     # USDT to spend per trade

# Technical indicator thresholds
RSI_BUY_THRESHOLD = 30       # Only buy when RSI is below 30 (oversold)
RSI_SELL_THRESHOLD = 70      # Only sell when RSI is above 70 (overbought)
MACD_CONFIRMATION = True     # Enforce MACD condition

# Run duration in minutes (set to 30 minutes)
DURATION_MINUTES = 5

# -------------------------------
# HELPER FUNCTIONS
# -------------------------------

def get_weekly_support_resistance(symbol):
    """
    Fetch one week of 1-hour klines and calculate:
        - Support (min of lows)
        - Resistance (max of highs)
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


def calculate_grid_levels(avg_support, avg_resistance, levels=GRID_LEVELS):
    """
    Divide the range between support and resistance into grid levels.
    """
    grid_spacing = (avg_resistance - avg_support) / (levels + 1)
    grid_levels = [avg_support + grid_spacing * (i + 1) for i in range(levels)]
    return grid_levels, grid_spacing


def get_technical_indicators(symbol, interval="15m", lookback="1 day ago UTC"):
    """
    Retrieve recent klines and compute technical indicators:
        - RSI (14-period)
        - MACD and its signal line
    """
    try:
        klines = client.get_historical_klines(symbol, interval, lookback)
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'qav', 'num_trades', 'taker_base_vol', 'taker_quote_vol', 'ignore'
        ])
        df['close'] = df['close'].astype(float)
        df['volume'] = df['volume'].astype(float)
        rsi = ta.momentum.RSIIndicator(df['close'], window=14).rsi().iloc[-1]
        macd_series = ta.trend.MACD(df['close'])
        macd = macd_series.macd().iloc[-1]
        macd_signal = macd_series.macd_signal().iloc[-1]
        return rsi, macd, macd_signal
    except Exception as e:
        print(f"Error calculating indicators for {symbol}: {e}")
        return None, None, None


def get_current_price(symbol):
    """
    Get the current market price for a given symbol.
    """
    try:
        return float(client.get_symbol_ticker(symbol=symbol)['price'])
    except Exception as e:
        print(f"Error fetching current price for {symbol}: {e}")
        return None


def is_near_level(price, level, tolerance):
    """
    Returns True if the price is within the specified tolerance of the level.
    """
    return abs(price - level) <= tolerance


def place_order(symbol, side, quantity):
    """
    Place a buy/sell order on Binance Testnet.
    """
    try:
        order = client.create_order(
            symbol=symbol,
            side=side,
            type='MARKET',
            quantity=quantity
        )
        print(f"Order placed: {order}")
        return order
    except Exception as e:
        print(f"Error placing {side} order for {symbol}: {e}")
        return None


# -------------------------------
# TRADING BOT MAIN FUNCTION
# -------------------------------

def run_trading_bot(duration_minutes=DURATION_MINUTES):
    """
    Run the trading bot for a fixed duration (in minutes).
    """
    start_time = time.time()
    end_time = start_time + duration_minutes * 60

    # Track open positions and closed trades
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
                rsi, macd, macd_signal = get_technical_indicators(symbol)
                if rsi is None:
                    continue
                print(f"{symbol} >> RSI: {rsi:.2f} | MACD: {macd:.8f} | Signal: {macd_signal:.8f}")

                # BUY LOGIC
                for i, level in enumerate(grid_info["grid_levels"]):
                    already_bought = any(pos.get("grid_index") == i for pos in open_positions[symbol])
                    if already_bought:
                        continue
                    if current_price <= level + grid_info["tolerance"]:
                        if rsi < RSI_BUY_THRESHOLD and (not MACD_CONFIRMATION or macd > macd_signal):
                            quantity = TRADE_USDT_AMOUNT / current_price
                            order = place_order(symbol, 'BUY', quantity)
                            if order:
                                target_sell = grid_info["grid_levels"][i + 1] if i + 1 < len(grid_info["grid_levels"]) else grid_info["resistance"]
                                open_positions[symbol].append({
                                    "grid_index": i,
                                    "buy_price": current_price,
                                    "quantity": quantity,
                                    "target_sell": target_sell
                                })

                # SELL LOGIC
                for pos in open_positions[symbol][:]:
                    if current_price >= pos["target_sell"] - grid_info["tolerance"]:
                        if rsi > RSI_SELL_THRESHOLD and (not MACD_CONFIRMATION or macd < macd_signal):
                            order = place_order(symbol, 'SELL', pos["quantity"])
                            if order:
                                profit = (current_price - pos["buy_price"]) * pos["quantity"]
                                closed_trades.append({
                                    "symbol": symbol,
                                    "buy_price": pos["buy_price"],
                                    "sell_price": current_price,
                                    "quantity": pos["quantity"],
                                    "profit": profit
                                })
                                open_positions[symbol].remove(pos)
            except Exception as e:
                print(f"Error processing {symbol}: {e}")
        time.sleep(15)  # Wait before the next check

    # Calculate and print total profit
    total_profit = sum(trade["profit"] for trade in closed_trades)
    print("\n=== Trading session completed ===")
    print(f"Total closed trades: {len(closed_trades)}")
    print(f"Total profit over {duration_minutes} minutes: {total_profit:.8f} USDT")
    return total_profit, closed_trades


if __name__ == "__main__":
    run_trading_bot(duration_minutes=DURATION_MINUTES)