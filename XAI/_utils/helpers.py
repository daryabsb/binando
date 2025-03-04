from decimal import Decimal
import math
import pandas as pd
import ta
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
    symbol_info = client.get_symbol_info(symbol)
    lot_size_filter = next((f for f in symbol_info["filters"] if f["filterType"] == "LOT_SIZE"), None)
    if lot_size_filter:
        return Decimal(lot_size_filter["stepSize"]), Decimal(lot_size_filter["minQty"])
    raise ValueError(f"No LOT_SIZE filter for {symbol}")


def is_bullish_trend(client, symbol, pullback=False):
    """Check if a coin is in a strong uptrend or pullback using Zero Lag Trend Signals."""
    timeframes = ["5m", "15m", "1h", "4h",
                  "1d"] if not pullback else ["15m", "1h", "4h", "1d"]

    # Assume get_price returns a string or float
    current_price = Decimal(get_price(client, symbol))

    trends = []
    for tf in timeframes:
        zlma, atr, volatil = get_zlma(client, symbol, tf)

        if zlma is not None and volatil is not None:
            if current_price > zlma + volatil:
                trends.append(True)
            elif current_price < zlma - volatil:
                trends.append(False)
            else:
                trends.append(None)
        else:
            print(f"Invalid ZLMA or Volatility for {symbol}")
            trends.append(None)

    # Return True if all trends are bullish, False if all are bearish, else None
    if all(trend is True for trend in trends):
        return True
    elif all(trend is False for trend in trends):
        return False
    else:

        return None  # Mixed or insufficient data


def get_klines_data(client, symbol, interval, limit):
    klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
    for i, kline in enumerate(klines):
        try:
            # Example for close price, but you might want to check all relevant fields
            close_price = Decimal(kline[4])
        except ValueError:
            print(
                f"NaN or invalid value detected at index {i} for {symbol} on {interval}")
    return klines

# Use this function to fetch data


def get_zlma(client, symbol, interval, length=70, mult=Decimal("1.7")):
    klines = get_klines_data(client, symbol, interval, length * 4)
    # klines = client.get_klines(symbol=symbol, interval=interval, limit=length * 4)  # Increased limit for lookback

    # Extract OHLCV data
    src = [Decimal(k[4]) for k in klines]  # Close price for ZLMA calculation
    highs = [Decimal(k[2]) for k in klines]
    lows = [Decimal(k[3]) for k in klines]
    closes = [Decimal(k[4]) for k in klines]

    # ATR Calculation
    atr_values = []
    for i in range(1, len(closes)):
        tr = max(highs[i] - lows[i],
                 abs(highs[i] - closes[i - 1]),
                 abs(lows[i] - closes[i - 1]))
        atr_values.append(tr)

    # Use the last 'length' periods for ATR, ensure enough data
    if len(atr_values) >= length:
        atr = sum(atr_values[-length:]) / Decimal(length)
    else:
        atr = Decimal("0")

    # Volatility Calculation (highest ATR over 3x length period)
    lookback = min(length * 3, len(atr_values))
    if lookback > 0:
        volatil = max(atr_values[-lookback:]) * mult
    else:
        volatil = Decimal("0")

    # ZLMA Calculation
    min_length = 20  # or whatever minimum you decide
    # Adjust length based on data available
    length = min(max(len(src) // 4, min_length), 70)
    lag = math.floor((length - 1) / 2)

    print(f'src:{len(src)} || lag: {lag}')
    if len(src) > lag:
        # Compute ZLMA as per ProBuilder: average[length,1](src+(src-src[lag]))
        zlma_values = []
        for i in range(lag, len(src)):
            diff = src[i] + (src[i] - src[i - lag])  # Zero-lag adjustment
            zlma_values.append(diff)

        if len(zlma_values) >= length:
            zlma = sum(zlma_values[-length:]) / Decimal(length)
        else:
            zlma = sum(zlma_values) / Decimal(len(zlma_values)
                                              ) if zlma_values else Decimal("0")
    else:
        zlma = Decimal("0")

    return zlma, atr, volatil  # Return ZLMA, ATR, and Volatility


timeframes = [
    "1m",
    "3m",
    "5m",
    "15m",
    "30m",
    "1h",
    "2h",
    "4h",
    "6h",
    "8h",
    "12h",
    "1d",
    "3d",
    "1w",
    "1M",
]

'''
BURGERUSDT: [None, None, None, None, True]
1MBABYDOGEUSDT: [None, None, None, None, True]
DOGEUSDT: [None, None, None, None, None]
PEPEUSDT: [False, False, None, None, None]
TFUELUSDT: [None, None, None, None, True]
TRUMPUSDT: [None, None, None, None, None]
SHIBUSDT: [None, None, None, None, None]
XRPUSDT: [None, None, None, None, None]
ENSUSDT: [None, True, None, None, True]
def is_bullish_trend(client, symbol, pullback=True):
    """Check if a coin is in a strong uptrend or pullback using ZLMA in multiple timeframes."""
    timeframes = ["5m", "15m", "1h", "4h", "1d"]
    if pullback:
        timeframes = ["15m", "1h", "4h", "1d"]  # Ignore 5m for pullbacks
    
    current_price = get_price(client, symbol)

    # ✅ Fetch ZLMA for all timeframes
    bullish_trend = all(current_price > get_zlma(client, symbol, tf)[0] for tf in timeframes)  
    # bullish_trend = all(print(f'{symbol} => {get_zlma(client, symbol, tf)}') for tf in timeframes)
    for tf in timeframes:
        print(f'{symbol} => {get_zlma(client, symbol, tf)}')  

    return bullish_trend


def get_zlma(client, symbol, interval):

    """Calculate Zero Lag Moving Average (ZLMA) and ATR for a given symbol and interval."""
    klines = client.get_klines(symbol=symbol, interval=interval, limit=50)  # Get last 50 candles
    
    # Extract OHLCV data
    highs = [Decimal(k[2]) for k in klines]
    lows = [Decimal(k[3]) for k in klines]
    closes = [Decimal(k[4]) for k in klines]

    # ✅ ATR Calculation (14-period standard)
    atr_values = []
    for i in range(1, len(closes)):
        tr = max(highs[i] - lows[i], 
                 abs(highs[i] - closes[i - 1]), 
                 abs(lows[i] - closes[i - 1]))  # True Range formula
        atr_values.append(tr)

    atr = sum(atr_values[-14:]) / Decimal(14)  # 14-period ATR

    # ✅ ZLMA Calculation
    alpha = Decimal("2") / (Decimal(len(closes)) + Decimal("1"))
    zlma = sum(closes) / len(closes)  # SMA as the starting point

    for close in closes:
        zlma = (alpha * close) + ((Decimal("1") - alpha) * zlma)  # ZLMA formula

    return zlma, atr  # Return both ZLMA & ATR

'''
