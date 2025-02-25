import sqlite3
import time
from datetime import datetime
from client.client import get_client
import asyncio
import websockets
import json

# Initialize Binance client
client = get_client(testnet=False)

# WebSocket to fetch real-time prices
class PriceMonitor:
    def __init__(self, symbols):
        self.data = {}
        self.url = "wss://testnet.binance.vision/stream?streams=" + "/".join([f"{symbol.lower()}usdt@depth5" for symbol in symbols])

    async def fetch_prices(self):
        try:
            async with websockets.connect(self.url) as websocket:
                while True:
                    message = await websocket.recv()
                    self.handle_data(json.loads(message))
        except Exception as e:
            print(f"WebSocket error: {e}")

    def handle_data(self, message):
        market_id = message["stream"].split("@")[0].upper()
        asks = [(float(a[0]), float(a[1])) for a in message["data"]["asks"] if len(a) > 1]
        if asks:
            ask = min(asks, key=lambda t: t[0])
            self.data[market_id] = ask[0]  # Store just the price

    def get_price(self, symbol):
        return self.data.get(symbol + "USDT", None)

# Fetch symbols from my_account to monitor
def get_symbols():
    conn = sqlite3.connect('testnet_account.db')
    c = conn.cursor()
    c.execute("SELECT symbol FROM my_account WHERE symbol != 'USDT'")
    symbols = [row[0] for row in c.fetchall()]
    conn.close()
    return symbols

# Monitor function
def monitor_account():
    symbols = get_symbols()
    if not symbols:
        print("No assets other than USDT found yet.")
        symbols = []  # Default to empty if no other assets
    monitor = PriceMonitor(symbols)
    
    # Start WebSocket in a separate task
    loop = asyncio.get_event_loop()
    loop.create_task(monitor.fetch_prices())

    while True:
        conn = sqlite3.connect('testnet_account.db')
        c = conn.cursor()

        # Fetch all assets
        c.execute("SELECT symbol, balance FROM my_account")
        assets = c.fetchall()

        # Fetch total PNL
        c.execute("SELECT account_pnl FROM account_pnl")
        total_pnl = c.fetchone()[0]

        # Calculate real-time PNL
        usd_value = 0
        report_lines = ["",f"=== Profit Report ==="]
        
        for symbol, balance in assets:
            if symbol == 'USDT':
                usd_value += balance
                report_lines.append(f"{symbol}: {balance:.8f}")
            else:
                price = monitor.get_price(symbol)
                if price:
                    asset_value = balance * price
                    usd_value += asset_value
                    report_lines.append(f"{symbol}: {balance:.8f} ({asset_value:.8f} USD)")
                else:
                    # If price not available, use last PNL from db
                    c.execute("SELECT pnl FROM my_account WHERE symbol = ?", (symbol,))
                    last_pnl = c.fetchone()[0]
                    usd_value += last_pnl
                    report_lines.append(f"{symbol}: {balance:.8f} (Price unavailable, using last PNL: {last_pnl:.8f} USD)")

        # Profit/Loss calculation (total PNL - initial 150 USDT)
        profit_loss = usd_value - 150.0

        report_lines.extend([
            "",
            f"PNL: {usd_value:.8f} USD",
            f"Profit/Loss: {profit_loss:.8f} USDT",
            f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "===================="
        ])

        # Clear terminal and print report
        print("\033c", end="")  # Clear terminal (works on Unix-like systems)
        print("\n".join(report_lines))

        conn.close()
        time.sleep(300)  # 5 minutes

# Run the monitor
if __name__ == "__main__":
    print("Starting account monitor...")
    monitor_account()