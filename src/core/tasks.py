import json
import os
from decimal import Decimal
from django.utils import timezone
from datetime import datetime, timedelta, timezone as dt_timezone
from src.services.client import get_client
from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.conf import settings
from django.apps import apps  # .models import Symbol, CryptoCategory
from django.utils.text import slugify
from binance import ThreadedWebsocketManager

# @shared_task
def test_tasks():
    print('test_works')
    return 'Bravo!!'


# @shared_task
def update_usd_value():
    from src.market.utils import get_total_usd
    total_usd = get_total_usd()

    group_name = 'total_usd_update'
    message_type = 'total_usd'

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': message_type,
            'data': str(total_usd),  # Convert datetime to string
        }
    )
    print('Total usd updated!')
    return True


# @shared_task
def update_symbols():
    from django.forms import model_to_dict
    Symbol = apps.get_model('market', 'Symbol')
    Kline = apps.get_model('market', 'Kline')

    symbols = Symbol.objects.filter(active=True)

    for symbol in symbols:
        last_kline = Kline.objects.filter(symbol=symbol.pair).last()
        try:
            symbol.price = last_kline.close
            symbol.volume_24h = str(last_kline.volume)
            symbol.save()
        except Exception as e:
            print(f"{symbol.ticker}: {e}")
    print('Symbols updated!')
    return True

    # json_path = os.path.join(settings.BASE_DIR, 'trading', 'data', 'coins.json')
    # if not os.path.exists(json_path):
    #     return

    # with open(json_path, 'r') as f:
    #     coins = json.load(f)

    # for coin_data in coins:
    #     symbol = Symbol.objects.filter(ticker=coin_data['ticker']).first()
    #     if symbol:
    #         # Update fields
    #         symbol.rank = coin_data['rank']
    #         symbol.price = coin_data['price']
    #         symbol.change_24h = coin_data['change_24h']
    #         symbol.market_cap = coin_data['market_cap']
    #         symbol.volume_24h = coin_data['volume24h']
    #         symbol.circ_supply = coin_data['circ_supply']
    #         symbol.save()  # Triggers WorkflowMixin.notify if included

    #         # Update categories
    #         symbol.categories.clear()
    #         category_names = coin_data['category'].split(', ')
    #         for cat_name in category_names:
    #             category, _ = CryptoCategory.objects.get_or_create(
    #                 name=cat_name,
    #                 defaults={'slug': slugify(cat_name), 'rank': symbol.rank}
    #             )
    #             symbol.categories.add(category)


# @shared_task
def update_klines(symbols=None):
    """Update Kline data for the last 15 minutes."""
    import zoneinfo
    from tzlocal import get_localzone
    from datetime import timezone as dt_timezone
    from django.conf import settings

    KLINE_FETCH_INTERVAL = settings.KLINE_FETCH_INTERVAL
    KLINE_FETCH_PERIOD = settings.KLINE_FETCH_PERIOD

    interval = KLINE_FETCH_INTERVAL

    Symbol = apps.get_model("market", "Symbol")
    Kline = apps.get_model("market", "Kline")
    if symbols is None:
        symbols = Symbol.objects.sorted_symbols()

    client = get_client()
    now = timezone.now()

    start_date = now - KLINE_FETCH_PERIOD

    start_time = now - timedelta(hours=24)

    local_start = start_date.astimezone(dt_timezone.utc)
    local_now = now.astimezone(dt_timezone.utc)

    from_date_ms = int(local_start.timestamp() * 1000)  # Correct order
    to_date_ms = int(local_now.timestamp() * 1000)

    for symbol in symbols:
        try:
            print(
                f"Fetching last 15min klines for {symbol} from {local_start} to {local_now}")

            klines = client.get_historical_klines(
                symbol, interval, from_date_ms, to_date_ms)

            if not klines:
                print(f"No klines returned for {symbol}")
                continue

            batch = []
            for kline in klines:
                close_time = datetime.fromtimestamp(
                    int(kline[6]) / 1000, tz=dt_timezone.utc)

                obj = Kline(
                    symbol=symbol,
                    time=close_time,
                    open=Decimal(kline[1]),
                    high=Decimal(kline[2]),
                    low=Decimal(kline[3]),
                    close=Decimal(kline[4]),
                    volume=Decimal(kline[5])
                )
                batch.append(obj)

            if batch:
                Kline.objects.bulk_create(batch, ignore_conflicts=True)
                print(f"Inserted {len(batch)} klines for {symbol}")

        except Exception as e:
            print(f"Error fetching klines for {symbol}: {e}")

    print('Symbols updated!')
    return True


@shared_task
def update_system_data():
    klines_updated = update_klines()
    if klines_updated:
        symbols_updated = update_symbols()
        if symbols_updated:
            total_usd = update_usd_value()

            if total_usd:
                print('System updated successfully with the latest data!')

