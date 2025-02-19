import pandas as pd
from decimal import Decimal, ROUND_DOWN, ROUND_UP
from ta.momentum import ROCIndicator
import pandas_ta
# client = get_client(testnet=True)


class Symbol:
    """Represents a trading pair and provides analysis utilities."""

    def __init__(self, client, symbol="USDT"):
        self.client = client
        self.symbol = symbol
        # self.info = self.get_info()

    def get_info(self):
        print(self.symbol)
        return self.symbol #.symbols_info.get(self.symbol, {})

    def get_price(self):
        """Fetches latest price for the symbol."""
        return self.client.get_price(self.symbol)

    def get_min_notional(self):
        """Fetch the minimum notional value required for a trade."""
        try:
            exchange_info = self.client.get_symbol_info(self.symbol)
            filters = exchange_info["filters"]
            for f in filters:
                if f["filterType"] == "NOTIONAL":
                    return Decimal(f["minNotional"])
        except Exception as e:
            print(f"⚠️ Error fetching minNotional for {self.symbol}: {e}")
        return Decimal("0.0")  # Default value

    def get_lot_size(self):
        """Fetches minimum lot size for an order."""
        return Decimal(next((f["stepSize"] for f in self.info["filters"] if f["filterType"] == "LOT_SIZE"), "0"))

    def get_balance(self, symbol=None):
        """Retrieve the available USDT balance."""
        if not symbol:
            symbol = self.symbol

        if not self.client:
            return 0.0
        if symbol == "USDT":
            balance = self.client.get_asset_balance(asset="USDT")
        else:
            asset = symbol.replace("USDT", "")  # Extract asset name
            balance = self.client.get_asset_balance(asset=asset)
        return float(balance["free"])

    def get_step_size_and_min_qty(self):
        """Retrieve the step size and minimum quantity for a given symbol."""

        exchange_info = self.client.get_symbol_info(self.symbol['symbol'])

        print('What is this? ', exchange_info['orderTypes']['filters'])
        step_size = min_qty = None

        for f in exchange_info["filters"]:
            if f["filterType"] == "LOT_SIZE":
                step_size = Decimal(f["stepSize"])
                min_qty = Decimal(f["minQty"])

        return step_size, min_qty

    def get_sma(self, period=20):
        """Fetch historical prices and calculate SMA."""
        try:
            klines = self.client.get_klines(symbol=self.symbol, interval="15m", limit=period)  # 15-minute candles
            closes = [float(k[4]) for k in klines]  # Closing prices

            if len(closes) < period:
                print(f"⚠️ Not enough data for SMA {period}.")
                return None

            df = pd.DataFrame(closes, columns=["close"])
            df["sma"] = pandas_ta.sma(df["close"], length=period)

            return df["sma"].iloc[-1]  # Latest SMA value
        except Exception as e:
            print(f"⚠️ Error calculating SMA for {self.symbol}: {e}")
            return None

    def get_roc(self, period=24):
        """Fetch historical prices and calculate the Rate of Change (ROC) indicator."""
        try:
            klines = self.client.get_klines(
                symbol=self.symbol, interval="1h", limit=period + 1)
            close_prices = [Decimal(kline[4]) for kline in klines]

            if len(close_prices) < period + 1:
                print(f"⚠️ Not enough data for {self.symbol} ROC calculation.")
                return Decimal("0.0")

            close_series = pd.Series(close_prices, dtype="float64")
            roc = ROCIndicator(close_series, window=period).roc().iloc[-1]
            return Decimal(str(roc)) / 100  # Convert to decimal format
        except Exception as e:
            print(f"⚠️ Error fetching ROC for {self.symbol}: {e}")
            return Decimal("0.0")

    def get_zlma(self, interval):
        """Calculate Zero Lag Moving Average (ZLMA) and ATR for a given symbol and interval."""
        klines = self.client.get_klines(symbol=self.symbol, interval=interval, limit=50)  # Get last 50 candles
        
        # Extract OHLCV data
        highs = [Decimal(k[2]) for k in klines]
        lows = [Decimal(k[3]) for k in klines]
        closes = [Decimal(k[4]) for k in klines]

        # ✅ ATR Calculation (14-period standard)
        atr_values = []
        for i in range(1, len(closes)):
            tr = max(highs[i] - lows[i], 
                    abs(highs[i] - closes[i - 1]), 
                    abs(lows[i] - closes[i - 1]))  # True Range formula
            atr_values.append(tr)

        atr = sum(atr_values[-14:]) / Decimal(14)  # 14-period ATR

        # ✅ ZLMA Calculation
        alpha = Decimal("2") / (Decimal(len(closes)) + Decimal("1"))
        zlma = sum(closes) / len(closes)  # SMA as the starting point

        for close in closes:
            zlma = (alpha * close) + ((Decimal("1") - alpha) * zlma)  # ZLMA formula

        return zlma, atr  # Return both ZLMA & ATR

    def is_bullish_trend(self, pullback=False):
        """Check if a coin is in a strong uptrend or pullback using ZLMA in multiple timeframes."""
        timeframes = ["5m", "15m", "1h", "4h", "1d"]
        if pullback:
            timeframes = ["15m", "1h", "4h", "1d"]  # Ignore 5m for pullbacks
        
        current_price = self.get_price()

        # ✅ Fetch ZLMA for all timeframes
        bullish_trend = all(current_price > self.get_zlma(tf)[0] for tf in timeframes)  

        return bullish_trend

    def calculate_quantity(self, amount, trade_type):
        """Calculate correct quantity based on Binance precision rules and risk management."""
        from bot.coins import get_sma

        price = self.get_price() 
        step_size, min_qty = self.get_step_size_and_min_qty()
        min_notional = self.get_min_notional()

        sma = Decimal(self.get_sma(period=20) or price)  # Avoid None

        # ✅ Ensure valid step size & min qty
        if not step_size or not min_qty:
            print(f"⚠️ Error fetching step size or minQty for {self.symbol}.")
            return None

        step_size, min_qty, min_notional = map(
            Decimal, (step_size, min_qty, min_notional))

        # ✅ Use fixed trading percentage
        USDT_TRADE_PERCENTAGE = Decimal("0.25")  # 25% of total USDT
        PER_TRADE_PERCENTAGE = Decimal("0.10")  # 10% of allocated balance

        # ✅ Buy: Allocate a portion of available USDT
        if trade_type == "BUY":
            # usdt_balance = Decimal(get_usdt_balance(client))
            usdt_balance = Decimal("10.0") if price < sma else Decimal("5.0")
            trade_usdt = (usdt_balance * USDT_TRADE_PERCENTAGE) * \
                PER_TRADE_PERCENTAGE
            quantity = (trade_usdt / price).quantize(step_size,
                                                    rounding=ROUND_DOWN)

        # ✅ Sell: Trade a portion of the coin balance worth `trade_usdt`
        else:  # trade_type == "SELL"
            available_balance = Decimal(self.get_balance() or 0)
            trade_usdt = (available_balance * price *
                        USDT_TRADE_PERCENTAGE) * PER_TRADE_PERCENTAGE
            quantity = (trade_usdt / price).quantize(step_size,
                                                    rounding=ROUND_DOWN)

        # ✅ Ensure order meets minNotional and minQty
        if (quantity * price) < min_notional or quantity < min_qty:
            print(
                f"⚠️ {self.symbol} Order too small ({quantity * price} < {min_notional}), skipping.")
            return None

        return str(quantity)  # Convert to string for Binance API


ingo = {'symbol': 'XRPUSDT', 'status': 'TRADING', 'baseAsset': 'XRP', 
        'baseAssetPrecision': 8, 'quoteAsset': 'USDT', 'quotePrecision': 8, 
        'quoteAssetPrecision': 8, 'baseCommissionPrecision': 8, 
        'quoteCommissionPrecision': 8, 
        'orderTypes': [
            'LIMIT', 'LIMIT_MAKER', 'MARKET', 'STOP_LOSS', 'STOP_LOSS_LIMIT', 
            'TAKE_PROFIT', 'TAKE_PROFIT_LIMIT'], 'icebergAllowed': True, 
            'ocoAllowed': True, 'otoAllowed': True, 'quoteOrderQtyMarketAllowed': True, 
            'allowTrailingStop': True, 'cancelReplaceAllowed': True, 
            'isSpotTradingAllowed': True, 'isMarginTradingAllowed': False, 
            'filters': [
                {
                    'filterType': 'PRICE_FILTER', 'minPrice': '0.00010000',
                    'maxPrice': '10000.00000000', 'tickSize': '0.00010000'
                }, 
                {
                    'filterType': 'LOT_SIZE', 'minQty': '1.00000000', 
                    'maxQty': '9222449.00000000', 'stepSize': '1.00000000'
                }, 
                {
                    'filterType': 'ICEBERG_PARTS', 'limit': 10
                }, 
                {
                    'filterType': 'MARKET_LOT_SIZE', 'minQty': '0.00000000', 
                    'maxQty': '2578738.88284518', 'stepSize': '0.00000000'}, 
            ], 
        'permissions': [], 
        'permissionSets': [['SPOT']], 
        'defaultSelfTradePreventionMode': 'EXPIRE_MAKER', 
        'allowedSelfTradePreventionModes': 
            ['NONE', 'EXPIRE_TAKER', 'EXPIRE_MAKER', 'EXPIRE_BOTH']
    } 