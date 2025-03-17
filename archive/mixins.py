# trading/models.py
import json
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP
from django.contrib.contenttypes.models import ContentType
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging
# Ensure Kline is imported


class WorkflowMixin:
    def notify(self, event, content=None, exception_id=None):
        from src.market.models import Notification, CryptoCurency, Kline
        logger = logging.getLogger(__name__)
        content_type = ContentType.objects.get_for_model(self.__class__)
        obj_id = self.pk
        channel_layer = get_channel_layer()

        # Generate descriptive content and prepare data
        if content_type.model == 'order':
            print('Order triggered')
            # Order-specific logic
            action = 'bought' if self.order_type == 'BUY' else 'sold'
            amount = 'USD' if self.ticker != 'USDT' else self.ticker
            # per unit on {self.timestamp}
            content = f"You {action} {self.quantity:.2f} {self.ticker} for {self.value:.4f} {amount} at {self.price}"

            group_name = 'trade_notifications'
            message_type = 'trade_update'

            notification = Notification(
                content_type=content_type,
                object_id=obj_id,
                content=content,
                event=event,
                exception_id=exception_id,
            )
            data = {
                'order_type': self.order_type,
                'quantity': f'{self.quantity.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)}',
                'ticker': self.ticker,
                'price': f'{self.price.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)}',
                'value': f'{self.value.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)}',
                'content': content,
                'content_type': content_type,
                'object_id': obj_id,
                'event': event,
                'exception_id': exception_id,
                'timestamp': self.timestamp,  # Keep as datetime
            }
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': message_type,
                    'data': json.dumps(data, default=str),
                }
            )

            crypto = self.crypto

            first_kline = Kline.objects.filter(
                symbol=f"{crypto.ticker}USDT").order_by('-time').first()

            latest_price = first_kline.close if first_kline else Decimal(
                "0.00")
            usd_value = Decimal(crypto.balance) * latest_price

            # Calculate total USD value of all coins
            total_usd = Decimal("0.0")
            for crypto in CryptoCurency.objects.exclude(ticker='USDT'):
                price = Kline.objects.filter(
                    symbol=f"{crypto.ticker}USDT").order_by('-time').first().close
                total_usd += crypto.balance * price
            total_usd += CryptoCurency.objects.get(ticker='USDT').balance

            crypto_data = {
                'ticker': crypto.ticker,
                'balance': f'{Decimal(crypto.balance).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)}',
                'pnl': f'{Decimal(crypto.pnl).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)}',
                'usd_value': f'{usd_value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)}',
                'total_usd': f'{total_usd.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)}',
                'event': event,
                # Assuming timestamp fields
                'timestamp': crypto.updated if hasattr(crypto, 'updated_at') else crypto.timestamp,
            }

            # group_name = 'balances_notifications'
            # message_type = 'balances_update'

            channel_layer = get_channel_layer()

            # async_to_sync(channel_layer.group_send)(
            #     group_name,
            #     {
            #         'type': message_type,
            #         # 'data': json.dumps(data, default=str),
            #         'data': json.dumps(crypto_data, default=str),
            #     }
            # )

            notification.is_sent = True
            notification.save()
            logger.info(f"Notification created: {notification}")

        # elif content_type.model == 'cryptocurency':
        #     print('Crypto triggered')
        #     # CryptoCurency-specific logic
        #     if event == Notification.WorkflowEvents.CREATED:
        #         content = f"New currency {self.ticker} added with balance {self.balance}"
        #     elif event == Notification.WorkflowEvents.UPDATED:
        #         content = f"Balance of {self.ticker} updated to {self.balance}, PNL now {self.pnl}"
        #     elif event == Notification.WorkflowEvents.DELETED:
        #         content = f"Currency {self.ticker} removed"
        #     else:
        #         content = f"{self.ticker} event {event} occurred"

        #     # Calculate latest USD value for this coin
        #     first_kline = Kline.objects.filter(
        #         symbol=f"{self.ticker}USDT").order_by('-time').first()

            # latest_price = first_kline.close if first_kline else Decimal(
            #     "0.00")
            # usd_value = Decimal(self.balance) * latest_price

            # # Calculate total USD value of all coins
            # total_usd = Decimal("0.0")
            # for crypto in CryptoCurency.objects.exclude(ticker='USDT'):
            #     price = Kline.objects.filter(
            #         symbol=f"{crypto.ticker}USDT").order_by('-time').first().close
            #     total_usd += crypto.balance * price
            # total_usd += CryptoCurency.objects.get(ticker='USDT').balance

            # data = {
            #     'ticker': self.ticker,
            #     'balance': f'{Decimal(self.balance).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)}',
            #     'pnl': f'{Decimal(self.pnl).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)}',
            #     'usd_value': f'{usd_value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)}',
            #     'total_usd': f'{total_usd.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)}',
            #     'event': event,
            #     # Assuming timestamp fields
            #     'timestamp': self.updated if hasattr(self, 'updated_at') else self.timestamp,
            # }
            # group_name = 'balances_notifications'
            # message_type = 'balances_update'

            # channel_layer = get_channel_layer()

            # async_to_sync(channel_layer.group_send)(
            #     group_name,
            #     {
            #         'type': message_type,
            #         # 'data': json.dumps(data, default=str),
            #         'data': json.dumps(data, default=str),
            #     }
            # )

        else:
            # Fallback for other models
            content = content or f"{self.__class__.__name__} {obj_id} - Event {event}"
            data = {
                'content': content,
                'event': event,
                'timestamp': timezone.now(),
            }
            group_name = 'crypto_updates'
            message_type = 'balance_update'

            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': message_type,
                    'data': json.dumps(data, default=str),
                }
            )
