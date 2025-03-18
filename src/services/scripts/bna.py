
from time import sleep
from src.services.tasks import run_trading
from datetime import datetime, timedelta, timezone as dt_timezone
from src.services.client import get_client
from django.apps import apps
from src.services.bnArb import BnArber
from django.utils import timezone
from decimal import Decimal
from celery import shared_task
from datetime import timedelta
import pytz
import pandas as pd


def update_klines(symbols=None):
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

import requests
from src.market.utils import get_tradingview_widget_url
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
    symbols = Symbol.objects.all()
    for symbol in symbols:
        # symbol.active = False if symbol.ticker not in currencies else True
        symbol.active = True
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


def run():
    from urllib.parse import unquote
    # import requests
    # Example usage
    # symbol = "BTCUSD"
    # url = get_tradingview_widget_url(symbol)
    # try:
    #     from urllib import unquote
    # except ImportError:
    #         from urllib.parse import unquote
    # # print(unquote("https://s.tradingview.com/widgetembed/?hideideas=1&overrides=%7B%7D&enabled_features=%5B%5D&disabled_features=%5B%5D&locale=in#%7B%22symbol%22%3A%22BITSTAMP%3ABTCUSD%22%2C%22frameElementId%22%3A%22tradingview_de890%22%2C%22interval%22%3A%22D%22%2C%22hide_side_toolbar%22%3A%220%22%2C%22allow_symbol_change%22%3A%221%22%2C%22save_image%22%3A%221%22%2C%22details%22%3A%221%22%2C%22calendar%22%3A%221%22%2C%22hotlist%22%3A%221%22%2C%22studies%22%3A%22%5B%5D%22%2C%22theme%22%3A%22light%22%2C%22style%22%3A%221%22%2C%22timezone%22%3A%22Etc%2FUTC%22%2C%22withdateranges%22%3A%221%22%2C%22studies_overrides%22%3A%22%7B%7D%22%2C%22utm_medium%22%3A%22widget%22%2C%22utm_campaign%22%3A%22chart%22%2C%22utm_term%22%3A%22BITSTAMP%3ABTCUSD%22%2C%22page-uri%22%3A%22__NHTTP__%22%7D"))
    # print(unquote(url))
    # print(url)



    # url = f'https://s.tradingview.com/widgetembed/?hideideas=1&overrides={}&enabled_features=[]&disabled_features=[]&locale=in#{"symbol":"BITSTAMP:BTCUSD","frameElementId":"tradingview_de890","interval":"D","hide_side_toolbar":"0","allow_symbol_change":"1","save_image":"1","details":"1","calendar":"1","hotlist":"1","studies":"[]","theme":"light","style":"1","timezone":"Etc/UTC","withdateranges":"1","studies_overrides":"{}","utm_medium":"widget","utm_campaign":"chart","utm_term":"BITSTAMP:BTCUSD","page-uri":"__NHTTP__"}'
    
    # data = requests.get(url)
    # print(data.content)
    # usdt_obj = CryptoCurency.objects.get(ticker="USDT")
    # print(f'INITIAL USD BALANCE: {usdt_obj.balance}')
    # update_total_usd()
    update_symbols()
    # while True:
        # update_klines()
    # reset_cryptos()
    # while True:
    #     run_trading()
    #     sleep(3)
    # update_symbols()

