import ccxt
import time
import datetime
import statistics
import logging
"""
Binance/vol_scan.py
대충 만드는 중...
"""

COLOR_RED = '\033[91m'
COLOR_GREEN = '\033[92m'
COLOR_END = '\033[0m'
LOG_PATH = f"./logs/{datetime.datetime.now().strftime('%Y%m%d%_H%M%S')}.log"
TICKER = "BTC/USDT" # 거래량을 탐지할 바이낸스 거래소 Ticker
INTERVAL = "15m"    # 캔들 유형
COUNT = 60          # 거래량 평균
VOL_MEAN = 10       # 거래량 평균 몇 배 이상 시...
SLEEP_TIME = 1      # 탐지 간격(초)

binance = ccxt.binance()
vol_list = []

# 로그 설정
logger = logging.getLogger(__name__)
streamHandler = logging.StreamHandler()
fileHandler = logging.FileHandler(LOG_PATH)
logger.addHandler(streamHandler)
logger.addHandler(fileHandler)
logger.setLevel(level=logging.INFO)

# 초기화
ohlcv = binance.fetch_ohlcv(TICKER, INTERVAL, limit=1)
price_old = ohlcv[0][4]
vol_old = ohlcv[0][5]

print(f"Binance {TICKER} {INTERVAL} 거래량 탐지...")

while True:
  # 현재 가격과 거래량 얻어오기
  ohlcv = binance.fetch_ohlcv(TICKER, INTERVAL, limit=1)
  price_new = ohlcv[0][4]
  vol_new = ohlcv[0][5]

  # 거래량 증가분 및 가격 증감분 계산
  price_diff = price_new - price_old
  vol_diff = round(vol_new - vol_old, 2)
  if(vol_diff < 0):
    vol_diff = round(vol_new, 2)

  # 거래량 증가분 평균 계산
  if(len(vol_list) >= COUNT):
    del vol_list[0]
  vol_list.append(vol_diff)
  vol_mean = round(statistics.mean(vol_list), 2)

  # 메시지 및 로그 생성
  current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
  price_per = round((ohlcv[0][4] - ohlcv[0][1]) / ohlcv[0][1] * 100, 2)
  msg_price_per = f"{COLOR_GREEN}({price_per}%){COLOR_END}" if price_per >= 0 else f"{COLOR_RED}({price_per}%){COLOR_END}"
  ## 거래량 증가분이 거래량 증가분 평균보다 VOL_MEAN배 높으면 🌟을 붙임
  msg_star = "🌟" if vol_diff >= vol_mean * VOL_MEAN else ""
  ## 메시지 형식: [현재시간: 거래량_증가분 (가격_증감분) / 거래량_증가분_평균 (🌟)]
  message = f"{current_time}: {vol_diff} {msg_price_per} / {vol_mean} {msg_star}"
  logger.info(message)

  # 현재 가격 및 거래량을 직전 변수에 대입
  price_old = price_new
  vol_old = vol_new

  time.sleep(SLEEP_TIME)