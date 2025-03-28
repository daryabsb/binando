import pytz
from datetime import datetime, timedelta
from django.utils import timezone
from django.apps import apps
from src.services.config import data
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
import os


def get_total_usd():
    CryptoCurency = apps.get_model('market', 'CryptoCurency')
    Symbol = apps.get_model('market', 'Symbol')
    # Calculate total USD
    total_usd = 0.0
    for crypto in CryptoCurency.objects.exclude(ticker='USDT'):
        try:
            symbol = Symbol.objects.get(ticker=crypto.ticker)
            total_usd += float(crypto.balance) * float(symbol.price)
        except Symbol.DoesNotExist:
            continue
    try:
        total_usd += float(CryptoCurency.objects.get(ticker='USDT').balance)
    except CryptoCurency.DoesNotExist:
        pass

    return total_usd


def upload_image_file_path(instance, filename):
    # Generate file path for new recipe image
    model = instance._meta.model.__name__.lower()
    # ext = filename.split('.')[-1]
    # filename = f'{uuid.uuid4()}.{ext}'

    return os.path.join(f'uploads/{model}/', filename)


def get_tradingview_widget_url(symbol, interval="D", theme="light", style="1", timezone="Etc/UTC"):
    # Base URL
    from urllib.parse import urlencode
    base_url = "https://s.tradingview.com/widgetembed/"

    # Parameters for the URL
    params = {
        "hideideas": "1",
        "overrides": "{}",
        "enabled_features": "[]",
        "disabled_features": "[]",
        "locale": "in",
    }

    # Fragment (part after the #)
    fragment = {
        "symbol": f"BITSTAMP:{symbol}",
        "frameElementId": "tradingview_de890",
        "interval": interval,
        "hide_side_toolbar": "0",
        "allow_symbol_change": "1",
        "save_image": "1",
        "details": "1",
        "calendar": "1",
        "hotlist": "1",
        "studies": "[]",
        "theme": theme,
        "style": style,
        "timezone": timezone,
        "withdateranges": "1",
        "studies_overrides": "{}",
        "utm_medium": "widget",
        "utm_campaign": "chart",
        "utm_term": f"BITSTAMP:{symbol}",
        "page-uri": "__NHTTP__",
    }

    # Combine base URL, query parameters, and fragment
    query_string = urlencode(params)
    fragment_string = urlencode(fragment)
    full_url = f"{base_url}?{query_string}#{fragment_string}"

    return full_url

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


def send_websocket_message(group_name, message_type, data):
    """
    Manually send a WebSocket message to a specified group.

    Args:
        group_name (str): The group to send the message to (e.g., 'crypto_updates', 'trade_notifications').
        message_type (str): The type of message (e.g., 'balance_update', 'trade_update').
        data (dict): The data payload to send (e.g., {'ticker': 'TURBO', 'balance': '5268.8467'}).
    """
    channel_layer = get_channel_layer()
    if channel_layer is None:
        print("Error: Channel layer not available. Ensure Channels is configured.")
        return

    message = {
        'type': message_type,
        'data': data
    }
    async_to_sync(channel_layer.group_send)(
        group_name,
        message
    )
    print(
        f"Sent WebSocket message to {group_name}: {json.dumps(message, indent=2)}")
