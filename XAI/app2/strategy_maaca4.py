from binance.client import Client
import pandas as pd
import time
import ta  # Technical Analysis Library
from XAI.BinanceKeys import test_api_key, test_secret_key

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

# List of symbols to trade (e.g. altcoins/meme coins)
SYMBOLS = [
    "DOGEUSDT",
    "SHIBUSDT",
    "PEPEUSDT",
    "XRPUSDT",
    "ETHUSDT",
    "SOLUSDT",
    # "BERAUSDT",
    "BNBUSDT",
    "TRUMPUSDT",
    "BTCUSDT",
    # add more symbols as desired
]

# Grid & technical parameters
GRID_LEVELS = 5              # Number of grid levels between support and resistance
# Tolerance as a fraction of the grid spacing (for “near” detection)
TOLERANCE_FACTOR = 0.1
TRADE_USDT_AMOUNT = 10.0     # USDT to spend per trade

# Technical indicator thresholds
RSI_BUY_THRESHOLD = 50       # Only buy when RSI is below 30 (oversold)
RSI_SELL_THRESHOLD = 90      # Only sell when RSI is above 70 (overbought)
# Enforce MACD condition: buy if MACD > signal; sell if MACD < signal
MACD_CONFIRMATION = True

# Run duration in hours (set to 6 hours here)
DURATION_HOURS = 6

RISK_PER_TRADE = 0.01  # Risk 1% of account balance per trade
account_balance = float(client.get_asset_balance(asset='USDT')['free'])
TRADE_USDT_AMOUNT = account_balance * RISK_PER_TRADE

# -------------------------------
# HELPER FUNCTIONS
# -------------------------------


def get_weekly_support_resistance(symbol):
    """
    Fetch one week of 1-hour klines and calculate:
        - Average support (mean of lows)
        - Average resistance (mean of highs)
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
        avg_resistance = df['high'].mean()
        avg_support = df['low'].mean()
        return avg_support, avg_resistance
    except Exception as e:
        print(f"Error fetching weekly data for {symbol}: {e}")
        return None, None


def calculate_grid_levels(avg_support, avg_resistance, levels=GRID_LEVELS):
    grid_spacing = (avg_resistance - avg_support) / (levels + 1)
    grid_levels = [avg_support + grid_spacing * (i + 1) for i in range(levels)]
    return grid_levels, grid_spacing


def calculate_grid_levels_OLD(avg_support, avg_resistance, levels=GRID_LEVELS):
    """
    Divide the range between average support and resistance into grid levels.
    Returns:
        - grid_levels: a list of levels (from lower to higher)
        - grid_spacing: the difference between adjacent levels
    """
    grid_spacing = (avg_resistance - avg_support) / (levels + 1)
    grid_levels = [avg_support + grid_spacing * (i + 1) for i in range(levels)]
    return grid_levels, grid_spacing


def get_technical_indicators(symbol, interval="15m", lookback="1 day ago UTC"):
    """
    Retrieve recent klines and compute technical indicators:
        - RSI (using a 14-period window)
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

# -------------------------------
# TRADING BOT MAIN FUNCTION
# -------------------------------


def is_trending(symbol, interval="1h", threshold=25, lookback="2 days ago UTC"):
    try:
        klines = client.get_historical_klines(
            symbol, interval, lookback)  # Fetch 2 days of data
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'qav', 'num_trades', 'taker_base_vol', 'taker_quote_vol', 'ignore'
        ])
        df['close'] = df['close'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        adx = ta.trend.ADXIndicator(
            df['high'], df['low'], df['close'], window=14).adx()
        if len(adx) == 0:
            return False
        return adx.iloc[-1] > threshold
    except Exception as e:
        print(f"Error checking trend for {symbol}: {e}")
        return False


def run_trading_bot(duration_hours=DURATION_HOURS):
    """
    Run the trading bot for a fixed duration (in hours). For each symbol:
        1. Calculate weekly average support/resistance and build grid levels.
        2. Check if the market is trending. If it is, skip trading for that symbol.
        3. In a loop until the duration expires, check the current price and technical indicators.
        4. If the price is near a grid level (and that grid level has not already been triggered) and the 
            conditions are met (RSI below threshold and MACD bullish), place a BUY (simulate buying TRADE_USDT_AMOUNT).
        5. For any open position, if the current price reaches the target sell level (the next grid level or resistance)
            and the sell conditions are met (RSI above threshold and MACD bearish), SELL that position.
        6. At the end of the session, report the total profit from all closed trades.
    """
    start_time = time.time()
    end_time = start_time + duration_hours * 3600

    # For each symbol, we will track:
    # - The grid levels and related tolerance
    # - A list of open positions: each is a dict with keys: grid_index, buy_price, quantity, target_sell
    symbol_grids = {}
    open_positions = {symbol: [] for symbol in SYMBOLS}
    closed_trades = []  # Records closed trades (for profit calculation)

    # Initialize grid levels for each symbol using weekly data.
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

    # Main trading loop (runs until the duration expires)
    while time.time() < end_time:
        for symbol in SYMBOLS:
            try:
                if symbol not in symbol_grids:
                    continue

                # Check if the market is trending
                if is_trending(symbol):
                    print(f"{symbol} >> Market is trending. Skipping grid trading.")
                    continue

                grid_info = symbol_grids[symbol]
                current_price = get_current_price(symbol)
                if current_price is None:
                    continue
                print(f"{symbol} >> Current Price: {current_price:.8f}")

                # Get recent technical indicators (15m timeframe)
                rsi, macd, macd_signal = get_technical_indicators(symbol)
                if rsi is None:
                    continue
                print(
                    f"{symbol} >> RSI: {rsi:.2f} | MACD: {macd:.8f} | Signal: {macd_signal:.8f}")

                # ---------------
                # BUY LOGIC:
                # ---------------
                # For each grid level, if we have not already opened a position for that level:
                for i, level in enumerate(grid_info["grid_levels"]):
                    already_bought = any(
                        pos.get("grid_index") == i for pos in open_positions[symbol])
                    if already_bought:
                        continue
                    # If the current price is at or below (level + tolerance), we consider a buy.
                    if current_price <= level + grid_info["tolerance"]:
                        # Additional technical condition: RSI is below threshold and MACD is bullish (if required)
                        if rsi < RSI_BUY_THRESHOLD and (not MACD_CONFIRMATION or macd > macd_signal):
                            quantity = TRADE_USDT_AMOUNT / current_price
                            # (For live trading, you would call the Binance order API here.)
                            print(
                                f"{symbol} >> BUY order placed at {current_price:.8f} (grid level {i} ≈ {level:.8f}). Quantity: {quantity:.10f}")
                            # Define the target sell price as the next grid level (or use the resistance if at the top)
                            target_sell = grid_info["grid_levels"][i + 1] if i + 1 < len(
                                grid_info["grid_levels"]) else grid_info["resistance"]
                            open_positions[symbol].append({
                                "grid_index": i,
                                "buy_price": current_price,
                                "quantity": quantity,
                                "target_sell": target_sell
                            })
                        else:
                            print(
                                f"{symbol} >> Buy conditions not met for grid level {i} (RSI: {rsi:.6f}, MACD condition: {macd > macd_signal if MACD_CONFIRMATION else 'N/A'}).")

                # ---------------
                # SELL LOGIC:
                # ---------------
                # For each open position, if current price reaches or exceeds the target sell level (minus tolerance)
                for pos in open_positions[symbol][:]:
                    if current_price >= pos["target_sell"] - grid_info["tolerance"]:
                        # Additional technical condition for selling: RSI above threshold and MACD bearish (if required)
                        if rsi > RSI_SELL_THRESHOLD and (not MACD_CONFIRMATION or macd < macd_signal):
                            profit = (current_price -
                                      pos["buy_price"]) * pos["quantity"]
                            print(
                                f"{symbol} >> SELL order placed at {current_price:.8f} for position bought at {pos['buy_price']:.8f}. Profit: {profit:.8f} USDT")
                            closed_trades.append({
                                "symbol": symbol,
                                "buy_price": pos["buy_price"],
                                "sell_price": current_price,
                                "quantity": pos["quantity"],
                                "profit": profit
                            })
                            open_positions[symbol].remove(pos)
                        else:
                            print(
                                f"{symbol} >> Sell conditions not met (RSI: {rsi:.6f}, MACD condition: {macd < macd_signal if MACD_CONFIRMATION else 'N/A'}).")
            except Exception as e:
                print(f"Error processing {symbol}: {e}")
        # Wait before the next check (every 15 seconds)
        time.sleep(15)

    # Session finished—calculate and print total profit.
    total_profit = sum(trade["profit"] for trade in closed_trades)
    print("\n=== Trading session completed ===")
    print(f"Total closed trades: {len(closed_trades)}")
    print(f"Total profit over {duration_hours} hours: {total_profit:.8f} USDT")
    return total_profit, closed_trades


if __name__ == "__main__":
    run_trading_bot(duration_hours=DURATION_HOURS)
