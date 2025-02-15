from decimal import Decimal, ROUND_UP
from _utils.helpers import get_min_notional
from bot.coins import get_price


def place_order(client, symbol, side, quantity):
    """Place a market order (buy/sell) with balance validation and LOT_SIZE handling."""
    if not quantity or Decimal(quantity) <= 0:
        print(f"⚠️ Skipping {side} order for {symbol} (Invalid quantity: {quantity})")
        return

    # Get trading rules (LOT_SIZE)
    exchange_info = client.get_exchange_info()
    symbol_info = next((s for s in exchange_info["symbols"] if s["symbol"] == symbol), None)

    if not symbol_info:
        print(f"⚠️ No trading info for {symbol}. Skipping order.")
        return

    lot_size_filter = next((f for f in symbol_info["filters"] if f["filterType"] == "LOT_SIZE"), None)

    if lot_size_filter:
        min_qty = Decimal(lot_size_filter["minQty"])  # Minimum tradable quantity
        step_size = Decimal(lot_size_filter["stepSize"])  # Step size for rounding

        # Adjust quantity to be a valid multiple of step size
        adjusted_quantity = (Decimal(quantity) // step_size) * step_size

        if adjusted_quantity < min_qty:
            print(f"❌ {symbol} Order rejected (Adjusted quantity {adjusted_quantity} < minQty {min_qty}). Skipping.")
            return

        quantity = adjusted_quantity  # Update with valid quantity

    try:
        order = client.order_market(symbol=symbol, side=side, quantity=str(quantity))
        print(f"✅ {side.upper()} Order placed for {symbol}: {quantity}")
    except Exception as e:
        print(f"❌ Error placing {side} order for {symbol}: {str(e)}")
