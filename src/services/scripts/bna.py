
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


@shared_task
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


def run():

    update_klines()


async def main():
    pass
    # try:

    #     bn = BnArber(
    #         data["currencies"],
    #         # data["public"],
    #         # data["secret"],
    #         data["max_amount"]
    #     )
    #     await bn.run()
    # except Exception as e:
    #     print(f"Error in main: {e}")
