from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from src.market.models import CryptoCurency, Symbol, Kline  # Adjust import path
import time
from celery import shared_task
from django.conf import settings
from src.services.mixins import TechnicalAnalysisMixin, OrderHandler

# Main BnArber Class


class BnArber(TechnicalAnalysisMixin, OrderHandler):
    def __init__(self, curs, max_amount):
        self.curs = curs  # List of base currencies (e.g., ['BURGER', 'TRX'])
        self.max_amount = max_amount
        self.min_amount = 10
        self.timeout = False
        self.precision = self._load_precision()

    def _load_precision(self):
        """Load precision data from Symbol model or defaults."""
        precision = {}
        try:
            for symbol in Symbol.objects.all():
                # Assume Symbol model has a precision field or derive from min_qty
                precision[symbol.pair] = symbol.precision if hasattr(
                    symbol, 'precision') else 8
        except Exception as e:
            print(f"Error loading precision data: {e}")
        return precision

    def get_trade_amount(self, symbol, current_price):
        """Calculate trade amount with a minimum of 6 USDT."""
        try:
            usdt_obj = CryptoCurency.objects.get(ticker="USDT")
            usdt_balance = float(usdt_obj.balance)
            max_trade_usdt = usdt_balance * 0.1  # MAX_POSITION_PERCENT = 0.1
            euro_available = min(max_trade_usdt, self.max_amount)

            trade_usdt = max(
                euro_available, 6.0) if usdt_balance >= 6.0 else 0.0
            trade_amount = self.floor(
                trade_usdt / current_price, self.precision.get(symbol, 8))
            print(f'{symbol} ||| max_trade_usdt: {max_trade_usdt} | euro_available: {euro_available} | trade_amount: {trade_amount}')
            return trade_amount
        except Exception as e:
            print(f"Error calculating trade amount for {symbol}: {e}")
            return 0.0

    def get_balance(self, cur):
        """Fetch balance from CryptoCurency model."""
        try:
            currency = CryptoCurency.objects.get(ticker=cur)
            return float(currency.balance)
        except CryptoCurency.DoesNotExist:
            return 0.0
        except Exception as e:
            print(f"Error fetching balance for {cur}: {e}")
            return 0.0

    def get_sorted_symbols(self):
        """Sort symbols by total volume over the last 14 days."""
        trending_coins = []
        VOLUME_THRESHOLD = Decimal('100000.0')

        symbols = Symbol.objects.filter(active=True).values('pair')
        for symbol_data in symbols:
            symbol = symbol_data['pair']  # e.g., 'BURGERUSDT'
            try:
                klines = Kline.objects.filter(symbol=symbol).order_by(
                    '-time')[:4032]  # ~14 days
                if not klines:
                    continue

                total_volume = sum(Decimal(str(kline.volume)) *
                                   Decimal(str(kline.close)) for kline in klines)
                if total_volume < VOLUME_THRESHOLD:
                    continue

                trending_coins.append({
                    "symbol": symbol,
                    "volume": total_volume,
                })
            except Exception as e:
                print(f"⚠️ Skipping {symbol}: Error - {str(e)}")
                continue

        sorted_coins = sorted(
            trending_coins, key=lambda x: float(x["volume"]), reverse=True)
        return [coin["symbol"] for coin in sorted_coins]

    def check_klines_freshness(self):
        """Verify kline data is up-to-date within 15 minutes."""
        sorted_symbols = self.get_sorted_symbols()
        current_time = timezone.now()
        freshness_threshold = current_time - timedelta(minutes=15)
        all_fresh = True

        for symbol in sorted_symbols:  # symbol is now 'BURGERUSDT'
            ticker = symbol.replace("USDT", "")
            try:
                latest_kline = Kline.objects.filter(
                    symbol=symbol).order_by('-time').first()
                if not latest_kline:
                    print(f"WARNING: No kline data for {symbol}")
                    all_fresh = False
                    continue

                if latest_kline.time < freshness_threshold:
                    print(
                        f"WARNING: Kline data for {symbol} is outdated. Latest close: {latest_kline.time}, Expected: >{freshness_threshold}")
                    all_fresh = False
                    continue

                klines = Kline.objects.filter(
                    symbol=symbol).order_by('-time')[:18]
                if len(klines) < 18:
                    print(
                        f"WARNING: Insufficient klines for {symbol} ({len(klines)} found, expected 18)")
                    all_fresh = False
                    continue

                for i in range(1, len(klines)):
                    expected_time = klines[i-1].time - timedelta(minutes=5)
                    if klines[i].time != expected_time:
                        print(
                            f"WARNING: Gap detected in {symbol} klines between {klines[i-1].time} and {klines[i].time}")
                        all_fresh = False
                        break

                print(
                    f"Kline data for {symbol} is up-to-date and complete. Latest close: {latest_kline.time}")

            except Exception as e:
                print(f"Error checking klines for {ticker}: {e}")
                all_fresh = False

        return all_fresh

    def get_rates(self):
        """Main trading logic using Kline data."""
        COOLDOWN_SECONDS = 60
        STOP_LOSS_PCT = 0.05
        TAKE_PROFIT_PCT = 0.03
        MIN_TRADE_USDT = 6.0
        SELL_THRESHOLD_RANGE = (5.5, 6.5)

        if not hasattr(self, 'last_trade_time'):
            self.last_trade_time = {cur: 0 for cur in self.curs}
        if not hasattr(self, 'positions'):
            self.positions = {}

        sorted_symbols = self.get_sorted_symbols()
        for symbol in sorted_symbols:
            ticker = symbol.replace("USDT", "")
            try:
                latest_kline = Kline.objects.filter(
                    symbol=symbol).order_by('-time').first()
                if not latest_kline:
                    print(f"Skipping {symbol}: No kline data available")
                    continue

                current_price = float(latest_kline.close)
                if current_price <= 0:
                    print(
                        f"Skipping {symbol}: Invalid price - {current_price}")
                    continue

                current_time = time.time()
                if current_time - self.last_trade_time.get(ticker, 0) < COOLDOWN_SECONDS:
                    continue

                usdt_balance = self.get_balance("USDT")
                trade_amount = self.get_trade_amount(symbol, current_price)
                buy_signals, sell_signals = self.get_signals(
                    symbol, current_price)

                with transaction.atomic():
                    if ticker in self.positions:
                        pos = self.positions[ticker]
                        if current_price > pos["buy_price"] * (1 + TAKE_PROFIT_PCT):
                            crypto = CryptoCurency.objects.get(ticker=ticker)
                            available_balance = float(crypto.balance)
                            if available_balance > 0:
                                sell_amount = self.floor(
                                    available_balance, self.precision.get(symbol, 8))
                                if sell_amount * current_price > self.min_amount:
                                    trade_value = sell_amount * current_price
                                    pnl = trade_value - \
                                        (sell_amount * pos["buy_price"])
                                    crypto.balance -= Decimal(str(sell_amount))
                                    crypto.pnl = Decimal('0')
                                    crypto.updated = timezone.now()
                                    crypto.save()

                                    usdt_crypto = CryptoCurency.objects.get(
                                        ticker='USDT')
                                    usdt_crypto.balance += Decimal(
                                        str(trade_value))
                                    usdt_crypto.pnl = usdt_crypto.balance
                                    usdt_crypto.updated = timezone.now()
                                    usdt_crypto.save()

                                    self.order(symbol, "SELL", sell_amount)
                                    self.last_trade_time[ticker] = current_time
                                    del self.positions[ticker]
                                    print(
                                        f"TAKE PROFIT SELL {sell_amount} {symbol} at {current_price} (PNL: {pnl:.2f})")
                                    print("USDT Balance:",
                                          self.get_balance("USDT"), "USDT")

                        elif current_price < pos["buy_price"] * (1 - STOP_LOSS_PCT):
                            crypto = CryptoCurency.objects.get(ticker=ticker)
                            available_balance = float(crypto.balance)
                            if available_balance > 0:
                                sell_amount = self.floor(
                                    available_balance, self.precision.get(symbol, 8))
                                if sell_amount * current_price > self.min_amount:
                                    trade_value = sell_amount * current_price
                                    pnl = trade_value - \
                                        (sell_amount * pos["buy_price"])
                                    crypto.balance -= Decimal(str(sell_amount))
                                    crypto.pnl = Decimal('0')
                                    crypto.updated = timezone.now()
                                    crypto.save()

                                    usdt_crypto = CryptoCurency.objects.get(
                                        ticker='USDT')
                                    usdt_crypto.balance += Decimal(
                                        str(trade_value))
                                    usdt_crypto.pnl = usdt_crypto.balance
                                    usdt_crypto.updated = timezone.now()
                                    usdt_crypto.save()

                                    self.order(symbol, "SELL", sell_amount)
                                    self.last_trade_time[ticker] = current_time
                                    del self.positions[ticker]
                                    print(
                                        f"STOP LOSS SELL {sell_amount} {symbol} at {current_price} (PNL: {pnl:.2f})")
                                    print("USDT Balance:",
                                          self.get_balance("USDT"), "USDT")

                    elif buy_signals >= 2 and trade_amount > 0 and usdt_balance >= MIN_TRADE_USDT:
                        trade_value = trade_amount * current_price
                        if usdt_balance >= trade_value:
                            crypto, created = CryptoCurency.objects.get_or_create(
                                ticker=ticker,
                                defaults={'name': ticker, 'balance': Decimal(str(trade_amount)), 'pnl': Decimal(
                                    str(trade_value)), 'updated': timezone.now()}
                            )
                            if not created:
                                crypto.balance = Decimal(str(trade_amount))
                                crypto.pnl = Decimal(str(trade_value))
                                crypto.updated = timezone.now()
                                crypto.save()

                            usdt_crypto = CryptoCurency.objects.get(
                                ticker='USDT')
                            usdt_crypto.balance -= Decimal(str(trade_value))
                            usdt_crypto.pnl = usdt_crypto.balance
                            usdt_crypto.updated = timezone.now()
                            usdt_crypto.save()

                            self.order(symbol, "BUY", trade_amount)
                            self.last_trade_time[ticker] = current_time
                            self.positions[ticker] = {
                                "buy_price": current_price}
                            print(
                                f"BUY {trade_amount} {symbol} at {current_price}")
                            print("USDT Balance:",
                                  self.get_balance("USDT"), "USDT")
                        else:
                            print(
                                f"Insufficient USDT balance for BUY {trade_amount} {symbol}")

                    elif sell_signals >= 3:
                        crypto = CryptoCurency.objects.get(ticker=ticker)
                        available_balance = float(crypto.balance)
                        if available_balance > 0:
                            asset_value = available_balance * current_price
                            sell_amount = available_balance if SELL_THRESHOLD_RANGE[0] <= asset_value <= SELL_THRESHOLD_RANGE[1] else self.floor(
                                available_balance, self.precision.get(symbol, 8))
                            if sell_amount * current_price > self.min_amount:
                                trade_value = sell_amount * current_price
                                pnl = trade_value - \
                                    (sell_amount * self.positions[ticker]
                                     ["buy_price"]) if ticker in self.positions else 0
                                crypto.balance -= Decimal(str(sell_amount))
                                crypto.pnl = Decimal(
                                    '0') if crypto.balance <= 0 else crypto.balance * Decimal(str(current_price))
                                crypto.updated = timezone.now()
                                crypto.save()

                                usdt_crypto = CryptoCurency.objects.get(
                                    ticker='USDT')
                                usdt_crypto.balance += Decimal(
                                    str(trade_value))
                                usdt_crypto.pnl = usdt_crypto.balance
                                usdt_crypto.updated = timezone.now()
                                usdt_crypto.save()

                                self.order(symbol, "SELL", sell_amount)
                                self.last_trade_time[ticker] = current_time
                                if ticker in self.positions:
                                    del self.positions[ticker]
                                sell_type = "SELL (LOW VALUE)" if SELL_THRESHOLD_RANGE[
                                    0] <= asset_value <= SELL_THRESHOLD_RANGE[1] else "SELL"
                                print(
                                    f"{sell_type} {sell_amount} {symbol} at {current_price} (Value: {asset_value:.2f} USD, PNL: {pnl:.2f})")
                                print("USDT Balance:",
                                      self.get_balance("USDT"), "USDT")

                    CryptoCurency.objects.filter(balance__lte=0).delete()

                time.sleep(5)

            except Exception as e:
                print(f"Error in get_rates for {ticker}: {e}")

        self.timeout = False

    def floor(self, nbr, precision):
        """Floor a number to specified precision."""
        if precision == 0:
            return int(nbr)
        return int(nbr * 10 ** precision) / 10 ** precision
