from src.services.bnArb import BnArber
from src.services.config import data
import asyncio
from src.services.client import get_client
from django.apps import apps
from datetime import datetime
from decimal import Decimal
from django.forms import model_to_dict
import pandas as pd
def update_klines2(symbols=None):
    from src.services.config import data
    if symbols is None:
        symbols = data["currencies"]

    client = get_client()
    for symbol in symbols:
        symbol_full = symbol + "USDT"
        try:
            Kline = apps.get_model("market", "Kline")
            klines = client.get_klines(symbol=symbol_full, interval="15m", limit=1)
            dataset = pd.DataFrame(klines)
            if not klines:
                continue
            kline = klines[0]

            # Convert the timestamp from milliseconds to a UTC datetime
            timestamp_ms = int(kline[0])
            timestamp = datetime.fromtimestamp(timestamp_ms / 1000, tz=pytz.utc)

            # print(f'timestamp: {timestamp}|open: {Decimal(kline[1])}|high: {Decimal(kline[2])}|low: {Decimal(kline[3])}|close: {Decimal(kline[4])}|volume: {Decimal(kline[5])}')

            # Optionally, if you want to view this timestamp in Asia/Baghdad time:
            # baghdad_tz = pytz.timezone("Asia/Baghdad")
            # timestamp = timestamp.astimezone(baghdad_tz)
            
            kline_obj = Kline(
                symbol=symbol_full,
                timestamp=timestamp,
                time=timestamp,
                open=kline[1],
                high=kline[2],
                low=kline[3],
                close=kline[4],
                volume=kline[5],
            )
            kline_obj.save()
            # timestamp: 2025-03-05 10:45:00+00:00
            # open: 0.20541000
            # high: 0.20568000
            # low: 0.20378000
            # close: 0.20478000
            # volume: 20244605.00000000
            print(kline_obj)
            # print(model_to_dict(kline_obj))
        except Exception as e:
            print(f"Error updating kline for {symbol}: {e}")

import pytz
timestamp_format = '%Y-%m-%d %H:%M:%S' 
eastern = pytz.timezone("US/Eastern")
timestamp_str = "2025-03-05 12:06:00"


def run():

    update_klines2()
    # Use this approach for Python 3.7+
    # while True:
    #     asyncio.run(main())





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