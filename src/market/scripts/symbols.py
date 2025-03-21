import os
import json
from django.conf import settings
from src.market.models import Symbol, CryptoCategory
from django.utils.text import slugify
from src.services.client import get_client

count = 0


def initial_data():
    global count
    print('Initial called')

    client = get_client()

    json_path = os.path.join(
        settings.BASE_DIR, 'market', 'coins.json')

    if not os.path.exists(json_path):
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        coins = json.load(f)

    for coin_data in coins:

        # if symbol:
        #     if symbol.coin == coin_data['coin'] or symbol.rank == coin_data['rank']:
        #         continue
        # coin = str(symbol).replace('USDT', '')
        try:
            symbol_data = client.get_ticker(
                symbol=f"{coin_data['ticker']}USDT")

            symbol = Symbol.objects.filter(ticker=coin_data['ticker']).first()
            if not symbol:
                try:
                    symbol = Symbol.objects.filter(
                        coin=coin_data['coin']).first()

                    symbol = Symbol(
                        coin=coin_data['coin'],
                        ticker=coin_data['ticker'],
                        pair=f'{coin_data["ticker"]}USDT',
                        rank=coin_data['rank'],
                        price=coin_data['price'],
                        change_24h=coin_data['change_24h'],
                        market_cap=coin_data['market_cap'],
                        volume_24h=coin_data['volume24h'],
                        circ_supply=coin_data['circ_supply'],
                        logo=coin_data['logo'],
                    )
                    symbol.save(force_insert=True)
                except Exception as e:
                    print("Coin exists: ", e)
                    continue
            if symbol_data:
                print("symbol: ",
                      f"{coin_data['ticker']} || {coin_data['rank']}")
        except Exception as e:
            print(f'Invalid coin detected: {e}')

        #     # Create new symbol
        #         count += 1
        #         print(count)

        # else:
        #     # Update existing symbol
        #     symbol.coin = coin_data['coin']
        #     symbol.rank = coin_data['rank']
        #     symbol.price = coin_data['price']
        #     symbol.change_24h = coin_data['change_24h']
        #     symbol.market_cap = coin_data['market_cap']
        #     symbol.volume_24h = coin_data['volume24h']
        #     symbol.circ_supply = coin_data['circ_supply']
        #     symbol.logo = coin_data['logo']
        #     symbol.save(force_update=True)

        # # Handle categories
        # category_names = coin_data['category'].split(', ')
        # for cat_name in category_names:
        #     category, _ = CryptoCategory.objects.get_or_create(
        #         name=cat_name,
        #         defaults={'slug': slugify(cat_name), 'rank': symbol.rank}
        #     )
        #     symbol.categories.add(category)


def run():
    initial_data()
