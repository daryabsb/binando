from src.services.bnArb import BnArber
from src.services.config import data
import asyncio


async def main():
    try:

        bn = BnArber(
            data["currencies"],
            # data["public"],
            # data["secret"],
            data["max_amount"]
        )
        await bn.run()
    except Exception as e:
        print(f"Error in main: {e}")


def run():
    # Use this approach for Python 3.7+
    while True:
        asyncio.run(main())
