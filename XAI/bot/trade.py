from datetime import datetime, timedelta
from decimal import Decimal, ROUND_DOWN
from ta.momentum import ROCIndicator
from _utils.const import LAST_TRADE, PRICE_CHANGE_THRESHOLD as threshold
from _utils.helpers import get_min_notional
from bot.coins import get_coin_balance, get_price
from bot.coins import get_roc


def get_current_price(client, symbol):
    """Fetch the latest price for a symbol from Binance API and return as float."""
    try:
        ticker = client.get_ticker(symbol=symbol)
        raw_price = ticker["lastPrice"]  # Get price as string

        # Convert from scientific notation to standard float
        price = float(raw_price)

        # Ensure the price is valid (greater than zero)
        if price <= 0:
            print(
                f"⚠️ Received invalid price for {symbol}: {raw_price}. Possible API issue.")
            return 1e-8  # Smallest nonzero price to avoid division errors

        print(f'🔹 {symbol} Price: {price}')
        return price  # Return float instead of Decimal
    except Exception as e:
        print(f"⚠️ Error fetching current price for {symbol}: {e}")
        return 1e-8  # Return small valid number instead of None


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
    from bot.coins import get_sma
    current_price = get_current_price(client, symbol)

    sma = get_sma(client, symbol, period=20)

    if sma is None:
        return False  # No trade if SMA is missing

    # Default to current if not tracked
    last_price = LAST_TRADE.get(symbol, None)

    if last_price is None or last_price == Decimal("0.0"):
        last_price = current_price  # Initialize tracking to avoid division errors
    else:
        price_change = (Decimal(current_price) -
                        Decimal(last_price)) / Decimal(last_price)
        print('Price changed since last trde: ', price_change)

    # price_change_roc = get_roc(client, symbol)

    print(f'🔹 check {symbol} sma: {current_price} vs {sma}')

    if current_price < sma:  # * 0.995:  # Buy if price is 0.5% below SMA
        print(
            f"📈 BUY SIGNAL for {symbol} at {current_price} (below SMA {sma})")
        return True

    print(
        f"📈 SKIP-BUY: {symbol} | SMA: {sma:.2%} | Price: {current_price}")

    return False


def should_sell(client, symbol):
    """Check if we should place a SELL trade based on ROC."""
    from bot.coins import get_sma

    coin_balance = get_coin_balance(client, symbol)

    sma = get_sma(client, symbol, period=20)

    if sma is None:
        return False

    if coin_balance is None or coin_balance == Decimal("0.0"):
        return False  # No balance → no sell

    current_price = get_current_price(client, symbol)
    last_price = LAST_TRADE.get(symbol, current_price)

    price_change = (current_price - last_price) / last_price

    price_change_roc = get_roc(client, symbol)

    # if roc_meets_threshold(price_change_roc):
    #     print(f"🔄 Selling {symbol} | ROC Change: {price_change_roc:.2%}.")
    #     LAST_TRADE[symbol] = current_price
    #     return True

    if current_price > sma:  # * 1.005:  # Sell if price is 0.5% above SMA
        print(
            f"📉 SELL SIGNAL for {symbol} at {current_price} (above SMA {sma})")
        return True
    print(
        f"📈 SKIP-SELL: {symbol} | ROC: {price_change_roc:.2%} | Price: {current_price}")

    return False


def has_recent_trade(client, symbol, min_time_gap=5, price_change_threshold=0.5):
    """Check if a recent trade happened for this symbol based on time or price movement."""
    try:
        # Fetch last 5 trades for the symbol
        trades = client.get_my_trades(symbol=symbol, limit=5)
        if not trades:
            return False  # No trade history, safe to proceed

        last_trade = trades[-1]  # Get the most recent trade
        last_trade_time = datetime.utcfromtimestamp(
            last_trade["time"] / 1000)  # Convert from milliseconds

        # ✅ Ensure correct time calculation
        time_since_last_trade = abs(
            # Convert to minutes
            datetime.utcnow() - last_trade_time).total_seconds() / 60
        # ✅ Time filter (skip if a trade happened too recently)
        if time_since_last_trade < min_time_gap:
            print(
                f"⚠️ Skipping {symbol}: Last trade was {time_since_last_trade:.2f} min ago (Min gap: {min_time_gap} min).")
            return True

        # ✅ Price filter (skip if price change is too small)
        last_trade_price = Decimal(last_trade["price"])
        current_price = Decimal(get_price(client, symbol))
        price_change = abs(
            ((current_price - last_trade_price) / last_trade_price) * 100)

        if price_change < price_change_threshold:
            print(
                f"⚠️ Skipping {symbol}: Price change is only {price_change:.2f}% (Min required: {price_change_threshold}%).")
            return True

        return False  # ✅ Safe to trade

    except Exception as e:
        print(f"⚠️ Error checking trade history for {symbol}: {e}")
        return False  # Assume safe to trade if an error occurs
