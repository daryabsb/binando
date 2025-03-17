
from datetime import datetime, timedelta, timezone as dt_timezone
from src.services.client import get_client
from django.apps import apps
from src.services.bnArb import BnArber
from django.utils import timezone
from decimal import Decimal
from celery import shared_task
from datetime import timedelta
from django.db import transaction


'''
[2025-03-08 16:02:10,377: WARNING/MainProcess] All klines are fresh, starting trading...
[2025-03-08 16:02:10,421: WARNING/MainProcess] Error calculating trade amount for XRPUSDT: CryptoCurency matching query does not exist.
[2025-03-08 16:02:15,481: WARNING/MainProcess] Error calculating trade amount for PEPEUSDT: CryptoCurency matching query does not exist.
[2025-03-08 16:02:20,496: WARNING/MainProcess] Error calculating trade amount for TRUMPUSDT: CryptoCurency matching query does not exist.
'''



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
    return 'Done running the bot'


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
def flush_stagnant_positions():
    from src.services.bnArb import BnArber
    HOLD_TIME_SECONDS = 48 * 3600  # 48 hours
    PRICE_THRESHOLD_PCT = 0.05  # ±5%
    CryptoCurency = apps.get_model("market", "CryptoCurency")
    Order = apps.get_model("market", "Order")
    Kline = apps.get_model("market", "Kline")
    Symbol = apps.get_model("market", "Symbol")

    usdt_crypto = CryptoCurency.objects.get(ticker='USDT')
    for crypto in CryptoCurency.objects.exclude(ticker='USDT').filter(balance__gt=0):
        last_buy = Order.objects.filter(
            ticker=crypto.ticker, order_type='BUY').order_by('-timestamp').first()
        if not last_buy:
            continue

        time_held = (timezone.now() - last_buy.timestamp).total_seconds()
        if time_held < HOLD_TIME_SECONDS:
            continue

        current_price = float(Kline.objects.filter(
            symbol=f"{crypto.ticker}USDT").order_by('-time').first().close)
        entry_price = float(last_buy.price)
        price_change = (current_price - entry_price) / entry_price

        if abs(price_change) <= PRICE_THRESHOLD_PCT:
            with transaction.atomic():
                sell_amount = float(crypto.balance)
                trade_value = sell_amount * current_price
                crypto.balance = Decimal('0')
                crypto.updated = timezone.now()
                crypto.save()

                Order.objects.create(
                    ticker=crypto.ticker,
                    order_type='SELL',
                    quantity=Decimal(str(sell_amount)),
                    price=Decimal(str(current_price)),
                    value=Decimal(str(trade_value)),
                    crypto=crypto
                )

                usdt_crypto.balance += Decimal(str(trade_value))
                usdt_crypto.updated = timezone.now()
                usdt_crypto.save()

                print(
                    f"FLUSHED {sell_amount} {crypto.ticker} at {current_price} after {time_held/3600:.1f}h (Value: {trade_value:.2f}, Price Change: {price_change*100:.2f}%)")
                print("USDT Balance:", usdt_crypto.balance)

    symbols = Symbol.objects.filter(active=True).values_list(
        "ticker", flat=True)

    usdt_crypto.pnl = BnArber(
        curs=symbols, max_amount=15).calculate_total_pnl()
    usdt_crypto.save()
