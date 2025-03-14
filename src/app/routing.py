# your_app_name/routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/crypto/', consumers.CryptoConsumer.as_asgi()),
    re_path(r'ws/notification/', consumers.NotificationConsumer.as_asgi()),
    re_path(r'ws/balances/', consumers.BalancesConsumer.as_asgi()),
]
