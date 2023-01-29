import ccxt
import telegram
import time
import datetime
import os
import logging
import threading
from playsound import playsound
from dotenv import load_dotenv
"""
Binance/vol_val_scan.py
* Date: 2023. 1. 16.
* Author: Jeon Won
* Func: Binance 가상화폐의 거래량을 일정 시간(간격) 동안 스캔하여 거래량이 기준치 이상 터졌을 때 알림
* Usage: 설정 값 입력 후 `python3 vol_scan.py` 명령어 실행
"""

# 상승(GREEN) 및 하락(RED) 색상 표시를 위한 클래스
class Colors:
  RED = '\033[31m'
  GREEN = '\033[32m'
  RESET = '\033[0m'

# 대충 상수...
load_dotenv()
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")      ## 텔레그렘 봇 토큰
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")  ## 텔레그램 봇 아이디
TICKER = "BTC/USDT"    ## 거래량을 탐지할 바이낸스 거래소 Ticker
INTERVAL = "15m"       ## 캔들 유형
SLEEP_TIME = 1         ## 탐지 간격(초)
VOL_STANDARD = 100     ## 거래량 기준치(거래량이 얼마 이상 발생했을 때 알림을 줄 것인가?)
IS_ALARMING = True     ## 소리 알림 여부
IS_TELEGRAMING = False ## 텔레그램 알림 여부
IS_LOGGING = True      ## 로그 기록 여부

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
bot = telegram.Bot(TELEGRAM_TOKEN)
binance = ccxt.binance()
ohlcv = binance.fetch_ohlcv(TICKER, INTERVAL, limit=1) ## 시가, 고가, 저자, 종가, 거래량(Open, High, Low, Close, Volume) 얻어오기
price_old = ohlcv[0][4]
vol_old = ohlcv[0][5]

print(f"Binance {TICKER} {INTERVAL} 캔들 거래량을 {SLEEP_TIME}초 간격으로 탐지합니다.")
print(f"거래량이 {SLEEP_TIME}초간 {VOL_STANDARD}개 이상 발생하면 알림이 발생합니다.")

while True:
  try: 
    # 현재 가격과 거래량 얻어오기
    ohlcv = binance.fetch_ohlcv(TICKER, INTERVAL, limit=1)
    price_new = ohlcv[0][4]
    vol_new = ohlcv[0][5]

    # 가격 증감분 및 거래량 증가분 계산
    price_diff = price_new - price_old
    vol_diff = round(vol_new - vol_old, 2)
    if(vol_diff < 0):
      vol_diff = round(vol_new)

    # 푸시 알림용 메시지 생성: 상승(GREEN) 및 하락(RED) 색상 표시하지 않음
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    price_per = round((ohlcv[0][4] - ohlcv[0][1]) / ohlcv[0][1] * 100, 2)
    push_msg = f"{current_time} {TICKER} {INTERVAL} {SLEEP_TIME}초간 발생한 거래량: {vol_diff} ({price_per}%)"

    # 콘솔 출력용 메시지 생성: 상승(GREEN) 및 < 하락(RED) 색상 표시
    if(price_diff > 0):
      console_msg = f"{current_time} {TICKER} {INTERVAL} {SLEEP_TIME}초간 발생한 거래량: {Colors.GREEN}{vol_diff} ({price_per}%){Colors.RESET}"
    elif(price_diff < 0):
      console_msg = f"{current_time} {TICKER} {INTERVAL} {SLEEP_TIME}초간 발생한 거래량: {Colors.RED}{vol_diff} ({price_per}%){Colors.RESET}"
    else:
      console_msg = f"{current_time} {TICKER} {INTERVAL} {SLEEP_TIME}초간 발생한 거래량: {vol_diff} ({price_per}%)"

    # 거래량 증가분이 기준치 이상이면 알림
    if(vol_diff >= VOL_STANDARD):
      push_msg = push_msg + " 🌟"
      console_msg = console_msg + " 🌟"
      if(IS_ALARMING):
        threading.Thread(target=playsound, args=("alarm.mp3",), daemon=True).start()
      if(IS_TELEGRAMING):
        bot.sendMessage(TELEGRAM_CHAT_ID, text=push_msg)
      if(IS_LOGGING):
        logger.info(push_msg)
    
    # 콘솔 메시지 출력
    print(console_msg)

    # 현재 가격 및 거래량을 Old 변수에 대입한 후 SLEEP_TIME초 간 대기
    price_old = price_new
    vol_old = vol_new
    time.sleep(SLEEP_TIME)

  # 오류 발생 처리
  except Exception as e:
    if(IS_LOGGING):
      logger.critical(e)
    else:
      print(e)