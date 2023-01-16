import ccxt
import time
import datetime
import statistics
import logging
from playsound import playsound
"""
Binance/vol_scan.py
* Date: 2023. 1. 16.
* Author: Jeon Won
* Func: Binance 가상화폐의 거래량을 일정 간격 동안 스캔하여 거래량이 기준 이상 터졌을 때 알림
* Usage: 설정 값 입력 후 `python3 vol_scan.py` 명령어 실행
"""

TICKER = "BTC/USDT" # 거래량을 탐지할 바이낸스 거래소 Ticker
INTERVAL = "15m"    # 캔들 유형
COUNT = 60          # 최근 탐지한 거래랑 몇 건으로 평균을 계산할 것인가?
VOL_MEAN = 10       # 거래량 평균 몇 배 이상 시 알림을 줄 것인가?
SLEEP_TIME = 3      # 탐지 간격(초)
IS_ALARM = True     # 소리 알림 여부
IS_LOGGING = True   # 로그 기록 여부

# 로그 설정
if(IS_LOGGING):
  log_path = f"./logs/{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
  logger = logging.getLogger(__name__)
  streamHandler = logging.StreamHandler()
  fileHandler = logging.FileHandler(log_path)
  logger.addHandler(streamHandler)
  logger.addHandler(fileHandler)
  logger.setLevel(level=logging.INFO)

# 초기화
binance = ccxt.binance()
ohlcv = binance.fetch_ohlcv(TICKER, INTERVAL, limit=1) # 시가, 고가, 저자, 종가, 거래량(Open, High, Low, Close, Volume) 얻어오기
price_old = ohlcv[0][4]
vol_old = ohlcv[0][5]
vol_list = [] # 스캔한 거래량을 COUNT개 만큼 저장할 리스트

print(f"Binance {TICKER} {INTERVAL} 캔들 거래량을 {SLEEP_TIME}초 간격으로 탐지합니다.")
print(f"거래량이 평균 대비 {VOL_MEAN}배 터지면 알림이 발생합니다.")
print("출력 값은 '날짜시간: SLEEP_TIME초간_발생한_거래량 (가격변동율) / 최근_COUNT건의_평균거래량' 입니다.")

while True:
  # 현재 가격과 거래량 얻어오기
  ohlcv = binance.fetch_ohlcv(TICKER, INTERVAL, limit=1)
  price_new = ohlcv[0][4]
  vol_new = ohlcv[0][5]

  #  가격 증감분 및 거래량 증가분 계산
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
  
  ## 거래량 증가분이 거래량 증가분 평균보다 VOL_MEAN배 높으면 🌟을 붙이고 알람 처리
  msg_star = "🌟" if vol_diff >= vol_mean * VOL_MEAN else ""
  if(IS_ALARM and msg_star == "🌟"):
    playsound("alarm.mp3")

  ## 메시지 & 로그 형식: [현재시간: 거래량_증가분 (가격_증감분) / 거래량_증가분_평균 (🌟)]
  message = f"{current_time}: {vol_diff} ({price_per}%) / {vol_mean} {msg_star}"
  if(IS_LOGGING):
    logger.info(message)
  else:
    print(message)

  # 현재 가격 및 거래량을 Old 변수에 대입
  price_old = price_new
  vol_old = vol_new

  time.sleep(SLEEP_TIME)