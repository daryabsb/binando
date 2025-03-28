import json
import time
import dateparser
import pytz
from datetime import datetime, timedelta, timezone as tz
from django.utils import timezone
from binance.client import Client
from src.services.client import get_client

client = get_client()


def date_to_milliseconds(date_str):
    """Convert UTC date to milliseconds
    If using offset strings add "UTC" to date string e.g. "now UTC", "11 hours ago UTC"
    See dateparse docs for formats http://dateparser.readthedocs.io/en/latest/
    :param date_str: date in readable format, i.e. "January 01, 2018", "11 hours ago UTC", "now UTC"
    :type date_str: str
    """
    # get epoch value in UTC
    epoch = datetime.utcfromtimestamp(0).replace(tzinfo=pytz.utc)
    # parse our date string
    d = dateparser.parse(date_str)
    # if the date is not timezone aware apply UTC timezone
    if d.tzinfo is None or d.tzinfo.utcoffset(d) is None:
        d = d.replace(tzinfo=pytz.utc)

    # return the difference in time
    return int((d - epoch).total_seconds() * 1000.0)
# print(date_to_milliseconds("January 01, 2018"))
# print(date_to_milliseconds("11 hours ago UTC"))
# print(date_to_milliseconds("now UTC"))


def interval_to_milliseconds(interval):
    """Convert a Binance interval string to milliseconds
    :param interval: Binance interval string 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w
    :type interval: str
    :return:
         None if unit not one of m, h, d or w
         None if string not in correct format
         int value of interval in milliseconds
    """
    ms = None
    seconds_per_unit = {
        "m": 60,
        "h": 60 * 60,
        "d": 24 * 60 * 60,
        "w": 7 * 24 * 60 * 60
    }

    unit = interval[-1]
    if unit in seconds_per_unit:
        try:
            ms = int(interval[:-1]) * seconds_per_unit[unit] * 1000
        except ValueError:
            pass
    return ms
# print(interval_to_milliseconds(Client.KLINE_INTERVAL_1MINUTE))
# print(interval_to_milliseconds(Client.KLINE_INTERVAL_30MINUTE))
# print(interval_to_milliseconds(Client.KLINE_INTERVAL_1WEEK))


def get_historical_klines(symbol, interval, start_str, end_str=None):
    """Get Historical Klines from Binance
    See dateparse docs for valid start and end string formats http://dateparser.readthedocs.io/en/latest/
    If using offset strings for dates add "UTC" to date string e.g. "now UTC", "11 hours ago UTC"
    :param symbol: Name of symbol pair e.g BNBBTC
    :type symbol: str
    :param interval: Biannce Kline interval
    :type interval: str
    :param start_str: Start date string in UTC format
    :type start_str: str
    :param end_str: optional - end date string in UTC format
    :type end_str: str
    :return: list of OHLCV values
    """
    # create the Binance client, no need for api key

    # init our list
    output_data = []

    # setup the max limit
    limit = 500

    # convert interval to useful value in seconds
    timeframe = interval_to_milliseconds(interval)

    # convert our date strings to milliseconds
    start_ts = date_to_milliseconds(start_str)

    # if an end time was passed convert it
    end_ts = None
    if end_str:
        end_ts = date_to_milliseconds(end_str)

    idx = 0
    # it can be difficult to know when a symbol was listed on Binance so allow start time to be before list date
    symbol_existed = False
    while True:
        # fetch the klines from start_ts up to max 500 entries or the end_ts if set
        temp_data = client.get_klines(
            symbol=symbol,
            interval=interval,
            limit=limit,
            startTime=start_ts,
            endTime=end_ts
        )

        # handle the case where our start date is before the symbol pair listed on Binance
        if not symbol_existed and len(temp_data):
            symbol_existed = True

        if symbol_existed:
            # append this loops data to our output data
            output_data += temp_data

            # update our start timestamp using the last value in the array and add the interval timeframe
            start_ts = temp_data[len(temp_data) - 1][0] + timeframe
        else:
            # it wasn't listed yet, increment our start date
            start_ts += timeframe

        idx += 1
        # check if we received less than the required limit and exit the loop
        if len(temp_data) < limit:
            # exit the while loop
            break

        # sleep after every 3rd call to be kind to the API
        if idx % 3 == 0:
            time.sleep(1)

    return output_data
# fetch 5 minute klines for the last day up until now
# klines = get_historical_klines("BNBBTC", Client.KLINE_INTERVAL_5MINUTE, "5 minutes ago UTC")
# # fetch 30 minute klines for the last month of 2017
# klines = get_historical_klines("ETHBTC", Client.KLINE_INTERVAL_30MINUTE, "1 Dec, 2017", "1 Jan, 2018")
# print(klines[0])

# # fetch weekly klines since it listed
# klines = get_historical_klines("NEOBTC", Client.KLINE_INTERVAL_1WEEK, "1 Jan, 2017")
# print(klines[0])

# kline0 = [
#     timezone.datetime.fromtimestamp(1742889900000 / 1000, tz=tz.utc), 
#     '0.00741000', '0.00741200', '0.00740200', '0.00741100', '42.15700000', 
#     timezone.datetime.fromtimestamp(1742890199999 / 1000, tz=tz.utc), 
#     '0.31224144', 79, '25.64400000', '0.18993065', '0']


def insert_data_to_db():
    from src.market.models import Symbol

    symbols = Symbol.objects.filter(active=True,enabled=True).values_list('pair', flat=True)

    for symbol in symbols:
    
        end = timezone.now()
        start = end - timedelta(days=1)
        end_str = end.strftime("%d %b, %Y")
        start_str = start.strftime("%d %b, %Y")
        interval = Client.KLINE_INTERVAL_5MINUTE

        try:
            klines = get_historical_klines(symbol, interval, start_str, end_str)

            print(f'{symbol} || {len(klines)}')
            # print(f'{symbol} || {timezone.datetime.fromtimestamp(klines[0][0] / 1000, tz=tz.utc).strftime("%Y-%m-%d %H:%M:%S @UTC")}')
            # open a file with filename including symbol, interval and start and end converted to milliseconds
            # with open(
            #     "Binance_{}_{}_{}-{}.json".format(
            #         symbol, 
            #         interval, 
            #         date_to_milliseconds(start),
            #         date_to_milliseconds(end)
            #     ),
            #     'w' # set file write mode
            # ) as f:
            #     f.write(json.dumps(klines))
        except Exception as e:
            print(e)
            




def run():
    # insert_data_to_db()
    from django.db.models import Count
    from src.market.models import Kline

    # Find duplicate Klines
    duplicates = Kline.objects.values('symbol', 'interval', 'end_time').annotate(count=Count('id')).filter(count__gt=1)

    # Remove duplicates, keeping the first entry
    for dup in duplicates:
        Kline.objects.filter(
            symbol=dup['symbol'],
            interval=dup['interval'],
            end_time=dup['end_time']
        ).order_by('id')[1:].delete()

