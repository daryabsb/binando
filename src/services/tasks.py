
from datetime import datetime, timedelta, timezone as dt_timezone

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


# @shared_task
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
