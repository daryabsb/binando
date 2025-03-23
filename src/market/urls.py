from django.urls import path
from django.shortcuts import render
from django.http import HttpResponse
from src.market.utils import send_websocket_message
from src.market import views


def index2(request):
    return render(request, 'index2.html')


def test_websocket2(request):
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
    path('', views.index, name='index'),
    path('test-websocket/', views.test_websocket, name='test_websocket'),
    path('balances/', views.balances, name='balances'),
    path('cryptos/', views.cryptos, name='cryptos'),
    path('usdt-update/', views.update_usdt, name='usdt-update'),
    path('balances-data/', views.balances_data, name='balances-data'),
    path('total-usd/', views.total_usd, name='total_usd'),
    path('notifications/', views.notifications, name='notifications'),
]
