import math
import pandas as pd


def pr(command1='', command2='', command3='', command4='', command5='', command6='', command7='', command8='', command9='', command10=''):
    print(command1, command2, command3, command4, command5,
          command6, command7, command8, command9, command10)


def get_history(client, symbol, interval, start, end=None):
    bars = client.get_historical_klines(symbol=symbol, interval=interval,
                                        start_str=start, end_str=end, limit=1000)
    df = pd.DataFrame(bars)
    df["Date"] = pd.to_datetime(df.iloc[:, 0], unit="ms")
    df.columns = ["Open Time", "Open", "High", "Low", "Close", "Volume",
                  "Clos Time", "Quote Asset Volume", "Number of Trades",
                  "Taker Buy Base Asset Volume", "Taker Buy Quote Asset Volume", "Ignore", "Date"]
    df = df[["Date", "Open", "High", "Low", "Close", "Volume"]].copy()
    df.set_index("Date", inplace=True)
    for column in df.columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    return df


def stream_data(msg):
    ''' define how to process incoming WebSocket messages '''
    print(msg)
    time = pd.to_datetime(msg["E"], unit="ms")
    price = msg["c"]

    print("Time: {} | Price: {}".format(time, price))


def stream_candles(df, msg):
    ''' define how to process incoming WebSocket messages '''
    # extract the required items from msg
    event_time = pd.to_datetime(msg["E"], unit="ms")
    start_time = pd.to_datetime(msg["k"]["t"], unit="ms")
    first = float(msg["k"]["o"])
    high = float(msg["k"]["h"])
    low = float(msg["k"]["l"])
    close = float(msg["k"]["c"])
    volume = float(msg["k"]["v"])
    complete = msg["k"]["x"]

    # print out
    print("Time: {} | Price: {}".format(event_time, close))

    # feed df (add new bar / update latest bar)
    df.loc[start_time] = [first, high, low, close, volume, complete]


def format_quantity(client, symbol, quantity):
    """
    Adjusts the quantity to the allowed precision based on the symbol's LOT_SIZE filter.
    """
    try:
        info = client.get_symbol_info(symbol)
        if info is None:
            return quantity  # fallback if no info is available
        for f in info['filters']:
            if f['filterType'] == 'LOT_SIZE':
                step_size = float(f['stepSize'])
                # Determine the number of decimals allowed from the step size.
                # For example, a step size of 0.001 allows 3 decimals.
                decimals = int(round(-math.log10(step_size), 0))
                formatted_quantity = round(quantity, decimals)
                # Alternatively, you could use string formatting to be extra sure:
                # formatted_quantity = float(f"{{:.{decimals}f}}".format(quantity))
                return formatted_quantity
        return quantity
    except Exception as e:
        print(f"Error formatting quantity for {symbol}: {e}")
        return quantity
