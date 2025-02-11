
from decimal import Decimal
from symbols import get_percentage_options

INTERVAL_PRIZE:str = "1_day" 
# Trade settings
TRADE_ALLOCATION_PERCENTAGE = 0.10  # 10% of total USDT balance
MINIMUM_TRADE_AMOUNT = 5  # Minimum order amount in USDT to cover fees


MAX_TRADE_PERCENTAGE = Decimal(0.25)  # Max 25% of coin balance per trade

# PRICE_CHANGE_THRESHOLD = 0.015  # 1.5% threshold for buy/sell
PRICE_CHANGE_THRESHOLD = get_percentage_options(
    "5%")  # 1.5% threshold for buy/sell

# Store last trade price per symbol
LAST_TRADE = {}

SIDE_BUY = "BUY"
SIDE_SELL = "SELL"

# List of meme coin symbols to trade
meme_coins = [
    "DOGEUSDT",
    "SHIBUSDT",
    "PEPEUSDT",
    "XRPUSDT",
    "TRUMPUSDT",
    "ENSUSDT",
    "MANTAUSDT",
    "TURBOUSDT",
    "SUIUSDT",
    "TFUELUSDT",
    "LTCUSDT",
    "1000CHZUSDT",
    "BNXUSDT",
    "TRXUSDT",
    "DOTUSDT",
    "CAKEUSDT",
    "STPTUSDT",
    "SCRUSDT",
    "NEARUSDT",
    "AUDIOUSDT",
    "WLDUSDT",
    "ETHFIUSDT",
    "DGBUSDT",
    "WINGUSDT",
    "AIRUSDT",
    "JSTUSDT",
    "HOTUSDT",
    "ARDRUSDT",
    "XEMUSDT",
    "SEIUSDT",
    "BBTCUSDT",
    "BTTCUSDT",
    "JTOUSDT",
    "DGBUSDT",
    "TRXUSDT",
    "FLMUSDT",
    "GRAVUSDT",
    "SONICUSDT",
    "SFPUSDT",
    "DIAUSDT",
    "ARDRUSDT",
    "JUPUSDT",
    "BELUSDT",
    "JUVUSDT",
    "WOOUSDT",
    "1MBABYDOGEUSDT",
    "BLURUSDT",
    "STRKUSDT",
    "DFUSDT",
    "FLOKIUSDT",
    "SANDUSDT",
    "SCRTUSDT",
    "COOKIEDOGEUSDT",
    "COOKIEUSDT",
    "HARDUSDT",
    "UNIUSDT",
]


'''
ltc =           "LTCUSDT"
1000cheems =    "1000CHZUSDT"
bnx =           "BNXUSDT"
trx =           "TRXUSDT"
dot =           "DOTUSDT"
cake =          "CAKEUSDT"
stpt =          "STPTUSDT"
scr =           "SCRUSDT"
near =          "NEARUSDT"
audio =         "AUDIOUSDT"
wld =           "WLDUSDT"
ethfi =         "ETHFIUSDT"
dgb =           "DGBUSDT"
wing =          "WINGUSDT"
air =           "AIRUSDT"
jst =           "JSTUSDT"
hot =           "HOTUSDT"
ardr =          "ARDRUSDT"
xem =           "XEMUSDT"
sei =           "SEIUSDT"
bbtc =          "BBTCUSDT"
bttc =          "BTTCUSDT"
jto =           "JTOUSDT"
dgb =           "DGBUSDT"
trx =           "TRXUSDT"
flm =           "FLMUSDT"
grav =          "GRAVUSDT"
sonic =         "SONICUSDT"
sfp =           "SFPUSDT"
dia =           "DIAUSDT"
ardr =          "ARDRUSDT"
jup =           "JUPUSDT"
bel =           "BELUSDT"
juv =           "JUVUSDT"
woo =           "WOOUSDT"
1mbabydoge =    "1MBABYDOGEUSDT"
blur =          "BLURUSDT"
strk =          "STRKUSDT"
df =            "DFUSDT"
floki =         "FLOKIUSDT"
sand =          "SANDUSDT"
scrt =          "SCRTUSDT"
cookiedoge =    "COOKIEDOGEUSDT"
cookie =        "COOKIEUSDT"
hard =          "HARDUSDT"
uni =           "UNIUSDT"
'''