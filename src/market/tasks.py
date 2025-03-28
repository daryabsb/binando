# src/services/tasks.py
import asyncio
from celery import shared_task
from binance import BinanceSocketManager, AsyncClient
from binance import ThreadedWebsocketManager
from decouple import config
from src.market.models import Symbol, Kline
from django.utils import timezone
from decimal import Decimal
import threading
# src/services/tasks.py
from datetime import datetime, timedelta, timezone as dt_timezone
import time
from django.db import transaction
from django.utils.timezone import make_aware
from asgiref.sync import sync_to_async
from src.services.client import get_client

PUBLIC = config('api_key')
SECRET = config('secret_key')

# Maximum number of Klines to hold before flushing (optional limit)
BATCH_SIZE = 100
FLUSH_INTERVAL = 5  # Flush to DB every 5 seconds
batch_inserted = False


BATCH_SIZE = 100  # Maximum Klines before immediate flush
FLUSH_INTERVAL = 60  # Seconds between periodic flushes

client = get_client()


def normalize_to_5m(dt):
    """Round a datetime to the nearest 5-minute boundary."""
    epoch = dt.timestamp()
    rounded_epoch = (epoch // 300) * 300  # 300 seconds = 5 minutes
    return timezone.datetime.fromtimestamp(rounded_epoch, tz=dt_timezone.utc)


def fill_kline_gaps(symbols=None, interval='5m', period_type='days', period=8, batch_size=10):
    """
    Fetch historical Kline data with dynamic interval support.
    """
    print(
        f'Fetching {period} {period_type} of Kline data started for {interval}')
    end_time = timezone.now()
    if period_type == 'days':
        start_time = end_time - timedelta(days=period)
    else:
        start_time = end_time - timedelta(minutes=period)

    if symbols is None:
        symbols = Symbol.objects.filter(
            active=True, enabled=True).values_list('pair', flat=True)

    def get_interval_duration(interval_str):
        """Convert Binance interval string to timedelta."""
        unit = interval_str[-1]
        value = int(interval_str[:-1])
        if unit == 'm':
            return timedelta(minutes=value)
        elif unit == 'h':
            return timedelta(hours=value)
        elif unit == 'd':
            return timedelta(days=value)
        elif unit == 'w':
            return timedelta(weeks=value)
        else:
            raise ValueError(f"Unsupported interval: {interval_str}")

    def normalize_start(dt, interval_duration):
        """Round down to the nearest interval boundary."""
        epoch = dt.timestamp()
        seconds_per_interval = interval_duration.total_seconds()
        rounded_epoch = (epoch // seconds_per_interval) * seconds_per_interval
        return timezone.datetime.fromtimestamp(rounded_epoch, tz=dt_timezone.utc)

    interval_duration = get_interval_duration(interval)

    for i in range(0, len(symbols), batch_size):
        batch_symbols = symbols[i:i + batch_size]
        for symbol in batch_symbols:
            print(f"Fetching data for {symbol}...")
            try:
                klines = client.get_historical_klines(
                    symbol=symbol,
                    interval=interval,
                    start_str=int(start_time.timestamp() * 1000),
                    end_str=int(end_time.timestamp() * 1000)
                )

                kline_objects = []
                for kline in klines:
                    start_dt = timezone.datetime.fromtimestamp(
                        kline[0] / 1000, tz=dt_timezone.utc)
                    end_dt = timezone.datetime.fromtimestamp(
                        kline[6] / 1000, tz=dt_timezone.utc)

                    # Normalize start time and derive end time dynamically
                    normalized_start = normalize_start(
                        start_dt, interval_duration)
                    normalized_end = normalized_start + interval_duration

                    # Debug: Verify timestamps
                    print(f"{symbol} Raw: start={start_dt}, end={end_dt}")
                    print(
                        f"{symbol} Normalized: start={normalized_start}, end={normalized_end}")

                    kline_objects.append(Kline(
                        symbol=symbol,
                        interval=interval,
                        start_time=normalized_start,
                        end_time=normalized_end,
                        open=Decimal(kline[1]),
                        close=Decimal(kline[4]),
                        high=Decimal(kline[2]),
                        low=Decimal(kline[3]),
                        volume=Decimal(kline[5]),
                        quote_volume=Decimal(kline[7]),
                        taker_buy_base_volume=Decimal(kline[9]),
                        taker_buy_quote_volume=Decimal(kline[10]),
                        trade_count=int(kline[8]),
                        is_closed=True,
                        time=normalized_end  # Use normalized end time as 'time'
                    ))

                Kline.objects.bulk_create(kline_objects, ignore_conflicts=True)
                print(f"Inserted {len(kline_objects)} Klines for {symbol}")
            except Exception as e:
                print(f"Error fetching or saving Klines for {symbol}: {e}")
                return False

        time.sleep(1)

    print(f'Fetching {period} {period_type} of Kline data finished')
    return True


def stream_kline_data(interval='5m'):
    print(f'streaming started for {interval} klines @{timezone.now().time()}')
    kline_batch = []
    lock = threading.Lock()
    BATCH_SIZE = 100  # Adjust as needed
    FLUSH_INTERVAL = 60  # Adjust as needed

    def get_interval_duration(interval_str):
        """Convert Binance interval string to timedelta."""
        unit = interval_str[-1]
        value = int(interval_str[:-1])
        if unit == 'm':
            return timedelta(minutes=value)
        elif unit == 'h':
            return timedelta(hours=value)
        elif unit == 'd':
            return timedelta(days=value)
        elif unit == 'w':
            return timedelta(weeks=value)
        else:
            raise ValueError(f"Unsupported interval: {interval_str}")

    def normalize_start(dt, interval_duration):
        """Round down to the nearest interval boundary."""
        epoch = dt.timestamp()
        seconds_per_interval = interval_duration.total_seconds()
        rounded_epoch = (epoch // seconds_per_interval) * seconds_per_interval
        return timezone.datetime.fromtimestamp(rounded_epoch, tz=dt_timezone.utc)

    interval_duration = get_interval_duration(interval)

    def handle_socket_message(msg):
        try:
            data = msg['data']
            kline = data['k']
            if kline['x']:  # Finalized Kline
                start_dt = timezone.datetime.fromtimestamp(
                    kline['t'] / 1000, tz=dt_timezone.utc)
                end_dt = timezone.datetime.fromtimestamp(
                    kline['T'] / 1000, tz=dt_timezone.utc)

                # Normalize start time and derive end time dynamically
                normalized_start = normalize_start(start_dt, interval_duration)
                normalized_end = normalized_start + interval_duration

                # Debug: Verify timestamps
                # print(f"{kline['s']} Raw: start={start_dt}, end={end_dt}")
                # print(
                #     f"{kline['s']} Normalized: start={normalized_start}, end={normalized_end}")

                with lock:
                    kline_batch.append({
                        'symbol': kline['s'],
                        'interval': kline['i'],
                        'start_time': normalized_start,
                        'end_time': normalized_end,
                        'open': Decimal(kline['o']),
                        'close': Decimal(kline['c']),
                        'high': Decimal(kline['h']),
                        'low': Decimal(kline['l']),
                        'volume': Decimal(kline['v']),
                        'quote_volume': Decimal(kline['q']),
                        'taker_buy_base_volume': Decimal(kline['V']),
                        'taker_buy_quote_volume': Decimal(kline['Q']),
                        'trade_count': kline['n'],
                        'is_closed': True,
                        'time': normalized_end  # Use normalized end time as 'time'
                    })
                    if len(kline_batch) >= BATCH_SIZE:
                        bulk_insert(kline_batch)
        except Exception as e:
            print(f"Error processing message: {e}")

    def bulk_insert(batch):
        if batch:
            with lock:
                Kline.objects.bulk_create(
                    [Kline(**data) for data in batch], ignore_conflicts=True)
                print(
                    f"Bulk inserted {len(batch)} Klines @{timezone.now().time()}")
                batch.clear()

    def periodic_flush():
        while True:
            time.sleep(FLUSH_INTERVAL)
            bulk_insert(kline_batch)

    twm = ThreadedWebsocketManager(api_key=PUBLIC, api_secret=SECRET)
    twm.start()

    symbols = Symbol.objects.filter(
        active=True, enabled=True).values_list('pair', flat=True)
    streams = [f"{symbol.lower()}@kline_{interval}" for symbol in symbols]

    twm.start_multiplex_socket(callback=handle_socket_message, streams=streams)

    flush_thread = threading.Thread(target=periodic_flush, daemon=True)
    flush_thread.start()

    twm.join()


@shared_task
def cleanup_old_klines():
    threshold = timezone.now() - timedelta(days=7)  # Keep 7 days of data
    deleted_count, _ = Kline.objects.filter(start_time__lt=threshold).delete()
    print(f"Deleted {deleted_count} old Klines")


def normalize_and_bulk_insert(binance_klines):
    """
    Normalizes Binance kline data and bulk inserts into the Kline model.

    Args:
        binance_klines (list): List of Binance kline dictionaries.
    """
    kline_objects = []

    for data in binance_klines:
        kline_data = data["k"]  # Extract kline data
        event_time = make_aware(datetime.utcfromtimestamp(
            data["E"] / 1000))  # Convert 'E' to datetime

        kline_obj = Kline(
            symbol=data["s"],  # "BTCUSDT"
            interval=kline_data["i"],  # "5m"
            start_time=make_aware(
                datetime.utcfromtimestamp(kline_data["t"] / 1000)),
            end_time=make_aware(
                datetime.utcfromtimestamp(kline_data["T"] / 1000)),
            open=kline_data["o"],
            close=kline_data["c"],
            high=kline_data["h"],
            low=kline_data["l"],
            volume=kline_data["v"],
            quote_volume=kline_data["q"],
            taker_buy_base_volume=kline_data["V"],
            taker_buy_quote_volume=kline_data["Q"],
            trade_count=kline_data["n"],
            is_closed=kline_data["x"],
            time=event_time  # Assign event time (E) as `time`
        )
        kline_objects.append(kline_obj)

    if kline_objects:
        with transaction.atomic():  # Ensure atomic insert
            Kline.objects.bulk_create(kline_objects)
        print(f"Inserted {len(kline_objects)} Kline records.")


'''

MSG = {
    'stream': 'dotusdt@kline_5m', 
    'data': {
        'e': 'kline', 
        'E': 1742576152973, 
        's': 'DOTUSDT', 
        'k': {
            't': 1742576100000, 
            'T': 1742576399999, 
            's': 'DOTUSDT', 
            'i': '5m', 
            'f': 400971181, 
            'L': 400971222, 
            'o': '4.47500000', 
            'c': '4.47400000', 
            'h': '4.47500000', 
            'l': '4.47100000', 
            'v': '1870.30000000', 
            'n': 42, 
            'x': False, 
            'q': '8364.30854000', 
            'V': '1189.22000000', 
            'Q': '5318.45000000', 
            'B': '0'
        }
    }
}
{
'symbol': '',
'interval': '',
'start_time': '',
'end_time': '',
'open': '',
'close': '',
'high': '',
'low': '',
'volume': '',
'quote_volume': '',
'taker_buy_base_volume': '',
'taker_buy_quote_volume': '',
'trade_count': '',
'is_closed': '',
'time': ''
}

        'symbol': f"{kline['s']}",
        'interval': kline['i'],
        'start_time': timezone.datetime.fromtimestamp(kline[0] / 1000, tz=timezone.utc),
        'end_time': timezone.datetime.fromtimestamp(kline[6] / 1000, tz=timezone.utc),
        'open': Decimal(kline[1]),
        'close': Decimal(kline[4]),
        'high': Decimal(kline[2]),
        'low': Decimal(kline[3]),
        'volume': Decimal(kline[5]),
        'quote_volume': Decimal(kline[7]),
        'taker_buy_base_volume': Decimal(kline[9]),
        'taker_buy_quote_volume': Decimal(kline[10]),
        'trade_count': int(kline[8]),
        'is_closed': True


{'symbol': ''}, = models.CharField(max_length=20, db_index=True)
{'interval': ''}, = models.CharField(max_length=10, default='5m')  # e.g., '5m'
{'start_time': ''}, = models.DateTimeField()  # Kline start time
{'end_time': ''}, = models.DateTimeField()  # Kline end time
{'#': ''}, timestamp = TimescaleDateTimeField(interval="2 week")
{'open': ''}, = models.DecimalField(max_digits=20, decimal_places=8)
{'close': ''}, = models.DecimalField(max_digits=20, decimal_places=8)
{'high': ''}, = models.DecimalField(max_digits=20, decimal_places=8)
{'low': ''}, = models.DecimalField(max_digits=20, decimal_places=8)
{'#': ''}, Volume fields: increase max_digits to handle large numbers
{'volume': ''}, = models.DecimalField(max_digits=30, decimal_places=8)
{'quote_volume': ''}, = models.DecimalField(max_digits=30, decimal_places=8)
{'taker_buy_base_volume': ''}, = models.DecimalField(
{'    max_digits': ''},=30, decimal_places=8)
{'taker_buy_quote_volume': ''}, = models.DecimalField(
{'    max_digits': ''},=30, decimal_places=8)
{'trade_count': ''}, = models.IntegerField()
{'is_closed': ''}, = models.BooleanField(default=False)
{'#': ''}, timestamp = models.BooleanField(default=False)
{'time': ''}, = TimescaleDateTimeField(interval="2 week")


MSG:  {'t': 1742576400000, 'T': 1742576699999, 's': 'CAKEUSDT', 'i': '5m', 'f': 137168360, 'L': 137170623, 'o': '2.69800000', 'c': '2.68100000', 'h': '2.70800000', 'l': '2.67600000', 'v': '160831.87000000', 'n': 2264, 'x': True, 'q': '433098.68756000', 'V': '79053.84000000', 'Q': '213039.26862000', 'B': '0'} 
MSG:  {'t': 1742576400000, 'T': 1742576699999, 's': 'JTOUSDT', 'i': '5m', 'f': 64825205, 'L': 64825640, 'o': '2.09000000', 'c': '2.09300000', 'h': '2.10200000', 'l': '2.09000000', 'v': '43605.10000000', 'n': 436, 'x': True, 'q': '91405.80880000', 'V': '30927.80000000', 'Q': '64813.73760000', 'B': '0'}        
MSG:  {'t': 1742576400000, 'T': 1742576699999, 's': 'NEARUSDT', 'i': '5m', 'f': 253433741, 'L': 253433897, 'o': '2.72400000', 'c': '2.72200000', 'h': '2.72400000', 'l': '2.71900000', 'v': '5736.70000000', 'n': 157, 'x': True, 'q': '15615.35770000', 'V': '2908.80000000', 'Q': '7919.29730000', 'B': '0'}        
MSG:  {'t': 1742576400000, 'T': 1742576699999, 's': 'XRPUSDT', 'i': '5m', 'f': 1070281041, 'L': 1070284271, 'o': '2.39680000', 'c': '2.38980000', 'h': '2.39700000', 'l': '2.38770000', 'v': '420401.00000000', 'n': 3231, 'x': True, 'q': '1005437.00400000', 'V': '141428.00000000', 'Q': '338291.33120000', 'B': '0'}
MSG:  {'t': 1742576400000, 'T': 1742576699999, 's': 'DIAUSDT', 'i': '5m', 'f': 38550234, 'L': 38550350, 'o': '0.41030000', 'c': '0.40950000', 'h': '0.41030000', 'l': '0.40940000', 'v': '6576.00000000', 'n': 117, 'x': True, 'q': '2695.93623000', 'V': '231.30000000', 'Q': '94.71915000', 'B': '0'}
MSG:  {'t': 1742576400000, 'T': 1742576699999, 's': 'TFUELUSDT', 'i': '5m', 'f': 70048701, 'L': 70048730, 'o': '0.03837000', 'c': '0.03829000', 'h': '0.03837000', 'l': '0.03826000', 'v': '17507.00000000', 'n': 30, 'x': True, 'q': '670.71057000', 'V': '6828.00000000', 'Q': '261.76968000', 'B': '0'}
MSG:  {'t': 1742576400000, 'T': 1742576699999, 's': 'JUVUSDT', 'i': '5m', 'f': 27587564, 'L': 27587813, 'o': '1.15600000', 'c': '1.14700000', 'h': '1.15700000', 'l': '1.14100000', 'v': '23896.86000000', 'n': 250, 'x': True, 'q': '27432.56952000', 'V': '11027.36000000', 'Q': '12679.07248000', 'B': '0'}        
MSG:  {'t': 1742576400000, 'T': 1742576699999, 's': 'BURGERUSDT', 'i': '5m', 'f': 57057851, 'L': 57058649, 'o': '0.09730000', 'c': '0.09900000', 'h': '0.10040000', 'l': '0.09730000', 'v': '853184.60000000', 'n': 799, 'x': True, 'q': '84317.93261000', 'V': '375523.50000000', 'Q': '37162.61101000', 'B': '0'}   
MSG:  {'t': 1742576400000, 'T': 1742576699999, 's': 'SUIUSDT', 'i': '5m', 'f': 296141628, 'L': 296142152, 'o': '2.27090000', 'c': '2.26710000', 'h': '2.27240000', 'l': '2.26400000', 'v': '81791.60000000', 'n': 525, 'x': True, 'q': '185399.81487000', 'V': '18484.80000000', 'Q': '41918.22939000', 'B': '0'}     
MSG:  {'t': 1742576400000, 'T': 1742576699999, 's': 'BTTCUSDT', 'i': '5m', 'f': 16482058, 'L': 16482093, 'o': '0.00000069', 'c': '0.00000069', 'h': '0.00000069', 'l': '0.00000068', 'v': '4169650120.0', 'n': 36, 'x': True, 'q': '2851.69598994', 'V': '1633390834.0', 'Q': '1127.03967546', 'B': '0'}
MSG:  {'t': 1742576400000, 'T': 1742576699999, 's': 'AUDIOUSDT', 'i': '5m', 'f': 63754501, 'L': 63754517, 'o': '0.08030000', 'c': '0.08020000', 'h': '0.08030000', 'l': '0.08010000', 'v': '19277.30000000', 'n': 17, 'x': True, 'q': '1546.82605000', 'V': '224.40000000', 'Q': '18.00425000', 'B': '0'}
MSG:  {'t': 1742576400000, 'T': 1742576699999, 's': 'SHIBUSDT', 'i': '5m', 'f': 1452062574, 'L': 1452065127, 'o': '0.00001262', 'c': '0.00001259', 'h': '0.00001262', 'l': '0.00001257', 'v': '3692499476.00', 'n': 2554, 'x': True, 'q': '46494.06811562', 'V': '2613987139.00', 'Q': '32902.75900826', 'B': '0'}    
MSG:  {'t': 1742576400000, 'T': 1742576699999, 's': 'TRUMPUSDT', 'i': '5m', 'f': 104226255, 'L': 104226662, 'o': '10.87000000', 'c': '10.86000000', 'h': '10.87000000', 'l': '10.83000000', 'v': '13045.99400000', 'n': 408, 'x': True, 'q': '141600.04675000', 'V': '4955.34100000', 'Q': '53796.15913000', 'B': '0'}
MSG:  {'t': 1742576400000, 'T': 1742576699999, 's': 'PEPEUSDT', 'i': '5m', 'f': 422599086, 'L': 422600348, 'o': '0.00000731', 'c': '0.00000731', 'h': '0.00000733', 'l': '0.00000729', 'v': '99973628120.00', 'n': 1263, 'x': True, 'q': '730920.95880959', 'V': '58496346829.00', 'Q': '427861.14746486', 'B': '0'}  
MSG:  {'t': 1742576400000, 'T': 1742576699999, 's': 'BELUSDT', 'i': '5m', 'f': 64745642, 'L': 64745649, 'o': '0.60740000', 'c': '0.60590000', 'h': '0.60740000', 'l': '0.60590000', 'v': '935.10000000', 'n': 8, 'x': True, 'q': '567.57167000', 'V': '424.20000000', 'Q': '257.40196000', 'B': '0'}
MSG:  {'t': 1742576400000, 'T': 1742576699999, 's': 'WINGUSDT', 'i': '5m', 'f': 36996420, 'L': 36996658, 'o': '3.16800000', 'c': '3.17300000', 'h': '3.18000000', 'l': '3.15800000', 'v': '3487.00000000', 'n': 239, 'x': True, 'q': '11053.88777000', 'V': '2488.18000000', 'Q': '7890.60807000', 'B': '0'}
MSG:  {'t': 1742576400000, 'T': 1742576699999, 's': 'AIUSDT', 'i': '5m', 'f': 51302462, 'L': 51302505, 'o': '0.18340000', 'c': '0.18300000', 'h': '0.18340000', 'l': '0.18260000', 'v': '33831.40000000', 'n': 44, 'x': True, 'q': '6186.65901000', 'V': '14453.50000000', 'Q': '2641.80090000', 'B': '0'}
MSG:  {'t': 1742576400000, 'T': 1742576699999, 's': 'WOOUSDT', 'i': '5m', 'f': 42792779, 'L': 42792797, 'o': '0.08490000', 'c': '0.08460000', 'h': '0.08490000', 'l': '0.08460000', 'v': '30082.20000000', 'n': 19, 'x': True, 'q': '2549.53787000', 'V': '7763.70000000', 'Q': '657.27232000', 'B': '0'}
MSG:  {'t': 1742576400000, 'T': 1742576699999, 's': 'TRXUSDT', 'i': '5m', 'f': 352020157, 'L': 352020636, 'o': '0.23600000', 'c': '0.23550000', 'h': '0.23600000', 'l': '0.23540000', 'v': '2576741.20000000', 'n': 480, 'x': True, 'q': '607270.78253000', 'V': '273536.00000000', 'Q': '64507.38436000', 'B': '0'}  
MSG:  {'t': 1742576400000, 'T': 1742576699999, 's': 'MANTAUSDT', 'i': '5m', 'f': 63661611, 'L': 63661665, 'o': '0.26000000', 'c': '0.25900000', 'h': '0.26000000', 'l': '0.25900000', 'v': '58700.10000000', 'n': 55, 'x': True, 'q': '15251.06470000', 'V': '17070.70000000', 'Q': '4438.38200000', 'B': '0'}        
MSG:  {'t': 1742576400000, 'T': 1742576699999, 's': 'TURBOUSDT', 'i': '5m', 'f': 34041100, 'L': 34041216, 'o': '0.00223800', 'c': '0.00222400', 'h': '0.00223800', 'l': '0.00222200', 'v': '9351949.00000000', 'n': 117, 'x': True, 'q': '20835.79700200', 'V': '2579108.00000000', 'Q': '5742.63582200', 'B': '0'}   
MSG:  {'t': 1742576400000, 'T': 1742576699999, 's': 'ENSUSDT', 'i': '5m', 'f': 90479885, 'L': 90479913, 'o': '16.51000000', 'c': '16.46000000', 'h': '16.52000000', 'l': '16.44000000', 'v': '137.20000000', 'n': 29, 'x': True, 'q': '2257.54380000', 'V': '126.12000000', 'Q': '2075.11300000', 'B': '0'}
MSG:  {'t': 1742576400000, 'T': 1742576699999, 's': '1MBABYDOGEUSDT', 'i': '5m', 'f': 51477426, 'L': 51477523, 'o': '0.00132620', 'c': '0.00132090', 'h': '0.00132620', 'l': '0.00132020', 'v': '4138520.00', 'n': 98, 'x': True, 'q': '5474.97403320', 'V': '1088214.00', 'Q': '1438.22041640', 'B': '0'}
MSG:  {'t': 1742576400000, 'T': 1742576699999, 's': 'DOTUSDT', 'i': '5m', 'f': 400971526, 'L': 400971829, 'o': '4.48300000', 'c': '4.46400000', 'h': '4.48700000', 'l': '4.46000000', 'v': '16149.19000000', 'n': 304, 'x': True, 'q': '72177.68560000', 'V': '5721.09000000', 'Q': '25562.11732000', 'B': '0'}       
MSG:  {'t': 1742576400000, 'T': 1742576699999, 's': 'DOGEUSDT', 'i': '5m', 'f': 1055887979, 'L': 1055889548, 'o': '0.16743000', 'c': '0.16704000', 'h': '0.16746000', 'l': '0.16694000', 'v': '1967466.00000000', 'n': 1570, 'x': True, 'q': '328709.88913000', 'V': '637224.00000000', 'Q': '106459.80326000', 'B': '0'}
MSG:  {'t': 1742576400000, 'T': 1742576699999, 's': 'ETHFIUSDT', 'i': '5m', 'f': 64731890, 'L': 64731934, 'o': '0.64100000', 'c': '0.64000000', 'h': '0.64200000', 'l': '0.63900000', 'v': '16046.10000000', 'n': 45, 'x': True, 'q': '10276.82840000', 'V': '5289.20000000', 'Q': '3385.52080000', 'B': '0'}
MSG:  {'t': 1742576400000, 'T': 1742576699999, 's': 'DGBUSDT', 'i': '5m', 'f': 37578372, 'L': 37578392, 'o': '0.00793000', 'c': '0.00789000', 'h': '0.00793000', 'l': '0.00789000', 'v': '165837.70000000', 'n': 21, 'x': True, 'q': '1311.76403200', 'V': '84453.00000000', 'Q': '668.57716600', 'B': '0'}
MSG:  {'t': 1742576400000, 'T': 1742576699999, 's': 'STPTUSDT', 'i': '5m', 'f': 54863642, 'L': 54863669, 'o': '0.04906000', 'c': '0.04895000', 'h': '0.04907000', 'l': '0.04895000', 'v': '21374.40000000', 'n': 28, 'x': True, 'q': '1048.05353400', 'V': '13250.50000000', 'Q': '649.78585800', 'B': '0'}
MSG:  {'t': 1742576400000, 'T': 1742576699999, 's': 'JUPUSDT', 'i': '5m', 'f': 79423158, 'L': 79423267, 'o': '0.51210000', 'c': '0.51080000', 'h': '0.51230000', 'l': '0.51030000', 'v': '23077.40000000', 'n': 110, 'x': True, 'q': '11805.21265000', 'V': '8933.90000000', 'Q': '4570.73494000', 'B': '0'}
MSG:  {'t': 1742576400000, 'T': 1742576699999, 's': 'WLDUSDT', 'i': '5m', 'f': 184221172, 'L': 184221464, 'o': '0.83200000', 'c': '0.83100000', 'h': '0.83300000', 'l': '0.82900000', 'v': '51597.10000000', 'n': 293, 'x': True, 'q': '42861.04490000', 'V': '36772.00000000', 'Q': '30551.99250000', 'B': '0'}      
MSG:  {'t': 1742576400000, 'T': 1742576699999, 's': 'SCRUSDT', 'i': '5m', 'f': 10173381, 'L': 10173394, 'o': '0.33500000', 'c': '0.33500000', 'h': '0.33500000', 'l': '0.33400000', 'v': '4357.40000000', 'n': 14, 'x': True, 'q': '1459.64200000', 'V': '98.90000000', 'Q': '33.13150000', 'B': '0'}
MSG:  {'t': 1742576400000, 'T': 1742576699999, 's': 'SFPUSDT', 'i': '5m', 'f': 60138179, 'L': 60138190, 'o': '0.53210000', 'c': '0.53260000', 'h': '0.53260000', 'l': '0.53210000', 'v': '1414.00000000', 'n': 12, 'x': True, 'q': '752.86890000', 'V': '1395.00000000', 'Q': '742.75900000', 'B': '0'}
MSG:  {'t': 1742576400000, 'T': 1742576699999, 's': 'BLURUSDT', 'i': '5m', 'f': 28865197, 'L': 28865395, 'o': '0.10550000', 'c': '0.10560000', 'h': '0.10590000', 'l': '0.10530000', 'v': '410434.40000000', 'n': 199, 'x': True, 'q': '43329.64125000', 'V': '235617.50000000', 'Q': '24898.79799000', 'B': '0'}     
MSG:  {'t': 1742576400000, 'T': 1742576699999, 's': 'LTCUSDT', 'i': '5m', 'f': 439212259, 'L': 439213383, 'o': '93.62000000', 'c': '93.44000000', 'h': '93.65000000', 'l': '93.30000000', 'v': '2505.91900000', 'n': 1125, 'x': True, 'q': '234215.32314000', 'V': '954.78200000', 'Q': '89270.51363000', 'B': '0'} 

'''
