import websockets
import asyncio
import json
import time
import random
# from binance.client import Client
import pandas as pd
import pandas_ta as ta
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


class BnArber:
    def __init__(self, curs, public, secret, max_amount):
        self.url = "wss://stream.binance.com:9443/stream?streams=btcusdt@depth5"
        self.curs = curs
        self.data = {}
        self.timeout = False
        self.min_amount = 5
        self.max_amount = max_amount
        self.SMA_WINDOW = 20
        # Client(public, secret, tld='com', testnet=True)
        self.client = self.get_client(public, secret, testnet=True)
        self.precision = {}
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
        print(self.client.ping())
        print("Operating Markets:", ', '.join(self.curs))
        print("Balance:", self.get_balance("USDT"), "USDT")
        for cur in self.curs:
            self.url += f"/{cur.lower()}usdt@depth5/{cur.lower()}btc@depth5"

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

        # if testnet else PUBLIC
        API_KEY = "ka0UEMniJVyL5My7VCAjTThzVtuVqR72ekQiaJRJdfLqv8gXPoOBZTZSZvIHeRFh"
        # if testnet else SECRET
        API_SECRET = "0g1SxoIXk6RWUyBgYl1JuGG279ljuPgIcnfivc58cYPeLLFTi1rE0LqqcUAbLmjK"

        client = Client(API_KEY, API_SECRET, testnet=testnet)

        # # Get Binance server time and adjust
        # server_time = client.get_server_time()['serverTime']
        # system_time = int(time.time() * 1000)
        # time_offset = server_time - system_time

        # # Set the timestamp offset manually
        # client.timestamp_offset = time_offset

        return client

    def handle_data(self, message):
        message = json.loads(message)
        market_id = message["stream"].split("@")[0]
        asks = [(float(a[0]), float(a[1])) for a in message["data"]["asks"]]
        ask = min(asks, key=lambda t: t[0])
        bids = [(float(a[0]), float(a[1])) for a in message["data"]["bids"]]
        bid = max(bids, key=lambda t: t[0])
        self.data[market_id.upper()] = {"ask": ask, "bid": bid}

    async def get_rates(self):
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

    def get_ask(self, market):
        return self.data[market]["ask"]

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
