import asyncio
import ccxt.pro as ccxtpro
from datetime import datetime, timezone, timedelta
"""
Binance/watch_orderbook.py
* Date: 2023. 8. 23.
* Author: Jeon Won
* Func: Binance 오더북 정보(가격, 물량) 표출
* Usage: 상수 값 입력 후 `python3 watch_orderbook.py` 명령어 실행
"""

# 클래스 --------------------------------------------------------------------

class Colors:  # 매도호가(RED) 및 매수호가(GREEN) 색상 표시를 위한 클래스
    RED = '\033[31m'
    GREEN = '\033[32m'
    RESET = '\033[0m'

# 상수 --------------------------------------------------------------------

TICKER = "BTC/USDT" 
MULTIPLE = 5          ## 호가가격 단위(USDT)
ORDERBOOK_COUNT = 10  ## 매도(매수)호가 개수

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

def limit_dict_size(dictionary, max_items):
    """Dictionary Item 개수를 제한합니다.
    
    Args:
      - dictinary: Dictionary 객체
      - max_items: Dictionary 객체가 가질 수 있는 최대 아이템 개수

    Returns: <class 'dict'>
    """
    if len(dictionary) <= max_items:
        return dictionary
    
    reduced_dict = {}
    count = 0
    
    for key, value in dictionary.items():
        if count < max_items:
            reduced_dict[key] = value
            count += 1
        else:
            break
    
    return reduced_dict

async def main():
    # 초기화
    exchange = ccxtpro.binance(config={
        'enableRateLimit': True,
        'options': {
            'defaultType': 'future'
        }
    })

    while True:
        # 주요 변수
        dict_asks = {}  ## 매도호가 정보를 호가가격 단위로 가공하여 담을 총괄(?) 딕셔너리
        dict_bids = {}  ## 매수호가 정보를 호가가격 단위로 가공하여 담을 총괄(?) 딕셔너리
        ticker_info = await exchange.watch_ticker(symbol=TICKER)  ## ticker 정보
        current_price = ticker_info["close"]                      ## 현재가
        orderbook = await exchange.watch_order_book(symbol=TICKER, limit=1000)  ## 오더북 정보
        asks = orderbook["asks"]  ## 매도호가
        bids = orderbook["bids"]  ## 매수호가

        for item in asks:  ## item: [가격, 물량]
            key = str(int(item[0] / MULTIPLE) * MULTIPLE)        ## 매도호가를 호가가격 단위로 가공

            if(key not in dict_asks.keys()):                     ## 딕셔너리에 해당 매도호가가 없다면
                dict_asks[key] = 0                               ## 0으로 초기화
            dict_asks[key] = round(dict_asks[key] + item[1], 3)  ## 딕셔너리에 해당 매도호가가 있으면 누적

        for item in bids:  
            key = str(int(item[0] / MULTIPLE) * MULTIPLE)        ## 매수호가를 호가가격 단위로 가공

            if(key not in dict_bids.keys()):                     ## 딕셔너리에 해당 매수호가가 없다면
                dict_bids[key] = 0                               ## 0으로 초기화
            dict_bids[key] = round(dict_bids[key] + item[1], 3)  ## 딕셔너리에 해당 매수호가가 있으면 누적

        # 매도(매수)호가 개수 제한
        dict_asks = limit_dict_size(dict_asks, ORDERBOOK_COUNT)
        dict_bids = limit_dict_size(dict_bids, ORDERBOOK_COUNT)

        # 매도(매수)호가 물량 합 계산
        sum_asks = round(sum(dict_asks.values()), 3)
        sum_bids = round(sum(dict_bids.values()), 3)

        # 매도(매수)호가를 내림차순으로 출력하기 위한 키 배열 생성
        key_dict_asks = sorted(dict_asks.keys(), reverse=True)
        key_dict_bids = sorted(dict_bids.keys(), reverse=True)

        # 출력(현재시간)
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"# {current_time} Binance {TICKER} Order Book")

        # 출력(매도호가)
        for key in key_dict_asks:
            print(f"{Colors.RED}{key}{Colors.RESET}: {dict_asks[key]}")
        
        # 출력(현재가, 매도물량, 매수물량)
        if(sum_asks > sum_bids):    ## 매도물량 > 매수물량 시 매도물량을 빨간색으로 표시
            print(f"# 현재가: {current_price} / {Colors.RED}매도물량: {sum_asks}{Colors.RESET} / 매수물량: {sum_bids}")
        elif(sum_asks < sum_bids):  ## 매도물량 < 매수물량 시 매수물량을 초록색으로 표시
            print(f"# 현재가: {current_price} / 매도물량: {sum_asks} / {Colors.GREEN}매수물량: {sum_bids}{Colors.RESET}")
        else:    
            print(f"# 현재가: {current_price} / 매도물량: {sum_asks} / 매수물량: {sum_bids}")

        # 출력(매수호가)
        for key in key_dict_bids:
            print(f"{Colors.GREEN}{key}{Colors.RESET}: {dict_bids[key]}")
        print("----------")
        
asyncio.run(main())