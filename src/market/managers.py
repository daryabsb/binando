from django.db import models
from decimal import Decimal

from django.db import models
from collections import defaultdict


class CryptoCurrencyManager(models.Manager):
    def get_cryptos_with_sparkline(self, kline_amount=28):
        """
        Fetches all cryptocurrencies with their latest klines formatted for sparkline charts.
        Optimized to use only 2 queries (1 for cryptos, 1 for klines).

        Args:
            kline_amount (int): Number of klines to fetch per crypto (default: 25).

        Returns:
            QuerySet: CryptoCurency objects with `.sparkline_data` attached.
        """
        from src.market.models import Kline

        # Fetch all cryptos
        cryptos = list(self.get_queryset().all())
        if not cryptos:
            return cryptos  # Empty list

        # Step 1: Bulk-fetch klines (1 query)
        symbols = [f"{crypto.ticker}USDT" for crypto in cryptos]
        klines = (
            Kline.objects
            .filter(symbol__in=symbols)
            .order_by('-time')[:kline_amount * len(symbols)]  # Smart limit
        )

        # Step 2: Group klines by symbol
        klines_by_symbol = defaultdict(list)
        for kline in klines:
            if len(klines_by_symbol[kline.symbol]) < kline_amount:
                klines_by_symbol[kline.symbol].append(kline)

        # Step 3: Attach sparkline data
        for crypto in cryptos:
            symbol = f"{crypto.ticker}USDT"
            crypto_klines = klines_by_symbol.get(symbol, [])

            # Use your existing formatting logic
            # crypto.klines = Kline.objects.get_klines_spark_list(
            #     symbol=symbol,
            #     # Ensure <= kline_amount
            #     amount=min(len(crypto_klines), kline_amount)
            # )
            # Use your existing formatting logic
            crypto.klines = Kline.objects.get_klines_sparkline_list(
                symbol=symbol,
                # Ensure <= kline_amount
                amount=min(len(crypto_klines), kline_amount)
            )

        return cryptos


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


class KlineManager(models.Manager):
    def get_klines(self, symbol, amount):
        if not symbol:
            return []
        elif 'USDT' not in symbol:
            symbol = f"{symbol}USDT"

        klines = self.filter(symbol=symbol).values_list(
            'open', 'high', 'low', 'close', 'end_time'
        )[:amount]

        return klines

    def get_klines_spark_list(self, symbol, amount):
        klines = self.get_klines(symbol, amount)
        klines_data = [{
            'x': (kline[4].timestamp() * 1000),
            'y': [
                float(kline[0]),
                float(kline[1]),
                float(kline[2]),
                float(kline[3])
            ],
        } for kline in klines]
        return klines_data

    def get_klines_sparkline_list(self, symbol, amount):
        klines = self.get_klines(symbol, amount)
        klines_data = [float(kline[3]) for kline in klines]
        return klines_data
