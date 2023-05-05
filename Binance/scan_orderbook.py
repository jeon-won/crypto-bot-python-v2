import os
import ccxt
import time
import datetime
import threading
from playsound import playsound
from dotenv import load_dotenv
"""
Binance/scan_orderbook.py
* Date: 2023. 5. 5.
* Author: Jeon Won
* Func: Binance 가상화폐의 오더북(호가창)을 일정 시간(간격) 동안 스캔하여 매도(매수) 물량 출력
* Usage: 상수 값 입력 후 `python3 scan_orderbook.py` 명령어 실행
"""

# 매도호가(asks), 매수호가(bids) 색상 표시를 위한 클래스
class Colors:
  RED = '\033[31m'
  GREEN = '\033[32m'
  RESET = '\033[0m'

# 대충 상수...
load_dotenv()        ## 환경변수 값 가져오기
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")      ## 텔레그렘 봇 토큰
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")  ## 텔레그램 봇 아이디
TICKER = "BTC/USDT"  ## 오더북을 탐지할 바이낸스 Ticker
COUNT = 250          ## 조사할 호가 개수
SLEEP_TIME = 0.5     ## 탐지 간격(초)
ALARM_STANDARD = 85  ## 알람 기준 퍼센트(매수/메도 물량 중 한 쪽이 이 값 이상이면 알림)
COLOR_STANDARD = 70  ## 컬러 표시 기준 퍼센트(매수/매도 물량 중 한 쪽이 이 값 이상이면 콘솔 창에 컬러 표시)

exchange = ccxt.binance()
print(f"Binance {TICKER} 오더북(호가)를 {SLEEP_TIME}초 간격으로 조사합니다.")
print(f"매수/매도 호가 물량이 {ALARM_STANDARD}% 이상인 경우 알림을 보냅니다.")
print("-----------------------------------------------------------")

while(True):
  orderbook = exchange.fetch_order_book(TICKER, COUNT)

  # 매도(asks)호가 물량과 매수(bids)호가 물량 계산
  sum_asks = 0
  sum_bids = 0
  for ask in orderbook['asks']:
    sum_asks = sum_asks + ask[1]
  for bid in orderbook['bids']:
    sum_bids = sum_bids + bid[1]
  sum_asks = round(sum_asks, 3)
  sum_bids = round(sum_bids, 3)

  # 매도호가 비율과 매수호가 비율 계산
  per_asks =  round(sum_asks / (sum_asks + sum_bids) * 100, 1)
  per_bids =  round(sum_bids / (sum_asks + sum_bids) * 100, 1)

  # 알림 조건: 매도/매수 호가 비율 중 하나가 ALARM_STANDARD 이상인 경우
  star = ""
  alarm_condition = (per_asks >= ALARM_STANDARD and per_bids < 100 - ALARM_STANDARD) or (per_bids >= ALARM_STANDARD and per_asks < 100 - ALARM_STANDARD)
  if(alarm_condition):
     threading.Thread(target=playsound, args=("alarm.mp3",), daemon=True).start()
     star = "🌟"
  
  current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

  # 컬러 표시 조건: 매도/매수 호가 비율 중 하나가 COLOR_STANDARD 값 이상인 경우
  if(per_asks > COLOR_STANDARD):    ## 매도호가 물량이 COLOR_STANDARD 이상이면 매도호가 물량에 빨간색 표시
    msg_bids = f"Buy {sum_bids}({per_bids}%) "
    msg_asks = f"{Colors.RED}{sum_asks}({per_asks}%) Sell{Colors.RESET}"
  elif(per_bids > COLOR_STANDARD):  ## 매수호가 물량이 COLOR_STANDARD 이상이면 매수호가 물량에 초록색 표시
    msg_bids = f"{Colors.GREEN}Buy {sum_bids}({per_bids}%) {Colors.RESET}"
    msg_asks = f"{sum_asks}({per_asks}%) Sell"
  else:                             ## 이 외엔 컬러를 표시하지 않음
    msg_bids = f"Buy {sum_bids}({per_bids}%)"
    msg_asks = f"{sum_asks}({per_asks}%) Sell"
  
  # 메시지 출력
  print(f"{current_time}: {msg_bids} ↔ {msg_asks} {star}")

  # 잠시 쉰 후 무한루프
  time.sleep(SLEEP_TIME)