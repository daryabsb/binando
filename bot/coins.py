import pandas as pd
from decimal import Decimal, ROUND_DOWN, ROUND_UP
from binance.client import Client

from bot.market import get_algoalpha_trend, get_volume
from _utils.const import meme_coins
from ta.momentum import ROCIndicator


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
            current_price = float(get_price(client, symbol))  # Convert Decimal to float
            roc = float(get_roc(client, symbol))  # Convert Decimal to float
            volume = float(get_volume(client, symbol))  # Convert Decimal to float
            
            # ✅ Filter only bullish coins
            if not is_bullish_trend(client, symbol):
                skipped_count += 1
                print(f"⚠️ Skipping {symbol}: Not bullish.")
                continue  # Skip if it's not consistently bullish

            algoalpha_trend = float(get_algoalpha_trend(client, symbol))  # Convert Decimal to float

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
    sorted_coins = sorted(trending_coins, key=lambda x: (x["volume"], abs(x["roc"]), x["algoalpha_trend"]), reverse=True)

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
    return 200  # float(balance["free"])


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


def calculate_quantity(client, symbol, amount, trade_type):
    """Calculate correct quantity based on Binance precision rules and risk management."""
    from _utils.helpers import get_min_notional, get_step_size_and_min_qty

    price = Decimal(get_price(client, symbol))
    step_size, min_qty = get_step_size_and_min_qty(client, symbol)
    min_notional = get_min_notional(client, symbol)

    # ✅ Ensure valid step size & min qty
    if not step_size or not min_qty:
        print(f"⚠️ Error fetching step size or minQty for {symbol}.")
        return None

    step_size, min_qty, min_notional = map(
        Decimal, (step_size, min_qty, min_notional))

    # ✅ Use fixed trading percentage
    USDT_TRADE_PERCENTAGE = Decimal("0.25")  # 25% of total USDT
    PER_TRADE_PERCENTAGE = Decimal("0.10")  # 10% of allocated balance

    # ✅ Buy: Allocate a portion of available USDT
    if trade_type == "BUY":
        usdt_balance = Decimal(get_usdt_balance(client))
        trade_usdt = (usdt_balance * USDT_TRADE_PERCENTAGE) * \
            PER_TRADE_PERCENTAGE
        quantity = (trade_usdt / price).quantize(step_size,
                                                 rounding=ROUND_UP)

    # ✅ Sell: Trade a portion of the coin balance worth `trade_usdt`
    else:  # trade_type == "SELL"
        available_balance = Decimal(get_coin_balance(client, symbol) or 0)
        trade_usdt = (available_balance * price *
                      USDT_TRADE_PERCENTAGE) * PER_TRADE_PERCENTAGE
        quantity = (trade_usdt / price).quantize(step_size,
                                                 rounding=ROUND_DOWN)

    # ✅ Ensure order meets minNotional and minQty
    if (quantity * price) < min_notional or quantity < min_qty:
        print(
            f"⚠️ {symbol} Order too small ({quantity * price} < {min_notional}), skipping.")
        return None

    return str(quantity)  # Convert to string for Binance API
