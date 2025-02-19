import time
from client.client import get_client
from client.symbol import Symbol
from client.trade import Trade
from binance.enums import *
from bot.market import is_market_stable, execute_trade
from server import start_background_cache_update


from bot.coins import get_sorted_symbols, get_usdt_balance, calculate_quantity

from bot.trade import should_sell, should_buy
from bot.order import place_order


def execute_strategy():
    """Enhanced trading strategy with risk management & fine-tuned filtering."""
    from _utils.cache import load_cached_sorted_symbols

    print("⏳ Trading bot started...")

    client = get_client(testnet=True)

    # ✅ Check if market is stable
    if not is_market_stable(client):
        print("⚠️ Market is too unstable! Skipping trades...")
        return

    # ✅ Check USDT balance

    # ✅ Get the best coins to trade
    sorted_coins = load_cached_sorted_symbols()
    # sorted_coins = get_sorted_symbols(client)
    if not sorted_coins:
        print("⚠️ No coins found. Skipping trades...")
        return

    for sym in sorted_coins:
        coin: Symbol = Symbol(client, sym)

        # if False:

        usdt_balance = coin.get_balance("USDT")

        symbol = coin.symbol["symbol"]
        price = coin.symbol['price']
        roc = coin.symbol['roc']

        print(f"🔹 {symbol} | ROC: {roc:.2%} | Price: {price}")

        
        if should_buy(client, symbol):
            quantity = coin.calculate_quantity(usdt_balance, "BUY")
            if usdt_balance < 5:
                print("⚠️ Not enough USDT to trade. Skipping...")
                return

            if quantity:
                
                print(
                    f"✅ Buying {symbol} | ROC: {roc:.2%} | Price: {price} | Trend: 🔥 Strong Uptrend")
                execute_trade(client, symbol, SIDE_BUY, quantity, price)
                # place_order(client, symbol, SIDE_BUY, quantity)

        elif should_sell(client, symbol):

            quantity = coin.calculate_quantity(usdt_balance, "SELL")
            if quantity:
                
                print(
                    f"✅ Selling {symbol} | ROC: {roc:.2%} | Price: {price} | Trend: 🔻 Strong Downtrend")
                execute_trade(client, symbol, SIDE_SELL, quantity, price)
                # place_order(client, symbol, SIDE_SELL, quantity)


start_background_cache_update(get_client(testnet=True))
# Run the strategy every hour
while True:
    execute_strategy()
    print("⏳ Waiting 1 hour before checking again...")
    time.sleep(10)
