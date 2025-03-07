import pytz
from datetime import datetime, timedelta
from django.utils import timezone
from django.apps import apps
from src.services.config import data


def prepare_binance_time(end_time=None, days_ago=14, date_format="%Y-%m-%d %H:%M:%S"):
    if end_time is None:
        end_time = timezone.now()

    start_time = end_time - timedelta(days=days_ago)

    to_date = datetime.strptime(end_time.strftime(date_format), date_format)
    from_date = datetime.strptime(
        start_time.strftime(date_format), date_format)

    print(f'to date: {to_date} | from date: {from_date}')  # Debug output

    to_date_ms = int(to_date.timestamp() * 1000)
    from_date_ms = int(from_date.timestamp() * 1000)

    return to_date_ms, from_date_ms


def convert_timestamp(timestamp):
    return datetime.fromtimestamp(
        timestamp / 1000, tz=pytz.utc
    )


def batch_insert_klines_data(
        klines,
        symbol=None,
        batch_size=100,
        verbose=False):
    Kline = apps.get_model('market', 'Kline')

    print(f'Length klines: {len(klines)}')
    if symbol is None:
        raise Exception(f"Batch failed. Symbol: {symbol} invalid")

    chunked_klines = []
    for data in klines:

        kline_dict = {
            'symbol': symbol,
            'time': convert_timestamp(data[6]),
            'timestamp': convert_timestamp(data[0]),
            'open': data[1],
            'high': data[2],
            'low': data[3],
            'close': data[4],
            'volume': data[5],
            'num_of_trades': data[8]
        }
        # print(kline_dict)
        chunked_klines.append(
            Kline(**kline_dict)
        )

    Kline.objects.bulk_create(chunked_klines, ignore_conflicts=True)
    print("finished chunk")
    return len(klines)


'''
    [
        1741185000000,      # 0 time
        '0.21870000',       # 1 open
        '0.22000000',       # 2 high
        '0.21600000',       # 3 low
        '0.21780000',       # 4 Close
        '280108.10000000',  # 5 volume
        1741185899999,      # 6 close_time
        '61127.38483000',   # 7 Quote asset volume
        825,                # 8 Number of trades
    ]
'''


def batch_insert_stock_data(
        dataset,
        company_obj=None,
        batch_size=1000,
        verbose=False):
    StockQuote = apps.get_model('market', 'StockQuote')
    batch_size = 1000
    if company_obj is None:
        raise Exception(f"Batch failed. Company Object {company_obj} invalid")
    for i in range(0, len(dataset), batch_size):
        if verbose:
            print("Doing chunk", i)
        batch_chunk = dataset[i:i+batch_size]
        chunked_quotes = []
        for data in batch_chunk:
            chunked_quotes.append(
                StockQuote(company=company_obj, **data)
            )
        StockQuote.objects.bulk_create(chunked_quotes, ignore_conflicts=True)
        if verbose:
            print("finished chunk", i)
    return len(dataset)
