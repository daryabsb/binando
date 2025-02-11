from _utils.const import LAST_TRADE


def should_trade(symbol, current_price, trade_type, threshold):
    """
    Check if we should place a trade based on price movement and prevent repeated trades.
    """
    last_price = LAST_TRADE.get(symbol, None)

    if last_price is None:
        LAST_TRADE[symbol] = current_price  # Initialize tracking
        return True  # Allow first trade

    price_change = (current_price - last_price) / last_price

    if trade_type == "BUY" and price_change <= -threshold:
        LAST_TRADE[symbol] = current_price  # Update last trade price
        return True
    elif trade_type == "SELL" and price_change >= threshold:
        LAST_TRADE[symbol] = current_price  # Update last trade price
        return True

    return False  # No trade if conditions are not met

