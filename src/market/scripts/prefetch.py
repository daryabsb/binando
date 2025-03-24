from django.db.models import Prefetch
from src.market.models import CryptoCurency, Kline
# Fetch all cryptocurrencies
from collections import defaultdict

def check_prefetch():

    try:
        # Fetch all cryptos
        cryptos = CryptoCurency.objects.all()

        # Generate all possible symbols (e.g., ["DOGEUSDT", "BTCUSDT", ...])
        symbols = [f"{crypto.ticker}USDT" for crypto in cryptos]

        # Bulk-fetch klines for all symbols in one query
        klines = Kline.objects.filter(symbol__in=symbols)

        # Group klines by symbol: {"DOGEUSDT": [kline1, kline2, ...]}
        klines_by_symbol = defaultdict(list)
        for kline in klines:
            klines_by_symbol[kline.symbol].append(kline)

        # Attach formatted sparkline data to each crypto
        for crypto in cryptos:
            symbol = f"{crypto.ticker}USDT"
            crypto_klines = klines_by_symbol.get(symbol, [])
            
            # Use your manager method to format klines for charts
            crypto.sparkline_data = Kline.objects.get_klines_spark_list(
                symbol=symbol,
                amount=25 # len(crypto_klines)  # Or a fixed amount (e.g., 100)
            )
        
        return cryptos
    except Exception as e:
        print(f"Error happened: {e}")
        return []


def run():
    cryptos = check_prefetch()
    for crypto in cryptos:
        print(crypto.sparkline_data)