from datetime import datetime, timedelta
from decimal import Decimal, ROUND_DOWN, ROUND_UP
from client.symbol import Symbol
from client import Client
from _utils.const import LAST_TRADE, PRICE_CHANGE_THRESHOLD as threshold

class Trade:
    """Handles trade execution and market analysis."""

    def __init__(self, client:Client, symbol:Symbol):
        self.client = client
        self.symbol = Symbol(client, symbol)


    def has_recent_trade(self, min_time_gap=180, price_change_threshold=0.5):
        """Check if a recent trade happened for this symbol based on time or price movement."""
        try:
            # Fetch last 5 trades for the symbol
            trades = self.client.get_my_trades(symbol=self.symbol, limit=5)
            if not trades:
                return False  # No trade history, safe to proceed

            last_trade = trades[-1]  # Get the most recent trade
            last_trade_time = datetime.utcfromtimestamp(
                last_trade["time"] / 1000)  # Convert from milliseconds

            # ✅ Ensure correct time calculation
            time_since_last_trade = abs(
                # Convert to minutes
                datetime.utcnow() - last_trade_time).total_seconds() / 60
            # ✅ Time filter (skip if a trade happened too recently)
            if time_since_last_trade < min_time_gap:
                print(
                    f"⚠️ Skipping {self.symbol}: Last trade was {time_since_last_trade:.2f} min ago (Min gap: {min_time_gap} min).")
                return True

            # ✅ Price filter (skip if price change is too small)
            last_trade_price = Decimal(last_trade["price"])
            current_price = Decimal(self.symbol.get_price())
            price_change = abs(
                ((current_price - last_trade_price) / last_trade_price) * 100)

            if price_change < price_change_threshold:
                print(
                    f"⚠️ Skipping {self.symbol}: Price change is only {price_change:.2f}% (Min required: {price_change_threshold}%).")
                return True

            return False  # ✅ Safe to trade

        except Exception as e:
            print(f"⚠️ Error checking trade history for {self.symbol}: {e}")
            return False  # Assume safe to trade if an error occurs

    def get_current_price(self):
        """Fetch the latest price for a symbol from Binance API."""
        try:
            ticker = self.client.get_ticker(symbol=self.symbol)
            return Decimal(ticker["lastPrice"])
        except Exception as e:
            print(f"⚠️ Error fetching current price for {self.symbol}: {e}")
            return Decimal("0.0")

    def is_valid_trade(self, price, quantity):
        """Check if trade meets Binance's minimum notional value."""
        min_notional = self.symbol.get_min_notional()
        notional_value = Decimal(price) * Decimal(quantity)
        print(f"🔹 {self.symbol} notional_value: {notional_value}")
        if notional_value < min_notional:
            print(f"⚠️ Order too small: {notional_value} < {min_notional}")
            return False
        return True

    def roc_meets_threshold(self, roc):
        """Check if ROC meets the buy/sell threshold."""
        roc = self.symbol.get_roc()
        return roc >= threshold or roc <= -threshold

    def should_buy(self):
        """Check if we should place a BUY trade based on ROC."""
        current_price = self.get_current_price()
        # Default to current if not tracked
        last_price = LAST_TRADE.get(self.symbol, None)
        if last_price is None or last_price == Decimal("0.0"):
            last_price = current_price  # Initialize tracking to avoid division errors

        price_change = (Decimal(current_price) -
                        Decimal(last_price)) / Decimal(last_price)

        price_change_roc = self.symbol.get_roc()

        if self.roc_meets_threshold():
            print(
                f"✅ Buying {self.symbol} based on ROC drop of {price_change_roc:.2%}.")
            LAST_TRADE[self.symbol] = current_price
            return True

        print(
            f"📈 SKIP-BUY: {self.symbol} | ROC: {price_change_roc:.2%} | Price: {current_price}")

        return False

    def should_sell(self):
        """Check if we should place a SELL trade based on ROC."""
        coin_balance = self.symbol.get_balance()
        if coin_balance is None or coin_balance == Decimal("0.0"):
            return False  # No balance → no sell

        current_price = self.get_current_price()
        last_price = LAST_TRADE.get(self.symbol, current_price)
        price_change = (current_price - last_price) / last_price

        price_change_roc = self.symbol.get_roc()

        if self.roc_meets_threshold():
            print(f"🔄 Selling {self.symbol} | ROC Change: {price_change_roc:.2%}.")
            LAST_TRADE[self.symbol] = current_price
            return True

        print(
            f"📈 SKIP-SELL: {self.symbol} | ROC: {price_change_roc:.2%} | Price: {current_price}")

        return False

    def place_order(self, side, quantity):
        """Place a market order (buy/sell) with balance validation, LOT_SIZE, and MIN_NOTIONAL handling."""
        if not quantity or Decimal(quantity) <= 0:
            print(
                f"⚠️ Skipping {side} order for {self.symbol} (Invalid quantity: {quantity})")
            return

        # Fetch Binance trading rules
        exchange_info = self.client.get_exchange_info()
        symbol_info = next(
            (s for s in exchange_info["symbols"] if s["symbol"] == self.symbol), None)

        if not symbol_info:
            print(f"⚠️ No trading info for {self.symbol}. Skipping order.")
            return

        lot_size_filter = next(
            (f for f in symbol_info["filters"] if f["filterType"] == "LOT_SIZE"), None)
        notional_filter = next(
            (f for f in symbol_info["filters"] if f["filterType"] == "MIN_NOTIONAL"), None)

        price = Decimal(self.symbol.get_price())  # Get latest market price
        total_value = Decimal(quantity) * price  # Calculate trade value
        print(f'price: {price} | total_value: {total_value}')
        # ✅ Ensure quantity meets LOT_SIZE requirements
        if lot_size_filter:
            min_qty = Decimal(lot_size_filter["minQty"])
            step_size = Decimal(lot_size_filter["stepSize"])

            # Adjust quantity to a valid multiple of step_size
            adjusted_quantity = (Decimal(quantity) // step_size) * step_size

            if adjusted_quantity < min_qty:
                print(
                    f"❌ {self.symbol} Order rejected (Adjusted quantity {adjusted_quantity} < minQty {min_qty}). Skipping.")
                return

            quantity = adjusted_quantity  # Update with valid quantity

        # ✅ Ensure total value meets minNotional
        # if notional_filter:
        min_notional = Decimal(self.symbol.get_min_notional())

        if total_value < min_notional:
            print(
                f"❌ {self.symbol} Order rejected (Total value {total_value} < minNotional {min_notional}). Adjusting quantity...")

            # Calculate the minimum required quantity
            adjusted_quantity = (
                min_notional / price).quantize(step_size, rounding=ROUND_UP)

            # Recheck adjusted quantity
            adjusted_total_value = adjusted_quantity * price

            print(
                f"🔹 Adjusted Quantity: {adjusted_quantity} | Adjusted Total Value: {adjusted_total_value}")

            if adjusted_quantity < min_qty:
                print(
                    f"❌ Adjusted quantity ({adjusted_quantity}) is below minQty ({min_qty}). Skipping order.")
                return

            quantity = adjusted_quantity  # Update quantity

        print(
            f"✅ Final Order Details: {side.upper()} {self.symbol} | Quantity: {quantity} | Price: {price} | Total: {quantity * price}")

        # 🔹 Try executing the order
        try:
            order = self.client.order_market(
                symbol=self.symbol, side=side, quantity=str(quantity))
            print(f"✅ {side.upper()} Order placed for {self.symbol}: {quantity}")
        except Exception as e:
            print(f"❌ Error placing {side} order for {self.symbol}: {str(e)}")
