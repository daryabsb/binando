from src.market.models import Symbol
import websockets
import asyncio

symbols = Symbol.objects.sorted_symbols()
base_url = "wss://stream.binance.com:9443/stream?streams="
# base_url = "wss://testnet.binance.vision/stream?streams="
timeout = False

def handle_data(message):
    print(message)


async def run_streams():
    global timeout

    # streams = [f"{cur.lower()}@depth20@1000ms" for cur in symbols]
    streams = [f"{cur.lower()}@depth20@kline_5m" for cur in symbols]
    url = base_url + "/".join(streams)

    # print(url)
    try:
        async with websockets.connect(url) as websocket:
            while True:
                try:
                    message = await websocket.recv()
                    handle_data(message)
                    if not timeout:
                        timeout = True
                        # asyncio.create_task(self.get_rates())
                except websockets.ConnectionClosed:
                    print(
                        "WebSocket connection closed, attempting to reconnect...")
                    break
                except Exception as e:
                    print(f"Error in websocket loop: {e}")
    except Exception as e:
        print(f"WebSocket connection failed: {e}")

def run():
    while True:
        asyncio.run(run_streams()) 
