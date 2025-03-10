# trading/utils.py
from src.market.utils import send_websocket_message

def run():
    # Test balance update
    send_websocket_message(
        'crypto_updates',
        'balance_update',
        {'ticker': 'PEPE', 'balance': '1000000.0', 'pnl': '0.25', 'updated': '2025-03-10T12:00:00Z'}
    )

    # Test trade notification
    # send_websocket_message(
    #     'trade_notifications',
    #     'trade_update',
    #     {'ticker': 'PEPE', 'order_type': 'SELL', 'quantity': '500000.0', 'price': '0.0000065', 'value': '3.25', 'timestamp': '2025-03-10T12:01:00Z'}
    # )