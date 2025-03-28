from src.market.tasks import stream_kline_data, fill_kline_gaps
from datetime import datetime, timezone as tz
from django.utils import timezone
# kline: [timezone.datetime.fromtimestamp(1742964000000 / 1000, tz=tz.utc), '2.45000000', '2.45040000', '2.44800000', '2.45030000', '165336.00000000', timezone.datetime.fromtimestamp(1742964299999 / 1000, tz=tz.utc), '404968.76100000', 1307, '103029.00000000', '252371.40310000', '0'],


def run():
    # fill_kline_gaps(period_type='minutes', period=1000)
    stream_kline_data()
