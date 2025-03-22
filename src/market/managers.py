from django.db import models
from decimal import Decimal


class SymbolManager(models.Manager):
    def sorted_symbols(self):
        """Sort symbols by total volume over the last 14 days, computed once at init."""
        from src.market.models import Kline  # Import inside to avoid circular import issues

        trending_coins = []
        VOLUME_THRESHOLD = Decimal('100000.0')

        symbols = self.filter(
            enabled=True, active=True).values_list('pair', flat=True)
        for symbol in symbols:
            try:
                klines = Kline.objects.filter(symbol=symbol).order_by(
                    '-time')[:2016]  # ~14 days (5-min intervals)
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
        return [coin["symbol"] for coin in sorted_coins]
