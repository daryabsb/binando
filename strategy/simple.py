import time
from client import get_client
from binance.enums import *
from bot.market import is_market_stable


from bot.coins import get_sorted_symbols, get_usdt_balance, calculate_quantity

from bot.trade import should_sell, should_buy
from bot.order import place_order


def execute_strategy():
    """Enhanced trading strategy with risk management & fine-tuned filtering."""
    print("⏳ Trading bot started...")

    client = get_client()

    # ✅ Check if market is stable
    if not is_market_stable(client):
        print("⚠️ Market is too unstable! Skipping trades...")
        return

    # ✅ Check USDT balance
    usdt_balance = get_usdt_balance(client)

    # ✅ Get the best coins to trade
    sorted_coins = get_sorted_symbols(client)

    for coin in sorted_coins:
        symbol = coin["symbol"]
        price = coin["price"]
        roc = coin["roc"]

        if should_buy(client, symbol, price):
            quantity = calculate_quantity(client, symbol, usdt_balance, "BUY")
            if quantity:
                print(
                    f"✅ Buying {symbol} | ROC: {roc:.2%} | Price: {price} | Trend: 🔥 Strong Uptrend")
                # place_order(client, symbol, SIDE_BUY, quantity)

        elif should_sell(client, symbol, price):
            if usdt_balance < 5:
                print("⚠️ Not enough USDT to trade. Skipping...")
                return

            quantity = calculate_quantity(client, symbol, usdt_balance, "SELL")
            if quantity:
                print(
                    f"✅ Selling {symbol} | ROC: {roc:.2%} | Price: {price} | Trend: 🔻 Strong Downtrend")
                # place_order(client, symbol, SIDE_SELL, quantity)


# Run the strategy every hour
while True:
    execute_strategy()
    print("⏳ Waiting 1 hour before checking again...")
    time.sleep(3)
