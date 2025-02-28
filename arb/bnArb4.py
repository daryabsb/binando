import os
import sqlite3
from decimal import Decimal
from dotenv import load_dotenv
import websockets
import asyncio
import json
import time
from datetime import datetime
import random
# from binance.client import Client
import pandas as pd
import pandas_ta
import ta
import time
from binance.client import Client as BinanceClient
# from BinanceKeys import test_api_key, test_secret_key, api_key, secret_key

GRID_LEVELS_COUNT = 5
TOLERANCE_FACTOR = 0.1
MAX_POSITION_PERCENT = 0.1  # 10% of USDT balance per trade
SMA_PERIOD = 20


load_dotenv()


def initialize_database():
    conn = sqlite3.connect('testnet_account3.db')
    c = conn.cursor()

    # Create my_account table
    c.execute('''CREATE TABLE IF NOT EXISTS my_account
                 (symbol TEXT PRIMARY KEY, balance REAL, pnl REAL, updated TEXT)''')

    # Create account_pnl table
    c.execute('''CREATE TABLE IF NOT EXISTS account_pnl
                 (account_pnl REAL, updated TEXT)''')

    # Insert initial USDT record if not exists
    c.execute("SELECT COUNT(*) FROM my_account WHERE symbol = 'USDT'")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO my_account (symbol, balance, pnl, updated) VALUES (?, ?, ?, ?)",
                  ('USDT', 150.0, 150.0, datetime.now().isoformat()))

    # Insert initial account_pnl if not exists
    c.execute("SELECT COUNT(*) FROM account_pnl")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO account_pnl (account_pnl, updated) VALUES (?, ?)",
                  (150.0, datetime.now().isoformat()))

    conn.commit()
    conn.close()


class Client(BinanceClient):
    """Handles Binance API requests with automatic time synchronization and exchange info loading."""

    def __init__(self, api_key, api_secret, testnet=True):
        super().__init__(api_key, api_secret, tld='com', testnet=testnet)

        # Synchronize time with Binance server
        self.sync_time()

        # Load exchange info
        self.load_exchange_info()

    def sync_time(self):
        """Synchronizes system time with Binance server time to prevent timestamp issues."""
        try:
            server_time = self.get_server_time()["serverTime"]
            system_time = int(time.time() * 1000)
            self.timestamp_offset = server_time - system_time
        except Exception as e:
            print(f"⚠️ Error synchronizing time: {e}")
            self.timestamp_offset = 0  # Default to zero offset if sync fails

    def load_exchange_info(self):
        """Loads exchange filters for all symbols to validate orders."""
        try:
            self.exchange_info = self.get_exchange_info()
            self.symbols_info = {s["symbol"]: s for s in self.exchange_info["symbols"]}
        except Exception as e:
            print(f"⚠️ Error loading exchange info: {e}")
            self.symbols_info = {}

    def get_adjusted_timestamp(self):
        """Returns the current timestamp adjusted with Binance server offset."""
        return int(time.time() * 1000) + self.timestamp_offset

    def get_price(self, symbol):
        """Fetch current price of a symbol."""
        try:
            return float(self.get_symbol_ticker(symbol=symbol)["price"])
        except Exception as e:
            print(f"⚠️ Error fetching price for {symbol}: {e}")
            return None


class BnArber:
    def __init__(self, curs, max_amount):
        initialize_database()
        self.public = os.getenv("public")  # public
        # Retrieve the variables
        self.secret = os.getenv("secret")  # secret
        self.url = "wss://stream.binance.com:9443/stream?streams=btcusdt@depth5"
        self.curs = curs
        self.data = {}
        self.timeout = False
        self.min_amount = 10
        self.max_amount = max_amount
        self.SMA_WINDOW = 20
        # Client(public, secret, tld='com', testnet=True)
        self.client = self.get_client(self.public, self.secret, testnet=True)
        self.precision = {}

        self.testnet = True

        try:
            for i in self.client.get_exchange_info()['symbols']:
                for f in i["filters"]:
                    if f["filterType"] == "LOT_SIZE":
                        if float(f["minQty"]) <= 1:
                            self.precision[i["symbol"]] = str(
                                int(1/float(f["minQty"]))).count("0")
                        else:
                            self.precision[i["symbol"]] = - \
                                1*int(f["minQty"].count("0"))
        except Exception as e:
            print(f"Error initializing precision data: {e}")

    async def run(self):
        print("Arbitrator started...")
        print("Ping response:", self.client.ping())  # Check API connectivity
        print("Operating Markets:", ', '.join(self.curs))
        print("Balance:", self.get_balance("USDT"), "USDT")

        # Construct the WebSocket URL correctly with only USDT pairs
        base_url = "wss://stream.binance.com:9443/stream?streams="  # For live trading
        if self.testnet:
            base_url = "wss://testnet.binance.vision/stream?streams="
        # Use wss://testnet.binance.vision/stream?streams= for Testnet
        streams = [f"{cur.lower()}usdt@depth5" for cur in self.curs]
        self.url = base_url + "/".join(streams)

        print(f"Connecting to WebSocket: {self.url}")  # Debug URL

        try:
            async with websockets.connect(self.url) as websocket:
                while True:
                    try:

                        message = await websocket.recv()
                        self.handle_data(message)
                        if not self.timeout:
                            self.timeout = True
                            asyncio.create_task(self.get_rates())
                    except websockets.ConnectionClosed:
                        print(
                            "WebSocket connection closed, attempting to reconnect...")
                        break
                    except Exception as e:
                        print(f"Error in websocket loop: {e}")
        except Exception as e:
            print(f"WebSocket connection failed: {e}")

    def get_client(self, PUBLIC, SECRET, testnet=False):
        client = Client(self.public, self.secret, testnet=testnet)
        return client

    def handle_data(self, message):
        try:
            message = json.loads(message)
            market_id = message["stream"].split("@")[0].upper()
            asks = [(float(a[0]), float(a[1]))
                    for a in message["data"]["asks"]]
            if not asks:  # Check if asks is empty
                print(f"Skipping {market_id}: No ask data available")
                return
            ask = min(asks, key=lambda t: t[0])
            self.data[market_id] = {"ask": [ask[0], ask[1]]}
            # Optional: Print for debugging
            # print(f"Updated self.data[{market_id}]: {self.data[market_id]}")
        except Exception as e:
            print(f"Error in handle_data: {e}")

    def get_volume(self, symbol):
        """Fetch 24h trading volume of a symbol from Binance."""
        try:
            ticker = self.client.get_ticker(symbol=symbol)
            # Volume in quote currency (USDT)
            return Decimal(ticker["quoteVolume"])
        except Exception as e:
            print(f"Error fetching volume for {symbol}: {e}")
            return Decimal('0.0')

    def get_sorted_symbols(self):
        """
        Sort and filter symbols by highest volume and price momentum.
        Returns a list of symbol strings (e.g., ['DOGEUSDT', 'LTCUSDT', ...]).
        """
        trending_coins = []
        # Minimum 24h volume in USDT (adjustable)
        VOLUME_THRESHOLD = Decimal('100000.0')

        for cur in self.curs:
            symbol = cur + "USDT"
            try:
                # Get current price from WebSocket data
                ask_data = self.get_ask(symbol)
                if not ask_data or not isinstance(ask_data, (list, tuple)) or len(ask_data) < 1:
                    print(f"⚠️ Skipping {symbol}: No ask data available")
                    continue
                # Convert to float for consistency
                current_price = float(ask_data[0])

                # Fetch 24-hour ticker data
                ticker = self.client.get_ticker(symbol=symbol)
                volume = self.get_volume(symbol)  # Already Decimal
                price_change_percent = Decimal(
                    ticker['priceChangePercent'])  # Convert to Decimal

                # Skip low-volume symbols
                if volume < VOLUME_THRESHOLD:
                    print(
                        f"⚠️ Skipping {symbol}: Volume {float(volume):.2f} USDT below threshold {float(VOLUME_THRESHOLD)}")
                    continue

                trending_coins.append({
                    "symbol": symbol,
                    "price": current_price,
                    "volume": volume,
                    "price_change_percent": price_change_percent
                })

            except Exception as e:
                print(f"⚠️ Skipping {symbol}: Error - {str(e)}")
                continue

        # Sort by a combined score: volume (primary) and price change (secondary)
        sorted_coins = sorted(trending_coins, key=lambda x: (float(
            x["volume"]) * (1 + abs(float(x["price_change_percent"])) / 100)), reverse=True)

        # Return just the symbol strings
        self.symbols = [coin["symbol"] for coin in sorted_coins]

    def get_sma(self, symbol, period=20):
        """Fetch historical prices and calculate SMA."""
        try:
            klines = self.client.get_klines(
                symbol=symbol, interval="15m", limit=period)  # 15-minute candles
            closes = [float(k[4]) for k in klines]  # Closing prices

            if len(closes) < period:
                print(f"⚠️ Not enough data for SMA {period}.")
                return None

            df = pd.DataFrame(closes, columns=["close"])
            df["sma"] = pandas_ta.sma(df["close"], length=period)

            return df["sma"].iloc[-1]  # Latest SMA value
        except Exception as e:
            print(f"⚠️ Error calculating SMA for {symbol}: {e}")
            return None

    def get_weekly_support_resistance(self, symbol):
        """
        Fetch one week of 1-hour klines and calculate:
        - Support: minimum of lows
        - Resistance: maximum of highs
        """
        try:
            klines = self.client.get_historical_klines(
                symbol, Client.KLINE_INTERVAL_1HOUR, "7 days ago UTC")
            df = pd.DataFrame(klines, columns=[
                'open_time', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'qav', 'num_trades', 'taker_base_vol', 'taker_quote_vol', 'ignore'
            ])
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            support = df['low'].min()
            resistance = df['high'].max()
            return support, resistance
        except Exception as e:
            print(f"Error fetching weekly data for {symbol}: {e}")
            return None, None

    def calculate_grid_levels(self, support, resistance, levels=GRID_LEVELS_COUNT):
        """
        Divide the range between support and resistance into grid levels.
        Returns:
        - grid_levels: list of grid levels (from low to high)
        - grid_spacing: spacing between levels
        """
        grid_spacing = (resistance - support) / (levels + 1)
        grid_levels = [support + grid_spacing * (i + 1) for i in range(levels)]
        return grid_levels, grid_spacing

    def get_technical_indicators(self, symbol, interval="15m", lookback="1 day ago UTC"):
        """
        Retrieve recent klines and compute technical indicators:
        - RSI (14-period)
        - MACD and MACD signal
        - Bollinger Bands (20-period, 2 std dev)
        - SMA50 (50-period Simple Moving Average)
        """
        try:
            klines = self.client.get_historical_klines(
                symbol, interval, lookback)
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'qav', 'num_trades', 'taker_base_vol', 'taker_quote_vol', 'ignore'
            ])
            df['close'] = df['close'].astype(float)
            df['volume'] = df['volume'].astype(float)

            rsi = ta.momentum.RSIIndicator(
                df['close'], window=14).rsi().iloc[-1]
            macd_series = ta.trend.MACD(df['close'])
            macd = macd_series.macd().iloc[-1]
            macd_signal = macd_series.macd_signal().iloc[-1]

            bb_indicator = ta.volatility.BollingerBands(
                df['close'], window=20, window_dev=2)
            bb_lower = bb_indicator.bollinger_lband().iloc[-1]
            bb_upper = bb_indicator.bollinger_hband().iloc[-1]

            sma50 = df['close'].rolling(window=50).mean().iloc[-1]

            return rsi, macd, macd_signal, bb_lower, bb_upper, sma50
        except Exception as e:
            print(f"Error calculating indicators for {symbol}: {e}")
            return None, None, None, None, None, None

    def check_stop_loss(self, pos, current_price, stop_loss_pct=0.05):
        """
        Return True if the current price is more than stop_loss_pct below the entry.
        """
        if current_price < pos["buy_price"] * (1 - stop_loss_pct):
            return True
        return False

    def recalc_grid_levels(self, symbol):
        """
        Recalculate grid levels for the symbol based on the latest weekly support/resistance.
        """
        support, resistance = self.get_weekly_support_resistance(symbol)
        if support is None or resistance is None:
            return None
        grid_levels, grid_spacing = self.calculate_grid_levels(
            support, resistance)
        tolerance = grid_spacing * TOLERANCE_FACTOR
        return {
            "support": support,
            "resistance": resistance,
            "grid_levels": grid_levels,
            "grid_spacing": grid_spacing,
            "tolerance": tolerance
        }

    async def get_rates(self):

        COOLDOWN_SECONDS = 60  # 1-minute cooldown
        MAX_POSITION_PERCENT = 0.1  # 10% of USDT balance per trade
        STOP_LOSS_PCT = 0.05  # 5% stop loss
        TAKE_PROFIT_PCT = 0.03  # 3% take profit
        MIN_TRADE_USDT = 6.0  # Minimum trade size
        SELL_THRESHOLD_RANGE = (5.5, 6.5)  # Sell if PNL between 5.5-6.5 USD

        if not hasattr(self, 'last_trade_time'):
            self.last_trade_time = {cur: 0 for cur in self.curs}
        if not hasattr(self, 'positions'):
            self.positions = {}

        conn = sqlite3.connect('testnet_account3.db')
        c = conn.cursor()
        for cur in self.curs:
            # cur = symbol.replace("USDT", "")
            symbol = cur + "USDT"
            try:
                # symbol = cur + "USDT"
                if symbol not in self.data:
                    print(
                        f"Skipping {symbol}: No market data available in self.data")
                    continue

                ask_data = self.get_ask(symbol)
                if ask_data is None or not isinstance(ask_data, (list, tuple)) or len(ask_data) < 1:
                    print(f"Skipping {symbol}: Invalid ask data - {ask_data}")
                    continue

                current_price = ask_data[0]
                if current_price <= 0:
                    print(
                        f"Skipping {symbol}: Invalid price - {current_price}")
                    continue

                current_time = time.time()
                if current_time - self.last_trade_time.get(cur, 0) < COOLDOWN_SECONDS:
                    continue

                usdt_balance = self.get_balance("USDT")
                trade_amount = self.get_trade_amount(symbol, current_price)
                buy_signals, sell_signals = await self.get_signals(symbol, current_price)

                # Check for low-value assets to sell
                available_balance = self.get_balance(cur)
                if available_balance > 0:
                    asset_value = available_balance * current_price
                    if SELL_THRESHOLD_RANGE[0] <= asset_value <= SELL_THRESHOLD_RANGE[1]:
                        sell_amount = available_balance  # Sell all
                        trade_value = sell_amount * current_price
                        c.execute(
                            "UPDATE my_account SET balance = 0, pnl = 0 WHERE symbol = ?", (cur,))
                        c.execute("UPDATE my_account SET balance = balance + ?, pnl = balance + ? WHERE symbol = 'USDT'",
                                  (trade_value, trade_value))
                        self.last_trade_time[cur] = current_time
                        if cur in self.positions:
                            del self.positions[cur]
                        print(
                            f"LOW VALUE SELL {sell_amount} {symbol} at {current_price} (Value: {asset_value:.2f} USD)")
                        print("USDT Balance:", self.get_balance("USDT"), "USDT")

                # Take-profit or stop-loss
                elif cur in self.positions:
                    pos = self.positions[cur]
                    if current_price > pos["buy_price"] * (1 + TAKE_PROFIT_PCT):
                        available_balance = self.get_balance(cur)
                        if available_balance > 0:
                            sell_amount = self.floor(
                                available_balance, self.precision.get(symbol, 8))
                            if sell_amount * current_price > self.min_amount:
                                trade_value = sell_amount * current_price
                                c.execute("UPDATE my_account SET balance = balance - ?, pnl = 0 WHERE symbol = ?",
                                          (sell_amount, cur))
                                c.execute("UPDATE my_account SET balance = balance + ?, pnl = balance + ? WHERE symbol = 'USDT'",
                                          (trade_value, trade_value))
                                self.last_trade_time[cur] = current_time
                                del self.positions[cur]
                                print(
                                    f"TAKE PROFIT SELL {sell_amount} {symbol} at {current_price}")
                                print("USDT Balance:",
                                      self.get_balance("USDT"), "USDT")
                    elif self.check_stop_loss(pos, current_price, STOP_LOSS_PCT):
                        available_balance = self.get_balance(cur)
                        if available_balance > 0:
                            sell_amount = self.floor(
                                available_balance, self.precision.get(symbol, 8))
                            if sell_amount * current_price > self.min_amount:
                                trade_value = sell_amount * current_price
                                c.execute("UPDATE my_account SET balance = balance - ?, pnl = 0 WHERE symbol = ?",
                                          (sell_amount, cur))
                                c.execute("UPDATE my_account SET balance = balance + ?, pnl = balance + ? WHERE symbol = 'USDT'",
                                          (trade_value, trade_value))
                                self.last_trade_time[cur] = current_time
                                del self.positions[cur]
                                print(
                                    f"STOP LOSS SELL {sell_amount} {symbol} at {current_price}")
                                print("USDT Balance:",
                                      self.get_balance("USDT"), "USDT")
                # Execute new trades
                elif buy_signals >= 2 and trade_amount > 0 and usdt_balance >= MIN_TRADE_USDT:
                    trade_value = trade_amount * current_price
                    if usdt_balance >= trade_value:
                        c.execute("INSERT OR REPLACE INTO my_account (symbol, balance, pnl, updated) VALUES (?, ?, ?, ?)",
                                  (cur, trade_amount, trade_value, datetime.now().isoformat()))
                        c.execute("UPDATE my_account SET balance = balance - ?, pnl = balance - ? WHERE symbol = 'USDT'",
                                  (trade_value, trade_value))
                        self.last_trade_time[cur] = current_time
                        self.positions[cur] = {"buy_price": current_price}
                        print(
                            f"BUY {trade_amount} {symbol} at {current_price}")
                        print("USDT Balance:", self.get_balance("USDT"), "USDT")
                    else:
                        print(
                            f"Insufficient USDT balance for BUY {trade_amount} {symbol}")

                elif sell_signals >= 3:
                    available_balance = self.get_balance(cur)
                    if available_balance > 0:
                        sell_amount = self.floor(
                            available_balance, self.precision.get(symbol, 8))
                        if sell_amount * current_price > self.min_amount:
                            trade_value = sell_amount * current_price
                            c.execute("UPDATE my_account SET balance = balance - ?, pnl = 0 WHERE symbol = ?",
                                      (sell_amount, cur))
                            c.execute("UPDATE my_account SET balance = balance + ?, pnl = balance + ? WHERE symbol = 'USDT'",
                                      (trade_value, trade_value))
                            self.last_trade_time[cur] = current_time
                            if cur in self.positions:
                                del self.positions[cur]
                            print(
                                f"SELL {sell_amount} {symbol} at {current_price}")
                            print("USDT Balance:",
                                  self.get_balance("USDT"), "USDT")

                # Update account_pnl
                c.execute("SELECT symbol, balance FROM my_account")
                total_pnl = 0
                for symbol, balance in c.fetchall():
                    if symbol == 'USDT':
                        total_pnl += balance
                    else:
                        price = current_price if symbol == cur else (self.get_ask(
                            symbol + "USDT")[0] if symbol + "USDT" in self.data else 0)
                        total_pnl += balance * price if price else 0

                c.execute("DELETE FROM my_account WHERE balance <= 0")
                c.execute("UPDATE account_pnl SET account_pnl = ?, updated = ?",
                          (total_pnl, datetime.now().isoformat()))

                conn.commit()
                await asyncio.sleep(5)

            except Exception as e:
                print(f"Error in get_rates for {cur}: {e}")

        conn.close()
        self.timeout = False

    async def get_signals(self, symbol, current_price):
        """Calculate buy and sell signals based on technical indicators."""
        rsi, macd, macd_signal, bb_lower, bb_upper, sma50 = self.get_technical_indicators(
            symbol)
        sma = self.get_sma(symbol, SMA_PERIOD)

        if any(x is None for x in [sma, rsi, macd, macd_signal, bb_lower, bb_upper]) or pd.isna(macd_signal):
            print(
                f"Skipping {symbol}: Indicator data incomplete - SMA: {sma}, RSI: {rsi}, MACD: {macd}/{macd_signal}")
            return 0, 0

        buy_signals = 0
        sell_signals = 0

        if current_price > sma:
            buy_signals += 1
        elif current_price < sma:
            sell_signals += 1

        if rsi < 30:
            buy_signals += 1
        elif rsi > 70:
            sell_signals += 1

        if macd > macd_signal:
            buy_signals += 1
        elif macd < macd_signal:
            sell_signals += 1

        if current_price < bb_lower * 1.01:
            buy_signals += 1
        elif current_price > bb_upper * 0.99:
            sell_signals += 1

        print(f'{symbol} ||| current_price: {current_price} ')
        print(f'{symbol} ||| sma: {sma} | rsi: {rsi} | macd: {macd}')
        print(
            f'{symbol} ||| macd_signal: {macd_signal} | bb_lower: {bb_lower}')
        print(f'{symbol} ||| bb_upper: {bb_upper} | sma50: {sma50}')
        print(
            f'{symbol} ||| buy signals: {buy_signals} | sell signals: {sell_signals}')

        return buy_signals, sell_signals

    def get_trade_amount(self, symbol, current_price):
        """Calculate trade amount with a minimum of 6 USDT."""
        usdt_balance = self.get_balance("USDT")
        max_trade_usdt = usdt_balance * MAX_POSITION_PERCENT
        euro_available = min(random.randint(
            self.min_amount, self.max_amount), max_trade_usdt)

        # Enforce minimum 6 USDT for buys
        trade_usdt = max(euro_available, 6.0) if usdt_balance >= 6.0 else 0.0
        trade_amount = self.floor(
            trade_usdt / current_price, self.precision.get(symbol, 8))
        print(f'{symbol} ||| max_trade_usdt: {max_trade_usdt} | euro_available: {euro_available} | trade_amount: {trade_amount}')
        return trade_amount

    async def get_rates__1(self):
        SMA_PERIOD = 20
        COOLDOWN_SECONDS = 60  # 1-minute cooldown

        STOP_LOSS_PCT = 0.05  # 5% stop loss
        TAKE_PROFIT_PCT = 0.03  # 3% take profit

        if not hasattr(self, 'last_trade_time'):
            self.last_trade_time = {cur: 0 for cur in self.curs}
        if not hasattr(self, 'positions'):
            self.positions = {}

        for cur in self.curs:
            try:
                symbol = cur + "USDT"
                if symbol not in self.data:
                    print(
                        f"Skipping {symbol}: No market data available in self.data")
                    continue

                ask_data = self.get_ask(symbol)
                if ask_data is None or not isinstance(ask_data, (list, tuple)) or len(ask_data) < 1:
                    print(f"Skipping {symbol}: Invalid ask data - {ask_data}")
                    continue

                current_price = ask_data[0]
                if current_price <= 0:
                    print(
                        f"Skipping {symbol}: Invalid price - {current_price}")
                    continue

                current_time = time.time()
                if current_time - self.last_trade_time.get(cur, 0) < COOLDOWN_SECONDS:
                    continue

                # Fetch indicators
                rsi, macd, macd_signal, bb_lower, bb_upper, sma50 = self.get_technical_indicators(
                    symbol)
                sma = self.get_sma(symbol, SMA_PERIOD)

                if any(x is None for x in [sma, rsi, macd, macd_signal, bb_lower, bb_upper]) or pd.isna(macd_signal):
                    print(
                        f"Skipping {symbol}: Indicator data incomplete - SMA: {sma}, RSI: {rsi}, MACD: {macd}/{macd_signal}")
                    continue

                # Risk management
                usdt_balance = self.get_balance("USDT")
                max_trade_usdt = 150 * MAX_POSITION_PERCENT  # usdt_balance
                euro_available = min(random.randint(
                    self.min_amount, self.max_amount), max_trade_usdt)
                trade_amount = self.floor(
                    euro_available / current_price, self.precision.get(symbol, 8))

                # Trading signals
                buy_signals = 0
                sell_signals = 0

                if current_price > sma:
                    buy_signals += 1
                elif current_price < sma:
                    sell_signals += 1

                if rsi < 40:
                    buy_signals += 1
                elif rsi > 60:
                    sell_signals += 1

                if macd > macd_signal:
                    buy_signals += 1
                elif macd < macd_signal:
                    sell_signals += 1

                # Near support (1% tolerance)
                if current_price < bb_lower * 1.01:
                    buy_signals += 1
                # Near resistance (1% tolerance)
                elif current_price > bb_upper * 0.99:
                    sell_signals += 1

                print(
                    f'{symbol} ||| max_trade_usdt: {max_trade_usdt} | euro_available: {euro_available} | trade_amount: {trade_amount}')
                print(f'{symbol} ||| current_price: {current_price} ')
                print(f'{symbol} ||| sma: {sma} | rsi: {rsi} | macd: {macd}')
                print(
                    f'{symbol} ||| macd_signal: {macd_signal} | bb_lower: {bb_lower}')
                print(f'{symbol} ||| bb_upper: {bb_upper} | sma50: {sma50}')
                print(
                    f'{symbol} ||| buy signals: {buy_signals} | sell signals: {sell_signals}')

                # Take-profit or stop-loss
                if cur in self.positions:
                    pos = self.positions[cur]
                    if current_price > pos["buy_price"] * (1 + TAKE_PROFIT_PCT):
                        available_balance = self.get_balance(cur)
                        if available_balance > 0:
                            sell_amount = self.floor(
                                available_balance, self.precision.get(symbol, 8))
                            if sell_amount * current_price > self.min_amount:
                                order_success = self.order(
                                    symbol, "SELL", sell_amount)
                                if order_success:
                                    self.last_trade_time[cur] = current_time
                                    del self.positions[cur]
                                    print(
                                        f"TAKE PROFIT SELL {sell_amount} {symbol} at {current_price}")
                                    print(
                                        f"Indicators - SMA: {sma}, RSI: {rsi}, MACD: {macd}/{macd_signal}, BB: {bb_lower}/{bb_upper}")
                                    print("Balance:", self.get_balance(
                                        "USDT"), "USDT")
                    elif self.check_stop_loss(pos, current_price, STOP_LOSS_PCT):
                        available_balance = self.get_balance(cur)
                        if available_balance > 0:
                            sell_amount = self.floor(
                                available_balance, self.precision.get(symbol, 8))
                            if sell_amount * current_price > self.min_amount:
                                order_success = self.order(
                                    symbol, "SELL", sell_amount)
                                if order_success:
                                    self.last_trade_time[cur] = current_time
                                    del self.positions[cur]
                                    print(
                                        f"STOP LOSS SELL {sell_amount} {symbol} at {current_price}")
                                    print(
                                        f"Indicators - SMA: {sma}, RSI: {rsi}, MACD: {macd}/{macd_signal}, BB: {bb_lower}/{bb_upper}")
                                    print("Balance:", self.get_balance(
                                        "USDT"), "USDT")

                # Execute new trades
                elif buy_signals >= 3 and trade_amount > 0:
                    order_success = self.order(symbol, "BUY", trade_amount)
                    if order_success:
                        self.last_trade_time[cur] = current_time
                        self.positions[cur] = {"buy_price": current_price}
                        print(
                            f"BUY {trade_amount} {symbol} at {current_price}")
                        print(
                            f"Indicators - SMA: {sma}, RSI: {rsi}, MACD: {macd}/{macd_signal}, BB: {bb_lower}/{bb_upper}")
                        print("Balance:", self.get_balance("USDT"), "USDT")
                    else:
                        print(f"Failed to BUY {trade_amount} {symbol}")

                elif sell_signals >= 3:
                    available_balance = self.get_balance(cur)
                    if available_balance > 0:
                        sell_amount = self.floor(
                            available_balance, self.precision.get(symbol, 8))
                        if sell_amount * current_price > self.min_amount:
                            order_success = self.order(
                                symbol, "SELL", sell_amount)
                            if order_success:
                                self.last_trade_time[cur] = current_time
                                if cur in self.positions:
                                    del self.positions[cur]
                                print(
                                    f"SELL {sell_amount} {symbol} at {current_price}")
                                print(
                                    f"Indicators - SMA: {sma}, RSI: {rsi}, MACD: {macd}/{macd_signal}, BB: {bb_lower}/{bb_upper}")
                                print("Balance:", self.get_balance(
                                    "USDT"), "USDT")
                            else:
                                print(f"Failed to SELL {sell_amount} {symbol}")

                await asyncio.sleep(5)

            except Exception as e:
                print(f"Error in get_rates for {cur}: {e}")

        self.timeout = False

    def get_balance__1(self, cur):
        try:
            re = self.client.get_asset_balance(asset=cur)
            return float(re["free"]) if re else 0
        except:
            return 0

    def get_balance(self, cur):
        try:
            conn = sqlite3.connect('testnet_account3.db')
            c = conn.cursor()
            c.execute("SELECT balance FROM my_account WHERE symbol = ?", (cur,))
            result = c.fetchone()
            conn.close()
            return float(result[0]) if result else 0.0
        except Exception as e:
            print(f"Error fetching balance for {cur}: {e}")
            return 0.0

    def sell_all(self):
        try:
            for cur in self.curs + ["USD"]:
                time.sleep(5)
                amount = self.floor(self.get_balance(
                    cur), self.precision.get(cur+"USDT", 8))
                if amount*self.get_bid(cur+"USDT")[0] > self.min_amount:
                    self.order(cur+"USDT", "SELL", amount)
        except Exception as e:
            print(f"Error in sell_all: {e}")

    def order(self, market, side, amount):
        try:
            if side.lower() == "buy":
                re = self.client.create_order(
                    symbol=market,
                    side=Client.SIDE_BUY,
                    type=Client.ORDER_TYPE_MARKET,
                    quantity=str(amount)
                )
                print("BUY", amount, market)
            elif side.lower() == "sell":
                re = self.client.create_order(
                    symbol=market,
                    side=Client.SIDE_SELL,
                    type=Client.ORDER_TYPE_MARKET,
                    quantity=str(amount)
                )
                print("SELL", amount, market)
            return re["status"] == "FILLED"
        except Exception as e:
            print(f"Order error: {e}")
            return False

    def get_bid(self, market):
        return self.data[market]["bid"]

    def get_ask__1(self, market):
        return self.data[market]["ask"]

    def get_ask(self, market):
        return self.data.get(market, {}).get("ask")

    def floor(self, nbr, precision):
        if precision == 0:
            return int(nbr)
        return int(nbr*10**precision)/10**precision


async def main():
    try:
        with open("arb/config.json", "r") as file:
            data = json.load(file)

        bn = BnArber(
            data["currencies"],
            # data["public"],
            # data["secret"],
            data["max_amount"]
        )
        await bn.run()
    except FileNotFoundError:
        print("config.json not found")
    except json.JSONDecodeError:
        print("Invalid JSON in config.json")
    except Exception as e:
        print(f"Error in main: {e}")

if __name__ == "__main__":
    # Use this approach for Python 3.7+
    while True:
        asyncio.run(main())
