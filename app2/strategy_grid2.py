from binance.client import Client
import time

API_KEY = "your_api_key"
API_SECRET = "your_api_secret"
client = Client(API_KEY, API_SECRET)

# List of symbols to trade.
SYMBOLS = [
    "DOGEUSDT",
    "SHIBUSDT",
    "PEPEUSDT",
    "XRPUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "BERAUSDT",
    "BNBUSDT",
    "TRUMPUSDT",
    "BTCUSDT",
]

# Starting capital in USDT.
global_usdt = 100.0

# Data structures to track prices, positions, and potential signals.
last_prices = {}      # Last observed price per symbol.
positions = {}        # Active positions: None or dict {"quantity": ..., "buy_price": ...}
trade_profits = {}    # Cumulative profit per symbol.
potential_buy = {}    # Tracks potential buy levels during a drop.
# Tracks potential sell peaks once profit threshold is reached.
potential_sell = {}

# === Initialize state using Binance price data ===
for sym in SYMBOLS:
    try:
        ticker = client.get_symbol_ticker(symbol=sym)
        price = float(ticker['price'])
        print(f"Initial price for {sym}: {price:.6f}")
    except Exception as e:
        print(f"Error fetching initial price for {sym}: {e}")
        price = 0.0  # You might want to handle this case differently.
    last_prices[sym] = price
    positions[sym] = None
    trade_profits[sym] = 0.0
    potential_buy[sym] = None
    potential_sell[sym] = None

# === Strategy Parameters ===
# When not in a position, if the price drops by DROP_THRESHOLD relative to the last price,
# we mark a potential buy. Then we wait for a rebound of at least REBOND_CONFIRMATION.
# 1.5% drop from last snapshot triggers potential buy.
DROP_THRESHOLD = 0.015
# 0.5% rebound from the low triggers an actual buy.
REBOND_CONFIRMATION = 0.005

# For selling, after entry, wait until the price has risen by PROFIT_THRESHOLD above the buy price.
# Then track a peak price and sell when a drop by TRAILING_STOP occurs from that peak.
# 1.5% profit above the buy price before considering sale.
PROFIT_THRESHOLD = 0.015
TRAILING_STOP = 0.005          # 0.5% drop from the peak triggers the sell.

# Number of intervals to run (each interval is 5 minutes).
num_intervals = 12

print("\n=== Starting live simulation with Binance price data ===\n")
for interval in range(num_intervals):
    print(f"\n===== Interval {interval + 1} =====")

    # Process each symbol.
    for sym in SYMBOLS:
        # Retrieve the current price using Binance API.
        try:
            ticker = client.get_symbol_ticker(symbol=sym)
            current_price = float(ticker['price'])
        except Exception as e:
            print(f"Error fetching price for {sym}: {e}")
            continue

        print(
            f"{sym}: Last Price = {last_prices[sym]:.6f}, Current Price = {current_price:.6f}")

        # --- BUY LOGIC (only if no open position) ---
        if positions[sym] is None:
            # If no potential buy is already recorded...
            if potential_buy[sym] is None:
                # Check if the price dropped by DROP_THRESHOLD compared to the last snapshot.
                if current_price <= last_prices[sym] * (1 - DROP_THRESHOLD):
                    potential_buy[sym] = current_price
                    print(
                        f"   Potential BUY: {sym} drop detected. Setting potential buy price to {current_price:.6f}")
            else:
                # If the drop continues, update the potential buy price.
                if current_price < potential_buy[sym]:
                    potential_buy[sym] = current_price
                    print(
                        f"   {sym} continues to drop. Updating potential buy price to {current_price:.6f}")
                # Once a rebound is detected (price rising by REBOND_CONFIRMATION from the low), execute buy.
                elif current_price >= potential_buy[sym] * (1 + REBOND_CONFIRMATION):
                    # 10% of available USDT.
                    invest_amount = global_usdt * 0.10
                    quantity = invest_amount / current_price
                    # In live trading, replace this simulation with an actual order, e.g.:
                    # order = client.order_market_buy(symbol=sym, quantity=quantity)
                    positions[sym] = {"quantity": quantity,
                                      "buy_price": current_price}
                    global_usdt -= invest_amount
                    print(
                        f"   BUY: {sym} - Purchased {quantity:.6f} units at {current_price:.6f} using {invest_amount:.2f} USDT")
                    # Clear the potential buy signal.
                    potential_buy[sym] = None

        # --- SELL LOGIC (only if currently in a position) ---
        else:
            buy_price = positions[sym]["buy_price"]
            # Check if we've reached the profit threshold.
            if current_price >= buy_price * (1 + PROFIT_THRESHOLD):
                if potential_sell[sym] is None:
                    potential_sell[sym] = current_price
                    print(
                        f"   Potential SELL: {sym} - Profit threshold reached. Setting potential sell peak to {current_price:.6f}")
                else:
                    # Update the peak if the price is still rising.
                    if current_price > potential_sell[sym]:
                        potential_sell[sym] = current_price
                        print(
                            f"   {sym} price rising. Updating potential sell peak to {current_price:.6f}")
                    # If the price drops by TRAILING_STOP from the peak, sell.
                    elif current_price <= potential_sell[sym] * (1 - TRAILING_STOP):
                        quantity = positions[sym]["quantity"]
                        proceeds = quantity * current_price
                        profit = proceeds - (quantity * buy_price)
                        trade_profits[sym] += profit
                        global_usdt += proceeds
                        print(
                            f"   SELL: {sym} - Sold {quantity:.6f} units at {current_price:.6f} for {proceeds:.2f} USDT (Profit: {profit:.2f} USDT)")
                        # Reset position and potential sell signal.
                        positions[sym] = None
                        potential_sell[sym] = None

        # Update the last price for the next interval.
        last_prices[sym] = current_price

    print(f"\nGlobal USDT balance: {global_usdt:.2f} USDT")

    # Wait for 5 minutes (300 seconds) before the next interval.
    time.sleep(300)

# === End-of-Session Reporting ===
print("\n=== Session Complete ===")
print(f"Final global USDT balance: {global_usdt:.2f} USDT")
for sym in SYMBOLS:
    print(f"  {sym}: Total Profit = {trade_profits[sym]:.2f} USDT")

# (Optional) Liquidate any open positions here if needed.
for sym in SYMBOLS:
    if positions[sym] is not None:
        quantity = positions[sym]["quantity"]
        buy_price = positions[sym]["buy_price"]
        # Get current price.
        try:
            ticker = client.get_symbol_ticker(symbol=sym)
            current_price = float(ticker['price'])
        except Exception as e:
            print(f"Error fetching price for liquidation of {sym}: {e}")
            continue
        proceeds = quantity * current_price
        profit = proceeds - (quantity * buy_price)
        trade_profits[sym] += profit
        global_usdt += proceeds
        print(
            f"Liquidating {sym}: Sold {quantity:.6f} units at {current_price:.6f} (Profit: {profit:.2f} USDT)")
        positions[sym] = None

print("\nAfter liquidation:")
print(f"Final global USDT balance: {global_usdt:.2f} USDT")
for sym in SYMBOLS:
    print(f"  {sym}: Total Profit = {trade_profits[sym]:.2f} USDT")
