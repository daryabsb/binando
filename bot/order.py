from decimal import Decimal, ROUND_UP
from _utils.helpers import get_min_notional
from bot.coins import get_price


def place_order(client, symbol, side, quantity):
    """Place a market order (buy/sell) with balance validation, LOT_SIZE, and MIN_NOTIONAL handling."""
    from _utils.helpers import get_min_notional
    if not quantity or Decimal(quantity) <= 0:
        print(
            f"⚠️ Skipping {side} order for {symbol} (Invalid quantity: {quantity})")
        return

    # Fetch Binance trading rules
    exchange_info = client.get_exchange_info()
    symbol_info = next(
        (s for s in exchange_info["symbols"] if s["symbol"] == symbol), None)

    if not symbol_info:
        print(f"⚠️ No trading info for {symbol}. Skipping order.")
        return

    lot_size_filter = next(
        (f for f in symbol_info["filters"] if f["filterType"] == "LOT_SIZE"), None)
    notional_filter = next(
        (f for f in symbol_info["filters"] if f["filterType"] == "MIN_NOTIONAL"), None)

    price = Decimal(get_price(client, symbol))  # Get latest market price
    total_value = Decimal(quantity) * price  # Calculate trade value
    print(f'price: {price} | total_value: {total_value}')
    # ✅ Ensure quantity meets LOT_SIZE requirements
    if lot_size_filter:
        min_qty = Decimal(lot_size_filter["minQty"])
        step_size = Decimal(lot_size_filter["stepSize"])

        # Adjust quantity to a valid multiple of step_size
        adjusted_quantity = (Decimal(quantity) // step_size) * step_size

        if adjusted_quantity < min_qty:
            print(
                f"❌ {symbol} Order rejected (Adjusted quantity {adjusted_quantity} < minQty {min_qty}). Skipping.")
            return

        quantity = adjusted_quantity  # Update with valid quantity

    # ✅ Ensure total value meets minNotional
    # if notional_filter:
    min_notional = Decimal(get_min_notional(client, symbol))

    if total_value < min_notional:
        print(
            f"❌ {symbol} Order rejected (Total value {total_value} < minNotional {min_notional}). Adjusting quantity...")

        # Calculate the minimum required quantity
        adjusted_quantity = (
            min_notional / price).quantize(step_size, rounding=ROUND_UP)

        # Recheck adjusted quantity
        adjusted_total_value = adjusted_quantity * price

        print(
            f"🔹 Adjusted Quantity: {adjusted_quantity} | Adjusted Total Value: {adjusted_total_value}")

        if adjusted_quantity < min_qty:
            print(
                f"❌ Adjusted quantity ({adjusted_quantity}) is below minQty ({min_qty}). Skipping order.")
            return

        quantity = adjusted_quantity  # Update quantity

    print(
        f"✅ Final Order Details: {side.upper()} {symbol} | Quantity: {quantity} | Price: {price} | Total: {quantity * price}")

    # 🔹 Try executing the order
    try:
        order = client.order_market(
            symbol=symbol, side=side, quantity=str(quantity))
        print(f"✅ {side.upper()} Order placed for {symbol}: {quantity}")
    except Exception as e:
        print(f"❌ Error placing {side} order for {symbol}: {str(e)}")
