# src/services/tasks.py
from celery import shared_task
from binance import ThreadedWebsocketManager
from decouple import config
from src.market.models import Symbol, Kline
from django.utils import timezone
from decimal import Decimal
import threading
# src/services/tasks.py
from datetime import timedelta
import time

PUBLIC = config('api_key')
SECRET = config('secret_key')

BATCH_SIZE = 100  # Maximum number of Klines to hold before flushing (optional limit)
FLUSH_INTERVAL = 60  # Seconds between bulk inserts

@shared_task
def stream_kline_data():
    kline_batch = []
    lock = threading.Lock()

    def handle_socket_message(msg):
        try:
            data = msg['data']
            kline = data['k']
            if kline['x']:  # Only process finalized Klines
                with lock:
                    kline_batch.append({
                        'symbol': kline['s'],
                        'interval': kline['i'],
                        'start_time': timezone.datetime.fromtimestamp(kline['t'] / 1000, tz=timezone.utc),
                        'end_time': timezone.datetime.fromtimestamp(kline['T'] / 1000, tz=timezone.utc),
                        'open': Decimal(kline['o']),
                        'close': Decimal(kline['c']),
                        'high': Decimal(kline['h']),
                        'low': Decimal(kline['l']),
                        'volume': Decimal(kline['v']),
                        'quote_volume': Decimal(kline['q']),
                        'taker_buy_base_volume': Decimal(kline['V']),
                        'taker_buy_quote_volume': Decimal(kline['Q']),
                        'trade_count': kline['n'],
                        'is_closed': True,
                    })
        except Exception as e:
            print(f"Error processing message: {e}")

    def bulk_insert():
        while True:
            time.sleep(FLUSH_INTERVAL)
            with lock:
                if kline_batch:
                    Kline.objects.bulk_create(
                        [Kline(**data) for data in kline_batch],
                        update_conflicts=True,
                        unique_fields=['symbol', 'start_time', 'interval'],
                        update_fields=['end_time', 'open', 'close', 'high', 'low', 'volume', 'quote_volume', 'taker_buy_base_volume', 'taker_buy_quote_volume', 'trade_count', 'is_closed']
                    )
                    print(f"Bulk inserted {len(kline_batch)} Klines")
                    kline_batch.clear()

    twm = ThreadedWebsocketManager(api_key=PUBLIC, api_secret=SECRET)
    twm.start()

    symbols = Symbol.objects.sorted_symbols()
    streams = [f"{symbol.lower()}@kline_5m" for symbol in symbols]

    twm.start_multiplex_socket(callback=handle_socket_message, streams=streams)

    # Start the bulk insert thread
    threading.Thread(target=bulk_insert, daemon=True).start()

    twm.join()  # Keeps the task running indefinitely



@shared_task
def cleanup_old_klines():
    threshold = timezone.now() - timedelta(days=7)  # Keep 7 days of data
    deleted_count, _ = Kline.objects.filter(start_time__lt=threshold).delete()
    print(f"Deleted {deleted_count} old Klines")