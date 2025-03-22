import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.template.loader import render_to_string


class UsdtConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add('usdt_notifications', self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard('usdt_notifications', self.channel_name)

    async def usdt_update(self, event):
        data = event['data']
        received_data = json.loads(data)  # Dict with 'content', etc.

        html = await sync_to_async(render_to_string)('partials/usdt-row.html', {'usdt': received_data})
        await self.send(text_data=html)
