from src.market.models import Kline
import pandas as pd
import ta
import time

# Mixin for Technical Analysis


class TechnicalAnalysisMixin:
    def get_signals(self, symbol, current_price):
        klines = Kline.objects.filter(symbol=symbol).order_by('-time')[:14]
        if len(klines) < 14:
            print(f"Skipping {symbol}: Insufficient kline data ({len(klines)} klines)")
            return 0, 0

        import pandas as pd
        import ta

        closes = [float(kline.close) for kline in klines]
        sma = sum(closes) / len(closes)
        rsi = ta.momentum.RSIIndicator(pd.Series(closes)).rsi().iloc[-1]
        macd_indicator = ta.trend.MACD(pd.Series(closes))
        macd = macd_indicator.macd().iloc[-1]
        macd_signal = macd_indicator.macd_signal().iloc[-1]
        bb = ta.volatility.BollingerBands(pd.Series(closes))
        bb_lower = bb.bollinger_lband().iloc[-1]
        bb_upper = bb.bollinger_hband().iloc[-1]

        buy_signals = sum([
            current_price > sma,
            rsi < 30,
            macd > macd_signal,
            current_price < bb_lower * 1.01
        ])
        sell_signals = sum([
            current_price < sma,
            rsi > 70,
            macd < macd_signal,
            current_price > bb_upper * 0.99
        ])

        return buy_signals, sell_signals

# Subclass for Order Handling
class OrderHandler:
    def order(self, market, side, amount):
        """Place a market order (stub for external API integration)."""
        try:
            # This would call an external service or task in production
            print(f"{side.upper()} {amount} {market}")
            # Placeholder: Assume order is filled; integrate with a real API via a task
            return True
        except Exception as e:
            print(f"Order error for {market}: {e}")
            return False

    def sell_all(self):
        """Sell all holdings for tracked currencies."""
        try:
            for symbol in self.curs:
                time.sleep(5)
                amount = self.floor(self.get_balance(
                    symbol), self.precision.get(symbol + "USDT", 8))
                latest_kline = Kline.objects.filter(
                    symbol=symbol + "USDT").order_by('-time').first()
                if latest_kline and amount * float(latest_kline.close) > self.min_amount:
                    self.order(symbol + "USDT", "SELL", amount)
        except Exception as e:
            print(f"Error in sell_all: {e}")
