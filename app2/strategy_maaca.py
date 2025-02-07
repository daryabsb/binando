from binance.client import Client
import pandas as pd
import time
import ta  # Technical Analysis Library
# from BinanceKeys import test_api_key, test_secret_key


API_KEY = 'test_api_key'
API_SECRET = 'test_secret_key'
client = Client(API_KEY, API_SECRET)

# SYMBOL = "BTCUSDT"
SYMBOL = "DOGEUSDT"
GRID_SIZE = 5  # Number of buy levels
BUY_PERCENT = 1 / 100  # Buy every 1% drop
SELL_PERCENT = 1.5 / 100  # Sell 1.5% above buy price
STOP_LOSS = 5 / 100  # Stop-loss at 5% below lowest buy
TRADE_AMOUNT = 0.0005  # Small trade size
RSI_THRESHOLD = 30  # Buy when RSI < 30
MACD_CONFIRMATION = True  # Only buy when MACD is bullish
VOLUME_THRESHOLD = 1.2  # Volume must be 20% above average


def get_historical_data(symbol, interval="15m", lookback="50 minutes ago UTC"):
    """Fetch recent market data for indicator calculations."""
    klines = client.get_historical_klines(symbol, interval, lookback)
    df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time',
                                       'quote_asset_volume', 'trades', 'taker_base_volume', 'taker_quote_volume', 'ignore'])
    df['close'] = df['close'].astype(float)
    df['volume'] = df['volume'].astype(float)
    return df


def calculate_indicators(symbol):
    """Calculate RSI, MACD, and volume strength."""
    df = get_historical_data(symbol)

    # RSI Calculation
    df["rsi"] = ta.momentum.RSIIndicator(df["close"], window=14).rsi()

    # MACD Calculation
    macd = ta.trend.MACD(df["close"])
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()

    # Volume Analysis
    df["volume_avg"] = df["volume"].rolling(window=20).mean()
    df["volume_strong"] = df["volume"] > (df["volume_avg"] * VOLUME_THRESHOLD)

    return df.iloc[-1]  # Return latest data


def should_buy(price):
    """Check if conditions are right to buy."""
    data = calculate_indicators(SYMBOL)

    # RSI must be below threshold
    if data["rsi"] >= RSI_THRESHOLD:
        return False

    # MACD must be bullish (MACD > Signal Line)
    if MACD_CONFIRMATION and data["macd"] <= data["macd_signal"]:
        return False

    # Volume must be strong
    if not data["volume_strong"]:
        return False

    return True


def should_sell(price, buy_price):
    """Check if conditions are right to sell."""
    data = calculate_indicators(SYMBOL)

    # RSI must be above 70 (overbought)
    if data["rsi"] <= 70:
        return False

    # MACD must be bearish (MACD < Signal Line)
    if data["macd"] >= data["macd_signal"]:
        return False

    # Price must be at least 1.5% above buy price
    if price < buy_price * (1 + SELL_PERCENT):
        return False

    return True


def place_grid_orders():
    """Set up buy and sell grid levels."""
    start_price = float(client.get_symbol_ticker(symbol=SYMBOL)["price"])
    buy_prices = [start_price * (1 - BUY_PERCENT * i)
                  for i in range(1, GRID_SIZE + 1)]
    sell_prices = [bp * (1 + SELL_PERCENT) for bp in buy_prices]

    print(f"Buy Levels: {buy_prices}")
    print(f"Sell Levels: {sell_prices}")

    return buy_prices, sell_prices


buy_prices, sell_prices = place_grid_orders()


def trade():
    """Main trading loop."""
    global buy_prices, sell_prices

    while True:
        try:
            current_price = float(
                client.get_symbol_ticker(symbol=SYMBOL)["price"])
            print(f"Current Price: {current_price}")

            # Buy Logic
            for i, buy_price in enumerate(buy_prices):
                if current_price <= buy_price and should_buy(current_price):
                    print(f"✅ Buying at {current_price}")
                    # order = client.order_market_buy(symbol=SYMBOL, quantity=TRADE_AMOUNT)
                    buy_prices[i] = None  # Mark as bought

            # Sell Logic
            for i, sell_price in enumerate(sell_prices):
                if buy_prices[i] is None and current_price >= sell_price and should_sell(current_price, sell_price):
                    print(f"✅ Selling at {current_price}")
                    # order = client.order_market_sell(symbol=SYMBOL, quantity=TRADE_AMOUNT)
                    buy_prices[i] = current_price  # Reset new buy level

            # Stop-Loss Check
            lowest_buy = min([p for p in buy_prices if p]
                             ) if any(buy_prices) else None
            if lowest_buy and current_price < lowest_buy * (1 - STOP_LOSS):
                print("🚨 Stop-loss triggered! Exiting trade.")
                break

            time.sleep(5)  # Wait before checking again

        except Exception as e:
            print(f"⚠ Error: {e}")
            time.sleep(5)


trade()
