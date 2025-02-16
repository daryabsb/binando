import time
from binance.client import Client as BinanceClient
from BinanceKeys import test_api_key, test_secret_key, api_key, secret_key

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


def get_client(testnet=False):
    API_KEY = test_api_key if testnet else api_key
    API_SECRET = test_secret_key if testnet else secret_key

    client = Client(API_KEY, API_SECRET, testnet=testnet)

    # # Get Binance server time and adjust
    # server_time = client.get_server_time()['serverTime']
    # system_time = int(time.time() * 1000)
    # time_offset = server_time - system_time

    # # Set the timestamp offset manually
    # client.timestamp_offset = time_offset

    return client