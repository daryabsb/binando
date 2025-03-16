import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.template.loader import render_to_string
from src.market.models import CryptoCurency, Kline


class CryptoConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add('crypto_updates', self.channel_name)
        # await self.channel_layer.group_add('trade_notifications', self.channel_name)
        # await self.channel_layer.group_add('trade_update', self.channel_name)
        await self.accept()
        await self.send_initial_data()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard('crypto_updates', self.channel_name)
        # await self.channel_layer.group_discard('trade_notifications', self.channel_name)

    async def balance_update(self, event):
        balances = await self.get_balances()
        html = await sync_to_async(render_to_string)('partials/balances.html', {'balances': balances})
        await self.send(text_data=html)

    async def trade_update(self, event):
        # e.g., "Test BUY 1000 TEST at 1.00 (Value: 1000.00) - timestamp"
        data = event['data']
        received_data = json.loads(data)

        balances = await self.get_balances()
        total = await self.get_total_usd()

        notification_html = await sync_to_async(render_to_string)('partials/notification.html',
                                                                {
                                                                    'notification': received_data,
                                                                    'balances': balances,
                                                                    'total': total,

                                                                }

                                                                )
        balances_html = await sync_to_async(render_to_string)('partials/balances.html', {'balances': balances})

        await self.send(text_data=balances_html)

        return data

    async def total_usd_update(self, event):
        total = await self.get_total_usd()
        await self.send(text_data=json.dumps({'data': f"{total:.2f}"}))

    @sync_to_async
    def get_balances(self):
        balances = []
        for crypto in CryptoCurency.objects.exclude(ticker='USDT'):
            latest_price = float(Kline.objects.filter(
                symbol=f"{crypto.ticker}USDT").order_by('-time').first().close)
            usd_value = float(crypto.balance) * latest_price
            balances.append({
                'ticker': crypto.ticker,
                'balance': float(crypto.balance),
                'usd_value': usd_value,
                'pnl': float(crypto.pnl),
            })
        usdt = CryptoCurency.objects.get(ticker='USDT')
        balances.append({
            'ticker': 'USDT',
            'balance': float(usdt.balance),
            'usd_value': float(usdt.balance),
            'pnl': float(usdt.pnl),
        })
        return balances

    @sync_to_async
    def get_total_usd(self):
        total = 0.0
        for crypto in CryptoCurency.objects.exclude(ticker='USDT'):
            latest_price = float(Kline.objects.filter(
                symbol=f"{crypto.ticker}USDT").order_by('-time').first().close)
            total += float(crypto.balance) * latest_price
        total += float(CryptoCurency.objects.get(ticker='USDT').balance)
        return total

    async def send_initial_data(self):
        data_dict = {
            "type": "notifications",
            "data": {
                "order_type": 'instance.order_type',
                "quantity": 'instance.quantity',
                "ticker": 'instance.ticker',
                "price": 'instance.price',
                "value": 'instance.value',
                "timestamp": 'instance.timestamp.isoformat()'
            }
        }
        data_json = json.dumps(data_dict)
        event = {'data': 'First notification'}
        balances = await self.get_balances()
        balances_html = await sync_to_async(render_to_string)('partials/balances.html', {'balances': balances})
        await self.send(text_data=balances_html)
        # notification = await self.trade_update(data_json)
        # notification_html = await sync_to_async(render_to_string)('partials/notification.html', {'notification': notification})
        # await self.send(text_data=notification_html)
        total = await self.get_total_usd()
        await self.send(text_data=json.dumps({'type': 'total_usd_update', 'data': f"{total:.2f}"}))

