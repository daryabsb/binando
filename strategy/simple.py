from decimal import Decimal
from _utils.client import get_client
import time
from binance.enums import *

from _utils.coins import (
    get_balance, get_usdt_balance, get_coin_balance, get_percentage_options, get_history_options,
    get_step_size_and_min_qty, get_previous_hour_price, calculate_quantity,
    get_price,
)
from _utils.const import (
    meme_coins, TRADE_ALLOCATION_PERCENTAGE, MAX_TRADE_PERCENTAGE,
    PRICE_CHANGE_THRESHOLD, MINIMUM_TRADE_AMOUNT, LAST_TRADE,
    SIDE_BUY, SIDE_SELL, INTERVAL_PRIZE
)

from _utils.trade import should_trade


def place_order(client, symbol, side, quantity):
    """Place a market order (buy/sell) with balance validation."""
    if not quantity:
        return  # Skip order if quantity is None

    balance = client.get_asset_balance(asset=symbol.replace("USDT", ""))
    available_balance = Decimal(balance["free"])

    if side == SIDE_SELL and available_balance < Decimal(quantity):
        print(
            f"❌ Insufficient balance for {symbol} ({available_balance} < {quantity}).")
        return

    try:
        order = client.order_market(
            symbol=symbol, side=side, quantity=quantity)
        print(f"✅ {side.upper()} Order placed for {symbol}: {quantity}")
    except Exception as e:
        print(f"❌ Error placing {side} order for {symbol}: {str(e)}")


from decimal import Decimal

def execute_strategy():
    """Monitor and execute the trading strategy while preventing duplicate trades."""
    print("⏳ Trading bot started...")
    client = get_client()

    usdt_balance = get_usdt_balance(client)

    # Ensure a fixed trade amount of 20 USDT (if balance allows)
    trade_amount = min(5, usdt_balance)

    print(f"🔹 Adjusted trade amount: {trade_amount} USDT")

    if trade_amount < MINIMUM_TRADE_AMOUNT:
        print("⚠️ Not enough USDT allocated for trading.")
        return

    for symbol in meme_coins:
        coin_balance = get_coin_balance(client, symbol)  # Fix missing coins issue
        current_price = get_price(client, symbol)
        previous_price = get_previous_hour_price(client, symbol, INTERVAL_PRIZE)

        price_change = (current_price - previous_price) / previous_price

        if should_trade(client, symbol, current_price, "BUY", PRICE_CHANGE_THRESHOLD):
            if trade_amount > 1:
                print(f"📉 {symbol} is DOWN {price_change:.2%}. Buying...")

                # Use trade_amount for BUY orders (ignoring balance)
                quantity = calculate_quantity(client, symbol, trade_amount, "BUY")

                if quantity:
                    print(f"✅ Buying {symbol} at {current_price}... Quantity: {quantity}")
                    place_order(client, symbol, SIDE_BUY, quantity)

        elif should_trade(client, symbol, current_price, "SELL", PRICE_CHANGE_THRESHOLD):
            if coin_balance is None or coin_balance == Decimal("0.0"):
                print(f"❌ No {symbol} balance to sell. Skipping.")
                continue

            print(f"📈 {symbol} is UP {price_change:.2%}. Selling...")

            # Use available balance for SELL orders
            quantity = calculate_quantity(client, symbol, trade_amount, "SELL")

            if quantity and Decimal(quantity) <= coin_balance:
                print(f"✅ Selling {symbol} at {current_price}... Quantity: {quantity}")
                place_order(client, symbol, SIDE_SELL, quantity)
            else:
                print(f"⚠️ Not enough {symbol} balance to sell. Skipping.")
        else:
            print(f"🔍 {symbol}: No trade (change: {price_change:.2%})")

# Run the strategy every hour
while True:
    execute_strategy()
    print("⏳ Waiting 1 hour before checking again...")
    time.sleep(60)
