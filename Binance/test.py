import ccxt
import module

binance = ccxt.binance()

ohlcvs = binance.fetch_ohlcv("BTC/USDT", "1h", limit=200)
print(type(module.get_ccxt_rsi(ohlcvs)))