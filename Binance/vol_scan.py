import ccxt
import telegram
import time
import datetime
import os
import logging
import threading
import statistics
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
load_dotenv()          ## 환경변수 값 가져오기
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")      ## 텔레그렘 봇 토큰
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")  ## 텔레그램 봇 아이디
TICKER = "BTC/USDT"     ## 거래량을 탐지할 바이낸스 거래소 Ticker
INTERVAL = "15m"        ## 캔들 유형
SLEEP_TIME = 1          ## 탐지 간격(초)
COUNT = 60              ## 최근 탐지한 거래랑 몇 건으로 평균을 계산할 것인가?
VOL_VAL_STANDARD = 100  ## 거래량 기준치(거래량이 얼마 이상 발생했을 때 알림을 줄 것인가?)
IS_ALARMING = True      ## 소리 알림 여부
IS_TELEGRAMING = False  ## 텔레그램 알림 여부
IS_LOGGING = True       ## 로그 기록 여부

# 초기화
bot = telegram.Bot(TELEGRAM_TOKEN)
binance = ccxt.binance()
ohlcv = binance.fetch_ohlcv(TICKER, INTERVAL, limit=1) ## 시가, 고가, 저자, 종가, 거래량(Open, High, Low, Close, Volume) 얻어오기
price_old = ohlcv[0][4]                                ## 프로그램 실행 시점 기준 현재 가격
vol_old = ohlcv[0][5]                                  ## 프로그램 실행 시점 기준 현재 거래량
vol_list = []                                          ## 거래량 모음 리스트
print(f"Binance {TICKER} {INTERVAL} 캔들 거래량을 {SLEEP_TIME}초 간격으로 탐지합니다.")
print(f"거래량이 {SLEEP_TIME}초간 {VOL_VAL_STANDARD}개 이상 발생하면 알림이 발생합니다.")
print(f"또한 최근 {COUNT}개 캔들의 평균 거래량도 계산합니다.")

# 로그 설정
if(IS_LOGGING):
  # log_path = f"./logs/2023-02.log"
  log_path = f"./logs/{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"  ## 파일명: 프로그램 시작 시간
  logger = logging.getLogger(__name__)
  streamHandler = logging.StreamHandler()
  fileHandler = logging.FileHandler(log_path)
  logger.addHandler(streamHandler)
  logger.addHandler(fileHandler)
  logger.setLevel(level=logging.INFO)
  print(f"{log_path} 경로에 로그를 기록합니다.")
print("--------------------------------------------------")

while True:
  try: 
    # 주요 변수
    ohlcv = binance.fetch_ohlcv(TICKER, INTERVAL, limit=1)  ## 시가, 고가, 저자, 종가, 거래량(Open, High, Low, Close, Volume)
    price_new = ohlcv[0][4]  ## 현재 가격
    vol_new = ohlcv[0][5]    ## 현재 거래량
    price_diff = price_new - price_old      ## 가격 증감분
    vol_diff = round(vol_new - vol_old, 2)  ## 거래량 증가분
    if(vol_diff < 0):
      vol_diff = round(vol_new)
    if(len(vol_list) >= COUNT):             ## 거래량 모음 리스트
      del vol_list[0]
    vol_list.append(vol_diff)
    vol_mean = round(statistics.mean(vol_list), 2)                         ## 거래량 평균
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")   ## 현재 시간
    price_per = round((ohlcv[0][4] - ohlcv[0][1]) / ohlcv[0][1] * 100, 2)  ## 가격 증감 퍼센트

    # 메시지
    vol_val_msg = ""  ## 순간 거래량 메시지
    vol_avg_msg = ""  ## 평균 거래량 메시지
    console_msg = ""  ## 콘솔 출력용 메시지 메시지
    push_msg = ""     ## 푸시(텔레그램) 전송용 메시지

    # 순간 거래량 메시지 생성: 상승(GREEN) 및 하락(RED) 색상 표시
    if(price_diff > 0):
      vol_val_msg = f"{current_time} {TICKER} {INTERVAL} {SLEEP_TIME}초간 발생한 거래량: {Colors.GREEN}{vol_diff} ({price_per}%){Colors.RESET}"
    elif(price_diff < 0):
      vol_val_msg = f"{current_time} {TICKER} {INTERVAL} {SLEEP_TIME}초간 발생한 거래량: {Colors.RED}{vol_diff} ({price_per}%){Colors.RESET}"
    else:
      vol_val_msg = f"{current_time} {TICKER} {INTERVAL} {SLEEP_TIME}초간 발생한 거래량: {vol_diff} ({price_per}%)"
    
    # 평균 거래량, 콘솔 출력용 및 푸시 전송용 메시지 생성
    vol_avg_msg = f"최근 {INTERVAL} 캔들봉 {COUNT}개 평균 거래량: {vol_mean}"
    console_msg = f"{vol_val_msg}\n{vol_avg_msg}"
    push_msg = f"{current_time} {TICKER} {INTERVAL} {SLEEP_TIME}초간 발생한 거래량: {vol_diff} ({price_per}%)\n{vol_avg_msg}"

    # 거래량 증가분이 기준치 이상이면 알림
    if(vol_diff >= VOL_VAL_STANDARD):
      console_msg = console_msg + " 🌟"
      if(IS_ALARMING):
        threading.Thread(target=playsound, args=("alarm.mp3",), daemon=True).start()
      if(IS_TELEGRAMING):
        bot.sendMessage(TELEGRAM_CHAT_ID, text=push_msg)
      if(IS_LOGGING):
        logger.info(push_msg)
    
    # 콘솔 메시지 출력
    print(console_msg)
    print("--------------------------------------------------")

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