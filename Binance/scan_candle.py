from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from pprint import pprint
from time import sleep
import asyncio, ccxt, os, telegram, time

# 상수 --------------------------------------------------------------------

load_dotenv()
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")      ## 텔레그렘 봇 토큰
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")  ## 텔레그램 봇 아이디
SLEEP_TIME = 150
SYMBOL = "BTC/USDT"

## 조사할 캔들 개수
CANDLE_COUNT_3M = 5
CANDLE_COUNT_5M = 5
CANDLE_COUNT_15M = 5
CANDLE_COUNT_30M = 4
CANDLE_COUNT_1H = 3
CANDLE_COUNT_4H = 2

## 꼬리캔들 몇 개 이상 생성되었을 때 알림을 줄 것인가...?
ALARM_COUNT_3M = 2
ALARM_COUNT_5M = 2
ALARM_COUNT_15M = 2
ALARM_COUNT_30M = 2
ALARM_COUNT_1H = 1
ALARM_COUNT_4H= 1

# 함수 --------------------------------------------------------------------

def get_tail_candle_count(ccxt_ohlcv):
    """위(아래)꼬리가 달린 캔들 개수를 반환합니다.
    
    Args: ccxt_ohlcv: ccxt의 fetch_ohlcv() 함수가 반환하는 값
    
    Returns: <class 'int'> 꼬리가 몸통보다 큰 캔들 개수를 반환합니다.
    """

    candle_count = 0

    for item in ccxt_ohlcv:
        open = item[1]
        high = item[2]
        low = item[3]
        close = item[4]

        if(close >= open):  # 양봉 꼬리캔들 개수 카운팅
            body = close - open
            tail_upper = high - close
            tail_bottom = open - low

        else:  # 음봉 꼬리캔들 개수 카운팅
            body = open - close
            tail_upper = high - open
            tail_bottom = close - low
        
        if(body < tail_upper or body < tail_bottom):
            candle_count = candle_count + 1
            
    return candle_count

async def main():
    bot = telegram.Bot(TELEGRAM_TOKEN)
    binance = ccxt.binance(config={
        'options': {
            'defaultType': 'future'
        }
    })

    while True:
        # 변수
        current_time = datetime.now()
        current_hour = current_time.hour
        current_minute = current_time.minute
        current_second = current_time.second
        message = ""  ## 텔레그램 전송 메시지

        # 캔들 체크 타이밍 조건: 각 캔들 갱신 직후 5초 이내
        is_3m_timing = current_minute % 3 == 0 and current_second < 5
        is_5m_timing = current_minute % 5 == 0 and current_second < 5
        is_15m_timing = current_minute % 15 == 0 and current_second < 5
        is_30m_timing = current_minute % 30 == 0 and current_second < 5
        is_1h_timing = current_minute == 0 and current_second < 5
        is_4h_timing = current_hour % 4 == 0 and current_minute == 0 and current_second < 5
        is_timing = is_3m_timing or is_5m_timing or is_15m_timing or is_30m_timing or is_1h_timing or is_4h_timing

        # 캔들 체크 타이밍에 캔들 검사
        if(is_timing): 
            if(is_3m_timing):  ## 각 캔들마다 꼬리캔들이 일정개수 이상이면 메시지 누적
                ohlcv_3m = binance.fetch_ohlcv(symbol=SYMBOL, timeframe="3m", limit=CANDLE_COUNT_3M)
                tail_candle_count = get_tail_candle_count(ohlcv_3m)
                if(tail_candle_count >= ALARM_COUNT_3M):
                    message = message + f"{SYMBOL} 3분봉 꼬리캔들: {tail_candle_count}개\n"
            if(is_5m_timing):
                ohlcv_5m = binance.fetch_ohlcv(symbol=SYMBOL, timeframe="5m", limit=CANDLE_COUNT_5M)
                tail_candle_count = get_tail_candle_count(ohlcv_5m)
                if(tail_candle_count >= ALARM_COUNT_5M):
                    message = message + f"{SYMBOL} 5분봉 꼬리캔들: {tail_candle_count}개\n"
            if(is_15m_timing):
                ohlcv_15m = binance.fetch_ohlcv(symbol=SYMBOL, timeframe="15m", limit=CANDLE_COUNT_15M)
                tail_candle_count = get_tail_candle_count(ohlcv_15m)
                if(tail_candle_count >= ALARM_COUNT_15M):
                    message = message + f"{SYMBOL} 15분봉 꼬리캔들: {tail_candle_count}개\n"
            if(is_30m_timing):
                ohlcv_30m = binance.fetch_ohlcv(symbol=SYMBOL, timeframe="30m", limit=CANDLE_COUNT_30M)
                tail_candle_count = get_tail_candle_count(ohlcv_30m)
                if(tail_candle_count >= ALARM_COUNT_30M):
                    message = message + f"{SYMBOL} 30분봉 꼬리캔들: {tail_candle_count}개\n"
            if(is_1h_timing):
                ohlcv_1h = binance.fetch_ohlcv(symbol=SYMBOL, timeframe="1h", limit=CANDLE_COUNT_1H)
                tail_candle_count = get_tail_candle_count(ohlcv_1h)
                if(tail_candle_count >= ALARM_COUNT_1H):
                    message = message + f"{SYMBOL} 1시간봉 꼬리캔들: {tail_candle_count}개\n"
            if(is_4h_timing):
                ohlcv_4h = binance.fetch_ohlcv(symbol=SYMBOL, timeframe="30m", limit=CANDLE_COUNT_4H)
                tail_candle_count = get_tail_candle_count(ohlcv_4h)
                if(tail_candle_count >= ALARM_COUNT_4H):
                    message = message + f"{SYMBOL} 4시간봉 꼬리캔들: {tail_candle_count}개\n"
            
            if(message != ""):  ## 메시지가 누적되면 텔레그램 메시지 전송
                message = str(current_time) + message
                await bot.sendMessage(TELEGRAM_CHAT_ID, text=message)

            sleep(SLEEP_TIME)
        
        else:
            sleep(1)

asyncio.run(main())