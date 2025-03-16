from decimal import Decimal
import json
from django.db import models
from django.utils import timezone

from src.market.mixins import WorkflowMixin
from src.market.utils import upload_image_file_path

from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _

from timescale.db.models.fields import TimescaleDateTimeField
from timescale.db.models.managers import TimescaleManager
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
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


class CryptoCurency(models.Model, WorkflowMixin):
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
        self.ticker = f"{self.ticker}".upper()
        super().save(*args, **kwargs)
        # tasks.sync_crypto_currency_quotes.delay(self.pk)


class Order(models.Model, WorkflowMixin):
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

    def to_dict(self):
        return {
            'order_type': str(self.order_type),
            'quantity': str(self.quantity),
            'ticker': str(self.ticker),
            'price': str(self.price),
            'value': str(self.value),
            'timestamp': str(self.timestamp.isoformat())
        }


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
    price = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    change_24h = models.CharField(max_length=10, blank=True)  # e.g., "+2.35%"
    market_cap = models.CharField(
        max_length=20, blank=True)  # e.g., "1.67T USD"
    volume_24h = models.CharField(
        max_length=20, blank=True)  # e.g., "28.37B USD"
    circ_supply = models.DecimalField(
        max_digits=15, decimal_places=2, default=0.00)
    precision = models.IntegerField(default=8)  # Add this
    active = models.BooleanField(default=True)
    logo = models.ImageField(null=True, blank=True, default='coins/XTVCUSDT.svg',
                            upload_to=upload_image_file_path)  # e.g., "coins\XTVCBTC.svg"
    timestamp = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.pair

    class Meta:
        ordering = ['rank', 'ticker']


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
# @receiver(post_save, sender=Order)
# def send_update(sender, instance, created, **kwargs):
#     channel_layer = get_channel_layer()
#     if sender == CryptoCurency:
#         group_name = 'crypto_updates'
#         message_type = 'balance_update'
#         data = {}  # HTMX fetches full table
#         # Trigger total USD update too
#         async_to_sync(channel_layer.group_send)(
#             'crypto_updates',
#             {'type': 'total_usd_update', 'data': ''}  # Data computed in consumer
#         )
#     elif sender == Order:
#         group_name = 'trade_notifications'
#         message_type = 'trade_update'
#         data_dict = {
#             "order_type": str(instance.order_type),
#             "quantity": str(instance.quantity),
#             "name": str(instance.crypto.name),
#             "ticker": str(instance.ticker),
#             "price": str(instance.price),
#             "value": str(instance.value),
#             "timestamp": str(instance.timestamp.isoformat())
#         }
#         data_json = json.dumps(data_dict)

#         # f"{instance.order_type} {instance.quantity} {instance.ticker} at {instance.price} (Value: {instance.value}) - {instance.timestamp.isoformat()}"
#         data = data_json
#         # Trigger balance and total USD updates on trade
#         async_to_sync(channel_layer.group_send)(
#             'crypto_updates',
#             {'type': 'balance_update', 'data': ''}
#         )
#         async_to_sync(channel_layer.group_send)(
#             'crypto_updates',
#             {'type': 'total_usd_update', 'data': ''}
#         )

#     async_to_sync(channel_layer.group_send)(
#         group_name,
#         {
#             'type': message_type,
#             'data': data
#         }
#     )


@receiver(post_save, sender=CryptoCurency)
@receiver(post_save, sender=Order)
def notify_on_save(sender, instance, created, **kwargs):
    event = Notification.WorkflowEvents.CREATED if created else Notification.WorkflowEvents.UPDATED
    instance.notify(event)


@receiver(post_delete, sender=CryptoCurency)
@receiver(post_delete, sender=Order)
def notify_on_delete(sender, instance, **kwargs):
    instance.notify(Notification.WorkflowEvents.DELETED)


# Signal to send WebSocket updates
# @receiver(post_save, sender=CryptoCurency)
# @receiver(post_save, sender=Order)
# def send_update(sender, instance, created, **kwargs):
#     channel_layer = get_channel_layer()
#     if sender == CryptoCurency:
#         group_name = 'crypto_updates'
#         message_type = 'balance_update'
#         data = {
#             'ticker': instance.ticker,
#             'balance': str(instance.balance),
#             'pnl': str(instance.pnl),
#             'updated': instance.updated.isoformat(),
#         }
#     elif sender == Order:
#         group_name = 'trade_notifications'
#         message_type = 'trade_update'
#         data = {
#             'ticker': instance.ticker,
#             'order_type': instance.order_type,
#             'quantity': str(instance.quantity),
#             'price': str(instance.price),
#             'value': str(instance.value),
#             'timestamp': instance.timestamp.isoformat(),
#         }

#     async_to_sync(channel_layer.group_send)(
#         group_name,
#         {
#             'type': message_type,
#             'data': data
#         }
#     )
