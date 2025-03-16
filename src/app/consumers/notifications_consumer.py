import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.template.loader import render_to_string

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add('trade_notifications', self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard('trade_notifications', self.channel_name)

    async def trade_update(self, event):
        data = event['data']
        received_data = json.loads(data)  # Dict with 'content', etc.

        html = await sync_to_async(render_to_string)('partials/notification.html', {'notification': received_data})
        await self.send(text_data=html)