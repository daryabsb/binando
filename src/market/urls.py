from django.urls import path
from django.shortcuts import render
from django.http import HttpResponse
from src.market.utils import send_websocket_message


def index(request):
    return render(request, 'index.html')


def test_websocket(request):
    # Example: Send a balance update
    send_websocket_message(
        group_name='crypto_updates',
        message_type='balance_update',
        data={
            'ticker': 'TURBO',
            'balance': '5268.8467',
            'pnl': '0.50',
            'updated': '2025-03-10T12:00:00Z'
        }
    )

    # Example: Send a trade notification
    send_websocket_message(
        group_name='trade_notifications',
        message_type='trade_update',
        data={
            'ticker': 'TURBO',
            'order_type': 'BUY',
            'quantity': '5268.8467',
            'price': '0.001138',
            'value': '6.00',
            'timestamp': '2025-03-10T12:00:00Z'
        }
    )
    return HttpResponse("Test messages sent to WebSocket.")


urlpatterns = [
    path('', index, name='index'),
    path('test-websocket/', test_websocket, name='test_websocket'),
]
