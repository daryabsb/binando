from decimal import Decimal, ROUND_UP
from _utils.helpers import get_min_notional
from bot.coins import get_price


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
