from src.market.tasks import stream_kline_data, fill_kline_gaps


def run():
    # fill_kline_gaps(days_back=1)
    stream_kline_data()
