from datetime import datetime
from playsound import playsound
from dotenv import load_dotenv
import asyncio
import time
import os
import logging
import threading
import statistics
import ccxt
import telegram
"""
Binance/scan_vol.py
* Date: 2023. 1. 16.
* Author: Jeon Won
* Func: Binance 가상화폐의 거래량을 일정 시간(간격) 동안 스캔하여 거래량이 기준치 이상 터졌을 때 알림
* Usage: 상수 값 입력 후 `python3 scan_vol.py` 명령어 실행
"""

# 상승(GREEN) 및 하락(RED) 색상 표시를 위한 클래스
class Colors:
  RED = '\033[31m'
  GREEN = '\033[32m'
  RESET = '\033[0m'

# 대충 상수...
load_dotenv()           ## 환경변수 값 가져오기
current_date = datetime.now()
LOG_PATH = f"./logs/{current_date.year}-{current_date.month}_Volume.log"
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")      ## 텔레그렘 봇 토큰
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")  ## 텔레그램 봇 아이디
TICKER = "BTC/USDT"     ## 거래량을 탐지할 바이낸스 거래소 Ticker
INTERVAL = "15m"        ## 캔들 유형(15m: 15분봉 / 1h: 1시간봉)
SLEEP_TIME = 1          ## 탐지 간격(초)
COUNT = 60              ## 최근 탐지한 거래랑 몇 건으로 평균을 계산할 것인가?
VOL_VAL_STANDARD = 200   ## 거래량 기준치(거래량이 얼마 이상 발생했을 때 알림을 줄 것인가?)
IS_ALARMING = True      ## 소리 알림 여부
IS_TELEGRAMING = False  ## 텔레그램 알림 여부
IS_LOGGING = True       ## 로그 기록 여부


async def main():
    # 초기화
    bot = telegram.Bot(TELEGRAM_TOKEN)
    binance = ccxt.binance(config={
        'options': {
            'defaultType': 'future'
        }
    })
    ohlcv = binance.fetch_ohlcv(TICKER, INTERVAL, limit=1)  ## 시가, 고가, 저자, 종가, 거래량(Open, High, Low, Close, Volume) 얻어오기
    old_price = ohlcv[0][4]  ## 프로그램 실행 시점 기준 현재 가격
    old_vol = ohlcv[0][5]    ## 프로그램 실행 시점 기준 현재 거래량
    list_vol = []            ## 거래량 모음 리스트
    print(f"Binance {TICKER} {INTERVAL} 캔들 거래량을 {SLEEP_TIME}초 간격으로 탐지합니다.")
    print(f"거래량이 {SLEEP_TIME}초간 {VOL_VAL_STANDARD}개 이상 발생하면 알림이 발생합니다.")
    print(f"또한 최근 {COUNT}개 캔들의 평균 거래량도 계산합니다.")
    print("---------------------------------------------------------------------")

    # 로그 설정
    if(IS_LOGGING):
      log_path = LOG_PATH
      # log_path = f"./logs/{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"  ## 파일명: 프로그램 시작 시간
      logger = logging.getLogger(__name__)
      streamHandler = logging.StreamHandler()
      fileHandler = logging.FileHandler(log_path)
      logger.addHandler(streamHandler)
      logger.addHandler(fileHandler)
      logger.setLevel(level=logging.INFO)
      print(f"{log_path} 경로에 로그를 기록합니다.")
    print("---------------------------------------------------------------------")

    await bot.sendMessage(TELEGRAM_CHAT_ID, text="Test")

    
    while True:
      try: 
        # 주요 변수
        ohlcv = binance.fetch_ohlcv(TICKER, INTERVAL, limit=1)  ## 시가, 고가, 저자, 종가, 거래량(Open, High, Low, Close, Volume)
        new_price = ohlcv[0][4]  ## 현재 가격
        new_vol = ohlcv[0][5]    ## 현재 거래량
        diff_price = new_price - old_price      ## 가격 증감분
        diff_vol = round(new_vol - old_vol, 2)  ## 거래량 증가분
        if(diff_vol < 0):
          diff_vol = round(new_vol)
        if(len(list_vol) >= COUNT):             ## 거래량 모음 리스트
          del list_vol[0]
        list_vol.append(diff_vol)
        mean_vol = round(statistics.mean(list_vol), 2)               ## 거래량 평균
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  ## 현재 시간
        price_per = round((ohlcv[0][4] - ohlcv[0][1]) / ohlcv[0][1] * 100, 2)  ## 가격 증감 퍼센트

        # 메시지
        msg_vol_val = ""  ## 순간 거래량 메시지
        msg_vol_avg = ""  ## 평균 거래량 메시지
        msg_console = ""  ## 콘솔 출력용 메시지 메시지 = 순간 거래량 메시지 + 평균 거래량 메시지
        msg_push = ""     ## 푸시(텔레그램) 전송용 메시지

        # 순간 거래량 메시지 생성: 상승(GREEN) 및 하락(RED) 색상 표시
        if(diff_price > 0):    ## 가격이 상승한 경우 초록색 표시
          msg_vol_val = f"{current_time}: {Colors.GREEN}{diff_vol} ({new_price}, {price_per}%){Colors.RESET}"
        elif(diff_price < 0):  ## 가격이 하락한 경우 빨간색 표시
          msg_vol_val = f"{current_time}: {Colors.RED}{diff_vol} ({new_price}, {price_per}%){Colors.RESET}"
        else:                  ## 가격 변동이 없는 경우 색을 표시하지 않음
          msg_vol_val = f"{current_time}: {diff_vol} ({new_price}, {price_per}%)"
        
        # 평균 거래량, 콘솔 출력용 및 푸시 전송용 메시지 생성
        msg_console = f"{msg_vol_val} {msg_vol_avg}"
        msg_push = f"{current_time} {TICKER} {INTERVAL} {SLEEP_TIME}초간 발생한 거래량: {diff_vol} (종가: {new_price}, {price_per}%)"

        # 거래량 증가분이 기준치 이상이면 알림
        if(diff_vol >= VOL_VAL_STANDARD):
          if(IS_ALARMING):
            threading.Thread(target=playsound, args=("alarm.mp3",), daemon=True).start()
          if(IS_TELEGRAMING):
            await bot.sendMessage(TELEGRAM_CHAT_ID, text=msg_push)
          if(IS_LOGGING):
            logger.info(msg_push)
          msg_console = msg_console + "🌟"
        
        # 콘솔 메시지 출력
        print(msg_console)

        # 현재 가격 및 거래량을 Old 변수에 대입한 후 SLEEP_TIME초 간 대기
        old_price = new_price
        old_vol = new_vol
        time.sleep(SLEEP_TIME)

      # 오류 발생 처리
      except Exception as e:
        if(IS_LOGGING):
          logger.critical(e)
        else:
          print(e)

asyncio.run(main())