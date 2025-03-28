# trading/views.py
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from src.market.models import CryptoCurency, Kline
from .utils import send_websocket_message


def index(request):
    return render(request, 'index2.html')


def test_websocket(request):
    send_websocket_message(
        'trade_notifications',
        'trade_update',
        {
            'ticker': 'TURBO',
            'order_type': 'BUY',
            'quantity': '5268.8467',
            'price': '0.001138',
            'value': '6.00',
            'timestamp': '2025-03-10T12:00:00Z'
        }
    )
    return HttpResponse("Test message sent.")


def balances(request):
    balances = []
    for crypto in CryptoCurency.objects.exclude(ticker='USDT'):
        close_price = float(Kline.objects.filter(
            symbol=f"{crypto.ticker}USDT").order_by('-time').first().close)

        latest_price = close_price if close_price else 0.00
        usd_value = float(crypto.balance) * latest_price
        balances.append({
            'ticker': crypto.ticker,
            'balance': float(crypto.balance),
            'usd_value': usd_value,
            'pnl': float(crypto.pnl),
        })
    # usdt = CryptoCurency.objects.get(ticker='USDT')
    # balances.append({
    #     'ticker': 'USDT',
    #     'balance': float(usdt.balance),
    #     'usd_value': float(usdt.balance),
    #     'pnl': float(usdt.pnl),
    # })
    return HttpResponse(render_to_string('partials/balances.html', {'balances': balances}))


def cryptos(request):

    cryptos = CryptoCurency.objects.get_cryptos_with_sparkline(kline_amount=25)
    for crypto in cryptos:
        last_kline = Kline.objects.filter(
            symbol=f"{crypto.ticker}USDT").order_by('-time').first()

        close_price = float(last_kline.close) if last_kline else float(1)

        # klines_list = Kline.objects.get_klines_spark_list(crypto.ticker, 25)

        latest_price = close_price if close_price else float(1)
        usd_value = float(crypto.balance) * latest_price
        crypto.usd_value = usd_value

    return render(request, 'partials/cryptos.html', {'cryptos': cryptos})


def update_usdt(request):
    usdt = CryptoCurency.objects.get(ticker='USDT')
    usdt_dict = {
        'ticker': 'USDT',
        'balance': float(usdt.balance),
        'usd_value': float(usdt.balance),
        'pnl': float(usdt.pnl),
    }
    return HttpResponse(render_to_string('partials/usdt-balance.html', {'usdt': usdt_dict}))


def balances_data(request):
    balances = []
    cryptos = CryptoCurency.objects.all()
    for crypto in cryptos:
        balances.append(crypto.to_payload())
    return JsonResponse({'data': balances}, safe=False)


def orders_data(request):
    from src.market.models import Order
    orders_list = []
    orders = Order.objects.all().order_by('-id')
    for order in orders:
        orders_list.append(order.to_payload())
    return JsonResponse({'data': orders_list}, safe=False)


def total_usd(request):
    from src.market.utils import get_total_usd
    total_usd = get_total_usd()
    data = {'total_usd': total_usd}
    return render(request, 'partials/total-usd.html', data)
    # return HttpResponse(f"{total:.2f}")


def notifications(request):
    # Initial empty list; updates come via WebSocket
    return HttpResponse('<li class="notification">No notifications yet.</li>')
