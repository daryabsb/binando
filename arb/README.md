# Binance Arbitrator

This bot is meant to trade **triangular arbitrage** on **binance**. Using the binance websocket api to retrieve data, it's pretty fast and executes trades at the blink of an eye. Nevertheless I didn't managed this to be profitable, as it's still to slow to take advantage of triangular arbitrage opportunities. Maybe with a good server location and low latency connection this could be profitable.

**Use at your own risk. I'm not responsible for any losses and/or  damage caused by this code**






## How it works

The script tracks the prices of each altcoin on the USDT **and**  the BTC market. If it detects a difference, greater than the cumulated trading fee, it buys altcoins on the cheaper market and sells on the more expensive. Below both possibilities are visualized:

![Triangular Arbitrage](https://github.com/georgk10/BinanceTriArb/blob/master/TriArb.PNG)

## Dependencies

This Bot is written and tested in Python3.6. It depends on websockets & python-binance modules. You can install these dependencies by navigating to the project folder and typing: 
>pip install -r requirements.txt 

## Setup

1. Download this repo
2. Create an Binance account
3. Make sure to have at least 10 USDT in your binance account
4. Create an api key and write down both (the public and secret) keys
5. Put your api keys inside the config.json file
6. (Optionally) adjust the maximum trade amount (in USDT) in config.json
7. (Optionally) adjust the tradable currencies in config.json - Note that a currencies must be available to trade on **both the USDT and BTC** markets, in order to be traded.
8. Start bnArb.py 


##

