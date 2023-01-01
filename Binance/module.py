import numpy as np
import pandas as pd
import ccxt
from pprint import pprint

def get_vol_top_tickers(top_num=0):
    """바이낸스의 최근 24시간 기준 거래량 높은 코인들을 얻어옵니다. 바이낸스 ticker 종류가 워낙 많아 오래 걸림...

    Args: top_num (거래량 상위 몇 개의 코인들을 얻어올 것인가?)
    
    Returns: list (잘못된 매개변수를 입력한 경우 None)
    """

    binance = ccxt.binance()
    markets = binance.load_markets()

    # USDT ticker list 저장
    tickers = []
    for ticker in markets:
        if(ticker[-4:] == "USDT"):
            tickers.append(ticker)
    
    # 24시간 내 거래량(USDT) 데이터 저장
    usdt_vol_24h = []
    for ticker in tickers:
        t = binance.fetch_ticker(ticker)
        usdt_vol_24h.append([ticker, t["quoteVolume"]])

    # 거래량 데이터를 내림차순으로 정렬
    sorted_usdt_vol_24h = sorted(usdt_vol_24h, key=(lambda x: x[1]), reverse=True)
    
    if(top_num == 0):   # top_num 값이 0이면 모든 리스트 반환
        return sorted_usdt_vol_24h
    elif(top_num > 0):  # top_num 값이 0보다 크면 상위 리스트 반환
        return sorted_usdt_vol_24h[:top_num]
    else:
        return


def get_ccxt_volume_mean(ohlcv_list: list):
    """ccxt의 fetch_ohlcv() 함수가 반환하는 list 객체를 받아 평균 거래량을 반환합니다. 

    Args: 
        - ohlcv_list: list (ccxt의 fetch_ohlcv() 함수의 반환값)
    
    Returns: <class 'numpy.float64'>
    """

    # 거래량을 모아놓은 numpy 배열 생성
    volume_array = []
    for ohlcv in ohlcv_list:
        volume_array.append(ohlcv[5])
    volume_np_array = np.array(volume_array)

    # 거래량 평균 반환
    return volume_np_array.mean()
    

def get_ccxt_bb(ticker: str, ohlcv_list: list, multiplier: int = 2):
    """ccxt의 fetch_ohlcv() 함수가 반환하는 list 객체를 받아 볼린저 밴드에 사용되는 값(중심선, 상한선, 하한선)을 계산합니다. 

    Args: 
        - ticker: ticker (예: "BTC/USDT") 
        - ohlcv_list: list (ccxt의 fetch_ohlcv() 함수의 반환값)
        - multipler: 승수 (기본값: 2)
    
    Returns: <class 'dict'>
    """

    # 종가를 모아놓은 numpy 배열 생성
    close_array = []
    for ohlcv in ohlcv_list:
        close_array.append(ohlcv[4])
    close_np_array = np.array(close_array)

    # 볼린저 밴드에 사용되는 값들 계산
    current_price = ohlcv_list[len(ohlcv_list)-1][4]  # 현재가
    std = close_np_array.std()                        # 종가 기준 표준편차
    mbb = close_np_array.mean()                       # 볼린저 밴드 중심선(이동평균)
    ubb = mbb + std * multiplier                      # 상한선 = 중심선 + 기간 내 표준편차 * 승수
    lbb = mbb - std * multiplier                      # 하한선 = 중신선 + 기간 내 표준편차 * 승수
    per_b = (current_price - lbb) / (ubb - lbb)       # %b = (가격 - 볼린저밴드하단선) / (볼린저밴드상단선 - 볼린저밴드하단선)

    # 볼린저 밴드에 사용되는 값들을 딕셔너리 형태로 생성 후 반환
    dict_bb = {}
    dict_bb["ticker"] = ticker
    dict_bb["mbb"] = mbb
    dict_bb["ubb"] = ubb
    dict_bb["lbb"] = lbb
    dict_bb["current_price"] = current_price
    dict_bb["per_b"] = per_b
    
    return dict_bb


def get_ccxt_candle_len_mean(ohlcv_list: list):
    """ccxt의 fetch_ohlcv() 함수가 반환하는 list 객체를 받아 캔들의 평균 캔들길이를 계산합니다. 

    Args: 
        - ohlcv_list: list (ccxt의 fetch_ohlcv() 함수의 반환값)

    Returns: <class 'numpy.float64'>
    """

    # 시가-종가 차이 값을 모아놓은 numpy 배열 생성
    len_array = []
    for ohlcv in ohlcv_list:
        len_array.append(abs(ohlcv[1] - ohlcv[4]))
    len_np_array = np.array(len_array)

    # 고가-저가 차이 평균값 반환
    return len_np_array.mean()


def get_ccxt_rsi(ohlcv_list: list):
    """ccxt의 fetch_ohlcv() 함수가 반환하는 list 객체를 받아 RSI 값을 계산합니다. (코드 출처: https://codereader37.tistory.com/173)

    Args: 
        - ohlcv_list: list (ccxt의 fetch_ohlcv() 함수의 반환값)
    
    Returns: <class 'numpy.float64'>
    """
    df = pd.DataFrame(ohlcv_list)
    rsi = rsi_calc(df, 14).iloc[-1]
    return rsi


def rsi_calc(ohlc: pd.DataFrame, period: int = 14):
    """DataFrame을 받아 RSI 값을 계산합니다. (코드 출처: https://codereader37.tistory.com/173)

    Args: 
        - ohlc: ccxt의 fetch_ohlcv() 함수가 반환하는 list를 Pandas DataFrame으로 변환한 객체
        - period: 이동평균 길이(기본: 14)
    
    Returns: <class 'pandas.core.series.Series'>
    """
    ohlc = ohlc[4].astype(float)
    delta = ohlc.diff()
    gains, declines = delta.copy(), delta.copy()
    gains[gains < 0] = 0
    declines[declines > 0] = 0

    _gain = gains.ewm(com=(period-1), min_periods=period).mean()
    _loss = declines.abs().ewm(com=(period-1), min_periods=period).mean()

    RS = _gain / _loss

    return pd.Series(100-(100/(1+RS)), name="RSI")
