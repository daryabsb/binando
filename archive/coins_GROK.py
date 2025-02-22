import pandas as pd
from decimal import Decimal, ROUND_DOWN, ROUND_UP
from binance.client import Client
import pandas_ta as ta
from bot.market import get_algoalpha_trend, get_volume
from _utils.const import meme_coins
from ta.momentum import ROCIndicator


def get_sma(client, symbol, period=20):
    """Fetch historical prices and calculate SMA."""
    try:
        klines = client.get_klines(
            symbol=symbol, interval="15m", limit=period)  # 15-minute candles
        closes = [float(k[4]) for k in klines]  # Closing prices

        if len(closes) < period:
            print(f"⚠️ Not enough data for SMA {period}.")
            return None

        df = pd.DataFrame(closes, columns=["close"])
        df["sma"] = ta.sma(df["close"], length=period)

        return df["sma"].iloc[-1]  # Latest SMA value
    except Exception as e:
        print(f"⚠️ Error calculating SMA for {symbol}: {e}")
        return None


def get_roc(client, symbol, period=24):
    """Fetch historical prices and calculate the Rate of Change (ROC) indicator."""
    try:
        klines = client.get_klines(
            symbol=symbol, interval="1h", limit=period + 1)
        close_prices = [Decimal(kline[4]) for kline in klines]

        if len(close_prices) < period + 1:
            print(f"⚠️ Not enough data for {symbol} ROC calculation.")
            return Decimal("0.0")

        close_series = pd.Series(close_prices, dtype="float64")
        roc = ROCIndicator(close_series, window=period).roc().iloc[-1]
        return Decimal(str(roc)) / 100  # Convert to decimal format
    except Exception as e:
        print(f"⚠️ Error fetching ROC for {symbol}: {e}")
        return Decimal("0.0")


def get_price(client, symbol):
    """Get the current price of a symbol."""
    ticker = client.get_symbol_ticker(symbol=symbol)
    return float(ticker["price"])


def calculate_trade_levels(df, risk_multiplier=1.5):
    """
    Generates Stop Loss (SL) and Take Profit (TP) based on ATR.
    - SL = 1 ATR away from entry price.
    - TP = 1.5x the risk (ATR) beyond entry.
    """
    df["stop_loss"] = df["close"] - df["atr"]  # SL for long positions
    df["take_profit"] = df["close"] + \
        (df["atr"] * risk_multiplier)  # 1.5x ATR for TP

    # Reverse for short positions
    df["short_stop_loss"] = df["close"] + df["atr"]
    df["short_take_profit"] = df["close"] - (df["atr"] * risk_multiplier)

    return df[["stop_loss", "take_profit", "short_stop_loss", "short_take_profit"]]


def get_sorted_symbols(client):
    """Sort and filter symbols based on strong trend signals, with caching."""
    from _utils.cache import load_cached_sorted_symbols, save_sorted_symbols
    from _utils.helpers import is_bullish_trend

    # ✅ Try loading from cache first
    # cached_symbols = load_cached_sorted_symbols()
    # if cached_symbols:
    #     return cached_symbols

    trending_coins = []
    skipped_count = 0  # Track skipped coins
    for symbol in meme_coins:
        try:
            # Convert Decimal to float
            current_price = float(get_price(client, symbol))
            roc = float(get_roc(client, symbol))  # Convert Decimal to float
            # Convert Decimal to float
            volume = float(get_volume(client, symbol))

            # ✅ Filter only bullish coins
            # if not is_bullish_trend(client, symbol):
            #     skipped_count += 1
            #     print(f"⚠️ Skipping {symbol}: Not bullish.")
            #     continue  # Skip if it's not consistently bullish

            algoalpha_trend = float(get_algoalpha_trend(
                client, symbol))  # Convert Decimal to float

            trending_coins.append({
                "symbol": symbol,
                "price": current_price,
                "roc": roc,
                "volume": volume,
                "algoalpha_trend": algoalpha_trend,
            })
        except Exception as e:
            print(f"⚠️ Skipping {symbol}: {e}")  # Log the error and continue

    # ✅ Sort by highest volume & momentum
    sorted_coins = sorted(trending_coins, key=lambda x: (
        x["volume"], abs(x["roc"]), x["algoalpha_trend"]), reverse=True)

    # ✅ Save sorted list to cache
    save_sorted_symbols(sorted_coins)

    return sorted_coins


def get_balance(client: Client, symbol="USDT"):
    """Retrieve the available USDT balance."""
    if not client:
        return 0.0
    if symbol == "USDT":
        balance = client.get_asset_balance(asset="USDT")
    else:
        asset = symbol.replace("USDT", "")  # Extract asset name
        balance = client.get_asset_balance(asset=asset)
    return float(balance["free"])


def get_usdt_balance(client):
    """Retrieve the available USDT balance."""
    balance = client.get_asset_balance(asset="USDT")
    balance = 200
    return balance  # float(balance["free"])


def get_coin_balance(client, symbol):
    """Retrieve the available balance for a specific coin, return 0 if not owned."""
    asset = symbol.replace("USDT", "")  # Extract asset name
    balance_info = client.get_asset_balance(asset=asset)

    if balance_info is None:
        return Decimal('0.0')  # If user has no balance, return 0 safely

    return Decimal(balance_info["free"])


def get_previous_hour_price(client, symbol, interval="1h"):
    """Get the price of a symbol one hour ago using historical klines."""
    selected_interval = get_history_options(interval)

    klines = client.get_klines(
        symbol=symbol, interval=selected_interval, limit=2)
    return float(klines[0][4])  # Closing price of the previous hour


def calculate_quantity3(client, symbol, amount, trade_type):
    """Calculate correct quantity based on Binance precision rules and risk management."""
    from _utils.helpers import get_min_notional, get_step_size_and_min_qty
    from bot.coins import get_sma

    price = Decimal(get_price(client, symbol))
    step_size, min_qty = get_step_size_and_min_qty(client, symbol)
    min_notional = get_min_notional(client, symbol)

    sma = Decimal(get_sma(client, symbol, period=20) or price)  # Avoid None

    # ✅ Ensure valid step size & min qty
    if not step_size or not min_qty:
        print(f"⚠️ Error fetching step size or minQty for {symbol}.")
        return None

    step_size, min_qty, min_notional = map(
        Decimal, (step_size, min_qty, min_notional))

    # ✅ Use fixed trading percentage
    USDT_TRADE_PERCENTAGE = Decimal("0.25")  # 25% of total USDT
    PER_TRADE_PERCENTAGE = Decimal("0.10")  # 10% of allocated balance

    trade_usdt = (amount * USDT_TRADE_PERCENTAGE) * \
        PER_TRADE_PERCENTAGE if amount >= Decimal("5") else Decimal("5")

    # ✅ Buy: Allocate a portion of available USDT
    if trade_type == "BUY":
        # usdt_balance = Decimal(get_usdt_balance(client))
        quantity = (trade_usdt / price).quantize(step_size,
                                                 rounding=ROUND_DOWN)
        print(f'')

    # ✅ Sell: Trade a portion of the coin balance worth `trade_usdt`
    else:  # trade_type == "SELL"
        available_balance = Decimal(get_coin_balance(client, symbol) or 0)
        trade_usdt = (available_balance * price *
                      USDT_TRADE_PERCENTAGE) * PER_TRADE_PERCENTAGE
        quantity = (trade_usdt / price).quantize(step_size,
                                                 rounding=ROUND_DOWN)
    # ✅ Ensure order meets minNotional and minQty
    # if (quantity * price) < min_notional or quantity < min_qty:
    #     print(
    #         f"⚠️ {symbol} Order too small ({quantity * price} < {min_notional}), skipping.")
    #     return None

    print(
        f'Trade usdt: {trade_usdt} || Step size: {step_size} || raw quantity: {quantity:.6f}')
    return str(quantity)  # Convert to string for Binance API


from decimal import Decimal, ROUND_DOWN, ROUND_UP

def calculate_quantity(client, symbol, amount, trade_type):
    from _utils.helpers import get_min_notional, get_step_size_and_min_qty
    USDT_TRADE_PERCENTAGE = Decimal("0.25")  # 25% of total USDT
    PER_TRADE_PERCENTAGE = Decimal("0.10")  # 10% of allocated balance
    # Fetch symbol-specific data
    price = Decimal(get_price(client, symbol))
    step_size, min_qty = get_step_size_and_min_qty(client, symbol)
    min_notional = get_min_notional(client, symbol)

    step_size = Decimal(step_size)
    min_qty = Decimal(min_qty)
    min_notional = Decimal(min_notional)

    desired_trade_usdt = Decimal('5.0000')  # Simplified from your logic
    trade_usdt = max(desired_trade_usdt, min_notional)

    if trade_type == "BUY":
        raw_quantity = trade_usdt / price  # e.g., 5 / 1.1777 ≈ 4.24556339
        steps = (raw_quantity / step_size).quantize(Decimal('1.'), rounding=ROUND_UP)  # 42.4556339 → 43
        quantity = steps * step_size  # 43 * 0.1 = 4.3
        notional = quantity * price  # 4.3 * 1.1777 ≈ 5.06411

        if notional < min_notional:
            print(f"⚠️ Notional {notional} below {min_notional}")
            return None

    else:  # trade_type == "SELL"
        available_balance = Decimal(get_coin_balance(client, symbol) or 0)
        if available_balance <= 0:
            print(f"⚠️ No {symbol} balance to sell.")
            return None
        # Desired quantity based on percentage of holdings
        desired_quantity = available_balance * USDT_TRADE_PERCENTAGE * PER_TRADE_PERCENTAGE
        trade_usdt = desired_quantity * price
        # Ensure trade_usdt meets min_notional
        trade_usdt = max(trade_usdt, min_notional)
        quantity = (trade_usdt / price).quantize(step_size, rounding=ROUND_DOWN)
        # Ensure quantity meets min_qty
        if quantity < min_qty:
            quantity = min_qty
        # Verify notional value
        notional = quantity * price
        if notional < min_notional:
            min_quantity = (min_notional / price).quantize(step_size, rounding=ROUND_UP)
            quantity = min_quantity if min_quantity <= available_balance else available_balance.quantize(step_size, rounding=ROUND_DOWN)
        # Final check against available balance
        if quantity > available_balance:
            print(f"⚠️ Insufficient {symbol} balance for sell order.")
            return None

    # Final validation
    if quantity < min_qty or notional < min_notional:
        print(f"⚠️ Cannot meet min_qty ({min_qty}) or min_notional ({min_notional}) for {symbol}.")
        return None

    return str(quantity)



















def calculate_quantity2(client, symbol, amount, trade_type):
    """
    Calculate the correct quantity for trading based on a fixed 5 USDT amount from a 200 USDT balance.

    Args:
        client: Binance client instance
        symbol: Trading pair (e.g., 'SANDUSDT')
        amount: Total USDT balance (e.g., 200)
        trade_type: 'BUY' or 'SELL'
        price: Current price of the coin (optional, fetched if not provided)
        min_notional: Minimum notional value (optional, fetched if not provided)
        min_qty: Minimum quantity (optional, fetched if not provided)
        step_size: Step size for quantity precision (optional, fetched if not provided)

    Returns:
        str: Quantity as a string formatted for Binance API, or None if invalid
    """
    from _utils.helpers import get_min_notional, get_step_size_and_min_qty
    from bot.coins import get_sma

    price = Decimal(get_price(client, symbol))
    step_size, min_qty = get_step_size_and_min_qty(client, symbol)
    min_notional = get_min_notional(client, symbol)

    # Fetch required data if not provided
    if price is None:
        price = Decimal(client.get_symbol_ticker(symbol=symbol)['price'])
    if step_size is None or min_qty is None or min_notional is None:
        info = client.get_symbol_info(symbol)
        # Convert to Decimal precision
        step_size = Decimal(info['quantityPrecision'])
        min_qty = Decimal(info['filters'][2]['minQty'])  # LOT_SIZE filter
        # MIN_NOTIONAL filter
        min_notional = Decimal(info['filters'][3]['minNotional'])

    # Convert inputs to Decimal for precision
    amount = Decimal(str(amount))  # Total balance (e.g., 200 USDT)
    # Convert precision to step size (e.g., 0.001)

    # Fixed trade amount: 5 USDT (2.5% of 200 USDT)
    print('TRADE_AMOUNT_USDT: ', amount * Decimal("0.025"))
    TRADE_AMOUNT_USDT = Decimal('5')

    if trade_type == "BUY":
        # Initial quantity calculation
        raw_quantity = TRADE_AMOUNT_USDT / price
        quantity = raw_quantity.quantize(step_size, rounding=ROUND_DOWN)
        total_value = quantity * price
        # Adjust quantity to meet minNotional and minQty
        if total_value < min_notional or quantity < min_qty:
            # Increase to meet minNotional
            adjusted_quantity = (
                min_notional / price).quantize(step_size, rounding=ROUND_UP)
            total_value = adjusted_quantity * price
            if adjusted_quantity < min_qty:
                adjusted_quantity = min_qty.quantize(
                    step_size, rounding=ROUND_UP)
                total_value = adjusted_quantity * price
            quantity = adjusted_quantity
            print(
                f"⚠️ Adjusted BUY quantity to meet filters: {quantity} (Value: {total_value} USDT)")
            return str(quantity)  # Convert to string for Binance API
    elif trade_type == "SELL":
        # Get available coin balance
        coin = symbol.replace('USDT', '')
        available_balance = Decimal(
            client.get_asset_balance(asset=coin)['free'] or '0')
        # Initial quantity calculation (limited by available balance)
        raw_quantity = TRADE_AMOUNT_USDT / price
        quantity = min(raw_quantity, available_balance).quantize(
            step_size, rounding=ROUND_DOWN)
        total_value = quantity * price
        # Adjust quantity to meet minNotional and minQty
        if total_value < min_notional or quantity < min_qty:
            adjusted_quantity = (
                min_notional / price).quantize(step_size, rounding=ROUND_UP)
            if adjusted_quantity < min_qty:
                adjusted_quantity = min_qty.quantize(
                    step_size, rounding=ROUND_UP)
            if adjusted_quantity <= available_balance:
                quantity = adjusted_quantity
                total_value = quantity * price
                print(
                    f"⚠️ Adjusted SELL quantity to meet filters: {quantity} (Value: {total_value} USDT)")
                return str(quantity)  # Convert to string for Binance API
            else:
                print(
                    f"⚠️ Insufficient balance for SELL: {available_balance} < {adjusted_quantity}")
                return None
        if quantity == 0:
            print(
                f"⚠️ No sufficient balance to sell (available: {available_balance})")
            return None
    else:
        print(f"❌ Invalid trade_type: {trade_type}. Use 'BUY' or 'SELL'.")
        return None


# Example usage
if __name__ == "__main__":
    from binance.client import Client
    client = Client('your_api_key', 'your_api_secret')
    symbol = 'SANDUSDT'
    total_balance = 200  # Your total USDT balance

    # Test BUY
    qty_buy = calculate_quantity(client, symbol, total_balance, 'BUY')
    print(f"BUY Quantity: {qty_buy}")

    # Test SELL
    qty_sell = calculate_quantity(client, symbol, total_balance, 'SELL')
    print(f"SELL Quantity: {qty_sell}")
