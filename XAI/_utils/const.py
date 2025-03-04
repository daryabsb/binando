
from decimal import Decimal
# from _utils.coins import get_percentage_options

INTERVAL_PRIZE: str = "1_day"
# Trade settings
TRADE_ALLOCATION_PERCENTAGE = 0.25  # 10% of total USDT balance
MINIMUM_TRADE_AMOUNT = 3  # Minimum order amount in USDT to cover fees


MAX_TRADE_PERCENTAGE = Decimal(0.25)  # Max 25% of coin balance per trade


def get_percentage_options(value: str):
    """Convert percentage string like '5%' into a decimal (e.g., 5% → 0.05)."""
    return float(value.strip('%')) / 100  # Ensure it's correctly converted


# PRICE_CHANGE_THRESHOLD = 0.015  # 1.5% threshold for buy/sell
PRICE_CHANGE_THRESHOLD = get_percentage_options(
    "5%")  # 1.5% threshold for buy/sell

# Store last trade price per symbol
LAST_TRADE = {}

SIDE_BUY = "BUY"
SIDE_SELL = "SELL"

# List of meme coin symbols to trade
meme_coins = [
    "BURGERUSDT",
    "1MBABYDOGEUSDT",
    "DOGEUSDT",
    "PEPEUSDT",
    "TFUELUSDT",
    "TRUMPUSDT",
    "SHIBUSDT",
    "XRPUSDT",
    "ENSUSDT",
    "MANTAUSDT",
    "TURBOUSDT",
    "SUIUSDT",
    "LTCUSDT",
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
    "AIUSDT",
    # "JSTUSDT",
    # "HOTUSDT",
    # "ARDRUSDT",
    # "XEMUSDT",
    # "SEIUSDT",
    # "BABYSORA2USD",
    # "BENCOUSD",
    # "WAGGUSD",
    "BTTCUSDT",
    "JTOUSDT",
    "SFPUSDT",
    "DIAUSDT",
    "JUPUSDT",
    "BELUSDT",
    "JUVUSDT",
    "WOOUSDT",
    "BLURUSDT",
    "STRKUSDT",
    "DFUSDT",
    "FLOKIUSDT",
    "SANDUSDT",
    # "SCRTUSDT",
    "COOKIEUSDT",
    "HARDUSDT",
    "UNIUSDT",
    "SYNUSDT",
    # "OCBOUSD",
    # "OMUSD",
    # "FARTCOINUSD",
]

currencies = [
        "BTC",
        "ETC",
        "DOGE",
        "PEPE",
        "1MBABYDOGE",
        "TRUMP",
        "SHIB",
        "ENS",
        "MANTA",
        "TURBO",
        "SUI",
        "LTC",
        "BNX",
        "QTUM",
        "NEO",
        "BNB",
        "EOS",
        "SNT",
        "BNT",
        "GAS",
        "BCC",
        "USDT",
        "HSR",
        "OAX",
        "DNT",
        "MCO",
        "ICN",
        "ZRX",
        "OMG",
        "WTC",
        "YOYO",
        "LRC",
        "TRX",
        "SNGLS",
        "STRAT",
        "BQX",
        "FUN",
        "KNC",
        "CDT",
        "XVG",
        "IOTA",
        "SNM",
        "LINK",
        "CVC",
        "TNT",
        "REP",
        "MDA",
        "MTL",
        "SALT",
        "NULS",
        "SUB",
        "STX",
        "MTH",
        "ADX",
        "ETC",
        "ENG",
        "AST",
        "GNT",
        "DGD",
        "BAT",
        "POWR",
        "BTG",
        "REQ",
        "EVX",
        "VIB",
        "ENJ",
        "VEN",
        "ARK",
        "XRP",
        "MOD",
        "STORJ",
        "KMD",
        "RCN",
        "EDO",
        "DATA",
        "DLT",
        "MANA",
        "PPT",
        "RDN",
        "GXS",
        "AMB",
        "ARN",
        "BCPT",
        "CND",
        "GVT",
        "POE",
        "BTS",
        "FUEL",
        "XZC",
        "QSP",
        "LSK",
        "BCD",
        "TNB",
        "ADA",
        "LEND",
        "XLM",
        "CMT",
        "WAVES",
        "WABI",
        "GTO",
        "ICX",
        "OST",
        "ELF",
        "AION",
        "WINGS",
        "BRD",
        "NEBL",
        "NAV",
        "VIBE",
        "LUN",
        "TRIG",
        "APPC",
        "CHAT",
        "RLC",
        "INS",
        "PIVX",
        "IOST",
        "STEEM",
        "NANO",
        "AE",
        "VIA",
        "BLZ",
        "SYS",
        "RPX",
        "NCASH",
        "POA",
        "ONT",
        "ZIL",
        "STORM",
        "XEM",
        "WAN",
        "WPR",
        "QLC",
        "GRS",
        "CLOAK",
        "LOOM",
        "BCN",
        "TUSD",
        "ZEN",
        "SKY",
        "THETA",
        "IOTX",
        "QKC",
        "AGI",
        "NXS",
        "SC",
        "NPXS",
        "KEY",
        "NAS",
        "MFT",
        "DENT",
        "IQ",
        "ARDR",
        "HOT",
        "VET",
        "DOCK",
        "POLY",
        "VTHO",
        "ONG",
        "PHX",
        "HC",
        "GO",
        "PAX",
        "RVN",
        "DCR",
        "USDC",
        "MITH",
        "BCHABC",
        "BCHSV",
        "REN",
        "BTT",
        "USDS",
        "FET",
        "TFUEL",
        "CELR",
        "MATIC",
        "ATOM",
        "PHB",
        "ONE",
        "FTM",
        "BTCB",
        "USDSB",
        "CHZ",
        "COS",
        "ALGO",
        "ERD",
        "BGBP",
        "DUSK",
        "ANKR",
        "WIN",
        "TUSDB",
        "COCOS",
        "PERL",
        "TOMO",
        "BUSD",
        "BAND",
        "BEAM",
        "HBAR",
        "XTZ",
        "NGN",
        "DGB",
        "NKN",
        "GBP",
        "EUR",
        "KAVA",
        "RUB",
        "UAH",
        "ARPA",
        "TRY",
        "CTXC",
        "AERGO",
        "TROY",
        "BRL",
        "VITE",
        "FTT",
        "AUD",
        "OGN",
        "DREP",
        "BULL",
        "BEAR",
        "ETHBULL",
        "ETHBEAR",
        "XRPBULL",
        "XRPBEAR",
        "EOSBULL",
        "EOSBEAR",
        "TCT",
        "WRX",
        "LTO",
        "ZAR",
        "MBL",
        "COTI",
        "BKRW",
        "BNBBULL",
        "BNBBEAR",
        "HIVE",
        "STPT",
        "SOL",
        "IDRT",
        "CTSI",
        "CHR",
        "HNT",
        "JST",
        "FIO",
        "BIDR",
        "STMX",
        "MDT",
        "PNT",
        "IRIS",
        "SXP",
        "SNX",
        "DAI",
        "DOT",
        "RUNE",
        "AVA",
        "BAL",
        "YFI",
        "SRM",
        "ANT",
        "CRV",
        "SAND",
        "OCEAN",
        "NMR",
        "LUNA",
        "IDEX",
        "RSR",
        "PAXG",
        "WNXM",
        "TRB",
        "EGLD",
        "BZRX",
        "WBTC",
        "KSM",
        "SUSHI",
        "YFII",
        "DIA",
        "BEL",
        "UMA",
        "NBS",
        "WING",
        "SWRV",
        "CREAM",
        "UNI",
        "OXT",
        "SUN",
        "AVAX",
        "BURGER",
        "BAKE",
        "FLM",
        "SCRT",
        "XVS",
        "CAKE",
        "SPARTA",
        "ALPHA",
        "ORN",
        "UTK",
        "NEAR",
        "VIDT",
        "AAVE",
        "FIL",
        "INJ",
        "CTK",
        "EASY",
        "AUDIO",
        "BOT",
        "AXS",
        "AKRO",
        "HARD",
        "KP3R",
        "RENBTC",
        "SLP",
        "STRAX",
        "UNFI",
        "CVP",
        "BCHA",
        "FOR",
        "FRONT",
        "ROSE",
        "HEGIC",
        "PROM",
        "BETH",
        "SKL",
        "GLM",
        "SUSD",
        "COVER",
        "GHST",
        "DF",
        "JUV",
        "PSG",
        "BVND",
        "GRT",
        "CELO",
        "TWT",
        "REEF",
        "OG",
        "ATM",
        "ASR",
        "1INCH",
        "RIF",
        "BTCST",
        "TRU",
        "DEXE",
        "CKB",
        "FIRO",
        "LIT",
        "PROS",
        "VAI",
        "SFP",
        "FXS",
        "DODO",
        "AUCTION",
        "UFT",
        "ACM",
        "PHA",
        "TVK",
        "BADGER",
        "FIS",
        "OM",
        "POND",
        "ALICE",
        "DEGO",
        "BIFI",
        "LINA"
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


⏳ Trading bot started...
🔹 Adjusted trade amount: 20 USDT
✅ Threshold set at: 5.00%
🔍 DOGEUSDT | SELL: Price Change: 0.00%, Threshold: 5.00%
🔍 DOGEUSDT: No trade (change: 0.49%)
✅ Threshold set at: 5.00%
🔍 PEPEUSDT | SELL: Price Change: 0.00%, Threshold: 5.00%
🔍 PEPEUSDT: No trade (change: 0.00%)
✅ Threshold set at: 5.00%
🔍 TFUELUSDT | SELL: Price Change: 0.00%, Threshold: 5.00%
🔍 TFUELUSDT: No trade (change: -4.50%)
✅ Threshold set at: 5.00%
🔍 TRUMPUSDT | SELL: Price Change: 0.00%, Threshold: 5.00%
🔍 TRUMPUSDT: No trade (change: 0.20%)
✅ Threshold set at: 5.00%
🔍 SHIBUSDT | SELL: Price Change: 0.00%, Threshold: 5.00%
🔍 SHIBUSDT: No trade (change: 0.57%)
✅ Threshold set at: 5.00%
🔍 XRPUSDT | SELL: Price Change: 0.00%, Threshold: 5.00%
🔍 XRPUSDT: No trade (change: -0.01%)
✅ Threshold set at: 5.00%
🔍 ENSUSDT | SELL: Price Change: 0.00%, Threshold: 5.00%
🔍 ENSUSDT: No trade (change: 0.95%)
✅ Threshold set at: 5.00%
🔍 MANTAUSDT | SELL: Price Change: 0.00%, Threshold: 5.00%
🔍 MANTAUSDT: No trade (change: 1.27%)
✅ Threshold set at: 5.00%
🔍 TURBOUSDT | SELL: Price Change: 0.00%, Threshold: 5.00%
🔍 TURBOUSDT: No trade (change: -1.84%)
✅ Threshold set at: 5.00%
🔍 SUIUSDT | SELL: Price Change: 0.00%, Threshold: 5.00%
🔍 SUIUSDT: No trade (change: -1.49%)
✅ Threshold set at: 5.00%
🔍 LTCUSDT | SELL: Price Change: 0.00%, Threshold: 5.00%
🔍 LTCUSDT: No trade (change: -1.36%)
✅ Threshold set at: 5.00%
🔍 BNXUSDT | SELL: Price Change: 0.00%, Threshold: 5.00%
🔍 BNXUSDT: No trade (change: 13.07%)
✅ Threshold set at: 5.00%
🔍 TRXUSDT | SELL: Price Change: 0.00%, Threshold: 5.00%
🔍 TRXUSDT: No trade (change: -0.21%)
✅ Threshold set at: 5.00%
🔍 DOTUSDT | SELL: Price Change: 0.00%, Threshold: 5.00%
🔍 DOTUSDT: No trade (change: 0.73%)
✅ Threshold set at: 5.00%
🔍 CAKEUSDT | SELL: Price Change: 0.00%, Threshold: 5.00%
🔍 CAKEUSDT: No trade (change: 5.30%)
✅ Threshold set at: 5.00%
🔍 STPTUSDT | SELL: Price Change: 0.00%, Threshold: 5.00%
🔍 STPTUSDT: No trade (change: -2.91%)
✅ Threshold set at: 5.00%
🔍 SCRUSDT | SELL: Price Change: 0.00%, Threshold: 5.00%
🔍 SCRUSDT: No trade (change: 0.79%)
✅ Threshold set at: 5.00%
🔍 NEARUSDT | SELL: Price Change: 0.00%, Threshold: 5.00%
🔍 NEARUSDT: No trade (change: 0.22%)
✅ Threshold set at: 5.00%
🔍 AUDIOUSDT | SELL: Price Change: 0.00%, Threshold: 5.00%
🔍 AUDIOUSDT: No trade (change: 0.40%)
✅ Threshold set at: 5.00%
🔍 WLDUSDT | SELL: Price Change: 0.00%, Threshold: 5.00%
🔍 WLDUSDT: No trade (change: -1.13%)
✅ Threshold set at: 5.00%
🔍 ETHFIUSDT | SELL: Price Change: 0.00%, Threshold: 5.00%
🔍 ETHFIUSDT: No trade (change: -0.73%)
✅ Threshold set at: 5.00%
🔍 DGBUSDT | SELL: Price Change: 0.00%, Threshold: 5.00%
✅ Threshold set at: 5.00%
🔍 TRXUSDT | BUY: Price Change: 0.00%, Threshold: 5.00%
✅ Threshold set at: 5.00%
🔍 TRXUSDT | SELL: Price Change: 0.00%, Threshold: 5.00%
🔍 TRXUSDT: No trade (change: -0.12%)
✅ Threshold set at: 5.00%
'''
