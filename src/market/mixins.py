
import json
from decimal import Decimal, ROUND_HALF_UP
from django.forms import model_to_dict


# trading/models.py


class WorkflowMixin:
    def notify(self, event, content=None, exception_id=None):
        from django.contrib.contenttypes.models import ContentType
        from src.market.models import Notification
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        import logging

        logger = logging.getLogger(__name__)
        content_type = ContentType.objects.get_for_model(self.__class__)
        obj_id = self.pk
        order_data = {}
        crypto_data = {}

        # Generate descriptive content
        channel_layer = get_channel_layer()

        if content is None:
            if content_type.model == 'order':
                action = 'bought' if self.order_type == 'BUY' else 'sold'
                amount = 'USD' if self.ticker != 'USDT' else self.ticker
                content = f"You {action} {self.quantity} {self.ticker} for {self.value} {amount} at {self.price} per unit on {self.timestamp}"

                order_data = {
                    'quantity': f'{self.quantity.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)}',
                    'price': f'{self.price.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)}',
                    'value': f'{self.value.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)}',

                }

            elif content_type.model == 'cryptocurency':
                # group_name = 'crypto_updates'
                # message_type = 'balance_update'

                if event == Notification.WorkflowEvents.CREATED:
                    content = f"New currency {self.ticker} added with balance {self.balance}"
                elif event == Notification.WorkflowEvents.UPDATED:
                    content = f"Balance of {self.ticker} updated to {self.balance}, PNL now {self.pnl}"
                elif event == Notification.WorkflowEvents.DELETED:
                    content = f"Currency {self.ticker} removed"
                else:
                    content = f"{self.ticker} event {event} occurred"
                crypto_data = {
                    'name': self.name,
                    'ticker': self.ticker,
                    'balance': self.balance,
                    'pnl': self.pnl

                }
            else:
                content = f"{self.__class__.__name__} {obj_id} - Event {event}"

        notification = Notification(
            content_type=content_type,
            object_id=obj_id,
            content=content,
            event=event,
            exception_id=exception_id,
        )
        notification.save()
        logger.info(f"Notification created: {notification}")

        data = {
            **crypto_data,
            'id': notification.id,
            'ticker': f'{self.ticker}',
            'content': notification.content,
            'event': notification.event,
            'timestamp': notification.commit_time,  # Keep as datetime object
        }
        # if event == Notification.WorkflowEvents.TRADE_EXECUTED and hasattr(self, 'to_dict'):
        #     trade_data = self.to_dict()
        #     trade_data['timestamp'] = self.timestamp  # Keep as datetime
        #     data = trade_data

        order_group_name = 'trade_notifications'
        order_message_type = 'trade_update'
        crypto_group_name = 'balances_notifications'
        crypto_message_type = 'balances_update'

        async_to_sync(channel_layer.group_send)(
            crypto_group_name,
            {
                'type': crypto_message_type,
                # Convert datetime to string only when sending
                'data': json.dumps(
                    {
                        **crypto_data,
                        'id': notification.id,
                        'ticker': f'{self.ticker}',
                        'content': notification.content,
                        'event': notification.event,
                        'timestamp': notification.commit_time,
                    }, default=str),
            }
        )
        async_to_sync(channel_layer.group_send)(
            order_group_name,
            {
                'type': order_message_type,
                # Convert datetime to string only when sending
                'data': json.dumps(
                    {
                        **order_data,
                        'id': notification.id,
                        'ticker': f'{self.ticker}',
                        'content': notification.content,
                        'event': notification.event,
                        'timestamp': notification.commit_time,
                    }, default=str),
            }
        )

        notification.is_sent = True
        notification.save()


data = {
    "order_type": "BUY",
    "quantity": "3.59023456",
    "name": "DOT", "ticker": "DOT",
    "price": "4.178", "value": "14.99999999168",
    "timestamp": "2025-03-14T11:10:30.161921+00:00"
}
received_data = {
    'order_type': 'BUY',
    'quantity': '3.59023456',
    'name': 'DOT',
    'ticker': 'DOT',
    'price': '4.178',
    'value': '14.99999999168',
    'timestamp': '2025-03-14T11:10:30.161921+00:00'
}
data = {"order_type": "BUY", "quantity": "3.59023456", "name": "DOT", "ticker": "DOT",
        "price": "4.178", "value": "14.99999999168", "timestamp": "2025-03-14T11:10:30.161921+00:00"}
received_data = {'order_type': 'BUY', 'quantity': '3.59023456', 'name': 'DOT', 'ticker': 'DOT',
                 'price': '4.178', 'value': '14.99999999168', 'timestamp': '2025-03-14T11:10:30.161921+00:00'}
