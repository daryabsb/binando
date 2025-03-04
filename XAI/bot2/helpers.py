from decimal import Decimal, ROUND_DOWN
import time
from client.client import Client, get_client

def get_price(client: Client, symbol: str):
    """Get the current price of the symbol."""
    ticker = client.get_symbol_ticker(symbol=symbol)
    return Decimal(ticker['price'])

def get_coin_balance(client: Client, symbol: str):
    """Get the available balance of the coin (for SELL)."""
    base_asset = symbol.replace('USDT', '')
    account_info = client.get_account()
    for balance in account_info['balances']:
        if balance['asset'] == base_asset:
            return Decimal(balance['free'])
    return Decimal('0')

def get_symbol_filters(client: Client, symbol: str):
    """
    Fetch LOT_SIZE and MIN_NOTIONAL filters.
    If filters are missing (common on testnet), use default fallback values.
    Adjust these defaults to suit your requirements.
    """
    try:
        exchange_info = client.get_exchange_info()
        symbol_info = next((s for s in exchange_info['symbols'] if s['symbol'] == symbol), None)
        if not symbol_info:
            print(f"⚠️ {symbol} not found in exchange info. Using default filters.")
            return {
                'stepSize': Decimal('0.0001'),
                'minQty': Decimal('0.0001'),
                'minNotional': Decimal('5')
            }
        lot_size = next((f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE'), None)
        min_notional = next((f for f in symbol_info['filters'] if f['filterType'] == 'MIN_NOTIONAL'), None)
        if not lot_size or not min_notional:
            print(f"⚠️ Missing filters for {symbol}. Using default filters.")
            return {
                'stepSize': Decimal('0.0001'),
                'minQty': Decimal('0.0001'),
                'minNotional': Decimal('5')
            }
        return {
            'stepSize': Decimal(lot_size['stepSize']),
            'minQty': Decimal(lot_size['minQty']),
            'minNotional': Decimal(min_notional['minNotional'])
        }
    except Exception as e:
        print(f"❌ Error fetching filters for {symbol}: {e}. Using default filters.")
        return {
            'stepSize': Decimal('0.0001'),
            'minQty': Decimal('0.0001'),
            'minNotional': Decimal('5')
        }

def calculate_quantity(client: Client, symbol: str, usdt_balance: Decimal, side: str):
    """Calculate the quantity for a BUY or SELL order."""
    filters = get_symbol_filters(client, symbol)
    if filters is None:
        raise ValueError(f"Missing filters for {symbol}.")

    step_size = filters['stepSize']
    min_qty = filters['minQty']
    min_notional = filters['minNotional']
    price = get_price(client, symbol)

    if side == 'BUY':
        # Start with 5 USDT, but ensure it meets minNotional
        trade_usdt = max(Decimal('5'), min_notional)
        # Adjust if usdt_balance is less than trade_usdt
        trade_usdt = min(trade_usdt, usdt_balance)
        # Calculate raw quantity
        raw_quantity = trade_usdt / price
        # Quantize to step_size using floor division
        quantity = (raw_quantity // step_size) * step_size
        # Ensure quantity meets min_qty
        if quantity < min_qty:
            quantity = min_qty
        # Ensure notional meets min_notional
        notional = quantity * price
        while notional < min_notional:
            quantity += step_size
            notional = quantity * price
        # Final check against usdt_balance
        if notional > usdt_balance:
            raise ValueError(f"Insufficient USDT balance for {symbol}.")

    elif side == 'SELL':
        # Get available coin balance
        available_balance = get_coin_balance(client, symbol)
        if available_balance <= 0:
            raise ValueError(f"No {symbol} balance to sell.")
        # Calculate quantity to sell (e.g., sell all)
        raw_quantity = available_balance
        # Quantize to step_size using floor division
        quantity = (raw_quantity // step_size) * step_size
        # Ensure quantity meets min_qty
        if quantity < min_qty:
            raise ValueError(f"Available quantity below min_qty for {symbol}.")
        # Ensure notional meets min_notional
        notional = quantity * price
        if notional < min_notional:
            raise ValueError(f"Notional value too low for {symbol}.")

    else:
        raise ValueError("Invalid side. Use 'BUY' or 'SELL'.")

    return quantity

def execute_trade(client: Client, symbol: str, side: str, quantity: Decimal, price: Decimal):
    """Execute the trade by placing an order."""
    print(f"🔹 Placing {side} order for {symbol} | Quantity: {quantity} | Price: {price}")
    place_order(client, symbol, side, quantity)

def place_order(client: Client, symbol: str, side: str, quantity: Decimal):
    """Place a market order on Binance."""
    try:
        order = client.order_market(
            symbol=symbol,
            side=side,
            quantity=str(quantity)
        )
        print(f"✅ {side} order placed for {symbol}")
    except Exception as e:
        print(f"❌ Error placing {side} order for {symbol}: {e}")

def get_usdt_balance(client: Client):
    """Get the available USDT balance."""
    account_info = client.get_account()
    for balance in account_info['balances']:
        if balance['asset'] == 'USDT':
            return Decimal(balance['free'])
    return Decimal('0')

def execute_strategy():
    """Enhanced trading strategy with risk management & fine-tuned filtering."""
    from bot.trade import should_sell, should_buy

    from bot.market import is_market_stable
    from _utils.cache import load_cached_sorted_symbols

    print("⏳ Trading bot started...")
    try:
        client = get_client(testnet=True)
    except Exception as e:
        print(f"❌ Connection is unstable: {e}")
        return

    if not is_market_stable(client):
        print("⚠️ Market is too unstable! Skipping trades...")
        return

    sorted_coins = load_cached_sorted_symbols()
    if not sorted_coins:
        print("⚠️ No coins found. Skipping trades...")
        return

    for coin in sorted_coins:
        symbol = coin["symbol"]
        # Using dummy signals
        if should_buy(client, symbol):
            try:
                usdt_balance = get_usdt_balance(client)
                quantity = calculate_quantity(client, symbol, usdt_balance, 'BUY')
                price = get_price(client, symbol)
                execute_trade(client, symbol, 'BUY', quantity, price)
            except Exception as e:
                print(f"⚠️ Error executing BUY trade for {symbol}: {e}")

        elif should_sell(client, symbol):
            try:
                # For SELL, available balance is used inside calculate_quantity.
                usdt_balance = get_usdt_balance(client)  # For consistency
                quantity = calculate_quantity(client, symbol, usdt_balance, 'SELL')
                price = get_price(client, symbol)
                execute_trade(client, symbol, 'SELL', quantity, price)
            except Exception as e:
                print(f"⚠️ Error executing SELL trade for {symbol}: {e}")

from server import start_background_cache_update
start_background_cache_update(get_client(testnet=True))
# Run the strategy every hour
while True:
    execute_strategy()
    print("⏳ Waiting 1 hour before checking again...")
    time.sleep(10)