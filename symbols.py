
# List of symbols to trade
SYMBOLS = [
    "BTCUSDT",
    "DOGEUSDT",
    "SHIBUSDT",
    "PEPEUSDT",
    "XRPUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "BNBUSDT",
    "TRUMPUSDT",
    "BTCUSDT",
    "ENSUSDT",
    "MANTAUSDT",
    "TURBOUSDT",
    "ETCUSDT",
    "SUIUSDT",
]


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


MEME_COINS = [
    "DOGEUSDT",
    "SHIBUSDT",
    "PEPEUSDT",
    "XRPUSDT",
    "TRUMPUSDT",
    "ENSUSDT",
    "MANTAUSDT",
    "TURBOUSDT",
    "SUIUSDT",
    "TFUELUSDT",
]
