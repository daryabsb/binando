from decimal import Decimal, ROUND_HALF_UP
import json
from time import sleep
from django.db import models
from django.utils import timezone

from src.workflow.models import WorkflowInstance, WorkflowMixin
from src.market.utils import upload_image_file_path
from .managers import SymbolManager

from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _

from timescale.db.models.fields import TimescaleDateTimeField
from timescale.db.models.models import TimescaleModel
from timescale.db.models.managers import TimescaleManager
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
# trading/models.py
# from ...archive import tasks_market
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
        # tasks_market.sync_company_stock_quotes.delay(self.pk)


class CryptoCurency(WorkflowInstance, WorkflowMixin):
    name = models.CharField(max_length=120)
    ticker = models.CharField(max_length=20, unique=True, db_index=True)
    description = models.TextField(blank=True, null=True)
    # EXAMPLE =  0.25386236600000167
    balance = models.DecimalField(max_digits=30, decimal_places=17)
    pnl = models.DecimalField(max_digits=30, decimal_places=17, default=0)
    active = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.ticker} ||| Balance: {self.balance:.4f} ||| PNL: {self.pnl:.4f}'

    def save(self, *args, **kwargs):
        created = self.pk is None
        self.ticker = self.ticker.upper()
        super().save(*args, **kwargs)

    def get_kline_data(self):
        """Fetch the latest Kline data for this crypto's ticker."""
        symbol = f"{self.ticker}USDT"  # e.g., 'BTCUSDT'
        kline = Kline.objects.filter(symbol=symbol).order_by('-time').first()
        if kline:
            return {
                # Assuming 'close' is the last price in USDT
                'last_price': float(kline.close),
                'change_24h': float(kline.change_24h) if hasattr(kline, 'change_24h') else None,
                'high_24h': float(kline.high),
                'low_24h': float(kline.low),
                'volume_24h': float(kline.volume),
                # From CryptoCurency
                'current_amount_holding': float(self.balance),
            }
        return {
            'last_price': 0.0,
            'change_24h': 0.0,
            'high_24h': 0.0,
            'low_24h': 0.0,
            'volume_24h': 0.0,
            'current_amount_holding': float(self.balance),
        }

    def to_payload(self):
        """Generate payload with USD value based on Symbol price."""
        try:
            symbol = Symbol.objects.get(ticker=self.ticker)
            usd_value = float(self.balance) * float(symbol.price)
        except Symbol.DoesNotExist:
            usd_value = 0.0

        print('balance: ', f'{self.balance}')

        kline_data = self.get_kline_data()

        return {
            'ticker': self.ticker,
            'balance': f'{self.balance:.4f}',
            'usd_value': f'{usd_value:.2f}',
            'pnl': f'{self.pnl}',
            'timestamp': self.updated.strftime("%Y-%m-%d %H:%M"),
            'last_price': f"{kline_data['last_price']:.2f}",
            'change_24h': f"{kline_data['change_24h']:.2f}" if kline_data['change_24h'] is not None else 'N/A',
            'high_24h': f"{kline_data['high_24h']:.2f}",
            'low_24h': f"{kline_data['low_24h']:.2f}",
            'volume_24h': f"{kline_data['volume_24h']:.2f}",
            'current_amount_holding': f"{kline_data['current_amount_holding']:.2f}",
        }
    
    def update_usdt(self):
        from django.apps import apps

        group_name = 'usdt_notifications'
        message_type = 'usdt_update'
        if self.ticker == 'USDT':
            data = self.to_payload()

            self.update(
                # event=event,
                group_name=group_name,
                message_type=message_type,
                data=data
            )
        else:
            pass


    def send_event(self):
        """Send event with total USD calculated from all CryptoCurency instances."""
        global called
        # event = Notification.WorkflowEvents.CREATED if not self.pk else Notification.WorkflowEvents.UPDATED
        total_usd = 0.0
        # Calculate total USD
        for crypto in CryptoCurency.objects.exclude(ticker='USDT'):
            try:
                symbol = Symbol.objects.get(ticker=crypto.ticker)
                total_usd += float(crypto.balance) * float(symbol.price)
            except Symbol.DoesNotExist:
                continue
        try:
            total_usd += float(CryptoCurency.objects.get(ticker='USDT').balance)
        except CryptoCurency.DoesNotExist:
            pass

        data = self.to_payload()
        # data['total_usd'] = f"{total_usd:.2f}"

        self.update(
            # event=event,
            group_name='balances_notifications',
            message_type='balances_update',
            data=data
        )


class Order(WorkflowInstance, WorkflowMixin):
    ORDER_TYPES = (
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
    )
    crypto = models.ForeignKey(
        CryptoCurency, on_delete=models.CASCADE, related_name='orders')
    ticker = models.CharField(max_length=10)
    order_type = models.CharField(max_length=4, choices=ORDER_TYPES)
    quantity = models.DecimalField(max_digits=30, decimal_places=8)
    price = models.DecimalField(
        max_digits=30, decimal_places=8)  # Price at execution
    value = models.DecimalField(
        max_digits=30, decimal_places=4)  # quantity * price
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.order_type} {self.quantity:.4f} {self.ticker} at {self.price:.8f} on {self.timestamp}"

    def get_content(self, event):
        """Generate descriptive content matching the old notify logic."""
        action = 'bought' if self.order_type == 'BUY' else 'sold'
        amount = 'USD' if self.ticker != 'USDT' else self.ticker
        return f"You {action} {self.quantity:.2f} {self.ticker} for {self.value:.4f} {amount} at {self.price}"

    def to_payload(self):
        """Override to_payload to match the old detailed data structure."""
        return {
            'order_type': self.order_type,
            'quantity': f'{self.quantity.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)}',
            'ticker': self.ticker,
            'price': f'{self.price.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)}',
            'value': f'{self.value.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)}',
            'content': self.get_content(Notification.WorkflowEvents.TRADE_EXECUTED),
            'content_type': str(ContentType.objects.get_for_model(self.__class__)),
            'object_id': self.pk,
            'event': Notification.WorkflowEvents.TRADE_EXECUTED,
            'exception_id': None,  # Adjust if you use this
            'timestamp': self.timestamp,  # Keep as datetime
        }

    def send_event(self):
        """Send trade event with detailed notification payload."""
        from .models import Notification
        event = Notification.WorkflowEvents.TRADE_EXECUTED
        self.notify(
            event=event,
            group_name='trade_notifications',
            message_type='trade_update',
            data=self.to_payload()
        )


class CryptoCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    rank = models.PositiveIntegerField(
        _('rank'), default=0, help_text="Order of importance")

    class Meta:
        verbose_name = _('crypto category')
        verbose_name_plural = _('crypto categories')
        ordering = ['rank', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Symbol(models.Model):
    coin = models.CharField(max_length=100, null=True,
                            blank=True, unique=True)  # e.g., "BTCBitcoin"
    ticker = models.CharField(max_length=50, unique=True, db_index=True)
    rank = models.PositiveIntegerField(null=True, blank=True, unique=True)
    categories = models.ManyToManyField(CryptoCategory, blank=True)
    pair = models.CharField(max_length=50, unique=True, db_index=True)
    price = models.DecimalField(max_digits=30, decimal_places=17, default=0.00)
    change_24h = models.CharField(max_length=50, blank=True)  # e.g., "+2.35%"
    market_cap = models.CharField(
        max_length=50, blank=True)  # e.g., "1.67T USD"
    volume_24h = models.CharField(
        max_length=50, blank=True)  # e.g., "28.37B USD"
    circ_supply = models.DecimalField(
        max_digits=30, decimal_places=17, default=0.00)
    precision = models.IntegerField(default=8)  # Add this
    active = models.BooleanField(default=True)
    enabled = models.BooleanField(default=True)
    logo = models.ImageField(null=True, blank=True, default='coins/XTVCUSDT.svg',
                             upload_to=upload_image_file_path)  # e.g., "coins\XTVCBTC.svg"
    timestamp = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    objects = SymbolManager()

    def __str__(self):
        return self.pair

    class Meta:
        ordering = ('rank', '-active', 'ticker',)


# class Kline(models.Model):
#     symbol = models.CharField(max_length=20, db_index=True)
#     open = models.DecimalField(max_digits=20, decimal_places=8)
#     close = models.DecimalField(max_digits=20, decimal_places=8)
#     high = models.DecimalField(max_digits=20, decimal_places=8)
#     low = models.DecimalField(max_digits=20, decimal_places=8)
#     # Volume fields: increase max_digits to handle large numbers
#     volume = models.DecimalField(max_digits=30, decimal_places=8)


class Kline(models.Model):
    symbol = models.CharField(max_length=20, db_index=True)
    interval = models.CharField(max_length=10, default='5m')  # e.g., '5m'
    start_time = models.DateTimeField()  # Kline start time
    end_time = models.DateTimeField()  # Kline end time
    # timestamp = TimescaleDateTimeField(interval="2 week")
    open = models.DecimalField(max_digits=20, decimal_places=8)
    close = models.DecimalField(max_digits=20, decimal_places=8)
    high = models.DecimalField(max_digits=20, decimal_places=8)
    low = models.DecimalField(max_digits=20, decimal_places=8)
    # Volume fields: increase max_digits to handle large numbers
    volume = models.DecimalField(max_digits=30, decimal_places=8)
    quote_volume = models.DecimalField(max_digits=30, decimal_places=8)
    taker_buy_base_volume = models.DecimalField(
        max_digits=30, decimal_places=8)
    taker_buy_quote_volume = models.DecimalField(
        max_digits=30, decimal_places=8)
    trade_count = models.IntegerField()
    is_closed = models.BooleanField(default=False)
    # timestamp = models.BooleanField(default=False)
    time = TimescaleDateTimeField(interval="2 week")

    objects = models.Manager()
    timescale = TimescaleManager()

    # class Meta:

    indexes = [
        models.Index(fields=['symbol', 'time']),
    ]
    # unique_together = ('symbol', 'start_time', 'interval')

    def __str__(self):
        return f"{self.symbol}||{self.time}: {self.close}|{self.volume}"


class Notification(models.Model):
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name=_('content type'),
        null=True,
        blank=True
    )
    object_id = models.PositiveIntegerField(
        verbose_name=_('object id'),
        null=True,
        blank=True
    )
    content = models.CharField(
        _('content'),
        max_length=999,
        null=True,
        blank=True
    )
    is_sent = models.BooleanField(
        _('is sent'),
        default=False
    )
    event = models.SmallIntegerField(
        _('event'),
        choices=[
            (1, 'Created'),
            (2, 'Updated'),
            (3, 'Deleted'),
            (4, 'Trade Executed'),
            (5, 'Error Occurred'),
        ],
        null=True,
        blank=True
    )
    commit_time = models.DateTimeField(
        _('commit time'),
        auto_now_add=True
    )
    send_time = models.DateTimeField(
        _('send time'),
        null=True,
        blank=True
    )
    exception_id = models.CharField(
        _('exception id'),
        max_length=255,
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['-commit_time']
        verbose_name = _('notification')
        verbose_name_plural = _('notifications')

    class WorkflowEvents:
        CREATED = 1
        UPDATED = 2
        DELETED = 3
        TRADE_EXECUTED = 4
        ERROR_OCCURRED = 5

    def save(self, *args, **kwargs):
        if self.is_sent and not self.send_time:
            self.send_time = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_event_display()} - {self.content} ({self.commit_time})"


# @receiver(post_save, sender=CryptoCurency)
# def notify_on_save(sender, instance, created, **kwargs):
#     # if created:
#     instance.send_event()

@receiver(post_save, sender=Order)
def notify_on_save(sender, instance, created, **kwargs):
    if created:
        instance.send_event()
        crypto = instance.crypto
        crypto.send_event()

@receiver(post_save, sender=CryptoCurency)
def update_usdt_on_save(sender, instance, created, **kwargs):
    if not created and instance.ticker == 'USDT':
        instance.update_usdt()
