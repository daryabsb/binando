# your_app_name/routing.py
from django.urls import re_path
from src.app.consumers import (
    NotificationConsumer, BalancesConsumer, CryptoConsumer,
    TotalsConsumer
    )

websocket_urlpatterns = [
    re_path(r'ws/crypto/', CryptoConsumer.as_asgi()),
    re_path(r'ws/notification/', NotificationConsumer.as_asgi()),
    re_path(r'ws/balances/', BalancesConsumer.as_asgi()),
    re_path(r'ws/total-usd/', TotalsConsumer.as_asgi()),
]
