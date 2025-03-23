import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.template.loader import render_to_string


class TotalsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add('total_usd_update', self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard('total_usd_update', self.channel_name)
    
    async def total_usd(self, event):
        data = json.loads(event['data'])
        # print(f'Event data: {event["data"]}')
        html = await sync_to_async(render_to_string)('partials/total-usd.html', {'total_usd':data})

        await self.send(text_data=str(html))
        # await self.send(text_data=str(data))
        # await self.channel_layer.group_send(
        #     self.room_group_name, {"type": "total_usd", "total_usd": data}
        # )