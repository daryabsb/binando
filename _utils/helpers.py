from decimal import Decimal
from bot.coins import get_price


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

def is_bullish_trend(client, symbol):
    """Check if a coin is in a strong uptrend using ZLMA in multiple timeframes."""
    timeframes = ["5m", "15m", "1h", "4h", "1d"]  # Short to long-term trends
    current_price = get_price(client, symbol)

    bullish_trend = all(current_price > get_zlma(
        client, symbol, tf) for tf in timeframes)

    return bullish_trend

def get_zlma(client, symbol, interval):
    """Calculate Zero Lag Moving Average (ZLMA) for a given symbol and interval."""
    klines = client.get_klines(
        symbol=symbol, interval=interval, limit=50)  # Get last 50 candles
    closes = [Decimal(k[4]) for k in klines]  # Close prices

    alpha = Decimal("2") / (Decimal(len(closes)) + Decimal("1"))
    zlma = sum(closes) / len(closes)  # Simple Moving Average as starting point

    for close in closes:
        zlma = (alpha * close) + \
            ((Decimal("1") - alpha) * zlma)  # ZLMA formula

    return zlma