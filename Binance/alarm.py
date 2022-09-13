from dotenv import load_dotenv
from playsound import playsound
import logging
import os
import sys
import re
import time
import datetime
import telegram
import ccxt
import module
"""
Binance/detect_bb_exceed.py
* Date: 2022. 9. 11.
* Author: Jeon Won
* Func: 비트코인 차트의 보조지표(거래량, RSI, 캔들길이, 볼린저 밴드) 값을 실시간 계산하여 롱숏 포지션 진입 시점이 다가왔다고 예상되었을 때 알림을 보냄
* Usage: 
  - 1. Binance/alert.py 파일을 열어 상수 값을 입력
  - 2. 5분봉을 조사하려면 `python3 Binance/alert.py 5m` 명령어 실행 (5m 대신 1m, 3m, 15m, 30m, 1h, 4h, 12h 입력)
  - 3. 5분봉을 백그라운드로 실행하여 조사하려면 `nohup python3 Binance/alert.py 5m &`
"""

# 환경변수 로드
load_dotenv()

# 조사할 코인과 캔들 정보
TICKERS = ["BTC/USDT", "ETH/USDT"]
TICKER_INTERVAL = sys.argv[1]
INTERVAL = int(re.sub(r'[^0-9]', '', TICKER_INTERVAL))

# 캔들 카운트(캔들 몇 개로 각 지표들을 조사할 것인가?)
COUNT_RSI = 200
COUNT_VOL = 70
COUNT_CANDLE_LEN = 70
COUNT_BB = 20
COUNT_MAX = max(COUNT_RSI, COUNT_VOL, COUNT_CANDLE_LEN, COUNT_BB)

# 알림 여부
IS_VOLUME_ALARM = True  # 거래량 알림 전송 여부
IS_RSI_ALARM = True     # RSI 알림 전송 여부
IS_CANDLE_ALARM = True  # 캔들크기 알림 전송 여부
IS_BB_ALARM = True      # %B 알림 전송 여부

# 알림 조건
ALERT_RSI_OVERBOUGHT = 80  # RSI 과매수 조건(RSI 값이 이 값보다 크면 과매수 알림)
ALERT_RSI_OVERSOLD = 20    # RSI 과매도 조건(RSI 값이 이 값보다 작으면 과매도 알림)
ALERT_VOL = 2.5            # 거래량 조건(현재 거래량이 평균 거래량보다 이 값의 배만큼 터졌을 때 알림)
ALERT_CANDLE_LEN = 3       # 캔들크기 조건(현재 캔들크기가 평균 캔들크기보다 이 값의 배만큼 터졌을 때 알림)
ALERT_BB_OVERBOUGHT = 1.15  # 볼린저 밴드 %B 과매수 조건(현재 %B 값이 이 값보다 크면 과매수 알림)
ALERT_BB_OVERSOLD = -0.15   # 볼린저 밴드 %B 과매도 조건(현재 %B 값이 이 값보다 작으면 과매도 알림)

# 알림 방법
IS_ALARM_SOUND = True    # 사운드 알림 여부
IS_ALARM_TELEGRAM = False  # 텔레그램 알림 전송 여부
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")      # 텔레그렘 봇 토큰
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")  # 텔레그램 봇 아이디

# 한 ticker를 조사한 후 다음 ticker를 조사하기 전 쉴 시간(초)
SLEEP_TIME = 1

# 로그 설정
logger = logging.getLogger(__name__)

# handler 생성 (stream, file) 및 logger instance에 handler 설정
now = datetime.datetime.now()
streamHandler = logging.StreamHandler()
fileHandler = logging.FileHandler(f"./logs/{now.year}-{now.month}-{now.day}.log")
logger.addHandler(streamHandler)
logger.addHandler(fileHandler)

# log level 설정 및 log 남기기
logger.setLevel(level=logging.INFO)
# logger.debug('my DEBUG log')
# logger.info('my INFO log')
# logger.warning('my WARNING log')
# logger.error('my ERROR log')
# logger.critical('my CRITICAL log')

# 초기 설정
bot = telegram.Bot(TELEGRAM_TOKEN) if IS_ALARM_TELEGRAM else None
binance = ccxt.binance()
notified_tickers = []  # 알림 보낸 ticker 리스트(캔들 갱신될 때마다 초기화함)
logger.info(f"[INFO] {datetime.datetime.now()} Binance {TICKERS} {TICKER_INTERVAL} 포지션 예상 진입시점 알림을 시작합니다.")

while True:    
    for ticker in TICKERS: 
        # 현재 캔들 알림을 보내지 않았다면 
        if(notified_tickers.count(ticker) == 0):
            # 각 지표에 사용할 OHLCV(Open, High, Low, Close, Volume) 얻어오기
            ohlcvs = binance.fetch_ohlcv(ticker, TICKER_INTERVAL, limit=COUNT_MAX)
            ohlcvs_rsi = ohlcvs[-COUNT_RSI:]
            ohlcvs_vol = ohlcvs[-COUNT_VOL:]
            ohlcvs_candle_len = ohlcvs[-COUNT_CANDLE_LEN:]
            ohlcvs_bb = ohlcvs[-COUNT_BB:]

            # 각 지표값 계산
            volume = ohlcvs[len(ohlcvs)-1][5]                                      # 현재 거래량
            volume_mean = module.get_ccxt_volume_mean(ohlcvs_vol)                  # 평균 거래량
            rsi = module.get_ccxt_rsi(ohlcvs_rsi)                                  # 현재 RSI
            candle_len = abs(ohlcvs[len(ohlcvs)-1][1] - ohlcvs[len(ohlcvs)-1][4])  # 현재 캔들길이
            candle_len_mean = module.get_ccxt_candle_len_mean(ohlcvs_candle_len)   # 평균 캔들길이
            bb = module.get_ccxt_bb(ticker, ohlcvs_bb, 2)["per_b"]                 # 현재 %B 값

            # 알림 조건 설정: 알림 보내도록 설정이 되어 있고, 계산된 지표값들이 알림 보낼 조건에 부합하는 경우 True
            is_volume_alert = IS_VOLUME_ALARM and (True if volume / volume_mean >= ALERT_VOL else False)
            is_rsi_alert = IS_RSI_ALARM and (True if rsi > ALERT_RSI_OVERBOUGHT or rsi < ALERT_RSI_OVERSOLD else False)
            is_candle_len_alert = IS_CANDLE_ALARM and (True if candle_len / candle_len_mean >= ALERT_CANDLE_LEN else False)
            is_bb_alert = IS_BB_ALARM and (True if bb > ALERT_BB_OVERBOUGHT or bb < ALERT_BB_OVERSOLD else False)
            is_alert = is_volume_alert or is_rsi_alert or is_candle_len_alert or is_bb_alert  # 위 4가지 조건 중 하나라도 부합하면 알림 보냄

            # 알림 조건에 부합하면
            if(is_alert):
                # 메시지 생성
                message_title = f"Binance {ticker} {INTERVAL}분봉 변동 알림"
                message_volume = f"- 거래량: 평균 {round(volume / volume_mean, 2)}배"
                message_rsi = f"- RSI: {round(rsi, 2)}"
                message_candle_len = f"- 캔들길이: 평균 {round(candle_len / candle_len_mean, 2)}배"
                message_bb = f"- %B: {round(bb, 2)}"
                message_time = f"- 현재시간: {datetime.datetime.now()}"

                message_volume_star = "⭐" if is_volume_alert else ""
                message_rsi_star = "⭐" if is_rsi_alert else ""
                message_candle_len_star = "⭐" if is_candle_len_alert else ""
                message_bb_star = "⭐" if is_bb_alert else ""

                message = f"""{message_title}\n{message_volume} {message_volume_star}\n{message_rsi} {message_rsi_star}\n{message_candle_len} {message_candle_len_star}\n{message_bb} {message_bb_star}\n{message_time}"""
                logger.info(f"[INFO] {message}")

                # 알림음 재생 또는 텔레그램 메시지 전송
                if(IS_ALARM_SOUND):
                    playsound("alarm.mp3")
                if(IS_ALARM_TELEGRAM):
                    bot.sendMessage(TELEGRAM_CHAT_ID, text=message)

                # 알림 보낸 ticker 리스트에 추가하여 다음 봉 갱신 전까지 알림을 보내지 못하도록 함
                notified_tickers.append(ticker)
                
        # 다음 봉 갱신 되면 알림 보냈던 ticker 리스트 초기화
        now = datetime.datetime.now()

        # ticker 리스트를 초기화 조건 계산
        list_clear_condition = False
        if(TICKER_INTERVAL in ['1m', '3m', '5m', '15m', '30m']):  # 분봉: 현재 시간(분)이 INTERVAL로 나누어 떨어지는지 확인
            list_clear_condition = True if divmod(now.minute, INTERVAL)[1] == 0 else False
        elif(TICKER_INTERVAL == '1h'):  # 1시간봉: 현재 시간(분)이 0분인지 확인
            list_clear_condition = True if now.minute == 0 else False
        elif(TICKER_INTERVAL in ['4h', '12h']):  # 4시간봉: 1, 5, 9, 13, 17, 21시마다 갱신되도록 현재 시간에 3을 더해서 4로 나누어 떨어지는지 확인. 12시간봉도 비슷함.
            list_clear_condition = True if divmod(now.hour + 3, INTERVAL)[1] else False
        else:
            list_clear_condition = False
        
        # ticker 리스트 초기화 조건에 부합하고 현재 시간(초)가 0~5초 사이면 ticker 리스트 초기화
        if(list_clear_condition and now.second > 0 and now.second < 5):
            notified_tickers.clear()
            logger.info(f"[INFO] {datetime.datetime.now()} ticker 리스트 초기화 완료")
            time.sleep(5)

        # 다음 ticker를 조사하기 전 쉼(API 호출 제한에 걸리지 않도록 하기 위함)
        time.sleep(SLEEP_TIME)