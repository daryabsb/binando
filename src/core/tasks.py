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


@shared_task
def test_tasks():
    print('test_works')
    return 'Bravo!!'


@shared_task
def update_klines(symbols=None):
    """Update Kline data for the last 15 minutes."""
    import zoneinfo
    from tzlocal import get_localzone
    from datetime import timezone as dt_timezone

    Symbol = apps.get_model("market", "Symbol")
    if symbols is None:
        symbols = Symbol.objects.filter(active=True).values_list(
            "ticker", flat=True)

    client = get_client()

    now = timezone.now()
    start_date = now - timedelta(minutes=150)

    now_utc = now.astimezone(dt_timezone.utc)
    start_utc = start_date.astimezone(dt_timezone.utc)

    tz_name = str(get_localzone())
    user_tz = zoneinfo.ZoneInfo(tz_name)

    local_now = now_utc.astimezone(dt_timezone.utc)
    local_start = start_utc.astimezone(dt_timezone.utc)

    to_date_ms = int(local_now.timestamp() * 1000)
    from_date_ms = int(local_start.timestamp() * 1000)

    for symbol in symbols:
        symbol_full = symbol + "USDT"
        try:
            # print(
            #     f"Fetching last 15min klines for {symbol_full} from {local_now} to {local_start}")

            klines = client.get_klines(
                symbol=symbol_full,
                interval="5m",
                startTime=from_date_ms,
                endTime=to_date_ms
            )

            if not klines:
                print(f"No klines returned for {symbol_full}")
                continue

            Kline = apps.get_model("market", "Kline")
            batch = []
            for kline in klines:
                # open_time = datetime.fromtimestamp(int(kline[0]) / 1000, tz=dt_timezone.utc)
                close_time = datetime.fromtimestamp(
                    int(kline[6]) / 1000, tz=dt_timezone.utc)

                obj = Kline(
                    # Store full symbol (e.g., 'BURGERUSDT')
                    symbol=symbol_full,
                    # timestamp=open_time,  # Opening time
                    time=close_time,      # Closing time
                    open=Decimal(kline[1]),
                    high=Decimal(kline[2]),
                    low=Decimal(kline[3]),
                    close=Decimal(kline[4]),
                    volume=Decimal(kline[5])
                )
                batch.append(obj)

            if batch:
                created_batch = Kline.objects.bulk_create(
                    batch, ignore_conflicts=True)
                print(
                    f"Inserted {len(created_batch)} klines for {symbol_full}, latest close: {batch[-1].time}")

                # Verify insertion
                # latest = Kline.objects.filter(
                #     symbol=symbol_full).order_by('-time').first()
                # if latest:
                #     print(
                #         f"DB verification for {symbol_full}: latest close {latest.time}")
                # else:
                #     print(
                #         f"WARNING: No klines found in DB for {symbol_full} after insert")
            else:
                print(f"No valid klines to insert for {symbol_full}")

        except Exception as e:
            print(f"Error updating kline for {symbol_full}: {e}")

    return 'Done updating klines'


@shared_task
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


@shared_task
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
