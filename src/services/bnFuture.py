from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from src.market.models import CryptoCurency, Symbol, Kline  # Adjust import path
import time
from celery import shared_task
from django.conf import settings
from src.services.mixins import TechnicalAnalysisMixin, OrderHandler
from binance.client import Client
testnet_api_key = "your_testnet_api_key"
testnet_api_secret = "your_testnet_api_secret"
client = Client(testnet_api_key, testnet_api_secret, testnet=True)
client.API_URL = 'https://testnet.binancefuture.com'  # Futures Testnet URL
# Main BnArber Class

from binance.client import Client
from binance.enums import *  # For order types like SIDE_BUY, ORDER_TYPE_MARKET
from decimal import Decimal
import time
from django.db import transaction
from django.utils import timezone
from src.market.models import CryptoCurency, Kline

class TradingBot:
    def __init__(self):
        self.curs = ['XRP', 'DOGE', 'PEPE', 'TRUMP', 'SHIB', 'BURGER', '1MBABYDOGE', 'TFUEL', 'TURBO']
        self.sorted_symbols = [f"{cur}USDT" for cur in self.curs]
        self.precision = {f"{cur}USDT": 8 for cur in self.curs}
        self.min_amount = 10.0
        self.client = Client("your_testnet_api_key", "your_testnet_api_secret", testnet=True)
        self.client.API_URL = 'https://testnet.binancefuture.com'

    def get_balance(self, ticker):
        try:
            crypto = CryptoCurency.objects.get(ticker=ticker)
            return float(crypto.balance)
        except CryptoCurency.DoesNotExist:
            return 0.0

    def get_trade_amount(self, symbol, price):
        # Simplified for testing; adjust as needed
        return 10.0 / price  # Example: $10 worth

    def get_signals(self, symbol, price):
        # Placeholder; use your signal logic
        return 3, 1  # Buy test case

    def floor(self, value, precision):
        return float(f"{value:.{precision}f}")

    def order(self, symbol, side, quantity):
        # Log orders for testing; replace with actual API calls
        print(f"PLACING ORDER: {side} {quantity} {symbol}")

    def get_rates(self):
        BUY_COOLDOWN_SECONDS = 86400  # 24 hours
        STOP_LOSS_PCT = 0.05  # 5% SL
        TAKE_PROFIT_PCT = 0.03  # 3% TP
        MIN_TRADE_USDT = 6.0

        if not hasattr(self, 'last_trade_time'):
            self.last_trade_time = {cur: 0 for cur in self.curs}
        if not hasattr(self, 'positions'):
            self.positions = {}

        usdt_crypto = CryptoCurency.objects.get(ticker='USDT')
        print(f"Starting USDT Balance (DB): {usdt_crypto.balance}")

        for symbol in self.sorted_symbols:
            ticker = symbol.replace("USDT", "")
            try:
                latest_kline = Kline.objects.filter(symbol=symbol).order_by('-time').first()
                if not latest_kline:
                    print(f"Skipping {symbol}: No kline data")
                    continue

                current_price = float(latest_kline.close)
                if current_price <= 0:
                    print(f"Skipping {symbol}: Invalid price")
                    continue

                current_time = time.time()
                time_since_last_trade = current_time - self.last_trade_time.get(ticker, 0)
                if time_since_last_trade < 60:  # General cooldown
                    print(f"Skipping {symbol}: On cooldown")
                    continue

                usdt_balance = self.get_balance("USDT")
                trade_amount = self.get_trade_amount(symbol, current_price)
                buy_signals, sell_signals = self.get_signals(symbol, current_price)
                print(f"{symbol} ||| current_price: {current_price} || buy_signals: {buy_signals} | sell_signals: {sell_signals}")

                if trade_amount <= 0:
                    print(f"Skipping {symbol}: Invalid trade amount")
                    continue

                with transaction.atomic():
                    if buy_signals >= 2 and trade_amount > 0 and usdt_balance >= MIN_TRADE_USDT:
                        try:
                            crypto = CryptoCurency.objects.get(ticker=ticker)
                            if float(crypto.balance) > 0 and time_since_last_trade < BUY_COOLDOWN_SECONDS:
                                print(f"Skipping BUY {symbol}: Holding {crypto.balance}, on cooldown ({time_since_last_trade:.2f}s)")
                                continue
                        except CryptoCurency.DoesNotExist:
                            pass

                        trade_value = trade_amount * current_price
                        if usdt_balance >= trade_value:
                            # Open long position
                            order = self.client.futures_create_order(
                                symbol=symbol,
                                side=SIDE_BUY,
                                type=ORDER_TYPE_MARKET,
                                quantity=trade_amount,
                                positionSide='LONG'
                            )
                            self.order(symbol, "BUY", trade_amount)

                            # Set Take Profit
                            tp_price = current_price * (1 + TAKE_PROFIT_PCT)
                            self.client.futures_create_order(
                                symbol=symbol,
                                side=SIDE_SELL,
                                type='TAKE_PROFIT_MARKET',
                                stopPrice=tp_price,
                                quantity=trade_amount,
                                positionSide='LONG',
                                timeInForce='GTC',
                                workingType='MARK_PRICE',
                                priceProtect=True
                            )
                            print(f"SET TP: SELL {trade_amount} {symbol} at {tp_price}")

                            # Set Stop Loss
                            sl_price = current_price * (1 - STOP_LOSS_PCT)
                            self.client.futures_create_order(
                                symbol=symbol,
                                side=SIDE_SELL,
                                type='STOP_MARKET',
                                stopPrice=sl_price,
                                quantity=trade_amount,
                                positionSide='LONG',
                                timeInForce='GTC',
                                workingType='MARK_PRICE',
                                priceProtect=True
                            )
                            print(f"SET SL: SELL {trade_amount} {symbol} at {sl_price}")

                            # Update DB
                            crypto, _ = CryptoCurency.objects.get_or_create(
                                ticker=ticker,
                                defaults={'name': ticker, 'balance': Decimal(str(trade_amount)), 'pnl': Decimal(str(trade_value)), 'updated': timezone.now()}
                            )
                            crypto.balance = Decimal(str(trade_amount))
                            crypto.pnl = Decimal(str(trade_value))
                            crypto.updated = timezone.now()
                            crypto.save()

                            usdt_crypto.balance -= Decimal(str(trade_value))
                            usdt_crypto.pnl = usdt_crypto.balance
                            usdt_crypto.updated = timezone.now()
                            usdt_crypto.save()

                            self.last_trade_time[ticker] = current_time
                            self.positions[ticker] = {"buy_price": current_price}
                            print(f"BUY {trade_amount} {symbol} at {current_price} (Value: {trade_value:.2f})")
                            print("USDT Balance:", self.get_balance("USDT"))

                    elif sell_signals >= 3:
                        try:
                            crypto = CryptoCurency.objects.get(ticker=ticker)
                            available_balance = float(crypto.balance)
                            if available_balance > 0:
                                # Close position manually (optional; TP/SL usually handle this)
                                order = self.client.futures_create_order(
                                    symbol=symbol,
                                    side=SIDE_SELL,
                                    type=ORDER_TYPE_MARKET,
                                    quantity=available_balance,
                                    positionSide='LONG'
                                )
                                trade_value = available_balance * current_price
                                pnl = trade_value - (available_balance * self.positions[ticker]["buy_price"]) if ticker in self.positions else 0

                                crypto.balance -= Decimal(str(available_balance))
                                crypto.pnl = Decimal('0')
                                crypto.updated = timezone.now()
                                crypto.save()

                                usdt_crypto.balance += Decimal(str(trade_value))
                                usdt_crypto.pnl = usdt_crypto.balance
                                usdt_crypto.updated = timezone.now()
                                usdt_crypto.save()

                                self.order(symbol, "SELL", available_balance)
                                self.last_trade_time[ticker] = current_time
                                if ticker in self.positions:
                                    del self.positions[ticker]
                                print(f"SELL {available_balance} {symbol} at {current_price} (Value: {trade_value:.2f}, PNL: {pnl:.2f})")
                                print("USDT Balance:", self.get_balance("USDT"))
                        except CryptoCurency.DoesNotExist:
                            print(f"No position to sell for {symbol}")

                    CryptoCurency.objects.filter(balance__lte=0).delete()

                time.sleep(5)

            except Exception as e:
                print(f"Error in get_rates for {ticker}: {e}")

        self.timeout = False