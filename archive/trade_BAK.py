import pandas as pd
from ta.momentum import ROCIndicator
from _utils.const import LAST_TRADE
from bot.coins import get_coin_balance
from decimal import Decimal


def get_24h_price_change(client, symbol):
    """Fetch the 24-hour price change percentage from Binance API."""
    try:
        ticker = client.get_ticker(symbol=symbol)
        # Convert to decimal
        price_change = Decimal(ticker["priceChangePercent"]) / 100
        return price_change
    except Exception as e:
        print(f"⚠️ Error fetching 24h price change for {symbol}: {e}")
        return Decimal("0.0")  # Default to no change if API fails


def get_roc(client, symbol, period=24):
    """Fetch historical prices and calculate ROC (Rate of Change) over the given period."""
    try:
        klines = client.get_klines(
            symbol=symbol, interval="1h", limit=period + 1)
        close_prices = [Decimal(kline[4])
                        for kline in klines]  # Closing prices

        # Ensure we have enough data
        if len(close_prices) < period + 1:
            print(f"⚠️ Not enough data for {symbol} ROC calculation.")
            return Decimal("0.0")

        # Convert to Pandas Series
        close_series = pd.Series(close_prices, dtype="float64")

        # Compute ROC
        roc = ROCIndicator(close_series, window=period).roc(
        ).iloc[-1]  # Get the latest ROC
        return Decimal(str(roc)) / 100  # Convert to decimal format
    except Exception as e:
        print(f"⚠️ Error fetching ROC for {symbol}: {e}")
        return Decimal("0.0")  # Default to no change if API fails


def should_trade(client, symbol, current_price, trade_type, threshold):
    """
    Check if we should place a trade based on the Rate of Change (ROC) indicator.
    Uses ROC if no balance or last trade exists.
    """
    last_price = LAST_TRADE.get(symbol, None)
    last_price = last_price if last_price else current_price  # Ensure it's not empty

    coin_balance = get_coin_balance(client, symbol)

    price_change_roc = get_roc(client, symbol)  # Get ROC over 24 hours

    # Use ROC if we have no balance or no previous trade
    if coin_balance is None or coin_balance == Decimal("0.0") and trade_type == "SELL":

        if price_change_roc <= threshold:  # Buying condition
            print(
                f"✅ Buying {symbol} based on ROC drop of {price_change_roc:.2%}.")
            return True
        else:
            return False  # Don't trade if it doesn't meet the condition
    elif trade_type == "SELL" and price_change_roc >= threshold:
        print(
            f"🔄 {symbol} | ROC Change: {price_change_roc:.2%}, Threshold: {threshold:.2%}")
        LAST_TRADE[symbol] = current_price  # Update last trade price
        return True

    # If we have a balance, use the previous trade price logic
    if last_price is None:
        last_price = current_price  # Initialize tracking
        LAST_TRADE[symbol] = current_price  # Initialize tracking
    #     return False  # Do not trade unless price change meets criteria

    last_price = Decimal(last_price) if last_price else Decimal("0.0")
    price_change = (Decimal(current_price) - last_price) / last_price
    print(f"🔍 {symbol} | {trade_type}: Price Change: {price_change:.2%}, Threshold: {threshold:.2%}")

    if trade_type == "BUY" and price_change <= -threshold:
        LAST_TRADE[symbol] = current_price  # Update last trade price
        return True

    elif trade_type == "SELL" and price_change >= threshold:
        LAST_TRADE[symbol] = current_price  # Update last trade price
        print(
            f"🔄 CHECK SHOULD: {symbol} | Reached here anyway")
        return True

    return False  # No trade if conditions are not met
