from src.market.utils import batch_insert_klines_data
from datetime import datetime, timedelta
from .utils import batch_insert_stock_data
from django.utils import timezone
from django.apps import apps
import redis
import json
from celery.schedules import crontab
from src.services.client import get_client
from src.services.config import data
from src.market.utils import prepare_binance_time
# from src.market.models import Kline
from decimal import Decimal
from celery import shared_task
from datetime import timedelta
import pytz
from datetime import datetime
timestamp_format = '%Y-%m-%d %H:%M:%S'
eastern = pytz.timezone("US/Eastern")
# import helpers.clients as helper_clients


'''
COMMANDS:

celery -A src worker -l info --pool=solo
celery -A src beat 

'''
interval = 30
DAYS_AGO = 14  # For 14-day RSI, adjust as needed
redis_client = redis.Redis(host='localhost', port=6379, db=0)
df = "%Y-%m-%d %H:%M:%S"


# @shared_task
def update_klines2(symbols=None):
    from src.services.config import data
    if symbols is None:
        symbols = data["currencies"]

    client = get_client()
    days_ago = data.get('days_ago', 14)  # Default to 14 days
    klines_per_request = 1000  # Binance API limit per request
    # 5-minute klines: 12 per hour, 24 hours, 14 days
    total_klines_needed = int(days_ago * 24 * 12)

    for symbol in symbols:
        symbol_full = symbol + "USDT"
        try:
            Kline = apps.get_model("market", "Kline")

            # Always fetch from now back 14 days
            end_time = timezone.now()
            to_date, from_date = prepare_binance_time(
                end_time, days_ago=days_ago)

            print(
                f"Fetching klines for {symbol_full} from {datetime.fromtimestamp(from_date / 1000)} to {datetime.fromtimestamp(to_date / 1000)}")

            all_klines = []
            current_from_date = from_date

            # Paginate to fetch all 14 days
            while current_from_date < to_date:
                klines = client.get_klines(
                    symbol=symbol_full,
                    interval="5m",
                    startTime=current_from_date,
                    endTime=to_date,
                    limit=klines_per_request
                )
                if not klines:
                    print(f"No klines returned for {symbol_full}")
                    break

                all_klines.extend(klines)
                # Move to next timestamp after last kline
                current_from_date = int(klines[-1][0]) + 1

                print(
                    f"Fetched {len(klines)} klines for {symbol_full}, last timestamp: {datetime.fromtimestamp(int(klines[-1][0]) / 1000)}")

                if len(klines) < klines_per_request:  # Less than limit means we've reached the end
                    break

            if not all_klines:
                print(f"No klines fetched for {symbol_full}")
                continue

            print(
                f"Total fetched {len(all_klines)} klines for {symbol_full}, last timestamp: {datetime.fromtimestamp(int(all_klines[-1][0]) / 1000)}")

            # Clear existing data for this symbol and insert new
            Kline.objects.filter(symbol=symbol).delete()
            batch_insert_klines_data(
                klines=all_klines,
                symbol=symbol_full,
                batch_size=500,  # Larger batch for efficiency
                verbose=True
            )

            # Verify last inserted record
            latest = Kline.objects.filter(
                symbol=symbol).order_by('-timestamp').first()
            print(
                f"Latest DB record for {symbol}: {latest.timestamp if latest else 'None'}")

        except Exception as e:
            print(f"Error updating kline for {symbol_full}: {e}")

    return 'Done'


def batch_insert_klines_data(klines, symbol, batch_size=1, verbose=False):
    Kline = apps.get_model("market", "Kline")
    batch = []
    for kline in klines:
        timestamp = datetime.fromtimestamp(int(kline[0]) / 1000)
        obj = Kline(
            symbol=symbol,
            timestamp=timestamp,
            time=timestamp,
            open=Decimal(kline[1]),
            high=Decimal(kline[2]),
            low=Decimal(kline[3]),
            close=Decimal(kline[4]),
            volume=Decimal(kline[5])
        )
        batch.append(obj)
        if len(batch) >= batch_size:
            Kline.objects.bulk_create(batch, ignore_conflicts=True)
            if verbose:
                print(
                    f"Inserted batch of {len(batch)} klines for {symbol}, last timestamp: {batch[-1].timestamp}")
            batch = []
    if batch:
        Kline.objects.bulk_create(batch, ignore_conflicts=True)
        if verbose:
            print(
                f"Inserted final batch of {len(batch)} klines for {symbol}, last timestamp: {batch[-1].timestamp}")


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


# @shared_task
# def update_prices():
#     from src.market.models import Symbol
#     client = get_client()
#     symbols = Symbol.objects.filter(active=True).values_list('pair', flat=True)
#     for symbol in symbols:
#         ticker = client.get_ticker(symbol=symbol)
#         redis_client.set(f"price:{symbol}", ticker['lastPrice'])


# Schedule in celery.py or beat
# CELERY_BEAT_SCHEDULE = {
#     'update-klines': {
#         'task': 'your_app.tasks.update_klines',
#         'schedule': crontab(minute='*/15'),  # Every 15 minutes
#         'args': (['DOGEUSDT', 'LTCUSDT', ...],),  # Your symbol list
#     },
# }


# @shared_task
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


# @shared_task
def sync_stock_data(days_ago=2):
    print("sync_stock_data works")
    pass
    # Company = apps.get_model("market", "Company")
    # companies = Company.objects.filter(active=True).values_list('id', flat=True)
    # for company_id in companies:
    #     sync_company_stock_quotes.delay(company_id, days_ago=days_ago)


# @shared_task
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


klines = [
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
    ],
    [1741185900000, '0.21750000', '0.21770000', '0.21240000', '0.21370000', '301592.80000000',
        1741186799999, '64694.85037000', 962, '128019.80000000', '27431.07816000', '0'],
    [1741186800000, '0.21340000', '0.21610000', '0.21300000', '0.21340000', '415376.70000000',
        1741187699999, '89123.71166000', 1169, '171710.90000000', '36859.73926000', '0'],
    [1741187700000, '0.21340000', '0.21420000', '0.20660000', '0.20710000', '744293.30000000',
        1741188599999, '156076.86056000', 1518, '369675.20000000', '77549.72322000', '0'],
    [1741188600000, '0.20690000', '0.20700000', '0.20010000', '0.20360000', '1025257.40000000',
        1741189499999, '209033.59170000', 2405, '487152.70000000', '99250.51215000', '0'],
    [1741189500000, '0.20350000', '0.20620000', '0.20300000', '0.20340000', '508452.70000000',
        1741190399999, '103962.45410000', 856, '261166.80000000', '53473.49685000', '0'],
    [1741190400000, '0.20340000', '0.20480000', '0.20010000', '0.20320000', '410012.80000000',
        1741191299999, '83114.25400000', 1100, '180046.40000000', '36549.62796000', '0'],
    [1741191300000, '0.20290000', '0.20290000', '0.20010000', '0.20220000', '542093.20000000',
        1741192199999, '109245.42991000', 1139, '299271.70000000', '60403.56454000', '0'],
    [1741192200000, '0.20220000', '0.20360000', '0.20010000', '0.20260000', '338082.90000000',
        1741193099999, '68423.23032000', 869, '159580.00000000', '32301.72151000', '0'],
    [1741193100000, '0.20260000', '0.20340000', '0.20260000', '0.20340000', '19677.10000000',
        1741193999999, '3996.11246000', 49, '16646.80000000', '3381.76767000', '0']
]
