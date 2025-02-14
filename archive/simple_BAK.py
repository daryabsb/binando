from decimal import Decimal, ROUND_UP
from _utils.client_BAK import get_client
import time
from binance.enums import *

from bot.coins import (
    get_balance, get_usdt_balance, get_coin_balance, get_percentage_options, get_history_options,
    get_step_size_and_min_qty, get_previous_hour_price, calculate_quantity,
    get_price, get_min_notional
)
from _utils.const import (
    meme_coins, TRADE_ALLOCATION_PERCENTAGE, MAX_TRADE_PERCENTAGE,
    PRICE_CHANGE_THRESHOLD, MINIMUM_TRADE_AMOUNT, LAST_TRADE,
    SIDE_BUY, SIDE_SELL, INTERVAL_PRIZE
)

from bot.trade import should_sell, should_buy


def place_order(client, symbol, side, quantity):
    """Place a market order (buy/sell) with balance validation."""

    if not quantity or Decimal(quantity) <= 0:
        print(
            f"⚠️ Skipping {side} order for {symbol} (Invalid quantity: {quantity})")
        return

    base_asset = symbol.replace("USDT", "").rstrip(
        "0123456789")  # Handle non-standard symbols
    balance = client.get_asset_balance(asset=base_asset)

    if not balance:
        print(f"⚠️ No balance info for {symbol}. Skipping order.")
        return

    available_balance = Decimal(balance["free"])

    # Ensure sufficient balance for SELL orders
    if side == "SELL" and available_balance < Decimal(quantity):
        print(
            f"❌ Insufficient balance for {symbol} ({available_balance} < {quantity}). Skipping.")
        return

    # Fetch minNotional for final check
    min_notional = get_min_notional(client, symbol)
    price = Decimal(get_price(client, symbol))  # Get latest price
    total_value = Decimal(quantity) * price  # Final notional check

    if total_value < min_notional:
        print(
            f"❌ {symbol} Order rejected ({total_value} < {min_notional}). Adjusting quantity...")
        adjusted_quantity = (
            min_notional / price).quantize(Decimal('1e-8'), rounding=ROUND_UP)

        # If adjusted quantity is too large, skip
        if adjusted_quantity > available_balance:
            print(
                f"❌ Adjusted quantity ({adjusted_quantity}) exceeds balance ({available_balance}). Skipping order.")
            return

        quantity = adjusted_quantity  # Update quantity

    # Execute order
    try:
        order = client.order_market(
            symbol=symbol, side=side, quantity=str(quantity))
        print(f"✅ {side.upper()} Order placed for {symbol}: {quantity} at {price}")
    except Exception as e:
        print(f"❌ Error placing {side} order for {symbol}: {str(e)}")


def execute_strategy():
    """Monitor and execute the trading strategy."""
    print("⏳ Trading bot started...")
    client = get_client()
    usdt_balance = get_usdt_balance(client)
    # Fixed trade amount of 10 USDT (if available)
    trade_amount = min(10, usdt_balance)

    print(f"🔹 Adjusted trade amount: {trade_amount} USDT")

    for symbol in meme_coins:
        if should_buy(client, symbol):
            quantity = calculate_quantity(client, symbol, trade_amount, "BUY")
            if quantity:
                print(f"✅ Buying {symbol} | Quantity: {quantity}")

        elif should_sell(client, symbol):
            coin_balance = get_coin_balance(client, symbol)
            if coin_balance and coin_balance > Decimal("0.0"):
                quantity = calculate_quantity(
                    client, symbol, trade_amount, "SELL")
                if quantity and Decimal(quantity) <= coin_balance:
                    print(f"✅ Selling {symbol} | Quantity: {quantity}")


# Run the strategy every hour
while True:
    execute_strategy()
    print("⏳ Waiting 1 hour before checking again...")
    time.sleep(3)
