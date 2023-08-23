from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from pprint import pprint
import asyncio
import ccxt
import os
import telegram
import time
"""
Binance/auto_trade.py
- 작성 중... (특정 조건에 부합할 때 바이낸스 선물 포지션 잡기)
"""

# 상수 --------------------------------------------------------------------

TICKER = "BTC/USDT"
SYMBOL = "BTCUSDT"
LEVERAGE = 5
PRICE_ERROR = 50                        # 포지션 예상가 오차 가격(USDT)
STD_VOLUME_OVERSHOOTING = 200           # 거래량 오버슈팅 기준(코인 수량)
STD_CANDLE_SIZE = 0.3                   # 포지션 잡을 캔들 크기 기준(%)
STD_VOLUME_OVERSHOOTING_TIME_TERM = 60  # 거래량 오버슈팅 발생 후 몇 초 내에 다른 조건이 부합하면 포지션을 자동으로 잡을 것인지...

# 전역변수 ------------------------------------------------------------------

time_overshooting = datetime(2023, 1, 1, 0, 0, 0)  # 거래량 터진 시간(프로그램 실행 시 과거시점으로 초기화)
unixtime_15m_position = 0  # 포지션 잡은 15분봉 기준 시간(프로그램 실행 시 과거시점으로 초기화) -> 15분봉 하나당 두 번 이상 포지션 잡지 않기 위해 사용
vol_previous = -1          # 직전 거래량(프로그램 실행 시 음수 값으로 초기화)
list_auto_position = [     # 포지션 리스트[포지션유형(long/short), 포지션예상가, 수익실현가, 손절가, 코인수량, 자동매매완료여부(반드시 False로)]
    # ["long", 20000, 30000, 10000, 0.001, False],   # 예: 롱 포지션을 20000 가격 근처에서 수익실현가 30000 및 손절가 10000으로 코인 0.001 수량 만큼 조건에 부합하면 잡음
    ["short", 30184, 30001, 30312, 0.001, False],
    ["short", 29651, 29575, 29900, 0.001, False],
    ["short", 29466, 29350, 29561, 0.001, False],
    ["long", 29258, 29332, 29150, 0.001, False],
    ["long", 29073, 29161, 28999, 0.001, False],
]

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


def get_volume_difference(ccxt_ohlcv):
    """현재 및 직전 거래량의 차이를 반환합니다.

    Args:
      - ccxt_ohlcv: ccxt의 fetch_ohlcv() 함수가 반환하는 값
    
    Returns: <class 'float'>
    """

    global vol_previous                              # 직전 거래량 계산을 위해 전역변수 사용해야 함...
    vol_current = ccxt_ohlcv[len(ccxt_ohlcv)-1][5]   # 현재 거래량

    if(vol_previous < 0):           # 프로그램 실행 직후인 경우
        vol_previous = vol_current  # 현재 거래량을 직전 거래량에 저장
        return 0.0

    vol_diff = round(vol_current - vol_previous, 3) # 거래량 차이 = 현재 거래량 - 직전 거래량
    # print(f"발생 거래량: {vol_diff}")

    if(vol_diff < 0):     # 봉 갱신된 경우
        vol_diff = 0      # 거래량 차이값과 
        vol_previous = 0  # 직전 거래량을 0으로 초기화
        return 0.0
    
    vol_previous = vol_current
    
    return vol_diff


def get_candle_avg_size(ccxt_ohlcv):
    """캔들의 평균 크기(%)를 반환합니다.

    Args: 
      - ccxt_ohlcv: ccxt의 fetch_ohlcv() 함수가 반환하는 값

    Returns: <class 'float'>
    """

    # 변수
    candle_per_sum = 0           ## 캔들 크기(%) 합계
    candle_per_avg = 0           ## 캔들 평균 크기
    ohlcv_len = len(ccxt_ohlcv)  ## 캔들 개수

    # 각 캔들의 증감률 및 전체 캔들의 평균 크기 계산
    for item in ccxt_ohlcv:
        open = item[1]
        close = item[4]
        rate = abs((close - open) / open) * 100  ## 증감율 = |(종가 - 시가) / 시가| * 100
        candle_per_sum = candle_per_sum + rate              ## 증감률을 누적한 후
    candle_per_avg = round(candle_per_sum / ohlcv_len, 2)   ## 캔들 개수만큼 나눠서 증감률 평균 계산

    return candle_per_avg


def is_all_bottomtail_candle(ccxt_ohlcv):
    """모든 캔들에 아래꼬리가 적당히(?) 달렸는지 확인합니다. 
    
    Args: ccxt_ohlcv: ccxt의 fetch_ohlcv() 함수가 반환하는 값
    
    Returns: <class 'bool'> 모든 캔들의 아래꼬리가 몸통보다 크면 True를 반환합니다.
    """

    for item in ccxt_ohlcv:
        open = item[1]
        low = item[3]
        close = item[4]
        
        if(close >= open):  # 양봉 캔들인 경우 
            body = close - open
            tail_bottom = open - low
        else:               # 음봉 캔들인 경우
            body = open - close
            tail_bottom = close - low

        if(body > tail_bottom):  # 몸통이 꼬리보다 크면 False
            return False  
            
    return True  # for 문을 무사히 돌았다면 모두 꼬리가 몸통보다 큰 캔들임


def is_all_uppertail_candle(ccxt_ohlcv):
    """모든 캔들에 위꼬리가 적당히(?) 달렸는지 확인합니다. 
    
    Args: ccxt_ohlcv: ccxt의 fetch_ohlcv() 함수가 반환하는 값
    
    Returns: <class 'bool'> 모든 캔들의 위꼬리가 몸통보다 크면 True를 반환합니다.
    """

    for item in ccxt_ohlcv:
        open = item[1]
        high = item[2]
        close = item[4]
        
        if(close >= open):  # 양봉 캔들인 경우
            body = close - open
            tail_upper = high - close
        else:               # 음봉 캔들인 경우
            body = open - close
            tail_upper = high - open

        if(body > tail_upper):  ## 몸통이 꼬리보다 크면 False
            return False
            
    return True  # for 문을 무사히 돌았다면 모두 꼬리가 적당히 달린 캔들임


def is_all_tail_candle(ccxt_ohlcv):
    """모든 캔들에 위꼬리 또는 아래꼬리가 적당히(?) 달렸는지 확인합니다. 
    
    Args: ccxt_ohlcv: ccxt의 fetch_ohlcv() 함수가 반환하는 값
    
    Returns: <class 'bool'> 모든 캔들의 꼬리가 몸통보다 크면 True를 반환합니다.
    """

    for item in ccxt_ohlcv:
        open = item[1]
        high = item[2]
        low = item[3]
        close = item[4]
        
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


# 코드 --------------------------------------------------------------------

# 초기화
load_dotenv()

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
bot = telegram.Bot(TELEGRAM_TOKEN)

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

# 레버리지 설정
resp = binance.fapiprivate_post_leverage({
    'symbol': SYMBOL,
    'leverage': LEVERAGE
})
pprint(resp)

# 포지션 자동매수 전략: 15분봉 캔들 크기가 0.3% 이상 & 1분 내로 거래량 오버슈팅 났을 때(캔들패턴 조건은 나중에 구현...)
while True:
    try: 
        ohlcv_15m = binance.fetch_ohlcv(TICKER, "15m", limit=1)
        price_current = ohlcv_15m[len(ohlcv_15m)-1][4]

        # 거래량이 터졌다면 거래량 터진 시간 저장
        volume = get_volume_difference(ohlcv_15m)
        if(volume >= STD_VOLUME_OVERSHOOTING):
            time_overshooting = datetime.now()

        # 캔들 크기 계산
        candle_15m_size = get_candle_avg_size(ohlcv_15m)

        # 시간 계산
        time_current = datetime.now()
        time_difference = time_current - time_overshooting
        time_difference_in_seconds = time_difference.total_seconds()
        # print(f"거래량: {volume} / 캔들크기: {candle_15m_size} / 시간차: {time_difference_in_seconds} / unixtime: {unixtime_15m_position}")

        # 포지션 자동매수 전략: 현재 15분봉 크기가 기준치 이상 & 기준시간 내로 거래량 오버슈팅 났을 때(캔들패턴 조건은 나중에 구현...)
        if(candle_15m_size >= STD_CANDLE_SIZE and time_difference_in_seconds <= STD_VOLUME_OVERSHOOTING_TIME_TERM):
            for item in list_auto_position:
                position = item[0]           # 포지션 유형(long / short)
                price = item[1]              # 포지션 에상가
                take_profit = item[2]        # 수익실현가
                stop_loss = item[3]          # 손절가
                amount = item[4]             # 포지션 수량
                is_position_taken = item[5]  # 포지션 생성 여부

                """
                * 포지션 자동매수 조건
                0. 현재 15분봉 크기가 기준치 이상이여야 하며, 기준시간(60초) 내로 거래량 오버슈팅이 나야 함
                1. 롱 또는 숏 포지션을 잡음(서로 조건이 약간 다름)
                2. 현재가가 포지션 예상가의 오차 범위 내에 있어야 함
                3. 아직 잡지 않은 포지션이여야 함
                4. 하나의 봉에 한 개의 포지션만 잡음(부처빔 같은 급격한 변동성 대응용이며, 봉 생성시간으로 구분함)
                """
                condition_long = (position == "long") and (price - (PRICE_ERROR * 2) <= price_current <= price + PRICE_ERROR) and (is_position_taken is False) and (unixtime_15m_position != ohlcv_15m[0][0])
                condition_short = (position == "short") and (price - PRICE_ERROR <= price_current <= price + (PRICE_ERROR * 2)) and (is_position_taken is False) and (unixtime_15m_position != ohlcv_15m[0][0])

                if(condition_long):
                    orders = [None] * 3
                    orders[0] = binance.create_order( # 롱(공매수) 포지션 시장가 주문
                        symbol=TICKER, 
                        type="MARKET",                ## MARKET: 시장가, LIMIT: 지정가
                        side="buy", 
                        amount=amount, 
                        # price=price,                ## LIMIT(지정가) 주문일 때 필요한 매개변수
                        params={
                            'positionSide': 'LONG'
                        }
                    )
                    orders[1] = binance.create_order(  # Take Profit 주문
                        symbol=TICKER,
                        type="TAKE_PROFIT_MARKET",
                        side="sell",
                        amount=amount,
                        params={
                            'positionSide': 'LONG',
                            'stopPrice': take_profit
                        }
                    )
                    orders[2] = binance.create_order(  # Stop Loss 주문
                        symbol=TICKER,
                        type="STOP_MARKET",
                        side="sell",
                        amount=amount,
                        params={
                            'positionSide': 'LONG',
                            'stopPrice': stop_loss
                        }
                    )
                    for order in orders:  # 주문 내역 출력
                        pprint(order)
                    asyncio.run(bot.sendMessage(TELEGRAM_CHAT_ID, text=f"Binacne {price} 근처 가격에 시장가로 Long 포지션 잡음."))

                if(condition_short):
                    orders = [None] * 3
                    orders[0] = binance.create_order(  # 숏(공매도) 포지션 주문
                        symbol=TICKER,
                        type="MARKET",                 ## MARKET: 시장가, LIMIT: 지정가
                        side="sell",
                        amount=amount,
                        # price=price,                 ## LIMIT(지정가) 주문일 때 필요한 매개변수
                        params={
                            'positionSide': 'SHORT'
                        }
                    )
                    orders[1] = binance.create_order(  # Take Profit 주문
                        symbol=TICKER,
                        type="TAKE_PROFIT_MARKET",
                        side="buy",
                        amount=amount,
                        params={
                            'positionSide': 'SHORT',
                            'stopPrice': take_profit
                        }
                    )
                    orders[2] = binance.create_order(  # Stop Loss 주문
                        symbol=TICKER,
                        type="STOP_MARKET",
                        side="buy",
                        amount=amount,
                        params={
                            'positionSide': 'SHORT',
                            'stopPrice': stop_loss
                        }
                    )
                    for order in orders:  # 주문내역 출력
                        pprint(order)
                    bot.sendMessage(TELEGRAM_CHAT_ID, text=f"Binacne {price} 근처 가격에 시장가로 Short 포지션 잡음.")
                    
                if(condition_long or condition_short):       # 플래그
                    item[5] = True                           ## 동일한 포지션을 잡지 않기 위해 포지션 생성 여부를 True 변경
                    unixtime_15m_position = ohlcv_15m[0][0]  ## 포지션 잡은 15분봉 시간 저장

    except Exception as e:
        pprint(e)
    
    time.sleep(1)
