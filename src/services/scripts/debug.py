from django.utils import timezone
from datetime import timedelta, timezone as dt_timezone
from src.market.models import Kline, Symbol
from django.conf import settings


def check_klines_freshness(n_klines=28):

    symbols = symbols = Symbol.objects.filter(
        active=True, enabled=True
        ).values_list('pair', flat=True)
    # for symbol in Symbol.objects.sorted_symbols():
    for symbol in symbols:
        print(f'Current Symbol: {symbol}')
        current_time = timezone.now()
        KLINE_FRESHNESS_LOOKBACK = settings.KLINE_FRESHNESS_LOOKBACK
        freshness_threshold = current_time - KLINE_FRESHNESS_LOOKBACK
        all_fresh = True
        try:
            # Get the latest Kline
            latest_kline = Kline.objects.filter(symbol=symbol).order_by('-end_time').first()
            if not latest_kline:
                print(f"WARNING: No Kline data for {symbol}")
                all_fresh = False
                return
            
    

            # Check freshness
            if latest_kline.end_time < freshness_threshold:
                print(f"WARNING: Kline data for {symbol} is outdated. Latest: {latest_kline.time}, Expected: >{freshness_threshold}")
                all_fresh = False
                return

            # Fetch the last n_klines, ordered by time descending
            klines = Kline.objects.filter(symbol=symbol).order_by('-end_time')[:n_klines]
            for kline in klines:
                print(f"KLINES for {symbol}: {kline.end_time}")
            print('==============================================\n')
            
            print(f"KLINES ||| length: {len(klines)} ||| first_time: {klines[0].end_time} ||| last_time: {klines[n_klines - 1].end_time}")
            print('==============================================\n')

            if len(klines) < n_klines:
                print(f"WARNING: Insufficient Klines for {symbol} ({len(klines)} found, expected {n_klines})")
                all_fresh = False
                return

            # Check total time span (earliest to latest should be (n_klines - 1) * 5 minutes)
            earliest_time = klines[n_klines - 1].end_time.astimezone(dt_timezone.utc)
            latest_time = klines[0].end_time.astimezone(dt_timezone.utc)
            expected_span = (n_klines - 1) * 5 * 60  # Total seconds expected
            actual_span = (latest_time - earliest_time).total_seconds()
            print(f"{symbol} ||| earliest_time: {earliest_time} ||| latest_time: {latest_time}")
            print('==============================================\n')
            print(f"{symbol} ||| (latest_time - earliest_time): {latest_time - earliest_time} ||| seconds: {(latest_time - earliest_time).total_seconds()}")
            print('==============================================\n')
            print(f"{symbol} ||| expected_span: {expected_span} ||| actual_span: {actual_span}")
            print('==============================================\n')
            print(f"{symbol} ||| abs(actual_span - expected_span): {abs(actual_span - expected_span)} ||| abs(actual_span - expected_span) > 2: {abs(actual_span - expected_span) > 2}")
            print('==============================================\n')
            '''
            earliest_time: 2025-03-25 09:34:59.999000+00:00 
            latest_time: 2025-03-25 10:45:00.021000+00:00
            (latest_time - earliest_time): 1:10:00.022000 ||| seconds: 4200.022
            expected_span: 8100 ||| actual_span: 4200.022
            abs(actual_span - expected_span): 3899.978 ||| abs(actual_span - expected_span) > 2: True
            '''
            if abs(actual_span - expected_span) > 2:  # Allow 2-second tolerance
                print(f"WARNING: Incorrect time span for {symbol}. Expected: {expected_span}s, Actual: {actual_span}s")
                all_fresh = False
                return

            # Check for gaps between consecutive Klines
            for i in range(1, len(klines)):
                expected_time = klines[i].time + timedelta(minutes=5)  # Since descending, next should be +5 min
                time_diff = (klines[i - 1].time - klines[i].time).total_seconds()
                if abs(time_diff - 300) > 2:  # 300 seconds = 5 minutes, with 2-second tolerance
                    print(f"WARNING: Gap detected in {symbol} Klines between {klines[i - 1].time} and {klines[i].time}")
                    all_fresh = False
                    break

        except Exception as e:
            print(f"Error checking Klines for {symbol}: {e}")
            all_fresh = False

    return all_fresh


def run():
    # print("Checking Kline data freshness...")
    check_klines_freshness()