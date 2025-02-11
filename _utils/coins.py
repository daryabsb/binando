from decimal import Decimal


def get_balance(client, symbol="USDT"):
    """Retrieve the available USDT balance."""
    if symbol == "USDT":
        balance = client.get_asset_balance(asset="USDT")
    else:
        asset = symbol.replace("USDT", "")  # Extract asset name
        balance = client.get_asset_balance(asset=asset)
    return float(balance["free"])


def get_usdt_balance(client):
    """Retrieve the available USDT balance."""
    balance = client.get_asset_balance(asset="USDT")
    return float(balance["free"])


def get_coin_balance(client, symbol):
    """Retrieve the available balance for a specific coin."""
    asset = symbol.replace("USDT", "")  # Extract asset name
    balance = client.get_asset_balance(asset=asset)
    return Decimal(balance["free"])


def get_percentage_options(key):
    PERCENTAGE_OPTIONS = {
        "1%": 0.01,
        "1.5%": 0.015,
        "2%": 0.02,
        "5%": 0.05,
        "10%": 0.10,
        "20%": 0.20,
        "50%": 0.50
    }
    return PERCENTAGE_OPTIONS[key]


def get_history_options(key):
    from binance.client import Client
    HISTORY_OPTIONS = {
        "1_hour": Client.KLINE_INTERVAL_1HOUR,
        "2_hours": Client.KLINE_INTERVAL_2HOUR,
        "6_hours": Client.KLINE_INTERVAL_6HOUR,
        "12_hours": Client.KLINE_INTERVAL_12HOUR,
        "1_day": Client.KLINE_INTERVAL_1DAY,
        "3_days": Client.KLINE_INTERVAL_3DAY,
        "1_week": Client.KLINE_INTERVAL_1WEEK,
        "1_month": Client.KLINE_INTERVAL_1MONTH
    }
    return HISTORY_OPTIONS[key]


def get_step_size_and_min_qty(client, symbol):
    """Retrieve the step size and minimum quantity for a given symbol."""
    exchange_info = client.get_symbol_info(symbol)

    step_size = min_qty = None

    for f in exchange_info["filters"]:
        if f["filterType"] == "LOT_SIZE":
            step_size = Decimal(f["stepSize"])
            min_qty = Decimal(f["minQty"])

    return step_size, min_qty


def get_previous_hour_price(client, symbol, interval="1h"):
    """Get the price of a symbol one hour ago using historical klines."""
    selected_interval = get_history_options(interval)

    klines = client.get_klines(
        symbol=symbol, interval=selected_interval, limit=2)
    return float(klines[0][4])  # Closing price of the previous hour


def get_price(client, symbol):
    """Get the current price of a symbol."""
    ticker = client.get_symbol_ticker(symbol=symbol)
    return float(ticker["price"])


def calculate_quantity(client, symbol, amount, MAX_TRADE_PERCENTAGE=0.1):
    """Calculate the correct quantity based on Binance precision rules."""
    price = Decimal(get_price(client, symbol))
    step_size, min_qty = get_step_size_and_min_qty(client, symbol)

    if not step_size or not min_qty:
        print(f"⚠️ Error fetching step size or minQty for {symbol}.")
        return None

    available_balance = get_balance(symbol)
    max_trade_amount = available_balance * MAX_TRADE_PERCENTAGE  # Limit trade size

    # Limit by max % balance
    raw_quantity = min(Decimal(amount) / price, max_trade_amount)
    quantity = (raw_quantity // step_size) * step_size  # Adjust to step size

    if quantity < min_qty:
        print(f"⚠️ {symbol} Order too small ({quantity} < {min_qty}), skipping.")
        return None

    return str(quantity)  # Convert to string to avoid precision issues
