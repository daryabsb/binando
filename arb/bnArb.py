import websockets
import asyncio
import json
import time
import random
# from binance.client import Client
import pandas as pd
import pandas_ta
import ta
import time
from binance.client import Client as BinanceClient
# from BinanceKeys import test_api_key, test_secret_key, api_key, secret_key


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

GRID_LEVELS_COUNT = 5
TOLERANCE_FACTOR = 0.1 

class BnArber:
    def __init__(self, curs, public, secret, max_amount):
        self.public = public
        self.secret = secret
        self.url = "wss://stream.binance.com:9443/stream?streams=btcusdt@depth5"
        self.curs = curs
        self.data = {}
        self.timeout = False
        self.min_amount = 15
        self.max_amount = max_amount
        self.SMA_WINDOW = 20
        # Client(public, secret, tld='com', testnet=True)
        self.client = self.get_client(public, secret, testnet=True)
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
                        print("WebSocket connection closed, attempting to reconnect...")
                        break
                    except Exception as e:
                        print(f"Error in websocket loop: {e}")
        except Exception as e:
            print(f"WebSocket connection failed: {e}")

    def get_client(self, PUBLIC, SECRET, testnet=False):

        client = Client(self.public, self.secret, testnet=testnet)
        return client

    def handle_data__1(self, message):
        message = json.loads(message)
        market_id = message["stream"].split("@")[0]
        asks = [(float(a[0]), float(a[1])) for a in message["data"]["asks"]]
        ask = min(asks, key=lambda t: t[0])
        bids = [(float(a[0]), float(a[1])) for a in message["data"]["bids"]]
        bid = max(bids, key=lambda t: t[0])
        self.data[market_id.upper()] = {"ask": ask, "bid": bid}

    def handle_data__2(self, message):
        try:
            message = json.loads(message)
            market_id = message["stream"].split("@")[0].upper()
            asks = [(float(a[0]), float(a[1])) for a in message["data"]["asks"]]
            ask = min(asks, key=lambda t: t[0])
            self.data[market_id] = {"ask": [ask[0], ask[1]]}  # Ensure format matches get_ask
        except Exception as e:
            print(f"Error in handle_data: {e}")


    def handle_data__3(self, message):
        try:
            message = json.loads(message)
            market_id = message["stream"].split("@")[0].upper()
            asks = [(float(a[0]), float(a[1])) for a in message["data"]["asks"]]
            ask = min(asks, key=lambda t: t[0])
            self.data[market_id] = {"ask": [ask[0], ask[1]]}
            # print(f"Updated self.data: {self.data}")  # Debug
        except Exception as e:
            print(f"Error in handle_data: {e}")

    def handle_data(self, message):
        try:
            message = json.loads(message)
            market_id = message["stream"].split("@")[0].upper()
            asks = [(float(a[0]), float(a[1])) for a in message["data"]["asks"]]
            if not asks:  # Check if asks is empty
                print(f"Skipping {market_id}: No ask data available")
                return
            ask = min(asks, key=lambda t: t[0])
            self.data[market_id] = {"ask": [ask[0], ask[1]]}
            # Optional: Print for debugging
            # print(f"Updated self.data[{market_id}]: {self.data[market_id]}")
        except Exception as e:
            print(f"Error in handle_data: {e}")

    # Assuming this is already in your code as provided
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
            klines = self.client.get_historical_klines(symbol, interval, lookback)
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'qav', 'num_trades', 'taker_base_vol', 'taker_quote_vol', 'ignore'
            ])
            df['close'] = df['close'].astype(float)
            df['volume'] = df['volume'].astype(float)

            rsi = ta.momentum.RSIIndicator(df['close'], window=14).rsi().iloc[-1]
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
        grid_levels, grid_spacing = self.calculate_grid_levels(support, resistance)
        tolerance = grid_spacing * TOLERANCE_FACTOR
        return {
            "support": support,
            "resistance": resistance,
            "grid_levels": grid_levels,
            "grid_spacing": grid_spacing,
            "tolerance": tolerance
        }






    async def get_rates(self):
        SMA_PERIOD = 20
        COOLDOWN_SECONDS = 60  # 1-minute cooldown
        MAX_POSITION_PERCENT = 0.1  # 10% of USDT balance per trade
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
                    print(f"Skipping {symbol}: No market data available in self.data")
                    continue

                ask_data = self.get_ask(symbol)
                if ask_data is None or not isinstance(ask_data, (list, tuple)) or len(ask_data) < 1:
                    print(f"Skipping {symbol}: Invalid ask data - {ask_data}")
                    continue

                current_price = ask_data[0]
                if current_price <= 0:
                    print(f"Skipping {symbol}: Invalid price - {current_price}")
                    continue

                current_time = time.time()
                if current_time - self.last_trade_time.get(cur, 0) < COOLDOWN_SECONDS:
                    continue

                # Fetch indicators
                rsi, macd, macd_signal, bb_lower, bb_upper, sma50 = self.get_technical_indicators(symbol)
                sma = self.get_sma(symbol, SMA_PERIOD)

                if any(x is None for x in [sma, rsi, macd, macd_signal, bb_lower, bb_upper]) or pd.isna(macd_signal):
                    print(f"Skipping {symbol}: Indicator data incomplete - SMA: {sma}, RSI: {rsi}, MACD: {macd}/{macd_signal}")
                    continue

                # Risk management
                usdt_balance = self.get_balance("USDT")
                max_trade_usdt = 150 * MAX_POSITION_PERCENT # usdt_balance
                euro_available = min(random.randint(self.min_amount, self.max_amount), max_trade_usdt)
                trade_amount = self.floor(euro_available / current_price, self.precision.get(symbol, 8))

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

                if current_price < bb_lower * 1.01:  # Near support (1% tolerance)
                    buy_signals += 1
                elif current_price > bb_upper * 0.99:  # Near resistance (1% tolerance)
                    sell_signals += 1
                
                
                print(f'{symbol} ||| sma: {sma} | rsi: {rsi} | macd: {macd}')
                print(f'{symbol} ||| macd_signal: {macd_signal} | bb_lower: {bb_lower}')
                print(f'{symbol} ||| bb_upper: {bb_upper} | sma50: {sma50}')
                print(f'{symbol} ||| buy signals: {buy_signals} | sell signals: {sell_signals}')

                # Take-profit or stop-loss
                if cur in self.positions:
                    pos = self.positions[cur]
                    if current_price > pos["buy_price"] * (1 + TAKE_PROFIT_PCT):
                        available_balance = self.get_balance(cur)
                        if available_balance > 0:
                            sell_amount = self.floor(available_balance, self.precision.get(symbol, 8))
                            if sell_amount * current_price > self.min_amount:
                                order_success = self.order(symbol, "SELL", sell_amount)
                                if order_success:
                                    self.last_trade_time[cur] = current_time
                                    del self.positions[cur]
                                    print(f"TAKE PROFIT SELL {sell_amount} {symbol} at {current_price}")
                                    print(f"Indicators - SMA: {sma}, RSI: {rsi}, MACD: {macd}/{macd_signal}, BB: {bb_lower}/{bb_upper}")
                                    print("Balance:", self.get_balance("USDT"), "USDT")
                    elif self.check_stop_loss(pos, current_price, STOP_LOSS_PCT):
                        available_balance = self.get_balance(cur)
                        if available_balance > 0:
                            sell_amount = self.floor(available_balance, self.precision.get(symbol, 8))
                            if sell_amount * current_price > self.min_amount:
                                order_success = self.order(symbol, "SELL", sell_amount)
                                if order_success:
                                    self.last_trade_time[cur] = current_time
                                    del self.positions[cur]
                                    print(f"STOP LOSS SELL {sell_amount} {symbol} at {current_price}")
                                    print(f"Indicators - SMA: {sma}, RSI: {rsi}, MACD: {macd}/{macd_signal}, BB: {bb_lower}/{bb_upper}")
                                    print("Balance:", self.get_balance("USDT"), "USDT")

                # Execute new trades
                elif buy_signals >= 3 and trade_amount > 0:
                    order_success = self.order(symbol, "BUY", trade_amount)
                    if order_success:
                        self.last_trade_time[cur] = current_time
                        self.positions[cur] = {"buy_price": current_price}
                        print(f"BUY {trade_amount} {symbol} at {current_price}")
                        print(f"Indicators - SMA: {sma}, RSI: {rsi}, MACD: {macd}/{macd_signal}, BB: {bb_lower}/{bb_upper}")
                        print("Balance:", self.get_balance("USDT"), "USDT")
                    else:
                        print(f"Failed to BUY {trade_amount} {symbol}")

                elif sell_signals >= 3:
                    available_balance = self.get_balance(cur)
                    if available_balance > 0:
                        sell_amount = self.floor(available_balance, self.precision.get(symbol, 8))
                        if sell_amount * current_price > self.min_amount:
                            order_success = self.order(symbol, "SELL", sell_amount)
                            if order_success:
                                self.last_trade_time[cur] = current_time
                                if cur in self.positions:
                                    del self.positions[cur]
                                print(f"SELL {sell_amount} {symbol} at {current_price}")
                                print(f"Indicators - SMA: {sma}, RSI: {rsi}, MACD: {macd}/{macd_signal}, BB: {bb_lower}/{bb_upper}")
                                print("Balance:", self.get_balance("USDT"), "USDT")
                            else:
                                print(f"Failed to SELL {sell_amount} {symbol}")

                await asyncio.sleep(5)

            except Exception as e:
                print(f"Error in get_rates for {cur}: {e}")

        self.timeout = False












    async def get_rates__8(self):
        SMA_PERIOD = 20
        COOLDOWN_SECONDS = 30 # 300  # 5-minute cooldown
        MAX_POSITION_PERCENT = 0.1  # 10% of USDT balance per trade
        STOP_LOSS_PCT = 0.05  # 5% stop loss
        GRID_LEVELS_COUNT = 5  # Number of grid levels

        if not hasattr(self, 'last_trade_time'):
            self.last_trade_time = {cur: 0 for cur in self.curs}
        if not hasattr(self, 'positions'):
            self.positions = {}  # Store buy price for stop-loss checking

        for cur in self.curs:
            try:
                symbol = cur + "USDT"
                if symbol not in self.data:
                    print(f"Skipping {symbol}: No market data available in self.data")
                    continue

                # Get current price from WebSocket data
                ask_data = self.get_ask(symbol)
                if ask_data is None or not isinstance(ask_data, (list, tuple)) or len(ask_data) < 1:
                    print(f"Skipping {symbol}: Invalid ask data - {ask_data}")
                    continue

                current_price = ask_data[0]
                if current_price <= 0:
                    print(f"Skipping {symbol}: Invalid price - {current_price}")
                    continue

                current_time = time.time()
                if current_time - self.last_trade_time.get(cur, 0) < COOLDOWN_SECONDS:
                    continue

                # Fetch technical indicators
                rsi, macd, macd_signal, bb_lower, bb_upper, sma50 = self.get_technical_indicators(symbol)
                sma = self.get_sma(symbol, SMA_PERIOD)

                if any(x is None for x in [sma, rsi, macd, macd_signal, bb_lower, bb_upper]) or pd.isna(macd_signal):
                    print(f"Skipping {symbol}: Indicator data incomplete - SMA: {sma}, RSI: {rsi}, MACD: {macd}/{macd_signal}, BB: {bb_lower}/{bb_upper}")
                    continue

                # Calculate grid levels (assume weekly support/resistance from your method)
                grid_data = self.recalc_grid_levels(symbol)
                if grid_data is None:
                    print(f"Skipping {symbol}: Failed to calculate grid levels")
                    continue
                grid_levels = grid_data["grid_levels"]

                # Risk management
                usdt_balance = self.get_balance("USDT")
                max_trade_usdt = 150 * MAX_POSITION_PERCENT # usdt_balance
                euro_available = min(random.randint(self.min_amount, self.max_amount), max_trade_usdt)
                trade_amount = self.floor(euro_available / current_price, self.precision.get(symbol, 8))

                # Trading signals
                buy_signals = 0
                sell_signals = 0

                # SMA: Price above SMA for buy, below for sell
                if current_price > sma:
                    buy_signals += 1
                elif current_price < sma:
                    sell_signals += 1

                # RSI: Oversold (<30) for buy, overbought (>70) for sell
                if rsi < 40:
                    buy_signals += 1
                elif rsi > 60:
                    sell_signals += 1

                # MACD: MACD line above signal for buy, below for sell
                if macd > macd_signal:
                    buy_signals += 1
                elif macd < macd_signal:
                    sell_signals += 1


                print(f'{symbol} ||| sma: {sma} | rsi: {rsi} | macd: {macd}')
                print(f'{symbol} ||| macd_signal: {macd_signal} | bb_lower: {bb_lower}')
                print(f'{symbol} ||| bb_upper: {bb_upper} | sma50: {sma50}')



                # Grid: Buy near support (lower grid), sell near resistance (upper grid)
                nearest_grid = min(grid_levels, key=lambda x: abs(x - current_price))

                # if current_price < grid_levels[0] + grid_data["tolerance"]:  # Near support
                #     buy_signals += 1
                # elif current_price > grid_levels[-1] - grid_data["tolerance"]:  # Near resistance
                #     sell_signals += 1
                
                if current_price < bb_lower + grid_data["tolerance"]:  # Near support
                    buy_signals += 1
                elif current_price > bb_upper - grid_data["tolerance"]:  # Near resistance
                    sell_signals += 1

                # Stop-loss check
                # if cur in self.positions and self.check_stop_loss(self.positions[cur], current_price, STOP_LOSS_PCT):
                #     available_balance = self.get_balance(cur)
                #     if available_balance > 0:
                #         sell_amount = self.floor(available_balance, self.precision.get(symbol, 8))
                #         if sell_amount * current_price > self.min_amount:
                #             order_success = self.order(symbol, "SELL", sell_amount)
                #             if order_success:
                #                 self.last_trade_time[cur] = current_time
                #                 print(f"STOP LOSS SELL {sell_amount} {symbol} at {current_price}")
                #                 print(f"Indicators - SMA: {sma}, RSI: {rsi}, MACD: {macd}/{macd_signal}, Grid: {nearest_grid}")
                #                 print("Balance:", self.get_balance("USDT"), "USDT")
                if cur in self.positions and current_price > self.positions[cur]["buy_price"] * 1.03:
                    available_balance = self.get_balance(cur)
                    if available_balance > 0:
                        sell_amount = self.floor(available_balance, self.precision.get(symbol, 8))
                        if sell_amount * current_price > self.min_amount:
                            order_success = self.order(symbol, "SELL", sell_amount)
                            if order_success:
                                self.last_trade_time[cur] = current_time
                                if cur in self.positions:
                                    del self.positions[cur]
                                print(f"TAKE PROFIT SELL {sell_amount} {symbol} at {current_price}")
                                del self.positions[cur]  # Remove position after selling
                            else:
                                print(f"Failed to execute STOP LOSS SELL {sell_amount} {symbol}")
                    continue

                # Execute trades (require 3/4 signals)
                if buy_signals >= 3 and trade_amount > 0:
                    order_success = self.order(symbol, "BUY", trade_amount)
                    if order_success:
                        self.last_trade_time[cur] = current_time
                        self.positions[cur] = {"buy_price": current_price}  # Store for stop-loss
                        print(f"BUY {trade_amount} {symbol} at {current_price}")
                        print(f"Indicators - SMA: {sma}, RSI: {rsi}, MACD: {macd}/{macd_signal}, Grid: {nearest_grid}")
                        print("Balance:", self.get_balance("USDT"), "USDT")
                    else:
                        print(f"Failed to BUY {trade_amount} {symbol}")

                elif sell_signals >= 3:
                    available_balance = self.get_balance(cur)
                    if available_balance > 0:
                        sell_amount = self.floor(available_balance, self.precision.get(symbol, 8))
                        if sell_amount * current_price > self.min_amount:
                            order_success = self.order(symbol, "SELL", sell_amount)
                            if order_success:
                                self.last_trade_time[cur] = current_time
                                if cur in self.positions:
                                    del self.positions[cur]  # Clear position after selling
                                print(f"SELL {sell_amount} {symbol} at {current_price}")
                                print(f"Indicators - SMA: {sma}, RSI: {rsi}, MACD: {macd}/{macd_signal}, Grid: {nearest_grid}")
                                print("Balance:", self.get_balance("USDT"), "USDT")
                            else:
                                print(f"Failed to SELL {sell_amount} {symbol}")

                await asyncio.sleep(5)

            except Exception as e:
                print(f"Error in get_rates for {cur}: {e}")

        self.timeout = False

    async def get_rates__7(self):
        SMA_PERIOD = 20
        RSI_PERIOD = 14
        ROC_PERIOD = 10
        MACD_FAST = 12
        MACD_SLOW = 26
        MACD_SIGNAL = 9
        COOLDOWN_SECONDS = 300  # 5-minute cooldown
        MAX_POSITION_PERCENT = 0.1  # 10% of USDT balance per trade

        if not hasattr(self, 'last_trade_time'):
            self.last_trade_time = {cur: 0 for cur in self.curs}

        for cur in self.curs:
            try:
                symbol = cur + "USDT"
                if symbol not in self.data:
                    print(f"Skipping {symbol}: No market data available in self.data")
                    continue

                # Get current price from WebSocket data
                ask_data = self.get_ask(symbol)
                if ask_data is None or not isinstance(ask_data, (list, tuple)) or len(ask_data) < 1:
                    print(f"Skipping {symbol}: Invalid ask data - {ask_data}")
                    continue

                current_price = ask_data[0]
                if current_price <= 0:
                    print(f"Skipping {symbol}: Invalid price - {current_price}")
                    continue

                current_time = time.time()
                if current_time - self.last_trade_time[cur] < COOLDOWN_SECONDS:
                    continue

                # Fetch klines for indicators
                try:
                    klines = self.client.get_klines(symbol=symbol, interval="15m", limit=max(SMA_PERIOD, RSI_PERIOD, ROC_PERIOD, MACD_SLOW))
                    closes = [float(k[4]) for k in klines]
                    if len(closes) < max(SMA_PERIOD, RSI_PERIOD, ROC_PERIOD, MACD_SLOW):
                        print(f"Skipping {symbol}: Insufficient klines data ({len(closes)})")
                        continue
                except Exception as e:
                    print(f"Skipping {symbol}: Failed to fetch klines - {e}")
                    continue

                # Convert closes to pandas Series for ta library
                close_series = pd.Series(closes)

                # Calculate indicators with ta library
                sma = self.get_sma(symbol, SMA_PERIOD)
                if sma is None:
                    print(f"Skipping {symbol}: SMA is None")
                    continue

                rsi = ta.momentum.RSIIndicator(close_series, window=RSI_PERIOD).rsi()
                rsi_value = rsi.iloc[-1] if rsi is not None and not rsi.isna().all() else None
                if rsi_value is None:
                    print(f"Skipping {symbol}: RSI is None")
                    continue

                roc = ta.momentum.ROCIndicator(close_series, window=ROC_PERIOD).roc()
                roc_value = roc.iloc[-1] if roc is not None and not roc.isna().all() else None
                if roc_value is None:
                    print(f"Skipping {symbol}: ROC is None")
                    continue

                macd_indicator = ta.trend.MACD(close_series, window_fast=MACD_FAST, window_slow=MACD_SLOW, window_sign=MACD_SIGNAL)
                macd_line = macd_indicator.macd().iloc[-1]
                signal_line = macd_indicator.macd_signal().iloc[-1]

                print(f' sma: {sma} | rsi: {rsi_value} | roc: {roc_value} | macd_line: {macd_line} | signal_line: {signal_line}')

                if pd.isna(macd_line) or pd.isna(signal_line):
                    print(f"Skipping {symbol}: MACD contains NaN - MACD: {macd_line}, Signal: {signal_line}")
                    continue

                # Risk management
                usdt_balance = self.get_balance("USDT")
                max_trade_usdt = 150.15615952 * MAX_POSITION_PERCENT
                euro_available = min(random.randint(self.min_amount, self.max_amount), max_trade_usdt)
                trade_amount = self.floor(euro_available / current_price, self.precision.get(symbol, 8))

                # Trading signals
                buy_signals = 0
                sell_signals = 0

                if current_price > sma:
                    buy_signals += 1
                elif current_price < sma:
                    sell_signals += 1

                if rsi_value < 30:
                    buy_signals += 1
                elif rsi_value > 70:
                    sell_signals += 1

                if roc_value > 0:
                    buy_signals += 1
                elif roc_value < 0:
                    sell_signals += 1

                if macd_line > signal_line:
                    buy_signals += 1
                elif macd_line < signal_line:
                    sell_signals += 1

                # Execute trades
                if buy_signals >= 3 and trade_amount > 0:
                    order_success = self.order(symbol, "BUY", trade_amount)
                    if order_success:
                        self.last_trade_time[cur] = current_time
                        print(f"BUY {trade_amount} {symbol} at {current_price}")
                        print(f"Indicators - SMA: {sma}, RSI: {rsi_value}, ROC: {roc_value}, MACD: {macd_line}/{signal_line}")
                        print("Balance:", self.get_balance("USDT"), "USDT")
                    else:
                        print(f"Failed to BUY {trade_amount} {symbol}")

                elif sell_signals >= 3:
                    available_balance = self.get_balance(cur)
                    if available_balance > 0:
                        sell_amount = self.floor(available_balance, self.precision.get(symbol, 8))
                        if sell_amount * current_price > self.min_amount:
                            order_success = self.order(symbol, "SELL", sell_amount)
                            if order_success:
                                self.last_trade_time[cur] = current_time
                                print(f"SELL {sell_amount} {symbol} at {current_price}")
                                print(f"Indicators - SMA: {sma}, RSI: {rsi_value}, ROC: {roc_value}, MACD: {macd_line}/{signal_line}")
                                print("Balance:", self.get_balance("USDT"), "USDT")
                            else:
                                print(f"Failed to SELL {sell_amount} {symbol}")

                await asyncio.sleep(5)

            except Exception as e:
                print(f"Error in get_rates for {cur}: {e}")

        self.timeout = False

    async def get_rates__6(self):
        SMA_PERIOD = 20
        RSI_PERIOD = 14
        ROC_PERIOD = 10
        MACD_FAST = 12
        MACD_SLOW = 26
        MACD_SIGNAL = 9
        COOLDOWN_SECONDS = 300  # 5-minute cooldown
        MAX_POSITION_PERCENT = 0.1  # 10% of USDT balance per trade

        if not hasattr(self, 'last_trade_time'):
            self.last_trade_time = {cur: 0 for cur in self.curs}

        for cur in self.curs:
            try:
                symbol = cur + "USDT"
                print('data = : ', self.data)
                if cur not in self.data:
                    print(f"Skipping {symbol}: No market data available in self.data")
                    continue

                # Check WebSocket data
                ask_data = self.get_ask(symbol)
                if ask_data is None or not isinstance(ask_data, (list, tuple)) or len(ask_data) == 0:
                    print(f"Skipping {symbol}: Invalid ask data - {ask_data}")
                    continue

                current_price = ask_data[0]
                if current_price <= 0:
                    print(f"Skipping {symbol}: Invalid price - {current_price}")
                    continue

                current_time = time.time()
                if current_time - self.last_trade_time[cur] < COOLDOWN_SECONDS:
                    continue

                # Fetch klines for indicators
                klines = self.client.get_klines(symbol=symbol, interval="15m", limit=max(SMA_PERIOD, RSI_PERIOD, ROC_PERIOD, MACD_SLOW))
                closes = [float(k[4]) for k in klines]
                if len(closes) < max(SMA_PERIOD, RSI_PERIOD, ROC_PERIOD, MACD_SLOW):
                    print(f"Skipping {symbol}: Insufficient klines data ({len(closes)})")
                    continue

                df = pd.DataFrame(closes, columns=["close"])

                # Calculate indicators
                sma = self.get_sma(symbol, SMA_PERIOD)
                rsi = ta.rsi(df["close"], length=RSI_PERIOD).iloc[-1]
                roc = ta.roc(df["close"], length=ROC_PERIOD).iloc[-1]
                macd = ta.macd(df["close"], fast=MACD_FAST, slow=MACD_SLOW, signal=MACD_SIGNAL)
                macd_line = macd[f'MACD_{MACD_FAST}_{MACD_SLOW}_{MACD_SIGNAL}'].iloc[-1]
                signal_line = macd[f'MACDs_{MACD_FAST}_{MACD_SLOW}_{MACD_SIGNAL}'].iloc[-1]
                print(f' sma: {sma} | rsi: {rsi} | roc: {roc} | macd: {macd} | macd_line: {macd_line} | signal_line: {signal_line}')
                
                if sma is None or rsi is None or roc is None or macd_line is None or signal_line is None:
                    print(f"Skipping {symbol}: One or more indicators are None - SMA: {sma}, RSI: {rsi}, ROC: {roc}, MACD: {macd_line}/{signal_line}")
                    continue

                # Risk management
                usdt_balance = self.get_balance("USDT")
                max_trade_usdt = usdt_balance * MAX_POSITION_PERCENT
                euro_available = min(random.randint(self.min_amount, self.max_amount), max_trade_usdt)
                trade_amount = self.floor(euro_available / current_price, self.precision.get(symbol, 8))

                # Trading signals
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

                if roc > 0:
                    buy_signals += 1
                elif roc < 0:
                    sell_signals += 1

                if macd_line > signal_line:
                    buy_signals += 1
                elif macd_line < signal_line:
                    sell_signals += 1

                # Execute trades
                if buy_signals >= 3 and trade_amount > 0:
                    order_success = self.order(symbol, "BUY", trade_amount)
                    if order_success:
                        self.last_trade_time[cur] = current_time
                        print(f"BUY {trade_amount} {symbol} at {current_price}")
                        print(f"Indicators - SMA: {sma}, RSI: {rsi}, ROC: {roc}, MACD: {macd_line}/{signal_line}")
                        print("Balance:", self.get_balance("USDT"), "USDT")
                    else:
                        print(f"Failed to BUY {trade_amount} {symbol}")

                elif sell_signals >= 3:
                    available_balance = self.get_balance(cur)
                    if available_balance > 0:
                        sell_amount = self.floor(available_balance, self.precision.get(symbol, 8))
                        if sell_amount * current_price > self.min_amount:
                            order_success = self.order(symbol, "SELL", sell_amount)
                            if order_success:
                                self.last_trade_time[cur] = current_time
                                print(f"SELL {sell_amount} {symbol} at {current_price}")
                                print(f"Indicators - SMA: {sma}, RSI: {rsi}, ROC: {roc}, MACD: {macd_line}/{signal_line}")
                                print("Balance:", self.get_balance("USDT"), "USDT")
                            else:
                                print(f"Failed to SELL {sell_amount} {symbol}")

                await asyncio.sleep(5)

            except Exception as e:
                print(f"Error in get_rates for {cur}: {e}")

        self.timeout = False

    async def get_rates__5(self):
        SMA_PERIOD = 20
        RSI_PERIOD = 14
        ROC_PERIOD = 10
        MACD_FAST = 12
        MACD_SLOW = 26
        MACD_SIGNAL = 9
        COOLDOWN_SECONDS = 300  # 5-minute cooldown between trades per symbol
        MAX_POSITION_PERCENT = 0.1  # Use only 10% of available USDT balance per trade

        # Track last trade time per symbol to enforce cooldown
        if not hasattr(self, 'last_trade_time'):
            self.last_trade_time = {cur: 0 for cur in self.curs}

        for cur in self.curs:
            try:
                symbol = cur + "USDT"
                if symbol not in self.data:
                    continue

                current_time = time.time()
                if current_time - self.last_trade_time[cur] < COOLDOWN_SECONDS:
                    continue  # Skip if still in cooldown

                # Get current price
                current_price = self.get_ask(symbol)[0]

                # Fetch klines for all indicators
                klines = self.client.get_klines(symbol=symbol, interval="15m", limit=max(SMA_PERIOD, RSI_PERIOD, ROC_PERIOD, MACD_SLOW))
                closes = [float(k[4]) for k in klines]  # Closing prices
                if len(closes) < max(SMA_PERIOD, RSI_PERIOD, ROC_PERIOD, MACD_SLOW):
                    print(f"Skipping {symbol} due to insufficient data")
                    continue

                df = pd.DataFrame(closes, columns=["close"])

                # Calculate indicators
                sma = self.get_sma(symbol, SMA_PERIOD)
                rsi = ta.rsi(df["close"], length=RSI_PERIOD).iloc[-1]
                roc = ta.roc(df["close"], length=ROC_PERIOD).iloc[-1]
                macd = ta.macd(df["close"], fast=MACD_FAST, slow=MACD_SLOW, signal=MACD_SIGNAL)
                macd_line = macd[f'MACD_{MACD_FAST}_{MACD_SLOW}_{MACD_SIGNAL}'].iloc[-1]
                signal_line = macd[f'MACDs_{MACD_FAST}_{MACD_SLOW}_{MACD_SIGNAL}'].iloc[-1]
                print(f' sma: {sma} | rsi: {rsi} | roc: {roc} | macd: {macd} | macd_line: {macd_line} | signal_line: {signal_line}')
                if sma is None or rsi is None or roc is None or macd_line is None:
                    print(f"Skipping {symbol} due to insufficient indicator data")
                    continue

                # Risk management: Limit position size
                usdt_balance = self.get_balance("USDT")
                max_trade_usdt = 150.59890092 * MAX_POSITION_PERCENT # usdt_balance
                euro_available = min(random.randint(self.min_amount, self.max_amount), max_trade_usdt)
                trade_amount = self.floor(euro_available / current_price, self.precision.get(symbol, 8))

                # Trading signals (require multiple confirmations)
                buy_signals = 0
                sell_signals = 0

                # SMA: Price above SMA for buy, below for sell
                if current_price > sma:
                    buy_signals += 1
                elif current_price < sma:
                    sell_signals += 1

                # RSI: Overbought (>70) for sell, oversold (<30) for buy
                if rsi < 30:
                    buy_signals += 1
                elif rsi > 70:
                    sell_signals += 1

                # ROC: Positive momentum for buy, negative for sell
                if roc > 0:
                    buy_signals += 1
                elif roc < 0:
                    sell_signals += 1

                # MACD: MACD line above signal line for buy, below for sell
                if macd_line > signal_line:
                    buy_signals += 1
                elif macd_line < signal_line:
                    sell_signals += 1

                # Require at least 3 out of 4 indicators to agree
                if buy_signals >= 3 and trade_amount > 0:
                    order_success = self.order(symbol, "BUY", trade_amount)
                    if order_success:
                        self.last_trade_time[cur] = current_time
                        print(f"BUY {trade_amount} {symbol} at {current_price}")
                        print(f"Indicators - SMA: {sma}, RSI: {rsi}, ROC: {roc}, MACD: {macd_line}/{signal_line}")
                        print("Balance:", self.get_balance("USDT"), "USDT")
                    else:
                        print(f"Failed to BUY {trade_amount} {symbol}")

                elif sell_signals >= 3:
                    available_balance = self.get_balance(cur)
                    if available_balance > 0:
                        sell_amount = self.floor(available_balance, self.precision.get(symbol, 8))
                        if sell_amount * current_price > self.min_amount:
                            order_success = self.order(symbol, "SELL", sell_amount)
                            if order_success:
                                self.last_trade_time[cur] = current_time
                                print(f"SELL {sell_amount} {symbol} at {current_price}")
                                print(f"Indicators - SMA: {sma}, RSI: {rsi}, ROC: {roc}, MACD: {macd_line}/{signal_line}")
                                print("Balance:", self.get_balance("USDT"), "USDT")
                            else:
                                print(f"Failed to SELL {sell_amount} {symbol}")

                # Delay to pace the loop
                await asyncio.sleep(5)

            except Exception as e:
                print(f"Error in get_rates for {cur}: {e}")

        self.timeout = False

    async def get_rates__4(self):
        SMA_PERIOD = 20  # Using the default period from your get_sma method

        for cur in self.curs:
            try:
                # Construct the USDT pair symbol
                symbol = cur + "USDT"
                
                # Skip if we don't have current market data
                if symbol not in self.data:
                    continue

                # Get current price (using ask price for simplicity)
                current_price = self.get_ask(symbol)[0]

                # Calculate SMA using your get_sma method
                sma = self.get_sma(symbol, SMA_PERIOD)

                if sma is None:
                    print(f"Skipping {symbol} due to insufficient SMA data")
                    continue

                # Determine trade amount
                euro_available = random.randint(self.min_amount, self.max_amount)
                trade_amount = self.floor(euro_available / current_price, self.precision.get(symbol, 8))

                # Trading logic based on SMA
                if current_price > sma:
                    # Price is above SMA (bullish), attempt to BUY
                    if trade_amount > 0:
                        order_success = self.order(symbol, "BUY", trade_amount)
                        if order_success:
                            print(f"BUY {trade_amount} {symbol} at {current_price} (Price > SMA: {sma})")
                            print("Balance:", self.get_balance("USDT"), "USDT")
                        else:
                            print(f"Failed to BUY {trade_amount} {symbol}")
                elif current_price < sma:
                    # Price is below SMA (bearish), attempt to SELL existing holdings
                    available_balance = self.get_balance(cur)
                    if available_balance > 0:
                        sell_amount = self.floor(available_balance, self.precision.get(symbol, 8))
                        if sell_amount * current_price > self.min_amount:  # Ensure minimum trade size
                            order_success = self.order(symbol, "SELL", sell_amount)
                            if order_success:
                                print(f"SELL {sell_amount} {symbol} at {current_price} (Price < SMA: {sma})")
                                print("Balance:", self.get_balance("USDT"), "USDT")
                            else:
                                print(f"Failed to SELL {sell_amount} {symbol}")
                else:
                    print(f"No action for {symbol}: Price ({current_price}) equals SMA ({sma})")

                # Small delay to avoid overwhelming the API
                await asyncio.sleep(1)

            except Exception as e:
                print(f"Error in get_rates for {cur}: {e}")

        self.timeout = False

    async def get_rates__3(self):
        # Dictionary to store price history for SMA calculation
        if not hasattr(self, 'price_history'):
            self.price_history = {market: [] for market in [cur + "USDT" for cur in self.curs] +
                                  [cur + "BTC" for cur in self.curs] + ["BTCUSDT"]}

        # SMA window size (e.g., 5 periods)
        # SMA_WINDOW = 5

        for cur in self.curs:
            try:
                if cur+"USDT" not in self.data or cur+"BTC" not in self.data or "BTCUSDT" not in self.data:
                    continue

                # Update price history with current ask prices
                markets = [cur+"USDT", cur+"BTC", "BTCUSDT"]
                for market in markets:
                    current_price = self.get_ask(market)[0]
                    self.price_history[market].append(current_price)

                # Calculate SMA using pandas_ta for each market
                sma_values = {}
                for market in markets:
                    if len(self.price_history[market]) >= self.SMA_WINDOW:
                        # Convert price history to pandas Series and calculate SMA
                        price_series = pd.Series(self.price_history[market])
                        sma = ta.sma(price_series, length=self.SMA_WINDOW)
                        # Get the latest SMA value
                        sma_values[market] = sma.iloc[-1]
                    else:
                        sma_values[market] = None  # Not enough data yet

                # Pattern 1: USDT -> ALTCOIN -> BTC -> USDT
                euro_available = random.randint(
                    self.min_amount, self.max_amount)
                x = self.floor(euro_available / self.get_ask(cur+"USDT")
                               [0], self.precision.get(cur+"USDT", 8))
                
                y = self.floor(x * 0.999, self.precision.get(cur+"BTC", 8))

                z = self.floor((y * 0.999) * self.get_bid(cur+"BTC")
                               [0], self.precision.get("BTCUSDT", 8))
                
                a = self.get_ask(cur+"USDT")[0] * x
                b = self.get_bid("BTCUSDT")[0] * z
                arbitrage = a / x * x / y * y / b if x and y and b else 0
                profit = b - a
                print(f' x: {x} | y: {y} | z: {z} | a: {a} | b: {b}')
                # Only trade if current price is above SMA (bullish trend) and arbitrage conditions are met
                if (sma_values[cur+"USDT"] and sma_values[cur+"BTC"] and sma_values["BTCUSDT"] and
                    self.get_ask(cur+"USDT")[0] > sma_values[cur+"USDT"] and
                        arbitrage < 0.99 and profit > 0 and euro_available > self.min_amount):
                    euro_available = min(euro_available, self.max_amount)
                    trade_amount = x
                    order_success = self.order(cur+"USDT", "BUY", trade_amount)
                    if order_success:
                        trade_amount = y
                        order_success = self.order(
                            cur+"BTC", "SELL", trade_amount)
                        if not order_success:
                            self.sell_all()
                            time.sleep(10)
                            print("Balance:", self.get_balance("USDT"), "USDT")
                            continue
                        trade_amount = z
                        order_success = self.order(
                            "BTCUSDT", "SELL", trade_amount)
                        if not order_success:
                            self.sell_all()
                            time.sleep(10)
                            print("Balance:", self.get_balance("USDT"), "USDT")
                            continue
                        print(a, "USDT, BUY", x, cur+"USDT, SELL", y, cur+"BTC, SELL", b,
                              "BTCUSDT - ARBITRAGE:", arbitrage, "PROFIT:", profit, "USDT")
                        print("Balance:", self.get_balance("USDT"), "USDT")
                        time.sleep(30)

                # Pattern 2: USDT -> BTC -> ALTCOIN -> USDT
                euro_available = random.randint(
                    self.min_amount, self.max_amount)
                x = self.floor(euro_available / self.get_ask("BTCUSDT")
                               [0], self.precision.get("BTCUSDT", 8))
                y = self.floor((x * 0.999) / self.get_ask(cur+"BTC")
                               [0], self.precision.get(cur+"BTC", 8))
                z = self.floor(y * 0.999, self.precision.get(cur+"USDT", 8))
                a = self.get_ask("BTCUSDT")[0] * x
                b = self.get_bid(cur+"USDT")[0] * z
                arbitrage = a / x * x / y * y / b if x and y and b else 0
                profit = b - a

                # Only trade if current price is above SMA (bullish trend) and arbitrage conditions are met
                if (sma_values["BTCUSDT"] and sma_values[cur+"BTC"] and sma_values[cur+"USDT"] and
                    self.get_ask("BTCUSDT")[0] > sma_values["BTCUSDT"] and
                        arbitrage < 0.99 and profit > 0 and euro_available > self.min_amount):
                    euro_available = min(euro_available, self.max_amount)
                    trade_amount = x
                    order_success = self.order("BTCUSDT", "BUY", trade_amount)
                    if order_success:
                        trade_amount = y
                        order_success = self.order(
                            cur+"BTC", "BUY", trade_amount)
                        if not order_success:
                            self.sell_all()
                            print("Balance:", self.get_balance("USDT"), "USDT")
                            time.sleep(10)
                            continue
                        trade_amount = z
                        order_success = self.order(
                            cur+"USDT", "SELL", trade_amount)
                        if not order_success:
                            self.sell_all()
                            print("Balance:", self.get_balance("USDT"), "USDT")
                            time.sleep(10)
                            continue
                        print(a, "USDT, BUY", x, "BTCUSDT, BUY", y, cur+"BTC, SELL", b,
                              cur+"USDT - ARBITRAGE:", arbitrage, "PROFIT:", profit, "USDT")
                        print("Balance:", self.get_balance("USDT"), "USDT")
                        time.sleep(30)

            except Exception as e:
                print(f"Error in get_rates for {cur}: {e}")
        self.timeout = False

    async def get_rates__2(self):
        # Dictionary to store price history for SMA calculation
        if not hasattr(self, 'price_history'):
            self.price_history = {market: [] for market in [cur + "USDT" for cur in self.curs] +
                                  [cur + "BTC" for cur in self.curs] + ["BTCUSDT"]}

        # SMA window size (e.g., 5 periods)
        # SMA_WINDOW = 5

        for cur in self.curs:
            try:
                if cur+"USDT" not in self.data or cur+"BTC" not in self.data or "BTCUSDT" not in self.data:
                    continue

                # Update price history with current ask prices
                markets = [cur+"USDT", cur+"BTC", "BTCUSDT"]
                for market in markets:
                    current_price = self.get_ask(market)[0]
                    self.price_history[market].append(current_price)
                    # Keep only the last SMA_WINDOW prices
                    if len(self.price_history[market]) > self.SMA_WINDOW:
                        self.price_history[market].pop(0)

                # Calculate SMA for each market
                sma_values = {}
                for market in markets:
                    if len(self.price_history[market]) == self.SMA_WINDOW:
                        sma_values[market] = sum(
                            self.price_history[market]) / self.SMA_WINDOW
                    else:
                        sma_values[market] = None  # Not enough data yet

                # Pattern 1: USDT -> ALTCOIN -> BTC -> USDT
                euro_available = random.randint(
                    self.min_amount, self.max_amount)
                x = self.floor(euro_available / self.get_ask(cur+"USDT")
                               [0], self.precision.get(cur+"USDT", 8))
                y = self.floor(x * 0.999, self.precision.get(cur+"BTC", 8))
                z = self.floor((y * 0.999) * self.get_bid(cur+"BTC")
                               [0], self.precision.get("BTCUSDT", 8))
                a = self.get_ask(cur+"USDT")[0] * x
                b = self.get_bid("BTCUSDT")[0] * z
                arbitrage = a / x * x / y * y / b if x and y and b else 0
                profit = b - a

                # Only trade if current price is above SMA (bullish trend) and arbitrage conditions are met
                if (sma_values[cur+"USDT"] and sma_values[cur+"BTC"] and sma_values["BTCUSDT"] and
                    self.get_ask(cur+"USDT")[0] > sma_values[cur+"USDT"] and
                        arbitrage < 0.99 and profit > 0 and euro_available > self.min_amount):
                    euro_available = min(euro_available, self.max_amount)
                    trade_amount = x
                    order_success = self.order(cur+"USDT", "BUY", trade_amount)
                    if order_success:
                        trade_amount = y
                        order_success = self.order(
                            cur+"BTC", "SELL", trade_amount)
                        if not order_success:
                            self.sell_all()
                            time.sleep(5)
                            print("Balance:", self.get_balance("USDT"), "USDT")
                            continue
                        trade_amount = z
                        order_success = self.order(
                            "BTCUSDT", "SELL", trade_amount)
                        if not order_success:
                            self.sell_all()
                            time.sleep(5)
                            print("Balance:", self.get_balance("USDT"), "USDT")
                            continue
                        print(a, "USDT, BUY", x, cur+"USDT, SELL", y, cur+"BTC, SELL", b,
                              "BTCUSDT - ARBITRAGE:", arbitrage, "PROFIT:", profit, "USDT")
                        print("Balance:", self.get_balance("USDT"), "USDT")
                        time.sleep(10)

                # Pattern 2: USDT -> BTC -> ALTCOIN -> USDT
                euro_available = random.randint(
                    self.min_amount, self.max_amount)
                x = self.floor(euro_available / self.get_ask("BTCUSDT")
                               [0], self.precision.get("BTCUSDT", 8))
                y = self.floor((x * 0.999) / self.get_ask(cur+"BTC")
                               [0], self.precision.get(cur+"BTC", 8))
                z = self.floor(y * 0.999, self.precision.get(cur+"USDT", 8))
                a = self.get_ask("BTCUSDT")[0] * x
                b = self.get_bid(cur+"USDT")[0] * z
                arbitrage = a / x * x / y * y / b if x and y and b else 0
                profit = b - a

                # Only trade if current price is above SMA (bullish trend) and arbitrage conditions are met
                if (sma_values["BTCUSDT"] and sma_values[cur+"BTC"] and sma_values[cur+"USDT"] and
                    self.get_ask("BTCUSDT")[0] > sma_values["BTCUSDT"] and
                        arbitrage < 0.99 and profit > 0 and euro_available > self.min_amount):
                    euro_available = min(euro_available, self.max_amount)
                    trade_amount = x
                    order_success = self.order("BTCUSDT", "BUY", trade_amount)
                    if order_success:
                        trade_amount = y
                        order_success = self.order(
                            cur+"BTC", "BUY", trade_amount)
                        if not order_success:
                            self.sell_all()
                            print("Balance:", self.get_balance("USDT"), "USDT")
                            time.sleep(5)
                            continue
                        trade_amount = z
                        order_success = self.order(
                            cur+"USDT", "SELL", trade_amount)
                        if not order_success:
                            self.sell_all()
                            print("Balance:", self.get_balance("USDT"), "USDT")
                            time.sleep(5)
                            continue
                        print(a, "USDT, BUY", x, "BTCUSDT, BUY", y, cur+"BTC, SELL", b,
                              cur+"USDT - ARBITRAGE:", arbitrage, "PROFIT:", profit, "USDT")
                        print("Balance:", self.get_balance("USDT"), "USDT")
                        time.sleep(10)

            except Exception as e:
                print(f"Error in get_rates for {cur}: {e}")
        self.timeout = False

    async def get_rates__(self):
        for cur in self.curs:
            try:
                if cur+"USDT" not in self.data or cur+"BTC" not in self.data or "BTCUSDT" not in self.data:
                    continue

                euro_available = random.randint(
                    self.min_amount, self.max_amount)
                x = self.floor(euro_available/self.get_ask(cur+"USDT")
                               [0], self.precision.get(cur+"USDT", 8))
                y = self.floor(x*0.999, self.precision.get(cur+"BTC", 8))
                z = self.floor((y*0.999)*self.get_bid(cur+"BTC")
                               [0], self.precision.get("BTCUSDT", 8))
                a = self.get_ask(cur+"USDT")[0]*x
                b = self.get_bid("BTCUSDT")[0]*z
                arbitrage = a/x*x/y*y/b if x and y and b else 0
                profit = b-a

                if arbitrage < 0.99 and profit > 0 and euro_available > self.min_amount:
                    euro_available = min(euro_available, self.max_amount)
                    trade_amount = x
                    order_success = self.order(cur+"USDT", "BUY", trade_amount)
                    if order_success:
                        trade_amount = y
                        order_success = self.order(
                            cur+"BTC", "SELL", trade_amount)
                        if not order_success:
                            self.sell_all()
                            time.sleep(10)
                            print("Balance:", self.get_balance("USDT"), "USDT")
                            continue
                        trade_amount = z
                        order_success = self.order(
                            "BTCUSDT", "SELL", trade_amount)
                        if not order_success:
                            self.sell_all()
                            time.sleep(10)
                            print("Balance:", self.get_balance("USDT"), "USDT")
                            continue
                        print(a, "USDT, BUY", x, cur+"USDT, SELL", y, cur+"BTC, SELL", b,
                              "BTCUSDT - ARBITRAGE:", arbitrage, "PROFIT:", profit, "USDT")
                        print("Balance:", self.get_balance("USDT"), "USDT")
                        time.sleep(30)

                euro_available = random.randint(
                    self.min_amount, self.max_amount)
                x = self.floor(euro_available/self.get_ask("BTCUSDT")
                               [0], self.precision.get("BTCUSDT", 8))
                y = self.floor((x*0.999)/self.get_ask(cur+"BTC")
                               [0], self.precision.get(cur+"BTC", 8))
                z = self.floor(y*0.999, self.precision.get(cur+"USDT", 8))
                a = self.get_ask("BTCUSDT")[0]*x
                b = self.get_bid(cur+"USDT")[0]*z
                arbitrage = a/x*x/y*y/b if x and y and b else 0
                profit = b-a

                if arbitrage < 0.99 and profit > 0 and euro_available > self.min_amount:
                    euro_available = min(euro_available, self.max_amount)
                    trade_amount = x
                    order_success = self.order("BTCUSDT", "BUY", trade_amount)
                    if order_success:
                        trade_amount = y
                        order_success = self.order(
                            cur+"BTC", "BUY", trade_amount)
                        if not order_success:
                            self.sell_all()
                            print("Balance:", self.get_balance("USDT"), "USDT")
                            time.sleep(10)
                            continue
                        trade_amount = z
                        order_success = self.order(
                            cur+"USDT", "SELL", trade_amount)
                        if not order_success:
                            self.sell_all()
                            print("Balance:", self.get_balance("USDT"), "USDT")
                            time.sleep(10)
                            continue
                        print(a, "USDT, BUY", x, "BTCUSDT, BUY", y, cur+"BTC, SELL", b,
                              cur+"USDT - ARBITRAGE:", arbitrage, "PROFIT:", profit, "USDT")
                        print("Balance:", self.get_balance("USDT"), "USDT")
                        time.sleep(30)
            except Exception as e:
                print(f"Error in get_rates for {cur}: {e}")
        self.timeout = False

    def get_balance(self, cur):
        try:
            re = self.client.get_asset_balance(asset=cur)
            return float(re["free"]) if re else 0
        except:
            return 0

    def sell_all(self):
        try:
            for cur in self.curs + ["BTC"]:
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
            data["public"],
            data["secret"],
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
