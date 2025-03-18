# trading/models.py
import json
import logging
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
# trading/models.py
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


class WorkflowInstance(models.Model):
    class Meta:
        abstract = True

    def to_payload(self):
        """Convert instance to a dict/JSON-ready payload."""
        data = {
            'model': self._meta.model_name,
            'id': self.pk,
        }
        # Add model-specific fields via subclass override or generic approach
        for field in self._meta.fields:
            if field.name not in ['id']:  # Exclude id, already added
                value = getattr(self, field.name)
                data[field.name] = value
        return data

    def get_content(self, event):
        """Generate a descriptive message for the event (override in subclasses if needed)."""
        return f"{self._meta.model_name} {self.pk} - Event {event}"


class WorkflowMixin:
    def notify(self, event, group_name, message_type, data=None, exception_id=None):
        """Base method to send a workflow event to WebSocket clients."""
        from src.market.models import Notification
        logger = logging.getLogger(__name__)
        content_type = ContentType.objects.get_for_model(self.__class__)

        # Use provided data or generate it
        payload = data or self.to_payload()
        content = self.get_content(event)

        # Create notification
        notification = Notification(
            content_type=content_type,
            object_id=self.pk,
            content=content,
            event=event,
            exception_id=exception_id,
        )
        notification.save()
        logger.info(f"Notification created: {notification}")

        # Send to WebSocket
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': message_type,
                # Convert datetime to string
                'data': json.dumps(payload, default=str),
            }
        )

        # total_usd = update_total_usd()

        # group_name = 'total_usd_update'
        # message_type = 'total_usd'

        # channel_layer = get_channel_layer()
        # print(f'updated updated 1')
        # async_to_sync(channel_layer.group_send)(
        #     'total_usd_update',
        #     {
        #         'type': 'total_usd',
        #         'data': str(total_usd),  # Convert datetime to string
        #     }
        # )

        notification.is_sent = True
        notification.save()

    def update(self, group_name, message_type, data=None, exception_id=None):
        payload = data or self.to_payload()
        # content = self.get_content(event)

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': message_type,
                # Convert datetime to string
                'data': json.dumps(payload, default=str),
            }
        )

    def create_data(self):
        """Default method to prepare data for creation events (e.g., adding rows)."""
        return self.to_payload()

    def update_data(self):
        """Default method for update events (e.g., updating totals, charts)."""
        return self.to_payload()

    def send_event(self):
        """Template method for models to override."""
        raise NotImplementedError("Subclasses must implement send_event()")
