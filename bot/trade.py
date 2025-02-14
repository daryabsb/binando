import pandas as pd
from decimal import Decimal
from ta.momentum import ROCIndicator
from _utils.const import LAST_TRADE, PRICE_CHANGE_THRESHOLD as threshold
from _utils.helpers import get_min_notional
from bot.coins import get_coin_balance
from bot.coins import get_roc


def get_current_price(client, symbol):
    """Fetch the latest price for a symbol from Binance API."""
    try:
        ticker = client.get_ticker(symbol=symbol)
        return Decimal(ticker["lastPrice"])
    except Exception as e:
        print(f"⚠️ Error fetching current price for {symbol}: {e}")
        return Decimal("0.0")


def is_valid_trade(client, symbol, price, quantity):
    """Check if trade meets Binance's minimum notional value."""
    min_notional = get_min_notional(client, symbol)
    notional_value = Decimal(price) * Decimal(quantity)
    print(f"🔹 {symbol} notional_value: {notional_value}")
    if notional_value < min_notional:
        print(f"⚠️ Order too small: {notional_value} < {min_notional}")
        return False
    return True

# def roc_meets_threshold(roc_value, is_buy):
#     """Check if ROC meets the buy/sell threshold."""
#     return roc_value <= -threshold if is_buy else roc_value >= threshold


def roc_meets_threshold(roc):
    """Check if ROC meets the buy/sell threshold."""
    return roc >= threshold or roc <= -threshold


def should_buy(client, symbol):
    """Check if we should place a BUY trade based on ROC."""
    current_price = get_current_price(client, symbol)
    # Default to current if not tracked
    last_price = LAST_TRADE.get(symbol, None)
    if last_price is None or last_price == Decimal("0.0"):
        last_price = current_price  # Initialize tracking to avoid division errors

    price_change = (Decimal(current_price) -
                    Decimal(last_price)) / Decimal(last_price)

    price_change_roc = get_roc(client, symbol)

    if roc_meets_threshold(price_change_roc):
        print(
            f"✅ Buying {symbol} based on ROC drop of {price_change_roc:.2%}.")
        LAST_TRADE[symbol] = current_price
        return True

    print(
        f"📈 SKIP-BUY: {symbol} | ROC: {price_change_roc:.2%} | Price: {current_price}")

    return False


def should_sell(client, symbol):
    """Check if we should place a SELL trade based on ROC."""
    coin_balance = get_coin_balance(client, symbol)
    if coin_balance is None or coin_balance == Decimal("0.0"):
        return False  # No balance → no sell

    current_price = get_current_price(client, symbol)
    last_price = LAST_TRADE.get(symbol, current_price)
    price_change = (current_price - last_price) / last_price

    price_change_roc = get_roc(client, symbol)

    if roc_meets_threshold(price_change_roc):
        print(f"🔄 Selling {symbol} | ROC Change: {price_change_roc:.2%}.")
        LAST_TRADE[symbol] = current_price
        return True

    print(
        f"📈 SKIP-SELL: {symbol} | ROC: {price_change_roc:.2%} | Price: {current_price}")

    return False
