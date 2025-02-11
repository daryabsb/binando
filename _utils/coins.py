
from decimal import Decimal
from _utils.client import get_client

client = get_client()

def get_balance(symbol="USDT"):
    """Retrieve the available USDT balance."""
    if symbol == "USDT":
        balance = client.get_asset_balance(asset="USDT")
    else:
        asset = symbol.replace("USDT", "")  # Extract asset name
        balance = client.get_asset_balance(asset=asset)
    return float(balance["free"])


def get_usdt_balance():
    """Retrieve the available USDT balance."""
    balance = client.get_asset_balance(asset="USDT")
    return float(balance["free"])


def get_coin_balance(symbol):
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


def get_step_size_and_min_qty(symbol):
    """Retrieve the step size and minimum quantity for a given symbol."""
    exchange_info = client.get_symbol_info(symbol)

    step_size = min_qty = None

    for f in exchange_info["filters"]:
        if f["filterType"] == "LOT_SIZE":
            step_size = Decimal(f["stepSize"])
            min_qty = Decimal(f["minQty"])

    return step_size, min_qty


def get_previous_hour_price(symbol, interval="1h"):
    """Get the price of a symbol one hour ago using historical klines."""
    selected_interval = get_history_options(interval)

    klines = client.get_klines(
        symbol=symbol, interval=selected_interval, limit=2)
    return float(klines[0][4])  # Closing price of the previous hour

