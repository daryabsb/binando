from datetime import timedelta

# settings.py or config.py
KLINE_FETCH_INTERVAL = "5m"  # Common interval for fetching klines
KLINE_FETCH_PERIOD = timedelta(hours=24)  # Standard historical data range
KLINE_FRESHNESS_LOOKBACK = timedelta(
    minutes=5)  # Freshness check (latest kline)
