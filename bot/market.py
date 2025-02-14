import random
import pandas as pd
from decimal import Decimal
from bot.coins import get_roc

active_trades = {}  # Store open trades


def get_volume(client, symbol):
    """Fetch 24h trading volume of a symbol from Binance."""
    ticker = client.get_ticker(symbol=symbol)
    return Decimal(ticker["quoteVolume"])  # Convert to Decimal for accuracy


def is_bullish_trend(client, symbol):
    """Check if a coin is in a strong uptrend using ZLMA in multiple timeframes."""
    timeframes = ["5m", "15m", "1h", "4h", "1d"]  # Short to long-term trends
    current_price = get_price(client, symbol)

    bullish_trend = all(current_price > get_zlma(
        client, symbol, tf) for tf in timeframes)

    return bullish_trend


def get_algoalpha_trend(client, symbol):
    """Fetch trend strength score from AlgoAlpha indicators."""
    # Placeholder: Replace with actual AlgoAlpha API call
    return Decimal(random.uniform(0, 1))  # Simulated trend score (0-1)


def get_zlma(client, symbol, interval):
    """Calculate Zero Lag Moving Average (ZLMA) for a given symbol and interval."""
    klines = client.get_klines(
        symbol=symbol, interval=interval, limit=50)  # Get last 50 candles
    closes = [Decimal(k[4]) for k in klines]  # Close prices

    alpha = Decimal("2") / (Decimal(len(closes)) + Decimal("1"))
    zlma = sum(closes) / len(closes)  # Simple Moving Average as starting point

    for close in closes:
        zlma = (alpha * close) + \
            ((Decimal("1") - alpha) * zlma)  # ZLMA formula

    return zlma


def get_volatility(client, symbol):
    """Calculate coin volatility based on price variations in the last 24h."""
    ticker = client.get_ticker(symbol=symbol)
    high_price = Decimal(ticker["highPrice"])
    low_price = Decimal(ticker["lowPrice"])
    current_price = Decimal(ticker["lastPrice"])

    return (high_price - low_price) / current_price  # Volatility percentage


def is_bullish_trend2(client, symbol):
    """Check if a coin is bullish in multiple timeframes using ZLMA & AlgoAlpha indicators."""
    timeframes = ["5m", "15m", "1h", "4h", "1d"]
    bullish_count = 0

    for tf in timeframes:
        zlma = get_zlma(client, symbol, tf)
        price = get_price(client, symbol)

        # ✅ Price should be above ZLMA for an uptrend
        if price > zlma:
            bullish_count += 1

    # ✅ Must be bullish in all timeframes
    return bullish_count == len(timeframes)


def is_market_stable(client):
    """Check if the overall market is stable (BTC & ETH as indicators)."""
    btc_roc = get_roc(client, "BTCUSDT")  # BTC Rate of Change
    eth_roc = get_roc(client, "ETHUSDT")  # ETH Rate of Change

    # ✅ If BTC or ETH drop more than -5%, the market is in panic mode
    if btc_roc < -5 or eth_roc < -5:
        print(
            f"⚠️ Market is unstable! BTC ROC: {btc_roc:.2%} | ETH ROC: {eth_roc:.2%}")
        return False

    return True


def calculate_stop_loss_and_take_profit(entry_price):
    """Calculate stop-loss and take-profit prices based on risk management strategy."""
    STOP_LOSS_PERCENT = Decimal("2")  # 2% stop-loss
    TAKE_PROFIT_PERCENT = Decimal("5")  # 5% take-profit

    stop_loss_price = entry_price * \
        (Decimal("1") - (STOP_LOSS_PERCENT / Decimal("100")))
    take_profit_price = entry_price * \
        (Decimal("1") + (TAKE_PROFIT_PERCENT / Decimal("100")))

    return stop_loss_price, take_profit_price


def track_trade(symbol, entry_price, stop_loss, take_profit):
    """Track open trades & dynamically update stop-loss."""
    active_trades[symbol] = {"entry": entry_price,
                             "stop_loss": stop_loss, "take_profit": take_profit}


def monitor_trades(client):
    """Monitor active trades & adjust stop-loss dynamically."""
    for symbol, trade in active_trades.items():
        current_price = get_price(client, symbol)

        # Update trailing stop-loss
        new_stop_loss = trailing_stop_loss(
            trade["entry"], current_price, trade["stop_loss"])
        active_trades[symbol]["stop_loss"] = new_stop_loss

        # Sell if stop-loss or take-profit is hit
        if current_price <= new_stop_loss:
            print(f"🚨 Selling {symbol} at {current_price} (Trailing Stop Hit)")
            # place_order(client, symbol, SIDE_SELL, get_coin_balance(client, symbol))
            del active_trades[symbol]

        elif current_price >= trade["take_profit"]:
            print(f"🎯 Selling {symbol} at {current_price} (Take-Profit Hit)")
            # place_order(client, symbol, SIDE_SELL, get_coin_balance(client, symbol))
            del active_trades[symbol]


def execute_trade(client, symbol, trade_type, quantity, entry_price):
    """Execute a trade with stop-loss and take-profit conditions."""
    stop_loss, take_profit = calculate_stop_loss_and_take_profit(entry_price)

    print(f"🔹 Placing {trade_type} order for {symbol} | Quantity: {quantity}")
    print(f"🚨 Stop-loss: {stop_loss} | 🎯 Take-profit: {take_profit}")

    # Place market order
    # order = place_order(client, symbol, trade_type, quantity)

    # Track stop-loss & take-profit
    track_trade(symbol, entry_price, stop_loss, take_profit)


def trailing_stop_loss(entry_price, current_price, last_stop_loss):
    """Adjust stop-loss dynamically as price rises to lock in profits."""
    TRAILING_STOP_PERCENT = Decimal("1")  # 1% trailing stop

    new_stop_loss = current_price * \
        (Decimal("1") - (TRAILING_STOP_PERCENT / Decimal("100")))

    return max(new_stop_loss, last_stop_loss)  # Always move stop-loss up
