from .utils import fetch_historical_klines, update_symbols
from src.services.tasks import run_trading
from time import sleep


def run():

    # import requests
    # Example usage
    # symbol = "BTCUSD"
    # url = get_tradingview_widget_url(symbol)
    # try:
    #     from urllib import unquote
    # except ImportError:
    #         from urllib.parse import unquote
    # # print(unquote("https://s.tradingview.com/widgetembed/?hideideas=1&overrides=%7B%7D&enabled_features=%5B%5D&disabled_features=%5B%5D&locale=in#%7B%22symbol%22%3A%22BITSTAMP%3ABTCUSD%22%2C%22frameElementId%22%3A%22tradingview_de890%22%2C%22interval%22%3A%22D%22%2C%22hide_side_toolbar%22%3A%220%22%2C%22allow_symbol_change%22%3A%221%22%2C%22save_image%22%3A%221%22%2C%22details%22%3A%221%22%2C%22calendar%22%3A%221%22%2C%22hotlist%22%3A%221%22%2C%22studies%22%3A%22%5B%5D%22%2C%22theme%22%3A%22light%22%2C%22style%22%3A%221%22%2C%22timezone%22%3A%22Etc%2FUTC%22%2C%22withdateranges%22%3A%221%22%2C%22studies_overrides%22%3A%22%7B%7D%22%2C%22utm_medium%22%3A%22widget%22%2C%22utm_campaign%22%3A%22chart%22%2C%22utm_term%22%3A%22BITSTAMP%3ABTCUSD%22%2C%22page-uri%22%3A%22__NHTTP__%22%7D"))
    # print(unquote(url))
    # print(url)

    # url = f'https://s.tradingview.com/widgetembed/?hideideas=1&overrides={}&enabled_features=[]&disabled_features=[]&locale=in#{"symbol":"BITSTAMP:BTCUSD","frameElementId":"tradingview_de890","interval":"D","hide_side_toolbar":"0","allow_symbol_change":"1","save_image":"1","details":"1","calendar":"1","hotlist":"1","studies":"[]","theme":"light","style":"1","timezone":"Etc/UTC","withdateranges":"1","studies_overrides":"{}","utm_medium":"widget","utm_campaign":"chart","utm_term":"BITSTAMP:BTCUSD","page-uri":"__NHTTP__"}'

    # data = requests.get(url)
    # print(data.content)
    # usdt_obj = CryptoCurency.objects.get(ticker="USDT")
    # print(f'INITIAL USD BALANCE: {usdt_obj.balance}')
    # update_total_usd()
    # update_symbols()
    # update_system_data()
    # while True:
    # update_klines()
    # reset_cryptos()
    while True:
        run_trading()
        sleep(3)
    # update_symbols()
    # batch_delete_kline_data()
    # from django.utils import timezone
    # from datetime import timedelta
    # minutes = 500
    # end_time = timezone.now()
    # start_time = end_time - timedelta(minutes=minutes)
    # print(start_time)
    # print(end_time)

    # fetch_historical_klines()
    # update_symbols()
