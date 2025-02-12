from _utils.const import LAST_TRADE
from _utils.coins import get_coin_balance
from decimal import Decimal

def get_24h_price_change(client, symbol):
    """Fetch the 24-hour price change percentage from Binance API."""
    try:
        ticker = client.get_ticker(symbol=symbol)
        price_change = Decimal(ticker["priceChangePercent"]) / 100  # Convert to decimal
        return price_change
    except Exception as e:
        print(f"⚠️ Error fetching 24h price change for {symbol}: {e}")
        return Decimal("0.0")  # Default to no change if API fails


def should_trade(client, symbol, current_price, trade_type, threshold):
    """
    Check if we should place a trade based on price movement.
    If no previous price exists, use Binance 24-hour price change instead.
    """
    last_price = LAST_TRADE.get(symbol, None)
    coin_balance = get_coin_balance(client, symbol)

    # If no balance and no last trade price, use 24-hour price change
    if coin_balance is None or coin_balance == Decimal("0.0"):
        price_change_24h = get_24h_price_change(client, symbol)  # Fetch 24h % change
        print(f"📊 {symbol} | 24h Price Change: {price_change_24h:.2%}, Threshold: {threshold:.2%}")

        if price_change_24h <= -threshold:  # Buying condition
            print(f"✅ Buying {symbol} based on 24h price drop of {price_change_24h:.2%}.")
            return True
        else:
            return False  # Don't trade if it doesn't meet the condition

    # If we have a balance, use the last trade price logic
    if last_price is None:
        LAST_TRADE[symbol] = current_price  # Initialize tracking
        return False  # Do not trade unless price change meets criteria

    price_change = (current_price - last_price) / last_price
    print(f"🔍 {symbol} | {trade_type}: Price Change: {price_change:.2%}, Threshold: {threshold:.2%}")

    if trade_type == "BUY" and price_change <= -threshold:
        LAST_TRADE[symbol] = current_price  # Update last trade price
        return True
    elif trade_type == "SELL" and price_change >= threshold:
        LAST_TRADE[symbol] = current_price  # Update last trade price
        return True

    return False  # No trade if conditions are not met




