import ccxt
import os
import sys
import time
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
from pprint import pprint
"""
Binance/auto_trade.py
- 작성 중... (특정 조건에 부합할 때 바이낸스 선물 포지션 잡기)
"""

# 상수 --------------------------------------------------------------------

PRICE_OPEN = sys.argv[1]        # 포지션 잡을 가격
PRICE_TAKE_PROFIT = sys.argv[2] # 수익실현가(Take Profit)
PRICE_STOP_LOSS = sys.argv[3]   # 손절가(Stop Loss)
TICKER = "BTC/USDT"
INTERVAL = "15m"

# 변수 --------------------------------------------------------------------

vol_previous = -1

# 함수 --------------------------------------------------------------------

def unixtime_to_gmt_plus9(unix_time):
    """Unix Time을 GMT+9 Time으로 변환합니다. 
    
    Args: unix_time(13자리)

    Returns: <class 'str'>
    """

    unix_time_milliseconds = int(unix_time) // 1000                 # Unix 시간을 밀리초 단위로 변환
    gmt_plus9 = timezone(timedelta(hours=9))                        # GMT+9의 시간대를 나타내는 timedelta 객체 생성
    dt = datetime.fromtimestamp(unix_time_milliseconds, gmt_plus9)  # Unix 시간을 GMT+9 시간대의 datetime 객체로 변환
    formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")               # 결과를 year-month-day-hour-minute-second 형식의 문자열로 변환하여 반환
    
    return formatted_time

def is_overshooting(ccxt_ohlcv, vol_overshoot):
    """거래량이 터졌는지 판별합니다.

    Args:
      - ccxt_ohlcv: ccxt의 fetch_ohlcv() 함수가 반환하는 값
      - vol_overshoot: 오버슈팅 거래량 기준(거래량이 이 값 이상 터졌다면 오버슈팅으로 간주)
    
    Returns: <class 'float'> (거래량이 터진 경우 터진 거래량을, 터지지 않은 경우 0.0 반환)
    """

    global vol_previous                              # 직전 거래량 계산을 위해 전역변수 사용해야 함...
    vol_current = ccxt_ohlcv[len(ccxt_ohlcv)-1][5]   # 현재 거래량

    if(vol_previous < 0):           # 프로그램 실행 직후인 경우
        vol_previous = vol_current  # 현재 거래량을 직전 거래량에 저장
        return 0.0

    vol_diff = round(vol_current - vol_previous, 3) # 거래량 차이 계산 = 현재 거래량 - 직전 거래량

    if(vol_diff < 0):     # 봉 갱신된 경우
        vol_diff = 0      # 거래량 차이값과 
        vol_previous = 0  # 직전 거래량을 0으로 초기화
        return 0.0
    
    vol_previous = vol_current
    
    if(vol_diff >= vol_overshoot):  # 오버슈팅나면 
        return vol_diff             # 거래량 차이값 리턴

    return 0.0


def is_all_tail_candle(ccxt_ohlcv):
    """모든 캔들에 위꼬리 또는 아래꼬리가 적당히(?) 달렸는지 확인합니다. 
    
    Args: ccxt_ohlcv: ccxt의 fetch_ohlcv() 함수가 반환하는 값
    
    Returns: <class 'bool'> 모든 캔들의 꼬리가 몸통보다 크면 True를 반환합니다.
    """

    for item in ccxt_ohlcv:
        open = item[1]   # 시가
        high = item[2]   # 고가
        low = item[3]    # 저가
        close = item[4]  # 종가
        
        if(close >= open):                                 # 양봉 캔들인 경우
            body = close - open
            tail_upper = high - close
            tail_bottom = open - low
            if(body > tail_upper and body > tail_bottom):  ## 꼬리가 적당히 달린 캔들이 아닌 경우
                return False                               ## False 반환
        
        else:                                              # 음봉 캔들인 경우
            body = open - close
            tail_upper = high - open
            tail_bottom = close - low
            if(body > tail_upper and body > tail_bottom):  ## 꼬리가 적당히 달린 캔들이 아닌 경우
                return False                               ## False 반환
            
    return True  # for 문을 무사히 돌았다면 모두 꼬리가 적당히 달린 캔들임

def is_last_big_candle(ccxt_ohlcv, last_candle_per):
    """모든 봉이 양봉(음봉)이고, 마지막 봉이 일정 크기 이상인지 확인합니다. (머프님 강의 1강 '마지막 봉이 가장 클 때' 응용)

    Args: 
      - ccxt_ohlcv: ccxt의 fetch_ohlcv() 함수가 반환하는 값
      - last_candle_per: 마지막 봉의 크기(%)
    
    Returns: <class 'bool'>
    """

    is_all_rising_candle = False
    is_all_falling_candle = False
    for item in ccxt_ohlcv:  # 각 캔들이 양봉인지 음봉인지 분석
        open = item[1]
        close = item[4]
        is_all_rising_candle = close > open
        is_all_falling_candle = open > close

    last = ccxt_ohlcv[len(ccxt_ohlcv)-1]  # 가장 최신 봉 분석
    print(last[0])
    opens = last[1]
    closes = last[4]
    per = round(abs(opens - closes) / opens * 100, 2)  # 상승(하락)률 = |종가 - 시가| / 시가 * 100
    print(per)
    
    

    return True

# 코드 --------------------------------------------------------------------

print(f"조건에 맞으면 {PRICE_OPEN} 가격에 포지션을 잡고 {PRICE_TAKE_PROFIT} 가격에 수익 실현하며, {PRICE_STOP_LOSS} 가격에 손절합니다.")


# 초기화
load_dotenv()
BINANCE_API_KEY = os.environ.get("BINANCE_API_KEY")
BINANCE_SECRET_KEY = os.environ.get("BINANCE_SECRET_KEY")
binance = ccxt.binance(config={
    'apiKey': BINANCE_API_KEY, 
    'secret': BINANCE_SECRET_KEY,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future'
    }
})

# 유닉스 시간을 년월일시분초로 변환된 시가(Open), 고가(High), 저가(Low), 종가(Close), 거래량(Volume) 배열 출력
# ohlcvs = binance.fetch_ohlcv(TICKER, INTERVAL, limit=5)
# for array in ohlcvs:
#     array[0] = unixtime_to_gmt_plus9(array[0])

while True:
    ohlcvs = binance.fetch_ohlcv(TICKER, INTERVAL, limit=10)
    for array in ohlcvs:
        array[0] = unixtime_to_gmt_plus9(array[0])
    pprint(ohlcvs)
    time.sleep(10)