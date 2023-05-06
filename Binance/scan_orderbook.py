import ccxt
import time
import threading
import logging
from datetime import datetime
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
TICKER = "BTC/USDT"  ## 오더북을 탐지할 바이낸스 Ticker
COUNT = 250          ## 조사할 호가 개수
SLEEP_TIME = 0.5     ## 탐지 간격(초)
ALARM_STANDARD = 80  ## 알람 기준 퍼센트(매수/메도 물량 중 한 쪽이 이 값 이상이면 알림)
COLOR_STANDARD = 80  ## 컬러 표시 기준 퍼센트(매수/매도 물량 중 한 쪽이 이 값 이상이면 콘솔 창에 컬러 표시)
IS_ALARMING = True
IS_LOGGING = True
current_date = datetime.now()
LOG_PATH = f"./logs/{current_date.year}-{current_date.month}_Orderbook.log"

# 초기화
exchange = ccxt.binance()
old_asks = 0
old_bids = 0

print(f"Binance {TICKER} 오더북(호가)를 {SLEEP_TIME}초 간격으로 조사합니다.")
print(f"매수/매도 호가 물량이 {ALARM_STANDARD}% 이상인 경우 알림을 보냅니다.")
print("-----------------------------------------------------------")

# 로그 설정
if(IS_LOGGING):
  log_path = LOG_PATH
  logger = logging.getLogger(__name__)
  streamHandler = logging.StreamHandler()
  fileHandler = logging.FileHandler(log_path)
  logger.addHandler(streamHandler)
  logger.addHandler(fileHandler)
  logger.setLevel(level=logging.INFO)
  print(f"{log_path} 경로에 로그를 기록합니다.")
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

  # 매도/매수호가 비율 계산
  per_asks = round(sum_asks / (sum_asks + sum_bids) * 100, 1)
  per_bids = round(sum_bids / (sum_asks + sum_bids) * 100, 1)

  # 알림 조건: 매도/매수 호가 비율 중 하나가 ALARM_STANDARD 이상인 경우
  alarm_condition = (per_asks >= ALARM_STANDARD and per_bids < 100 - ALARM_STANDARD) or (per_bids >= ALARM_STANDARD and per_asks < 100 - ALARM_STANDARD)
  if(alarm_condition and IS_ALARMING):
    threading.Thread(target=playsound, args=("alarm.mp3",), daemon=True).start()

  # 컬러 표시: 매도/매수 호가 비율 중 하나가 COLOR_STANDARD 값 이상인 경우
  if(per_asks > COLOR_STANDARD):    ## 매도호가 물량이 COLOR_STANDARD 이상이면 매도호가 물량에 빨간색 표시
    msg_bids = f"Buy {sum_bids}({per_bids}%) "
    msg_asks = f"{Colors.RED}{sum_asks}({per_asks}%) Sell{Colors.RESET}"
  elif(per_bids > COLOR_STANDARD):  ## 매수호가 물량이 COLOR_STANDARD 이상이면 매수호가 물량에 초록색 표시
    msg_bids = f"{Colors.GREEN}Buy {sum_bids}({per_bids}%) {Colors.RESET}"
    msg_asks = f"{sum_asks}({per_asks}%) Sell"
  else:                             ## 이 외엔 컬러를 표시하지 않음
    msg_bids = f"Buy {sum_bids}({per_bids}%)"
    msg_asks = f"{sum_asks}({per_asks}%) Sell"

  # 호가 물량변동(위아래 화살표) 표시
  if(sum_asks > old_asks):    ## 현재 매도호가 물량이 직전 매도호가 물량보다 큰 경우
    msg_bids = "↓ " + msg_bids  ### 매수호가 물량 하락
    msg_asks = msg_asks + " ↑"  ### 매도호가 물량 상승
  elif(sum_asks < old_asks):  ## 현재 매도호가 물량이 직전 매도호가 물량보다 작은 경우
    msg_bids = "↑ " + msg_bids  ### 매수호가 물량 상승
    msg_asks = msg_asks + " ↓"  ### 매도호가 물량 하락
  
  # 메시지 출력
  current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  star = ""  ## 알람 조건이 갖춰진 경우 메시지 끝에 별을 붙임
  if(alarm_condition):
    star = "🌟"
  print(f"{current_time}: {msg_bids} ↔ {msg_asks} {star}")

  # 알림 조건 충족 시 로깅
  if(alarm_condition and IS_LOGGING):
    msg_log = f"{current_time}: Buy {sum_bids}({per_bids}%) ↔ {sum_asks}({per_asks}%) Sell"
    logger.info(msg_log)

  # 현재 호가 물량을 Old 변수에 저장한 후 SLEEP_TIME초 간 대기
  old_asks = sum_asks
  old_bids = sum_bids
  time.sleep(SLEEP_TIME)