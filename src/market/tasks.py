import redis
import json
from celery.schedules import crontab
from src.services.client import get_client
from src.market.models import Kline
from decimal import Decimal
from celery import shared_task
from datetime import timedelta

from django.apps import apps
from django.utils import timezone

# import helpers.clients as helper_clients

from .utils import batch_insert_stock_data

'''
COMMANDS:

celery -A src worker -l info --pool=solo
celery -A src beat 

'''

interval = 30


DAYS_AGO = 14  # For 14-day RSI, adjust as needed


redis_client = redis.Redis(host='localhost', port=6379, db=0)


def handle_data(self, message):
    try:
        message = json.loads(message)
        market_id = message["stream"].split("@")[0].upper()
        asks = [(float(a[0]), float(a[1]))
                for a in message["data"]["asks"] if len(a) > 1]
        if asks:
            ask = min(asks, key=lambda t: t[0])
            self.data[market_id] = {"ask": [ask[0], ask[1]]}
            # Store price in Redis
            redis_client.set(f"price:{market_id}", ask[0])
    except Exception as e:
        print(f"Error in handle_data: {e}")


# @shared_task
# def run_trading():
#     bot = BnArber(...)  # Initialize your bot
#     bot.get_rates()


@shared_task
def update_prices():
    from src.market.models import Symbol
    client = get_client()
    symbols = Symbol.objects.filter(active=True).values_list('pair', flat=True)
    for symbol in symbols:
        ticker = client.get_ticker(symbol=symbol)
        redis_client.set(f"price:{symbol}", ticker['lastPrice'])


@shared_task
def update_klines(symbols):
    client = get_client()
    for symbol in symbols:
        try:
            klines = client.get_klines(
                symbol=symbol, interval="15m", limit=1)  # Latest 15m kline
            kline = klines[0]
            timestamp = timezone.from_timestamp(int(kline[0]) / 1000)
            Kline.objects.update_or_create(
                symbol=symbol,
                timestamp=timestamp,
                defaults={
                    'open': Decimal(kline[1]),
                    'high': Decimal(kline[2]),
                    'low': Decimal(kline[3]),
                    'close': Decimal(kline[4]),
                    'volume': Decimal(kline[5]),
                }
            )
            # Delete old data
            cutoff = timezone.now() - timedelta(days=DAYS_AGO)
            Kline.objects.filter(symbol=symbol, timestamp__lt=cutoff).delete()
        except Exception as e:
            print(f"Error updating kline for {symbol}: {e}")


# Schedule in celery.py or beat
CELERY_BEAT_SCHEDULE = {
    'update-klines': {
        'task': 'your_app.tasks.update_klines',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
        'args': (['DOGEUSDT', 'LTCUSDT', ...],),  # Your symbol list
    },
}


@shared_task
def sync_company_stock_quotes(company_id, days_ago=32, date_format="%Y-%m-%d", verbose=False):
    global interval
    interval += 1
    Company = apps.get_model("market", "Company")
    try:
        company_obj = Company.objects.get(id=company_id)
    except:
        company_obj = None
    if company_obj is None:
        raise Exception(f"Company Id {company_id} invalid")

    print(
        f"sync_company_stock_quotes for {company_obj.name} || {company_obj.ticker}!")
    return interval
    # company_ticker = company_obj.ticker
    # if company_ticker is None:
    #     raise Exception(f"{company_ticker} invalid")
    # now = timezone.now()
    # start_date = now - timedelta(days=days_ago)
    # to_date = start_date + timedelta(days=days_ago + 1)
    # to_date = to_date.strftime(date_format)
    # from_date = start_date.strftime(date_format)
    # client = helper_clients.PolygonAPIClient(
    #     ticker=company_ticker,
    #     from_date=from_date,
    #     to_date=to_date
    # )
    # dataset = client.get_stock_data()
    # if verbose:
    #     print('dataset length', len(dataset))
    # batch_insert_stock_data(dataset=dataset, company_obj=company_obj, verbose=verbose)


@shared_task
def sync_stock_data(days_ago=2):
    print("sync_stock_data works")
    pass
    # Company = apps.get_model("market", "Company")
    # companies = Company.objects.filter(active=True).values_list('id', flat=True)
    # for company_id in companies:
    #     sync_company_stock_quotes.delay(company_id, days_ago=days_ago)


@shared_task
def sync_historical_stock_data(years_ago=5, company_ids=[], use_celery=True, verbose=False):
    print("sync_historical_stock_data works")
    pass
    # Company = apps.get_model("market", "Company")
    # qs = Company.objects.filter(active=True)
    # if len(company_ids) > 0:
    #     qs = qs.filter(id__in=company_ids)
    # companies = qs.values_list('id', flat=True)
    # for company_id in companies:
    #     days_starting_ago = 30 * 12 * years_ago
    #     batch_size = 30
    #     for i in range(30, days_starting_ago, batch_size):
    #         if verbose:
    #             print("Historical sync days ago", i)
    #         if use_celery:
    #             sync_company_stock_quotes.delay(company_id, days_ago=i, verbose=verbose)
    #         else:
    #             sync_company_stock_quotes(company_id, days_ago=i,verbose=verbose)
    #         if verbose:
    #             print(i, "done\n")
