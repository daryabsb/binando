import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.template.loader import render_to_string


class BalancesConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add('balances_notifications', self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard('balances_notifications', self.channel_name)

    async def balances_update(self, event):
        data = event['data']
        received_data = json.loads(data)  # Dict with 'content', etc.

        html = await sync_to_async(render_to_string)('partials/balance.html', {'balance': received_data})
        await self.send(text_data=html)
