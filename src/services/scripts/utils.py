
from django.db.models import F, Func, Value
from django.db.models import F, Func
import time
from datetime import timedelta, timezone as dt_timezone
from src.market.models import Symbol, Kline
from decouple import config
from binance.client import Client
from src.market.utils import get_tradingview_widget_url
import requests
from time import sleep
from src.services.tasks import run_trading
from datetime import datetime, timedelta, timezone as dt_timezone
from src.services.client import get_client
from django.apps import apps

from django.utils import timezone
from decimal import Decimal

from datetime import timedelta
import pytz
import pandas as pd


def update_klines2(symbols=None):
    """Update Kline data for the last 15 minutes."""

    Symbol = apps.get_model("market", "Symbol")

    if symbols is None:
        symbols = Symbol.objects.filter(
            active=True).values_list("ticker", flat=True)

    client = get_client(testnet=True)
    for symbol in symbols:
        symbol_full = symbol + "USDT"
        try:
            Kline = apps.get_model("market", "Kline")
            end_time = timezone.now()
            from_time = end_time - timedelta(minutes=15)
            to_date_ms = int(end_time.timestamp() * 1000)
            from_date_ms = int(from_time.timestamp() * 1000)

            print(f"{symbol_full} - {from_time} - {end_time}")
            print(
                f"Fetching last 15min klines for {symbol_full} from {from_time} to {end_time}")

            klines = client.get_klines(
                symbol=symbol_full,
                interval="5m",
                startTime=from_date_ms,
                endTime=to_date_ms
            )

            if not klines:
                print(f"No klines returned for {symbol_full}")
                continue

            batch = []
            for kline in klines:
                # Create UTC-aware datetime objects directly using Python's datetime timezone.
                open_time = datetime.fromtimestamp(
                    int(kline[0]) / 1000, tz=dt_timezone.utc)
                close_time = datetime.fromtimestamp(
                    int(kline[6]) / 1000, tz=dt_timezone.utc)
                obj = Kline(
                    symbol=symbol,
                    timestamp=open_time,  # Opening time
                    time=close_time,      # Closing time
                    open=Decimal(kline[1]),
                    high=Decimal(kline[2]),
                    low=Decimal(kline[3]),
                    close=Decimal(kline[4]),
                    volume=Decimal(kline[5])
                )
                batch.append(obj)

            Kline.objects.bulk_create(batch, ignore_conflicts=True)
            print(
                f"Inserted {len(batch)} klines for {symbol_full}, latest close: {batch[-1].time}")

        except Exception as e:
            print(f"Error updating kline for {symbol_full}: {e}")


timestamp_format = '%Y-%m-%d %H:%M:%S'
eastern = pytz.timezone("US/Eastern")
timestamp_str = "2025-03-05 12:06:00"

# from src.services.config import data
# from src.market.models import Symbol
# tickers = data["currencies"]
# symbols = [Symbol(ticker=currency, pair=f"{currency}USDT") for currency in tickers]
# Symbol.objects.bulk_create(symbols, ignore_conflicts=True)
# print("Symbols created successfully!")
# from src.services.client import get_client
currencies = ["BURGER", "1MBABYDOGE", "DOGE", "PEPE", "TFUEL", "TRUMP", "SHIB", "XRP", "ENS", "MANTA", "TURBO",
              "SUI", "LTC", "BNX", "TRX", "DOT", "CAKE", "STPT", "SCR", "NEAR", "AUDIO", "WLD", "ETHFI", "DGB", "WING", "AI", "BTTC", "JTO", "SFP", "DIA", "JUP", "BEL", "JUV", "WOO", "BLUR",
              ]

# Use with requests
# response = requests.get(url)
# if response.status_code == 200:
#     print("Request successful!")
# else:
#     print(f"Request failed with status code: {response.status_code}")


def update_symbols():
    from src.services.tasks import run_trading
    from src.market.models import CryptoCurency

    # run_trading()
    from src.market.models import Symbol
    # symbols = Symbol.objects.filter(active=True)
    symbols = Symbol.objects.filter(enabled=True, active=True)
    # print(symbols.count())
    for symbol in symbols:
        # symbol.active = False if symbol.ticker not in currencies else True
        if symbol.ticker not in currencies:
            symbol.active = False
            symbol.save()

    # print("Symbols updated successfully!")
        # from django.utils import timezone
        # from datetime import datetime, timedelta, timezone as dt_timezone
        # end_time = timezone.now()  # Current UTC time
        # end_time = datetime.now()  # Current UTC time
        # from_time = end_time - timedelta(minutes=150)  # 15 minutes prior
        # to_date_ms = int(end_time.timestamp())
        # from_date_ms = int(from_time.timestamp())

        # print(f"Datetime now: {datetime.now()}")
        # print(f"End time: {end_time}")
        # # print(f"From time: {from_time}")

        # client = get_client(testnet=True)
        # symbol_full = "DOGEUSDT"
        # print(
        #     f"Fetching last 15min klines for {symbol_full} from {from_time} to {end_time}")

        # klines = client.get_klines(
        #     symbol=symbol_full,
        #     interval="5m",
        #     # startTime=from_date_ms,
        #     # endTime=to_date_ms
        # )

        # print(f"Klines: {len(klines)}")

        # update_klines()


def reset_cryptos():
    from src.market.models import CryptoCurency
    symbols = CryptoCurency.objects.all()
    for symbol in symbols:
        if symbol.ticker == 'USDT':
            symbol.balance = 150.0
            symbol.pnl = 0.0
            symbol.save()
        else:
            symbol.delete()


def batch_delete_kline_data():
    Kline = apps.get_model('market', 'Kline')
    dataset = Kline.objects.all()
    batch_size = 5000

    for i in range(150):
        try:
            queryset = dataset[:batch_size]
            for kline in queryset:
                kline.delete()

            print(i)
        except Exception as e:
            print(f'Error deleting queryset: {e}')

    # for i in range(0, len(dataset), batch_size):
    #     if verbose:
    #         print("Doing chunk", i)
    #     batch_chunk = dataset[i:i+batch_size]
    #     chunked_quotes = []
    #     for data in batch_chunk:
    #         chunked_quotes.append(
    #             StockQuote(company=company_obj, **data)
    #         )
    #     StockQuote.objects.bulk_create(chunked_quotes, ignore_conflicts=True)
    #     if verbose:
    #         print("finished chunk", i)
    # return len(dataset)


PUBLIC = config('api_key')
SECRET = config('secret_key')
client = Client(PUBLIC, SECRET)


def fetch_historical_klines(days=8, interval='5m', batch_size=10):
    """
    Fetch historical Kline data for the last 8 days for all symbols and insert into the database.

    Args:
        days (int): Number of days to fetch (default: 8).
        interval (str): Kline interval, e.g., '5m' for 5 minutes (default: '5m').
        batch_size (int): Number of symbols to process per batch (default: 10).
    """
    # Calculate time range: last 8 days
    print('fetching 8 days started')
    minutes = 10
    days = 8
    end_time = timezone.now()


    start_time = end_time - timedelta(days=days)
    # start_time = end_time - timedelta(minutes=minutes)

    # Get all symbols (assumes sorted_symbols() returns a list like ['BTC', 'ETH', ...])
    symbols = Symbol.objects.filter(active=True, enabled=True).values_list(
        'pair', flat=True)  # sorted_symbols()

    
    # Process symbols in batches to avoid overwhelming the API
    for i in range(0, len(symbols), batch_size):
        batch_symbols = symbols[i:i + batch_size]
        for symbol in batch_symbols:
            # kline_exists = Kline.objects.filter(symbol=symbol).exists()
            # last_kline = Kline.objects.filter(
            #     symbol=symbol).order_by('-start_time').first()
            # # Determine the start time for fetching missing data
            # if last_kline:
            #     start_time = last_kline.end_time  # Start from the end of the last Kline
            # if not kline_exists:
            #     continue
            # Fetch historical Kline data from Binance
            print(f"Fetching data for {symbol}...")
            klines = client.get_historical_klines(
                symbol=f"{symbol}",
                interval=interval,
                start_str=int(start_time.timestamp() * 1000),
                end_str=int(end_time.timestamp() * 1000)
            )

            # Prepare Kline objects for database insertion
            kline_objects = []
            for kline in klines:
                kline_objects.append(Kline(
                    symbol=f"{symbol}",
                    interval=interval,
                    start_time=timezone.datetime.fromtimestamp(
                        kline[0] / 1000, tz=dt_timezone.utc),
                    end_time=timezone.datetime.fromtimestamp(
                        kline[6] / 1000, tz=dt_timezone.utc),
                    open=Decimal(kline[1]),
                    close=Decimal(kline[4]),
                    high=Decimal(kline[2]),
                    low=Decimal(kline[3]),
                    volume=Decimal(kline[5]),
                    quote_volume=Decimal(kline[7]),
                    taker_buy_base_volume=Decimal(kline[9]),
                    taker_buy_quote_volume=Decimal(kline[10]),
                    trade_count=int(kline[8]),
                    is_closed=True,  # Historical data is always closed
                    time=timezone.datetime.fromtimestamp(
                        kline[6] / 1000, tz=dt_timezone.utc)
                ))

            # Insert all Klines for this symbol into the database efficiently
            Kline.objects.bulk_create(kline_objects, ignore_conflicts=True)
            print(f"Inserted {len(kline_objects)} Klines for {symbol}")

        # Small delay to respect Binance API rate limits
        time.sleep(1)
    print('fetching 8 days finished')

# Example usage:
# fetch_historical_klines(days=8, interval='5m')


count = 0


class Replace(Func):
    function = 'REPLACE'
    arity = 3  # REPLACE(string, from_string, to_string)


def update_klines():
    now = timezone.now()

    # Bulk update using REPLACE in SQL
    updated_count = Kline.objects.filter(symbol__contains='USDTUSDT').update(
        symbol=Replace(F('symbol'), Value('USDTUSDT'), Value('USDT'))
    )

    print(f'Updated {updated_count} records.')
    print(f'Completed at {timezone.now()}, started at {now}')
