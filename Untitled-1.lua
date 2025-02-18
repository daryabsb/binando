CAKEUSDT: HOLD Signal logged
SMAs -1 = short: 0.08753200000000001 vs long: 0.087361
SMAs -2 = short: 0.08749200000000001 vs long: 0.087345
STPTUSDT: HOLD Signal logged
SMAs -1 = short: 0.6166 vs long: 0.6186000000000003
SMAs -2 = short: 0.6166 vs long: 0.6189500000000002
SCRUSDT: HOLD Signal logged
SMAs -1 = short: 3.2376000000000005 vs long: 3.25135
SMAs -2 = short: 3.238200000000001 vs long: 3.2534
NEARUSDT: HOLD Signal logged
SMAs -1 = short: 0.1001 vs long: 0.10028499999999999
SMAs -2 = short: 0.1001 vs long: 0.10031499999999999
AUDIOUSDT: HOLD Signal logged
SMAs -1 = short: 1.1804000000000001 vs long: 1.18665
SMAs -2 = short: 1.1806 vs long: 1.1875
WLDUSDT: HOLD Signal logged
SMAs -1 = short: 1.1104 vs long: 1.1173000000000002
SMAs -2 = short: 1.1112000000000002 vs long: 1.1182500000000002
ETHFIUSDT: HOLD Signal logged
SMAs -1 = short: 0.00843 vs long: 0.008494
SMAs -2 = short: 0.008438 vs long: 0.008499999999999999
DGBUSDT: HOLD Signal logged
SMAs -1 = short: 3.6136 vs long: 3.621350000000001
SMAs -2 = short: 3.6152 vs long: 3.621950000000001
WINGUSDT: HOLD Signal logged
SMAs -1 = short: 0.26216000000000006 vs long: 0.26308000000000004
SMAs -2 = short: 0.26228 vs long: 0.263245
AIUSDT: HOLD Signal logged
SMAs -1 = short: 0.033786 vs long: 0.0338135
SMAs -2 = short: 0.033788 vs long: 0.03381750000000001
JSTUSDT: HOLD Signal logged
SMAs -1 = short: 0.001585 vs long: 0.0015910999999999998
SMAs -2 = short: 0.0015846 vs long: 0.0015921999999999998
HOTUSDT: HOLD Signal logged
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "C:\api\binando\XAI\sma.py", line 85, in <module>
    main()
  File "C:\api\binando\XAI\sma.py", line 69, in main
    df = fetch_klines(symbol, interval)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\api\binando\XAI\sma.py", line 24, in fetch_klines
    klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\api\binando\venv\Lib\site-packages\binance\client.py", line 693, in get_kline
    return self._get("klines", data=params, version=self.PRIVATE_API_VERSION)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\api\binando\venv\Lib\site-packages\binance\client.py", line 176, in _get
    return self._request_api("get", path, signed, version, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\api\binando\venv\Lib\site-packages\binance\client.py", line 113, in _request_
    return self._request(method, uri, signed, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\api\binando\venv\Lib\site-packages\binance\client.py", line 89, in _request
    return self._handle_response(self.response)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\api\binando\venv\Lib\site-packages\binance\client.py", line 98, in _handle_re
    raise BinanceAPIException(response, response.status_code, response.text)
binance.exceptions.BinanceAPIException: APIError(code=-1121): Invalid symbol.
(venv) 
darya@DARYA-HOME-DELL MINGW64 /c/api/binando (main)
$ python -m XAI.sma
SMAs -1 = short: 0.51496 vs long: 0.5120250000000001
SMAs -2 = short: 0.5158 vs long: 0.5115800000000001
BURGERUSDT: HOLD Signal logged
SMAs -1 = short: 0.00161808 vs long: 0.0016254750000000001
SMAs -2 = short: 0.0016181000000000001 vs long: 0.00162654
1MBABYDOGEUSDT: HOLD Signal logged
SMAs -1 = short: 0.254872 vs long: 0.25537899999999997
SMAs -2 = short: 0.25488600000000006 vs long: 0.25548000000000004
DOGEUSDT: HOLD Signal logged
SMAs -1 = short: 9.61e-06 vs long: 9.61e-06
SMAs -2 = short: 9.61e-06 vs long: 9.61e-06
PEPEUSDT: HOLD Signal logged
SMAs -1 = short: 0.04811 vs long: 0.04821399999999999
SMAs -2 = short: 0.04811 vs long: 0.04822399999999999
TFUELUSDT: HOLD Signal logged
SMAs -1 = short: 17.022000000000002 vs long: 17.099500000000003
SMAs -2 = short: 17.028 vs long: 17.110000000000003
TRUMPUSDT: HOLD Signal logged
SMAs -1 = short: 6.089000000000001e-05 vs long: 2.9397000000000003e-05
SMAs -2 = short: 6.089000000000001e-05 vs long: 2.7147500000000004e-05
SHIBUSDT: HOLD Signal logged
SMAs -1 = short: 2.62662 vs long: 2.625365
SMAs -2 = short: 2.6263199999999998 vs long: 2.6259799999999998
XRPUSDT: HOLD Signal logged
SMAs -1 = short: 26.796000000000003 vs long: 26.915499999999994
SMAs -2 = short: 26.812000000000005 vs long: 26.932999999999996
ENSUSDT: HOLD Signal logged
SMAs -1 = short: 0.393 vs long: 0.39520000000000005
SMAs -2 = short: 0.393 vs long: 0.3954000000000001
MANTAUSDT: HOLD Signal logged
SMAs -1 = short: 0.0034554000000000004 vs long: 0.0034675500000000002
SMAs -2 = short: 0.0034542000000000006 vs long: 0.0034687000000000003
TURBOUSDT: HOLD Signal logged
SMAs -1 = short: 3.1595000000000004 vs long: 3.1754800000000003
SMAs -2 = short: 3.16094 vs long: 3.17746
SUIUSDT: HOLD Signal logged
SMAs -1 = short: 120.97800000000001 vs long: 120.9195
SMAs -2 = short: 120.97800000000001 vs long: 120.9285
LTCUSDT: HOLD Signal logged
SMAs -1 = short: 0.8732 vs long: 0.8710100000000001
SMAs -2 = short: 0.8728800000000001 vs long: 0.8712500000000002
BNXUSDT: HOLD Signal logged
SMAs -1 = short: 0.23987999999999998 vs long: 0.24006000000000002
SMAs -2 = short: 0.23987999999999998 vs long: 0.24009500000000003
TRXUSDT: HOLD Signal logged
SMAs -1 = short: 4.8318 vs long: 4.8443000000000005
SMAs -2 = short: 4.8324 vs long: 4.846500000000001
DOTUSDT: HOLD Signal logged
SMAs -1 = short: 2.6271999999999998 vs long: 2.6342000000000003
SMAs -2 = short: 2.628 vs long: 2.6355000000000004
CAKEUSDT: HOLD Signal logged
SMAs -1 = short: 0.087566 vs long: 0.08737649999999998
SMAs -2 = short: 0.08753200000000001 vs long: 0.087361
STPTUSDT: HOLD Signal logged
SMAs -1 = short: 0.6164000000000001 vs long: 0.6182000000000002
SMAs -2 = short: 0.6166 vs long: 0.6186000000000003
SCRUSDT: HOLD Signal logged
SMAs -1 = short: 3.2366000000000006 vs long: 3.24955
SMAs -2 = short: 3.2376000000000005 vs long: 3.25135
NEARUSDT: HOLD Signal logged
SMAs -1 = short: 0.1001 vs long: 0.10025499999999998
SMAs -2 = short: 0.1001 vs long: 0.10028499999999999
AUDIOUSDT: HOLD Signal logged
SMAs -1 = short: 1.1802 vs long: 1.1857499999999999
SMAs -2 = short: 1.1804000000000001 vs long: 1.18665
WLDUSDT: HOLD Signal logged
SMAs -1 = short: 1.1096 vs long: 1.1163500000000002
SMAs -2 = short: 1.1104 vs long: 1.1173000000000002
ETHFIUSDT: HOLD Signal logged
SMAs -1 = short: 0.008424 vs long: 0.008487999999999999
SMAs -2 = short: 0.00843 vs long: 0.008494
DGBUSDT: HOLD Signal logged
SMAs -1 = short: 3.612 vs long: 3.620750000000001
SMAs -2 = short: 3.6136 vs long: 3.621350000000001
WINGUSDT: HOLD Signal logged
SMAs -1 = short: 0.2622 vs long: 0.262955
SMAs -2 = short: 0.26222 vs long: 0.263095
AIUSDT: HOLD Signal logged
SMAs -1 = short: 0.033788 vs long: 0.03381049999999999
SMAs -2 = short: 0.033788 vs long: 0.033814
JSTUSDT: HOLD Signal logged
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "C:\api\binando\XAI\sma.py", line 85, in <module>
    main()
  File "C:\api\binando\XAI\sma.py", line 69, in main
    df = fetch_klines(symbol, interval)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\api\binando\XAI\sma.py", line 24, in fetch_klines
    klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\api\binando\venv\Lib\site-packages\binance\client.py", line 693, in get_kline
    return self._get("klines", data=params, version=self.PRIVATE_API_VERSION)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\api\binando\venv\Lib\site-packages\binance\client.py", line 176, in _get
    return self._request_api("get", path, signed, version, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\api\binando\venv\Lib\site-packages\binance\client.py", line 113, in _request_
    return self._request(method, uri, signed, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\api\binando\venv\Lib\site-packages\binance\client.py", line 89, in _request
    return self._handle_response(self.response)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\api\binando\venv\Lib\site-packages\binance\client.py", line 98, in _handle_re
    raise BinanceAPIException(response, response.status_code, response.text)
binance.exceptions.BinanceAPIException: APIError(code=-1121): Invalid symbol.
(venv) 
darya@DARYA-HOME-DELL MINGW64 /c/api/binando (main)
$ python -m XAI.sma
BURGERUSDT: HOLD Signal logged
1MBABYDOGEUSDT: HOLD Signal logged
DOGEUSDT: HOLD Signal logged
PEPEUSDT: HOLD Signal logged
TFUELUSDT: HOLD Signal logged
TRUMPUSDT: HOLD Signal logged
SHIBUSDT: HOLD Signal logged
XRPUSDT: HOLD Signal logged
ENSUSDT: HOLD Signal logged
MANTAUSDT: HOLD Signal logged
TURBOUSDT: HOLD Signal logged
SUIUSDT: HOLD Signal logged
LTCUSDT: HOLD Signal logged
BNXUSDT: HOLD Signal logged
TRXUSDT: HOLD Signal logged
DOTUSDT: HOLD Signal logged
CAKEUSDT: HOLD Signal logged
STPTUSDT: HOLD Signal logged
SCRUSDT: HOLD Signal logged
NEARUSDT: HOLD Signal logged
AUDIOUSDT: HOLD Signal logged
WLDUSDT: HOLD Signal logged
ETHFIUSDT: HOLD Signal logged
DGBUSDT: HOLD Signal logged
WINGUSDT: HOLD Signal logged
AIUSDT: HOLD Signal logged
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "C:\api\binando\XAI\sma.py", line 80, in <module>
    main()
  File "C:\api\binando\XAI\sma.py", line 64, in main
    df = fetch_klines(symbol, interval)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\api\binando\XAI\sma.py", line 24, in fetch_klines
    klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\api\binando\venv\Lib\site-packages\binance\client.py", line 693, in get_kline
    return self._get("klines", data=params, version=self.PRIVATE_API_VERSION)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\api\binando\venv\Lib\site-packages\binance\client.py", line 176, in _get
    return self._request_api("get", path, signed, version, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\api\binando\venv\Lib\site-packages\binance\client.py", line 113, in _request_
    return self._request(method, uri, signed, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\api\binando\venv\Lib\site-packages\binance\client.py", line 89, in _request
    return self._handle_response(self.response)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\api\binando\venv\Lib\site-packages\binance\client.py", line 98, in _handle_re
    raise BinanceAPIException(response, response.status_code, response.text)
binance.exceptions.BinanceAPIException: APIError(code=-1121): Invalid symbol.
(venv) 
darya@DARYA-HOME-DELL MINGW64 /c/api/binando (main)
$ python -m XAI.sma
BURGERUSDT: SELL Signal logged
An error occurred - APIError(code=-1013): Filter failure: LOT_SIZE
1MBABYDOGEUSDT: HOLD Signal logged
DOGEUSDT: HOLD Signal logged
PEPEUSDT: HOLD Signal logged
TFUELUSDT: HOLD Signal logged
TRUMPUSDT: HOLD Signal logged
SHIBUSDT: HOLD Signal logged
XRPUSDT: HOLD Signal logged
ENSUSDT: HOLD Signal logged
MANTAUSDT: HOLD Signal logged
TURBOUSDT: HOLD Signal logged
SUIUSDT: HOLD Signal logged
LTCUSDT: HOLD Signal logged
BNXUSDT: HOLD Signal logged
TRXUSDT: HOLD Signal logged
DOTUSDT: HOLD Signal logged
CAKEUSDT: HOLD Signal logged
STPTUSDT: HOLD Signal logged
SCRUSDT: HOLD Signal logged
NEARUSDT: HOLD Signal logged
AUDIOUSDT: HOLD Signal logged
WLDUSDT: HOLD Signal logged
ETHFIUSDT: HOLD Signal logged
DGBUSDT: HOLD Signal logged
WINGUSDT: HOLD Signal logged
AIUSDT: HOLD Signal logged
⚠️ Error in the loop BABYSORA2USD: APIError(code=-1121): Invalid symbol.
⚠️ Error in the loop BENCOUSD: APIError(code=-1121): Invalid symbol.
⚠️ Error in the loop WAGGUSD: APIError(code=-1121): Invalid symbol.
BTTCUSDT: HOLD Signal logged
JTOUSDT: HOLD Signal logged
SFPUSDT: HOLD Signal logged
DIAUSDT: HOLD Signal logged
JUPUSDT: HOLD Signal logged
BELUSDT: HOLD Signal logged
JUVUSDT: HOLD Signal logged
WOOUSDT: HOLD Signal logged
BLURUSDT: HOLD Signal logged
STRKUSDT: HOLD Signal logged
DFUSDT: HOLD Signal logged
FLOKIUSDT: HOLD Signal logged
⚠️ Error in the loop SANDUSDT: HTTPSConnectionPool(host='testnet.binance.vision', port=44
read timeout=10)
SCRTUSDT: HOLD Signal logged
COOKIEUSDT: BUY Signal logged
⚠️ Error in the loop COOKIEUSDT: HTTPSConnectionPool(host='testnet.binance.vision', port=
 (read timeout=10)
HARDUSDT: HOLD Signal logged
UNIUSDT: HOLD Signal logged
SYNUSDT: HOLD Signal logged
⚠️ Error in the loop OCBOUSD: APIError(code=-1121): Invalid symbol.
⚠️ Error in the loop OMUSD: APIError(code=-1121): Invalid symbol.
⚠️ Error in the loop FARTCOINUSD: APIError(code=-1121): Invalid symbol.
BURGERUSDT: HOLD Signal logged
1MBABYDOGEUSDT: HOLD Signal logged
DOGEUSDT: HOLD Signal logged
PEPEUSDT: HOLD Signal logged
⚠️ Error in the loop TFUELUSDT: HTTPSConnectionPool(host='testnet.binance.vision', port=4
(read timeout=10)
TRUMPUSDT: HOLD Signal logged
SHIBUSDT: HOLD Signal logged
XRPUSDT: HOLD Signal logged
ENSUSDT: HOLD Signal logged
MANTAUSDT: HOLD Signal logged
⚠️ Error in the loop TURBOUSDT: HTTPSConnectionPool(host='testnet.binance.vision', port=4
(read timeout=10)
SUIUSDT: HOLD Signal logged
LTCUSDT: HOLD Signal logged
BNXUSDT: HOLD Signal logged
TRXUSDT: HOLD Signal logged
DOTUSDT: HOLD Signal logged
CAKEUSDT: BUY Signal logged
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "C:\api\binando\XAI\sma.py", line 84, in <module>
    main()
  File "C:\api\binando\XAI\sma.py", line 70, in main
    execute_trade(symbol, SIDE_BUY)
  File "C:\api\binando\XAI\sma.py", line 45, in execute_trade
    usdt_balance = get_usdt_balance(client)
                   ^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\api\binando\bot\coins.py", line 115, in get_usdt_balance
    balance = client.get_asset_balance(asset="USDT")
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\api\binando\venv\Lib\site-packages\binance\client.py", line 2059, in get_asse
    res = self.get_account(**params)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\api\binando\venv\Lib\site-packages\binance\client.py", line 2036, in get_acco
    return self._get("account", True, data=params)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\api\binando\venv\Lib\site-packages\binance\client.py", line 176, in _get
    return self._request_api("get", path, signed, version, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\api\binando\venv\Lib\site-packages\binance\client.py", line 113, in _request_
    return self._request(method, uri, signed, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\api\binando\venv\Lib\site-packages\binance\client.py", line 88, in _request
    self.response = getattr(self.session, method)(uri, headers=headers, data=data, **kwa
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ne 667, in send
    resp = conn.urlopen(
           ^^^^^^^^^^^^^
  File "C:\api\binando\venv\Lib\site-packages\urllib3\connectionpool.py", line 787, in urlopen
    response = self._make_request(
               ^^^^^^^^^^^^^^^^^^^
  File "C:\api\binando\venv\Lib\site-packages\urllib3\connectionpool.py", line 534, in _make_request       
    response = conn.getresponse()
               ^^^^^^^^^^^^^^^^^^
  File "C:\api\binando\venv\Lib\site-packages\urllib3\connection.py", line 516, in getresponse
-8859-1")
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^      
  File "C:\Users\darya\AppData\Local\Programs\Python\Python311\Lib\http\client.py", line 1378, in getresponn\Python311\Lib\socket.py", line 706, in readinto  
    return self._sock.recv_into(b)
           ^^^^^^^^^^^^^^^^^^^^^^^                 n\Python311\Lib\http\client.py", line 318, in begin     
  File "C:\Users\darya\AppData\Local\Programs\Python\Python311\Lib\ssl.py", line 1278, in recv_into   
    return self.read(nbytes, buffer)               n\Python311\Lib\http\client.py", line 279, in _read_stat
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\darya\AppData\Local\Programs\Pytho-8859-1")n\Python311\Lib\ssl.py", line 1134, in read        
    return self._sslobj.read(len, buffer)          n\Python311\Lib\socket.py", line 706, in readinto       
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
KeyboardInterrupt
                                                   n\Python311\Lib\ssl.py", line 1278, in recv_into        
(venv)
darya@DARYA-HOME-DELL MINGW64 /c/api/binando (main)
                                                   n\Python311\Lib\ssl.py", line 1134, in read
$ python manage.py runserver
Watching for file changes with StatReloader        
Performing system checks...

System check identified no issues (0 silenced).    
February 17, 2025 - 21:48:33
Django version 5.1.6, using settings 'src.settings'

Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
0/
Quit the server with CTRL-BREAK.

(venv)
darya@DARYA-HOME-DELL MINGW64 /c/api/binando (main)
$ python -m strategy.test
🔄 Starting background cache update thread...
⏳ Trading bot started...
⚠️ No coins found. Skipping trades...
⏳ Waiting 1 hour before checking again...
⏳ Trading bot started...
⚠️ No coins found. Skipping trades...
⏳ Waiting 1 hour before checking again...
⏳ Trading bot started...
⚠️ No coins found. Skipping trades...
⏳ Waiting 1 hour before checking again...
⚠️ Skipping BABYSORA2USD: APIError(code=-1121): Invalid symbol.
⚠️ Skipping BENCOUSD: APIError(code=-1121): Invalid symbol.
⚠️ Skipping WAGGUSD: APIError(code=-1121): Invalid symbol.
⏳ Trading bot started...
⚠️ No coins found. Skipping trades...
⏳ Waiting 1 hour before checking again...
⏳ Trading bot started...
⚠️ No coins found. Skipping trades...
⏳ Waiting 1 hour before checking again...
⚠️ Skipping OCBOUSD: APIError(code=-1121): Invalid symbol.
⚠️ Skipping OMUSD: APIError(code=-1121): Invalid symbol.
⚠️ Skipping FARTCOINUSD: APIError(code=-1121): Invalid symbol.
✅ Cached sorted symbols updated!
⏳ Trading bot started...
🔹 XRPUSDT | ROC: -4.86% | Price: 2.5775
📈 SKIP-BUY: XRPUSDT | ROC: -4.89% | Price: 2.56800000
🔄 Selling XRPUSDT | ROC Change: -5.21%.
✅ Selling XRPUSDT | ROC: -4.86% | Price: 2.5775 | Trend: 🔻 Strong Downtrend
🔹 Placing SELL order for XRPUSDT | Quantity: 4.87500000
🚨 Stop-loss: 2.62905000 | 🎯 Take-profit: 2.50017500
price: 2.57589999999999985647036737645976245403289794921875 | total_value: 12.55751249999999930029304096   
✅ Final Order Details: SELL XRPUSDT | Quantity: 4.00000000 | Price: 2.5758999999999998564703673764597624540  Selling XRPUSDT | ROC Change: -5.21%.
3289794921875 | Total: 10.30359999999999942588146951
✅ SELL Order placed for XRPUSDT: 4.00000000
🔹 SUIUSDT | ROC: -6.75% | Price: 3.1068
✅ Buying SUIUSDT based on ROC drop of -7.24%.
✅ Buying SUIUSDT | ROC: -6.75% | Price: 3.1068 | Trend: 🔥 Strong Uptrend
🔹 Placing BUY order for SUIUSDT | Quantity: 4.04452210
🚨 Stop-loss: 3.04466400 | 🎯 Take-profit: 3.20000400
price: 3.090599999999999791810978422290645539760589599609375 | total_value: 12.50000000225999915797490125
✅ Final Order Details: BUY SUIUSDT | Quantity: 4.00000000 | Price: 3.09059999999999979181097842229064553976
0589599609375 | Total: 12.36239999999999916724391369
✅ BUY Order placed for SUIUSDT: 4.00000000
🔹 LTCUSDT | ROC: 1.73% | Price: 125.78
📈 SKIP-BUY: LTCUSDT | ROC: 1.57% | Price: 126.01000000
📈 SKIP-SELL: LTCUSDT | ROC: 1.57% | Price: 126.01000000
🔹 BNXUSDT | ROC: -0.63% | Price: 0.9268
📈 SKIP-BUY: BNXUSDT | ROC: -0.38% | Price: 0.92920000
📈 SKIP-SELL: BNXUSDT | ROC: -0.38% | Price: 0.92920000
🔹 JUPUSDT | ROC: -14.33% | Price: 0.7156
✅ Buying JUPUSDT based on ROC drop of -14.43%.
✅ Buying JUPUSDT | ROC: -14.33% | Price: 0.7156 | Trend: 🔥 Strong Uptrend
🔹 Placing BUY order for JUPUSDT | Quantity: 17.51681615
🚨 Stop-loss: 0.70128800 | 🎯 Take-profit: 0.73706800
price: 0.713600000000000012079226507921703159809112548828125 | total_value: 12.50000000464000021158958997
✅ Final Order Details: BUY JUPUSDT | Quantity: 17.50000000 | Price: 0.7136000000000000120792265079217031598
09112548828125 | Total: 12.48800000000000021138646389
✅ BUY Order placed for JUPUSDT: 17.50000000
🔹 DOTUSDT | ROC: -5.56% | Price: 4.742
✅ Buying DOTUSDT based on ROC drop of -5.52%.
✅ Buying DOTUSDT | ROC: -5.56% | Price: 4.742 | Trend: 🔥 Strong Uptrend
🔹 Placing BUY order for DOTUSDT | Quantity: 2.63880093
🚨 Stop-loss: 4.64716000 | 🎯 Take-profit: 4.88426000
price: 4.73500000000000031974423109204508364200592041015625 | total_value: 12.49472240355000084374137437
✅ Final Order Details: BUY DOTUSDT | Quantity: 2.63000000 | Price: 4.73500000000000031974423109204508364200
592041015625 | Total: 12.45305000000000084092732777
✅ BUY Order placed for DOTUSDT: 2.63000000
🔹 UNIUSDT | ROC: -6.01% | Price: 9.559
✅ Buying UNIUSDT based on ROC drop of -5.99%.
✅ Buying UNIUSDT | ROC: -6.01% | Price: 9.559 | Trend: 🔥 Strong Uptrend
🔹 Placing BUY order for UNIUSDT | Quantity: 1.30725790
🚨 Stop-loss: 9.36782000 | 🎯 Take-profit: 9.84577000
price: 9.5619999999999993889332472463138401508331298828125 | total_value: 12.50000003979999920117816004
✅ Final Order Details: BUY UNIUSDT | Quantity: 1.30000000 | Price: 9.56199999999999938893324724631384015083
31298828125 | Total: 12.43059999999999920561322142
✅ BUY Order placed for UNIUSDT: 1.30000000
🔹 NEARUSDT | ROC: -9.50% | Price: 3.144
✅ Buying NEARUSDT based on ROC drop of -9.44%.
✅ Buying NEARUSDT | ROC: -9.50% | Price: 3.144 | Trend: 🔥 Strong Uptrend
🔹 Placing BUY order for NEARUSDT | Quantity: 3.97329943
🚨 Stop-loss: 3.08112000 | 🎯 Take-profit: 3.23832000
price: 3.14599999999999990762944435118697583675384521484375 | total_value: 12.50000000677999963298412389
✅ Final Order Details: BUY NEARUSDT | Quantity: 3.90000000 | Price: 3.1459999999999999076294443511869758367
5384521484375 | Total: 12.26939999999999963975483297
✅ BUY Order placed for NEARUSDT: 3.90000000
🔹 STPTUSDT | ROC: -0.21% | Price: 0.08658
📈 SKIP-BUY: STPTUSDT | ROC: -0.48% | Price: 0.08634000
📈 SKIP-SELL: STPTUSDT | ROC: -0.48% | Price: 0.08634000
🔹 DOGEUSDT | ROC: -5.74% | Price: 0.25175
✅ Buying DOGEUSDT based on ROC drop of -6.17%.
✅ Buying DOGEUSDT | ROC: -5.74% | Price: 0.25175 | Trend: 🔥 Strong Uptrend
🔹 Placing BUY order for DOGEUSDT | Quantity: 49.89223278
🚨 Stop-loss: 0.24671500 | 🎯 Take-profit: 0.25930250
price: 0.25053999999999998493649400188587605953216552734375 | total_value: 12.50000000070119924844805226
✅ Final Order Details: BUY DOGEUSDT | Quantity: 49.00000000 | Price: 0.250539999999999984936494001885876059
53216552734375 | Total: 12.27645999999999926188820609
✅ BUY Order placed for DOGEUSDT: 49.00000000
🔹 SANDUSDT | ROC: -10.54% | Price: 0.3657
✅ Buying SANDUSDT based on ROC drop of -10.54%.
✅ Buying SANDUSDT | ROC: -10.54% | Price: 0.3657 | Trend: 🔥 Strong Uptrend
🔹 Placing BUY order for SANDUSDT | Quantity: 34.18102270
🚨 Stop-loss: 0.35838600 | 🎯 Take-profit: 0.37667100
price: 0.36570000000000002504663143554353155195713043212890625 | total_value: 12.50000000139000085611947766✅ Final Order Details: BUY SANDUSDT | Quantity: 34.00000000 | Price: 0.365700000000000025046631435543531551
95713043212890625 | Total: 12.43380000000000085158546881
✅ BUY Order placed for SANDUSDT: 34.00000000
🔹 BURGERUSDT | ROC: -25.73% | Price: 0.386
✅ Buying BURGERUSDT based on ROC drop of -25.21%.
✅ Buying BURGERUSDT | ROC: -25.73% | Price: 0.386 | Trend: 🔥 Strong Uptrend
🔹 Placing BUY order for BURGERUSDT | Quantity: 32.15847698
🚨 Stop-loss: 0.37828000 | 🎯 Take-profit: 0.39758000
price: 0.388699999999999989963583857388584874570369720458984375 | total_value: 12.50000000212599967724414252
✅ Final Order Details: BUY BURGERUSDT | Quantity: 32.10000000 | Price: 0.3886999999999999899635838573885848
74570369720458984375 | Total: 12.47726999999999967783104182
✅ BUY Order placed for BURGERUSDT: 32.10000000
🔹 CAKEUSDT | ROC: -7.33% | Price: 2.566
✅ Buying CAKEUSDT based on ROC drop of -8.05%.
✅ Buying CAKEUSDT | ROC: -7.33% | Price: 2.566 | Trend: 🔥 Strong Uptrend
🔹 Placing BUY order for CAKEUSDT | Quantity: 4.90966222
🚨 Stop-loss: 2.51468000 | 🎯 Take-profit: 2.64298000
price: 2.545999999999999818811602381174452602863311767578125 | total_value: 12.50000001211999911042616951
✅ Final Order Details: BUY CAKEUSDT | Quantity: 4.90000000 | Price: 2.5459999999999998188116023811744526028
63311767578125 | Total: 12.47539999999999911217685167
✅ BUY Order placed for CAKEUSDT: 4.90000000
🔹 BELUSDT | ROC: -5.96% | Price: 0.8542
✅ Buying BELUSDT based on ROC drop of -5.96%.
✅ Buying BELUSDT | ROC: -5.96% | Price: 0.8542 | Trend: 🔥 Strong Uptrend
🔹 Placing BUY order for BELUSDT | Quantity: 14.63357528
🚨 Stop-loss: 0.83711600 | 🎯 Take-profit: 0.87982600
price: 0.85419999999999995932142837773426435887813568115234375 | total_value: 12.50000000417599940472705988✅ Final Order Details: BUY BELUSDT | Quantity: 14.60000000 | Price: 0.8541999999999999593214283777342643588
7813568115234375 | Total: 12.47131999999999940609285431
✅ BUY Order placed for BELUSDT: 14.60000000
🔹 DFUSDT | ROC: 2.20% | Price: 0.09169
📈 SKIP-BUY: DFUSDT | ROC: 2.28% | Price: 0.09179000
📈 SKIP-SELL: DFUSDT | ROC: 2.28% | Price: 0.09179000
🔹 AIUSDT | ROC: -9.50% | Price: 0.2553
✅ Buying AIUSDT based on ROC drop of -9.57%.
✅ Buying AIUSDT | ROC: -9.50% | Price: 0.2553 | Trend: 🔥 Strong Uptrend
🔹 Placing BUY order for AIUSDT | Quantity: 49.00039201
🚨 Stop-loss: 0.25019400 | 🎯 Take-profit: 0.26295900
price: 0.25509999999999999342747969421907328069210052490234375 | total_value: 12.50000000175099967794392852✅ Final Order Details: BUY AIUSDT | Quantity: 49.00000000 | Price: 0.25509999999999999342747969421907328069
210052490234375 | Total: 12.49989999999999967794650502
✅ BUY Order placed for AIUSDT: 49.00000000
🔹 SCRTUSDT | ROC: -8.87% | Price: 0.2364
✅ Buying SCRTUSDT based on ROC drop of -9.22%.
✅ Buying SCRTUSDT | ROC: -8.87% | Price: 0.2364 | Trend: 🔥 Strong Uptrend
🔹 Placing BUY order for SCRTUSDT | Quantity: 53.10110451
🚨 Stop-loss: 0.23167200 | 🎯 Take-profit: 0.24349200
price: 0.235399999999999998134825318629737012088298797607421875 | total_value: 12.50000000165399990095716432
✅ Final Order Details: BUY SCRTUSDT | Quantity: 53.10000000 | Price: 0.235399999999999998134825318629737012
088298797607421875 | Total: 12.49973999999999990095922442
✅ BUY Order placed for SCRTUSDT: 53.10000000
🔹 ENSUSDT | ROC: -6.77% | Price: 26.46
✅ Buying ENSUSDT based on ROC drop of -6.80%.
✅ Buying ENSUSDT | ROC: -6.77% | Price: 26.46 | Trend: 🔥 Strong Uptrend
🔹 Placing BUY order for ENSUSDT | Quantity: 0.47258980
🚨 Stop-loss: 25.93080000 | 🎯 Take-profit: 27.25380000
price: 26.449999999999999289457264239899814128875732421875 | total_value: 12.50000020999999966420475062
✅ Final Order Details: BUY ENSUSDT | Quantity: 0.47000000 | Price: 26.4499999999999992894572642398998141288
75732421875 | Total: 12.43149999999999966604491419
✅ BUY Order placed for ENSUSDT: 0.47000000
🔹 STRKUSDT | ROC: -8.77% | Price: 0.2185
✅ Buying STRKUSDT based on ROC drop of -8.89%.
✅ Buying STRKUSDT | ROC: -8.77% | Price: 0.2185 | Trend: 🔥 Strong Uptrend
🔹 Placing BUY order for STRKUSDT | Quantity: 57.28689276
🚨 Stop-loss: 0.21413000 | 🎯 Take-profit: 0.22505500
price: 0.2180999999999999883204537809433531947433948516845703125 | total_value: 12.49427131095599933091508826
✅ Final Order Details: BUY STRKUSDT | Quantity: 57.28000000 | Price: 0.218099999999999988320453780943353194
7433948516845703125 | Total: 12.49276799999999933099559257
✅ BUY Order placed for STRKUSDT: 57.28000000
🔹 JTOUSDT | ROC: -12.97% | Price: 2.543
✅ Buying JTOUSDT based on ROC drop of -12.97%.
✅ Buying JTOUSDT | ROC: -12.97% | Price: 2.543 | Trend: 🔥 Strong Uptrend
🔹 Placing BUY order for JTOUSDT | Quantity: 4.93291240
🚨 Stop-loss: 2.49214000 | 🎯 Take-profit: 2.61929000
price: 2.53399999999999980815346134477294981479644775390625 | total_value: 12.50000002159999905363783057
✅ Final Order Details: BUY JTOUSDT | Quantity: 4.90000000 | Price: 2.53399999999999980815346134477294981479
644775390625 | Total: 12.41659999999999905995196059
✅ BUY Order placed for JTOUSDT: 4.90000000
🔹 DIAUSDT | ROC: -7.13% | Price: 0.4985
✅ Buying DIAUSDT based on ROC drop of -7.13%.
✅ Buying DIAUSDT | ROC: -7.13% | Price: 0.4985 | Trend: 🔥 Strong Uptrend
🔹 Placing BUY order for DIAUSDT | Quantity: 25.07522568
🚨 Stop-loss: 0.48853000 | 🎯 Take-profit: 0.51345500
price: 0.498499999999999998667732370449812151491641998291015625 | total_value: 12.50000000147999996659308852
✅ Final Order Details: BUY DIAUSDT | Quantity: 25.00000000 | Price: 0.4984999999999999986677323704498121514
91641998291015625 | Total: 12.46249999999999996669330926
✅ BUY Order placed for DIAUSDT: 25.00000000
🔹 SYNUSDT | ROC: -16.65% | Price: 0.3414
✅ Buying SYNUSDT based on ROC drop of -16.46%.
✅ Buying SYNUSDT | ROC: -16.65% | Price: 0.3414 | Trend: 🔥 Strong Uptrend
🔹 Placing BUY order for SYNUSDT | Quantity: 36.52834600
🚨 Stop-loss: 0.33457200 | 🎯 Take-profit: 0.35164200
price: 0.342200000000000004174438572590588591992855072021484375 | total_value: 12.50000000120000015248533654
✅ Final Order Details: BUY SYNUSDT | Quantity: 36.50000000 | Price: 0.3422000000000000041744385725905885919
92855072021484375 | Total: 12.49030000000000015236700790
✅ BUY Order placed for SYNUSDT: 36.50000000
🔹 ETHFIUSDT | ROC: -8.14% | Price: 1.094
✅ Buying ETHFIUSDT based on ROC drop of -8.40%.
✅ Buying ETHFIUSDT | ROC: -8.14% | Price: 1.094 | Trend: 🔥 Strong Uptrend
🔹 Placing BUY order for ETHFIUSDT | Quantity: 11.45737856
🚨 Stop-loss: 1.07212000 | 🎯 Take-profit: 1.12682000
price: 1.0909999999999999698019337301957421004772186279296875 | total_value: 12.50000000895999965400932297
✅ Final Order Details: BUY ETHFIUSDT | Quantity: 11.40000000 | Price: 1.09099999999999996980193373019574210
04772186279296875 | Total: 12.43739999999999965574204452
✅ BUY Order placed for ETHFIUSDT: 11.40000000
🔹 COOKIEUSDT | ROC: -10.84% | Price: 0.1817
✅ Buying COOKIEUSDT based on ROC drop of -11.09%.
✅ Buying COOKIEUSDT | ROC: -10.84% | Price: 0.1817 | Trend: 🔥 Strong Uptrend
🔹 Placing BUY order for COOKIEUSDT | Quantity: 68.98454747
🚨 Stop-loss: 0.17806600 | 🎯 Take-profit: 0.18715100
price: 0.1811999999999999999555910790149937383830547332763671875 | total_value: 12.50000000156399999693647068
✅ Final Order Details: BUY COOKIEUSDT | Quantity: 68.90000000 | Price: 0.1811999999999999999555910790149937
383830547332763671875 | Total: 12.48467999999999999694022534
✅ BUY Order placed for COOKIEUSDT: 68.90000000
🔹 WLDUSDT | ROC: -10.13% | Price: 1.135