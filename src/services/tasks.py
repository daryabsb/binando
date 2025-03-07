
from datetime import datetime, timedelta, timezone as dt_timezone
from src.services.client import get_client
from django.apps import apps
from src.services.bnArb import BnArber
from django.utils import timezone
from decimal import Decimal
from celery import shared_task
from datetime import timedelta


@shared_task
def run_trading(symbols=None):
    """Run the BnArber bot periodically."""
    # bot = BnArber(curs=settings.TRADING_CURRENCIES, max_amount=100)  # Adjust max_amount as needed
    # Adjust max_amount as needed
    Symbol = apps.get_model("market", "Symbol")
    if symbols is None:
        symbols = Symbol.objects.filter(active=True).values_list(
            "ticker", flat=True)
    bot = BnArber(curs=symbols, max_amount=15)
    if bot.check_klines_freshness():
        print("All klines are fresh, starting trading...")
        bot.get_rates()
    else:
        print("Kline data issues detected, skipping trading until resolved.")


@shared_task
def update_klines(symbols=None):
    """Update Kline data for the last 15 minutes."""
    Symbol = apps.get_model("market", "Symbol")
    if symbols is None:
        symbols = Symbol.objects.filter(active=True).values_list(
            "ticker", flat=True)

    client = get_client(testnet=True)
    end_time = timezone.now()  # Current UTC time
    from_time = end_time - timedelta(minutes=15)  # 15 minutes prior
    to_date_ms = int(end_time.timestamp() * 1000)
    from_date_ms = int(from_time.timestamp() * 1000)

    for symbol in symbols:
        symbol_full = symbol + "USDT"
        try:
            print(
                f"Fetching last 15min klines for {symbol_full} from {from_time} to {end_time}")

            klines = client.get_klines(
                symbol=symbol_full,
                interval="5m",
                # startTime=from_date_ms,
                # endTime=to_date_ms
            )

            if not klines:
                print(f"No klines returned for {symbol_full}")
                continue

            Kline = apps.get_model("market", "Kline")
            batch = []
            for kline in klines:
                open_time = timezone.make_aware(datetime.fromtimestamp(
                    int(kline[0]) / 1000), dt_timezone.utc)
                close_time = timezone.make_aware(
                    datetime.fromtimestamp(int(kline[6]) / 1000), dt_timezone.utc)

                # Skip future klines
                if close_time > end_time:
                    print(
                        f"Skipping future kline for {symbol_full}: close_time {close_time} > end_time {end_time}")
                    continue

                # Ensure kline is within the requested window
                if open_time < from_time or close_time > end_time:
                    continue

                obj = Kline(
                    # Store full symbol (e.g., 'BURGERUSDT')
                    symbol=symbol_full,
                    timestamp=open_time,  # Opening time
                    time=close_time,      # Closing time
                    open=Decimal(kline[1]),
                    high=Decimal(kline[2]),
                    low=Decimal(kline[3]),
                    close=Decimal(kline[4]),
                    volume=Decimal(kline[5])
                )
                batch.append(obj)

            if batch:
                Kline.objects.bulk_create(batch, ignore_conflicts=True)
                print(
                    f"Inserted {len(batch)} klines for {symbol_full}, latest close: {batch[-1].time}")

                # Verify insertion
                latest = Kline.objects.filter(
                    symbol=symbol_full).order_by('-time').first()
                if latest:
                    print(
                        f"DB verification for {symbol_full}: latest close {latest.time}")
                else:
                    print(
                        f"WARNING: No klines found in DB for {symbol_full} after insert")
            else:
                print(f"No valid klines to insert for {symbol_full}")

        except Exception as e:
            print(f"Error updating kline for {symbol_full}: {e}")

    return 'Done'


# Celery Tasks


# Celery Beat Configuration (in celery.py)
# CELERY_BEAT_SCHEDULE = {
#     'update-klines': {
#         'task': 'your_app.tasks.update_klines',
#         'schedule': crontab(minute='*/15'),  # Every 15 minutes
#     },
#     'run-trading': {
#         'task': 'your_app.tasks.run_trading',
#         # Every 5 minutes (adjust as needed)
#         'schedule': crontab(minute='*/5'),
#     },
# }
