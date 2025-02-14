from decimal import Decimal


def get_min_notional(client, symbol):
    """Fetch the minimum notional value required for a trade."""
    try:
        exchange_info = client.get_symbol_info(symbol)
        filters = exchange_info["filters"]
        for f in filters:
            if f["filterType"] == "NOTIONAL":
                return Decimal(f["minNotional"])
    except Exception as e:
        print(f"⚠️ Error fetching minNotional for {symbol}: {e}")
    return Decimal("0.0")  # Default value


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
