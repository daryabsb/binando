from django.db import models

from timescale.db.models.models import TimescaleModel
from timescale.db.models.fields import TimescaleDateTimeField
from timescale.db.models.managers import TimescaleManager

from . import tasks
# Create your models here.


class Company(models.Model):
    name = models.CharField(max_length=120)
    ticker = models.CharField(max_length=20, unique=True, db_index=True)
    description = models.TextField(blank=True, null=True)
    active = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.ticker = f"{self.ticker}".upper()
        super().save(*args, **kwargs)
        tasks.sync_company_stock_quotes.delay(self.pk)


class CryptoCurency(models.Model):
    name = models.CharField(max_length=120)
    ticker = models.CharField(max_length=20, unique=True, db_index=True)
    description = models.TextField(blank=True, null=True)
    # EXAMPLE =  0.25386236600000167
    balance = models.DecimalField(max_digits=20, decimal_places=17)
    pnl = models.DecimalField(max_digits=20, decimal_places=17, default=0)
    active = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.ticker = f"{self.ticker}".upper()
        super().save(*args, **kwargs)
        # tasks.sync_crypto_currency_quotes.delay(self.pk)


# class Symbol(models.Model):
#     currency = models.OneToOneField(
#         CryptoCurency, on_delete=models.CASCADE, related_name='symbol'
#     )
#     # EXAMPLE =  0.25386236600000167
#     balance = models.DecimalField(max_digits=14, decimal_places=17)
#     pnl = models.DecimalField(max_digits=14, decimal_places=17, default=0)
#     active = models.BooleanField(default=True)
#     timestamp = TimescaleDateTimeField(auto_now_add=True)
#     updated = TimescaleDateTimeField(auto_now=True)

class Symbol(models.Model):
    ticker = models.CharField(max_length=20, unique=True, db_index=True)
    pair = models.CharField(max_length=20, unique=True, db_index=True)
    active = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.pair


class Kline(models.Model):
    symbol = models.CharField(max_length=20, db_index=True)
    time = TimescaleDateTimeField(interval="2 week")
    # timestamp = TimescaleDateTimeField(interval="2 week")
    open = models.DecimalField(max_digits=30, decimal_places=17)
    high = models.DecimalField(max_digits=30, decimal_places=17)
    low = models.DecimalField(max_digits=30, decimal_places=17)
    close = models.DecimalField(max_digits=30, decimal_places=17)
    volume = models.DecimalField(max_digits=30, decimal_places=17)
    num_of_trades = models.BigIntegerField(default=0)
    # time = TimescaleDateTimeField(interval="1 week")

    objects = models.Manager()
    timescale = TimescaleManager()

    class Meta:
        indexes = [
            models.Index(fields=['symbol', 'time']),
        ]
        unique_together = ['symbol', 'time']

    def __str__(self):
        return f"{self.symbol}||{self.timestamp}: {self.close}|{self.volume}"
# timestamp: 2025-03-05 10:45:00+00:00
# open: 0.23080000
# high: 0.23310000
# low: 0.22880000
# close: 0.23180000
# volume: 183015.00000000
