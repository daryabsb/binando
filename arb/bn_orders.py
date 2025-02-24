from client.client import get_client
import pandas as pd
from datetime import datetime, timedelta
from _utils.const import meme_coins  # Import your list of meme coins


def download_all_binance_orders_to_excel(hours=48, output_file="binance_all_orders.xlsx"):
    """
    Download the last 48 or 72 hours of orders from Binance Testnet and save to Excel.

    Args:
        api_key (str): Binance Testnet API key
        api_secret (str): Binance Testnet API secret
        symbol (str): Trading pair (e.g., 'BTCUSDT')
        hours (int): Time window in hours (default 48, can set to 72)
        output_file (str): Name of the output Excel file (default 'binance_orders.xlsx')

    Returns:
        None: Saves data to an Excel file or prints an error if unsuccessful
    """
    try:
        # Initialize Binance Testnet client
        client = get_client(testnet=True)

        # Ensure hours is a multiple of 24 to simplify iteration
        if hours % 24 != 0:
            hours = (hours // 24 + 1) * 24  # Round up to next multiple of 24
            print(
                f"Adjusted time range to {hours} hours to comply with 24-hour API limit.")
        # Calculate total time range
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        # Break into 24-hour chunks
        all_orders = []
        current_start = start_time
        while current_start < end_time:
            current_end = min(current_start + timedelta(hours=24), end_time)
            start_timestamp = int(current_start.timestamp() * 1000)
            end_timestamp = int(current_end.timestamp() * 1000)
            print(f"Fetching orders from {current_start} to {current_end}...")
            # Fetch orders for each meme coin symbol in this 24-hour window
            for symbol in meme_coins:
                try:
                    orders = client.get_all_orders(
                        symbol=symbol,
                        startTime=start_timestamp,
                        endTime=end_timestamp,
                        limit=1000
                    )
                    if orders:
                        all_orders.extend(orders)
                        print(f"Fetched {len(orders)} orders for {symbol}")
                    else:
                        print(f"No orders found for {symbol} in this period.")
                except Exception as e:
                    print(f"Error fetching orders for {symbol}: {str(e)}")
            current_start = current_end
        if not all_orders:
            print(
                f"No orders found for any meme coins in the last {hours} hours.")
            return
        # Convert to pandas DataFrame
        df = pd.DataFrame(all_orders)
        # Convert timestamps to readable format
        df['time'] = pd.to_datetime(df['time'], unit='ms')
        df['updateTime'] = pd.to_datetime(df['updateTime'], unit='ms')
        df['clientOrderId'] = df['clientOrderId'].astype(str)
        # Select and rename relevant columns
        df = df[['symbol', 'orderId', 'clientOrderId', 'price', 'origQty', 'executedQty',
                 'status', 'type', 'side', 'time', 'updateTime']]
        df.columns = ['Symbol', 'Order ID', 'Client Order ID', 'Price', 'Original Quantity',
                      'Executed Quantity', 'Status', 'Order Type', 'Side', 'Creation Time', 'Update Time']
        # Sort by Creation Time
        df = df.sort_values('Creation Time')
        # Save to Excel
        df.to_excel(output_file, index=False, engine='openpyxl')
        print(
            f"Successfully downloaded {len(df)} orders to '{output_file}' across {len(set(df['Symbol']))} meme coin symbols for the last {hours} hours.")
    except Exception as e:
        print(f"Error downloading orders: {str(e)}")


# Example usage
if __name__ == "__main__":
    # Replace with your Testnet API credentials
    # Download last 48 hours
    download_all_binance_orders_to_excel(hours=48)
    # Download last 72 hours
    # download_all_binance_orders_to_excel(api_key, api_secret, hours=72, output_file="binance_all_orders_72h.xlsx")
