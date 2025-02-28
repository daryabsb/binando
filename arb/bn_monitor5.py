import sqlite3
import time
from datetime import datetime
# from binance.client import Client
from client.client import get_client
import asyncio
import websockets
import json


client = get_client(testnet=False)


class PriceMonitor:
    def __init__(self, symbols):
        self.data = {}
        self.url = "wss://testnet.binance.vision/stream?streams=" + \
            "/".join([f"{symbol.lower()}@depth5" for symbol in symbols])
        print(f"Monitoring WebSocket URL: {self.url}")  # Debug

    async def fetch_prices(self):
        try:
            async with websockets.connect(self.url) as websocket:
                print("WebSocket connected")
                while True:
                    message = await websocket.recv()
                    self.handle_data(json.loads(message))
        except Exception as e:
            print(f"WebSocket error: {e}")

    def handle_data(self, message):
        try:
            market_id = message["stream"].split("@")[0].upper()
            asks = [(float(a[0]), float(a[1]))
                    for a in message["data"]["asks"] if len(a) > 1]
            if asks:
                ask = min(asks, key=lambda t: t[0])
                self.data[market_id] = ask[0]
                # print(f"Updated price for {market_id}: {ask[0]}")  # Debug (uncomment if needed)
        except Exception as e:
            print(f"Error handling WebSocket message: {e}")

    def get_price(self, symbol):
        return self.data.get(symbol, None)


def get_symbols():
    conn = sqlite3.connect('testnet_account5.db')
    c = conn.cursor()
    c.execute("SELECT symbol FROM my_account WHERE symbol != 'USDT'")
    symbols = [row[0] + "USDT" for row in c.fetchall()]  # Ensure USDT suffix
    conn.close()
    return symbols


def monitor_account():
    symbols = get_symbols()
    if not symbols:
        print("No assets other than USDT found yet.")
        symbols = []
    monitor = PriceMonitor(symbols)

    # Start WebSocket in a separate task
    loop = asyncio.get_event_loop()
    loop.create_task(monitor.fetch_prices())

    # Give WebSocket a moment to connect and fetch initial data
    time.sleep(5)  # Wait 5 seconds for initial prices

    while True:
        conn = sqlite3.connect('testnet_account5.db')
        c = conn.cursor()

        c.execute("SELECT symbol, balance FROM my_account")
        assets = c.fetchall()

        c.execute("SELECT account_pnl FROM account_pnl")
        total_pnl = c.fetchone()[0]

        usd_value = 0
        report_lines = ["=== Profit Report ==="]

        for symbol, balance in assets:
            if symbol == 'USDT':
                usd_value += balance
                report_lines.append(f"{symbol}: {balance:.8f}")
            else:
                price = monitor.get_price(symbol + "USDT")
                if price:
                    asset_value = balance * price
                    usd_value += asset_value
                    report_lines.append(
                        f"{symbol}: {balance:.8f} ({asset_value:.8f} USD)")
                else:
                    c.execute(
                        "SELECT pnl FROM my_account WHERE symbol = ?", (symbol,))
                    last_pnl = c.fetchone()[0]
                    usd_value += last_pnl
                    report_lines.append(
                        f"{symbol}: {balance:.8f} (Price unavailable, using last PNL: {last_pnl:.8f} USD)")

        profit_loss = usd_value - 150.0
        report_lines.extend([
            "",
            f"PNL: {usd_value:.8f} USD",
            f"Profit/Loss: {profit_loss:.8f} USDT",
            f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        ])

        report_lines.append("\n=== Recent Orders ===")
        c.execute(
            "SELECT symbol, side, amount, price, value, timestamp, pnl FROM order_history ORDER BY timestamp DESC LIMIT 20")
        orders = c.fetchall()
        for order in orders:
            symbol, side, amount, price, value, timestamp, pnl = order
            report_lines.append(
                f"{timestamp} | {side} {amount:.6f} {symbol} at {price:.6f} (Value: {value:.6f} USD, PNL: {pnl:.6f})")

        report_lines.append("====================")

        print("\033c", end="")
        print("\n".join(report_lines))

        conn.close()
        time.sleep(30)


if __name__ == "__main__":
    print("Starting account monitor...")
    monitor_account()
