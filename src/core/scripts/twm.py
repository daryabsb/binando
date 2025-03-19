from binance import ThreadedWebsocketManager
from decouple import config
from src.market.models import Symbol
testnet = False

PUBLIC = config('api_key')
SECRET = config('secret_key')


def handle_socket_message(msg):
    print(f"message type: {msg}")
    print(msg)

def run():
    print('Running twm started!')
    twm = ThreadedWebsocketManager(api_key=PUBLIC, api_secret=SECRET)
    print('Twm is warming up!')
    twm.start()
    print('Twm started!')

    symbols = Symbol.objects.sorted_symbols()


    # streams = ['dogeusdt@kline_5m', 'pepeusdt@kline_5m']
    streams = [f"{cur.lower()}@depth20@kline_5m" for cur in symbols]
    
    twm.start_multiplex_socket(callback=handle_socket_message, streams=streams)
    print('Twm is joining!')
    twm.join()

    # sleep(20)

    twm.stop()

'''
message_type = {
    'stream': 'dogeusdt@kline_5m', 
    'data': {
        'e': 'kline', 
        'E': 1742372914576, 
        's': 'DOGEUSDT', 
        'k': {
            't': 1742372700000, 'T': 1742372999999, 's': 'DOGEUSDT', 'i': '5m', 
            'f': 1054013557, 'L': 1054014081, 'o': '0.16783000', 'c': '0.16798000', 
            'h': '0.16802000', 'l': '0.16783000', 'v': '230623.00000000', 'n': 525, 
            'x': False, 'q': '38733.55281000', 'V': '159058.00000000', 'Q': '26714.95804000', 
            'B': '0'
            }
        }
    }
{
    'stream': 'dogeusdt@kline_5m', 
    'data': {
        'e': 'kline', 
        'E': 1742372914576, 
        's': 'DOGEUSDT', 
        'k': {
            't': 1742372700000, 'T': 1742372999999, 's': 'DOGEUSDT', 'i': '5m', 
            'f': 1054013557, 'L': 1054014081, 'o': '0.16783000', 'c': '0.16798000', 
            'h': '0.16802000', 'l': '0.16783000', 'v': '230623.00000000', 'n': 525, 
            'x': False, 'q': '38733.55281000', 'V': '159058.00000000', 'Q': '26714.95804000', 
            'B': '0'
        }
    }
}
'''