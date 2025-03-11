# your_app_name/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from src.market.models import CryptoCurency, Kline
from asgiref.sync import sync_to_async
from django.template.loader import render_to_string


class CryptoConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add('crypto_updates', self.channel_name)
        await self.channel_layer.group_add('trade_notifications', self.channel_name)
        await self.accept()
        await self.send_initial_data()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard('crypto_updates', self.channel_name)
        await self.channel_layer.group_discard('trade_notifications', self.channel_name)

    async def balance_update(self, event):
        balances = await self.get_balances()
        html = await sync_to_async(render_to_string)('partials/balances.html', {'balances': balances})
        await self.send(text_data=html)

    async def trade_update(self, event):
        data = event['data']
        html = f"<li class='notification'>{data}</li>"
        await self.send(text_data=json.dumps({'data': html}))

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
        # Initial balances
        balances = await self.get_balances()
        balances_html = await sync_to_async(render_to_string)('partials/balances.html', {'balances': balances})
        await self.send(text_data=balances_html)
        # Initial total USD
        total = await self.get_total_usd()
        await self.send(text_data=json.dumps({'type': 'total_usd_update', 'data': f"{total:.2f}"}))


class CryptoConsumer2(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add('crypto_updates', self.channel_name)
        await self.channel_layer.group_add('trade_notifications', self.channel_name)
        await self.accept()
        # Send initial data on connect
        await self.send_balances()

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
            latest_price = Kline.objects.filter(
                symbol=f"{crypto.ticker}USDT").order_by('-time').first()
            latest_price = float(latest_price.close) if latest_price else 0.0
            usd_value = float(crypto.balance) * latest_price
            total_usd += usd_value if crypto.ticker != 'USDT' else float(
                crypto.balance)

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
