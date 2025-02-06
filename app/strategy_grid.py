from binance.client import Client
import time

API_KEY = "your_api_key"
API_SECRET = "your_api_secret"
client = Client(API_KEY, API_SECRET)

SYMBOL = "BTCUSDT"
GRID_SIZE = 5  # Number of buy orders
BUY_PERCENT = 1 / 100  # Buy every 1% drop
SELL_PERCENT = 1.5 / 100  # Sell when price is 1.5% higher
STOP_LOSS = 5 / 100  # Stop-loss at 5% below lowest buy
TRADE_AMOUNT = 0.0005  # Small trade size


def get_current_price(symbol):
    return float(client.get_symbol_ticker(symbol=symbol)["price"])


def place_grid_orders():
    global last_buy_price
    start_price = get_current_price(SYMBOL)
    buy_prices = [start_price * (1 - BUY_PERCENT * i)
                  for i in range(1, GRID_SIZE + 1)]
    sell_prices = [bp * (1 + SELL_PERCENT) for bp in buy_prices]

    print(f"Placing Grid Orders:")
    print(f"Buy Prices: {buy_prices}")
    print(f"Sell Prices: {sell_prices}")

    return buy_prices, sell_prices


buy_prices, sell_prices = place_grid_orders()


def trade():
    while True:
        current_price = get_current_price(SYMBOL)
        print(f"Current Price: {current_price}")

        # Check for Buy Orders
        for i, buy_price in enumerate(buy_prices):
            if current_price <= buy_price:
                print(f"Buying at {buy_price}")
                # order = client.order_market_buy(symbol=SYMBOL, quantity=TRADE_AMOUNT)
                buy_prices[i] = None  # Mark as bought

        # Check for Sell Orders
        for i, sell_price in enumerate(sell_prices):
            if buy_prices[i] is None and current_price >= sell_price:
                print(f"Selling at {sell_price}")
                # order = client.order_market_sell(symbol=SYMBOL, quantity=TRADE_AMOUNT)
                buy_prices[i] = get_current_price(
                    SYMBOL)  # Reset new buy order

        # Stop-Loss Check
        if min([p for p in buy_prices if p]) * (1 - STOP_LOSS) > current_price:
            print("Stop-loss triggered! Exiting trade.")
            break

        time.sleep(5)  # Wait before checking again


trade()
