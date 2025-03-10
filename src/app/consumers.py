# your_app_name/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from src.market.models import CryptoCurency, Kline
from asgiref.sync import sync_to_async


class CryptoConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print(1)
        await self.channel_layer.group_add('crypto_updates', self.channel_name)
        print(2)
        await self.channel_layer.group_add('trade_notifications', self.channel_name)
        print(3)
        await self.accept()
        print(4)
        # Send initial data on connect
        await self.send_balances()
        print(5)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard('crypto_updates', self.channel_name)
        await self.channel_layer.group_discard('trade_notifications', self.channel_name)

    async def balance_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'balance_update',
            'data': event['data']
        }))

    async def trade_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'trade_update',
            'data': event['data']
        }))

    async def send_balances(self):
        balances, total_usd = await self.get_balances()  # Fetch data asynchronously

        await self.send(text_data=json.dumps({
            'type': 'initial_balances',
            'data': {
                'balances': balances,
                'total_usd': total_usd
            }
        }))

    @sync_to_async
    def get_balances(self):
        balances = []
        total_usd = 0.0

        cryptos = CryptoCurency.objects.exclude(ticker='USDT')
        for crypto in cryptos:
            latest_price = Kline.objects.filter(symbol=f"{crypto.ticker}USDT").order_by('-time').first()
            latest_price = float(latest_price.close) if latest_price else 0.0
            usd_value = float(crypto.balance) * latest_price
            total_usd += usd_value if crypto.ticker != 'USDT' else float(crypto.balance)

            balances.append({
                'ticker': crypto.ticker,
                'balance': str(crypto.balance),
                'usd_value': usd_value,
                'pnl': str(crypto.pnl),
            })

        try:
            usdt = CryptoCurency.objects.get(ticker='USDT')
            balances.append({
                'ticker': 'USDT',
                'balance': str(usdt.balance),
                'usd_value': float(usdt.balance),
                'pnl': str(usdt.pnl),
            })
            total_usd += float(usdt.balance)
        except CryptoCurency.DoesNotExist:
            pass  # Handle missing USDT gracefully

        return balances, total_usd
