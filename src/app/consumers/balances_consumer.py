import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async, async_to_sync
from django.template.loader import render_to_string



class BalancesConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("balances_notifications", self.channel_name)
        await self.channel_layer.group_add("receive_balances", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("balances_notifications", self.channel_name)
        await self.channel_layer.group_discard("receive_balances", self.channel_name)

    async def receive(self, text_data):
        """Handle incoming messages from WebSocket clients"""
        text_data_json = json.loads(text_data)
        message = text_data_json.get("message", "")

        # Broadcast the message to the group
        await self.channel_layer.group_send(
            "receive_balances", {"type": "receive_message", "message": message}
        )

    async def receive_message(self, event):
        """Handles messages sent to the 'receive_balances' group"""
        message = event["message"]

        # Send the message back to the WebSocket client
        await self.send(text_data=json.dumps({"message": message}))

    async def balances_update(self, event):
        data = event['data']
        received_data = json.loads(data)  # Dict with 'content', etc.

        html = await sync_to_async(render_to_string)("partials/balance.html", {"balance": received_data})
        await self.send(text_data=html)

    async def cryptos_update(self, event):
        data = event['data']
        received_data = json.loads(data)
        print('received_list = ', received_data)
        
        html = await sync_to_async(render_to_string)("partials/render-cryptos.html", {"cryptos": received_data})
        await self.send(text_data=html)