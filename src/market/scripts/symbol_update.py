
currencies = ["BURGER", "1MBABYDOGE", "DOGE", "PEPE", "TFUEL", "TRUMP", "SHIB", "XRP", "ENS", "MANTA", "TURBO",
                "SUI", "LTC", "BNX", "TRX", "DOT", "CAKE", "STPT", "SCR", "NEAR", "AUDIO", "WLD", "ETHFI", "DGB", "WING", "AI", "BTTC", "JTO", "SFP", "DIA", "JUP", "BEL", "JUV", "WOO", "BLUR",
                ]
def update_symbols():

    from src.market.models import Symbol
    symbols = Symbol.objects.all()
    for symbol in symbols:
        symbol.active = False if symbol.ticker not in currencies else True
        symbol.save()
    print("Symbols updated successfully!")


def run():
    update_symbols()