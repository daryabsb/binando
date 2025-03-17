import json
import os
from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.conf import settings
from django.apps import apps #.models import Symbol, CryptoCategory
from django.utils.text import slugify

@shared_task
def test_tasks():
    print('test_works')
    return 'Bravo!!'

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