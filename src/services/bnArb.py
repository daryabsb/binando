from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta, timezone as dt_timezone
from decimal import Decimal
from src.market.models import CryptoCurency, Symbol, Kline, Order  # Adjust import path
import time
from celery import shared_task
from django.conf import settings
from src.services.mixins import TechnicalAnalysisMixin, OrderHandler
from django.apps import apps
from src.services.client import get_client

# Main BnArber Class


class BnArber(TechnicalAnalysisMixin, OrderHandler):
    def __init__(self, curs, max_amount):
        self.curs = curs
        self.max_amount = max_amount
        self.min_amount = 10
        self.timeout = False
        self.precision = self._load_precision()
        # self.get_sorted_symbols()  # Precompute once at init
        self.sorted_symbols = Symbol.objects.sorted_symbols()

    def _load_precision(self):
        precision = {}
        try:
            for symbol in Symbol.objects.all():
                # Use getattr to safely check for 'precision', default to 8
                precision[symbol.pair] = getattr(symbol, 'precision', 8)
        except Exception as e:
            print(f"Error loading precision data: {e}")
        return precision

    def get_sorted_symbols(self):
        """Sort symbols by total volume over the last 14 days, computed once at init."""
        trending_coins = []
        VOLUME_THRESHOLD = Decimal('100000.0')

        symbols = Symbol.objects.filter(
            enabled=True, active=True).values('pair')
        for symbol_data in symbols:
            symbol = symbol_data['pair']
            try:
                klines = Kline.objects.filter(symbol=symbol).order_by(
                    '-time')[:4032]  # ~14 days (5-min intervals)
                if not klines:
                    continue

                total_volume = sum(Decimal(str(kline.volume)) *
                                   Decimal(str(kline.close)) for kline in klines)
                if total_volume < VOLUME_THRESHOLD:
                    continue

                trending_coins.append(
                    {"symbol": symbol, "volume": total_volume})
            except Exception as e:
                print(f"⚠️ Skipping {symbol}: Error - {str(e)}")
                continue

        sorted_coins = sorted(
            trending_coins, key=lambda x: float(x["volume"]), reverse=True)
        sorted_symbols = [coin["symbol"] for coin in sorted_coins]

        # Debug print of final sorted list
        # for coin in sorted_coins:
        #     print(f'{coin["symbol"]} ||| total_volume: {coin["volume"]} ||| DONE')
        return sorted_symbols

    def get_trade_amount(self, symbol, current_price):
        try:
            usdt_obj = CryptoCurency.objects.get(ticker="USDT")
            usdt_balance = float(usdt_obj.balance)
            max_trade_usdt = usdt_balance * 0.1
            euro_available = min(max_trade_usdt, self.max_amount)
            trade_usdt = max(
                euro_available, 6.0) if usdt_balance >= 6.0 else 0.0

            # Calculate raw trade amount
            raw_trade_amount = trade_usdt / current_price
            # print(f"{symbol} ||| raw_trade_amount: {raw_trade_amount} ||| current_price: {current_price}")

            # Cap trade amount to prevent overflow and impractical trades
            MAX_TRADE_UNITS = 1_000_000  # Adjust as needed
            trade_amount = min(raw_trade_amount, MAX_TRADE_UNITS)
            trade_amount = self.floor(
                trade_amount, self.precision.get(symbol, 8))

            return trade_amount
        except Exception as e:
            print(f"Error calculating trade amount for {symbol}: {e}")
            return 0.0

    def get_balance(self, cur):
        try:
            currency = CryptoCurency.objects.get(ticker=cur)
            return float(currency.balance)
        except CryptoCurency.DoesNotExist:
            return 0.0
        except Exception as e:
            print(f"Error fetching balance for {cur}: {e}")
            return 0.0

    def check_klines_freshness(self, n_klines=28):
        current_time = timezone.now()
        KLINE_FRESHNESS_LOOKBACK = settings.KLINE_FRESHNESS_LOOKBACK  # timedelta(minutes=5)
        freshness_threshold = current_time - KLINE_FRESHNESS_LOOKBACK
        all_fresh = True

        for symbol in self.sorted_symbols:
            try:
                # Get the latest Kline based on end_time
                latest_kline = Kline.objects.filter(symbol=symbol).order_by('-end_time').first()
                if not latest_kline:
                    print(f"WARNING: No Kline data for {symbol}")
                    all_fresh = False
                    continue

                # Check if the latest Kline is outdated (more than 5 minutes old)
                if latest_kline.end_time < freshness_threshold:
                    print(f"WARNING: Kline data for {symbol} is outdated. Latest end_time: {latest_kline.end_time}, Expected: >{freshness_threshold}")
                    all_fresh = False
                    continue

                # Fetch the last n_klines, ordered by end_time descending
                klines = Kline.objects.filter(symbol=symbol).order_by('-end_time')[:n_klines]

                if len(klines) < n_klines:
                    print(f"WARNING: Insufficient Klines for {symbol} ({len(klines)} found, expected {n_klines})")
                    all_fresh = False
                    continue

                # Check total time span using end_time
                earliest_end_time = klines[n_klines - 1].end_time.astimezone(dt_timezone.utc)
                latest_end_time = klines[0].end_time.astimezone(dt_timezone.utc)
                expected_span = (n_klines - 1) * 5 * 60  # Total seconds expected (5 min intervals)
                actual_span = (latest_end_time - earliest_end_time).total_seconds()
                if abs(actual_span - expected_span) > 2:  # 2-second tolerance
                    print(f"WARNING: Incorrect time span for {symbol}. Expected: {expected_span}s, Actual: {actual_span}s")
                    all_fresh = False
                    continue

                # Check for gaps between consecutive Klines using end_time
                for i in range(1, len(klines)):
                    time_diff = (klines[i - 1].end_time - klines[i].end_time).total_seconds()
                    if abs(time_diff - 300) > 2:  # 300 seconds = 5 minutes, 2-second tolerance
                        print(f"WARNING: Gap detected in {symbol} Klines between {klines[i - 1].end_time} and {klines[i].end_time}")
                        all_fresh = False
                        break

            except Exception as e:
                print(f"Error checking Klines for {symbol}: {e}")
                all_fresh = False

        return all_fresh

    def get_rates(self):
        BUY_COOLDOWN_SECONDS = 86400  # 24 hours
        STOP_LOSS_PCT = 0.05
        TAKE_PROFIT_PCT = 0.03
        MIN_TRADE_USDT = 6.0
        SELL_THRESHOLD_RANGE = (5.5, 6.5)
        MAX_SPEND_PCT = 0.5

        usdt_crypto = CryptoCurency.objects.get(ticker='USDT')
        initial_usdt = float(usdt_crypto.balance)
        max_spend = initial_usdt * MAX_SPEND_PCT
        spent_this_run = 0.0
        print(
            f"Starting USDT Balance (DB): {usdt_crypto.balance}, Max Spend This Run: {max_spend}")

        for symbol in self.sorted_symbols:
            ticker = symbol.replace("USDT", "")
            try:
                latest_kline = Kline.objects.filter(
                    symbol=symbol).order_by('-time').first()
                if not latest_kline:
                    print(f"Skipping {symbol}: No kline data")
                    continue

                current_price = float(latest_kline.close)
                if current_price <= 0:
                    print(f"Skipping {symbol}: Invalid price")
                    continue

                # =========================================
                current_time = time.time()
                usdt_balance = self.get_balance("USDT")
                trade_amount = self.get_trade_amount(symbol, current_price)
                trade_value = trade_amount * current_price
                buy_signals, sell_signals = self.get_signals(
                    symbol, current_price)
                print(
                    f"{symbol} ||| current_price: {current_price} || buy_signals: {buy_signals} | sell_signals: {sell_signals}")

                # if trade_amount <= 0:
                #     print(f"Skipping {symbol}: Invalid trade amount")
                #     continue
                # =========================================

                with transaction.atomic():
                    # Only check/create crypto object when buying or selling
                    if buy_signals >= 2 and trade_amount > 0 and usdt_balance >= MIN_TRADE_USDT:
                        # Check last buy
                        last_buy = Order.objects.filter(
                            ticker=ticker, order_type='BUY').order_by('-timestamp').first()
                        if last_buy:
                            try:
                                crypto = CryptoCurency.objects.get(
                                    ticker=ticker)
                                time_since_last_buy = (
                                    timezone.now() - last_buy.timestamp).total_seconds()
                                if float(crypto.balance) > 0 and time_since_last_buy < BUY_COOLDOWN_SECONDS:
                                    print(
                                        f"Skipping BUY {symbol}: Holding {crypto.balance}, last buy {time_since_last_buy:.2f}s ago")
                                    continue
                            except CryptoCurency.DoesNotExist:
                                pass  # Shouldn’t happen with last_buy, but safe check

                        if spent_this_run + trade_value > max_spend:
                            print(
                                f"Skipping BUY {symbol}: Exceeds max spend ({spent_this_run + trade_value:.2f} > {max_spend})")
                            continue

                        if usdt_balance >= trade_value:
                            crypto, created = CryptoCurency.objects.get_or_create(
                                ticker=ticker,
                                defaults={'name': ticker, 'balance': Decimal(
                                    '0'), 'pnl': Decimal('0'), 'updated': timezone.now()}
                            )
                            crypto.balance += Decimal(str(trade_amount))
                            crypto.updated = timezone.now()
                            crypto.save()

                            Order.objects.create(
                                ticker=ticker,
                                order_type='BUY',
                                quantity=Decimal(str(trade_amount)),
                                price=Decimal(str(current_price)),
                                value=Decimal(str(trade_value)),
                                crypto=crypto
                            )

                            usdt_crypto.balance -= Decimal(str(trade_value))
                            usdt_crypto.updated = timezone.now()
                            usdt_crypto.save()

                            spent_this_run += trade_value
                            self.order(symbol, "BUY", trade_amount)
                            print(
                                f"BUY {trade_amount} {symbol} at {current_price} (Value: {trade_value:.2f}, Total Balance: {crypto.balance})")
                            print(
                                f"USDT Balance: {self.get_balance('USDT')}, Spent This Run: {spent_this_run:.2f}")

                    elif sell_signals >= 2:
                        try:
                            crypto = CryptoCurency.objects.get(ticker=ticker)
                            available_balance = float(crypto.balance)
                            if available_balance > 0:
                                sell_amount = available_balance
                                trade_value = sell_amount * current_price
                                crypto.balance = Decimal('0')
                                crypto.updated = timezone.now()
                                crypto.save()

                                order = Order.objects.create(
                                    ticker=ticker,
                                    symbol=symbol,
                                    order_type='SELL',
                                    quantity=Decimal(str(sell_amount)),
                                    price=Decimal(str(current_price)),
                                    value=Decimal(str(trade_value)),
                                    crypto=crypto
                                )

                                usdt_crypto.balance += Decimal(
                                    str(trade_value))
                                usdt_crypto.updated = timezone.now()
                                usdt_crypto.save()

                                self.order(symbol, "SELL", sell_amount)
                                print(
                                    f"Order no.:{order.id} || SELL  {sell_amount} {symbol} at {current_price} (Value: {trade_value:.2f})")
                                print("USDT Balance:", self.get_balance("USDT"))
                        except CryptoCurency.DoesNotExist:
                            print(f"No position to sell for {symbol}")

                    # Delete zero-balance objects (except USDT)
                    CryptoCurency.objects.filter(
                        balance__lte=0).exclude(ticker='USDT').delete()
                time.sleep(2)

            except Exception as e:
                print(f"Error in get_rates for {ticker}: {e}")

        usdt_crypto.pnl = self.calculate_total_pnl()
        usdt_crypto.save()
        self.timeout = False

    def calculate_total_pnl(self):
        total_pnl = 0.0
        for crypto in CryptoCurency.objects.exclude(ticker='USDT'):
            orders = crypto.orders.all()
            buys = orders.filter(order_type='BUY')
            sells = orders.filter(order_type='SELL')
            total_bought = sum(float(o.value) for o in buys)
            total_sold = sum(float(o.value) for o in sells)
            current_value = float(crypto.balance) * float(Kline.objects.filter(
                symbol=f"{crypto.ticker}USDT").order_by('-time').first().close) if float(crypto.balance) > 0 else 0
            total_pnl += (total_sold + current_value) - total_bought
        return Decimal(str(total_pnl))

    def floor(self, nbr, precision):
        if precision == 0:
            return int(nbr)
        return int(nbr * 10 ** precision) / 10 ** precision
