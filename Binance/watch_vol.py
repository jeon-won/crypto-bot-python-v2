import asyncio
import ccxt.pro as ccxtpro
from pprint import pprint
from datetime import datetime, timedelta, timezone

# 상수

TICKER = "BTC/USDT"
INTERVAL = "15m"
VOL_VAL_STANDARD = 200

def convert_to_gmt9(input_str):
    # 문자열에서 마지막 6개 문자 (.445Z)를 제외하고 파싱
    dt_utc = datetime.strptime(input_str[:-6], '%Y-%m-%dT%H:%M:%S')
    
    # GMT+9 시간대로 변환
    gmt_offset = timedelta(hours=9)
    dt_gmt9 = dt_utc + gmt_offset
    
    return dt_gmt9


async def main():
    # 초기화
    exchange = ccxtpro.binance(config={
        'enableRateLimit': True,
        'options': {
            'defaultType': 'future'
        }
    })

    while True: 
        trades = await exchange.watch_trades(symbol=TICKER)
        # pprint(trades)
        for item in trades:
            order_datetime = item['datetime'].split('.')[0].replace('T', ' ')
            order_amount = item['amount']
            order_type = item['side']
            order_cost = item['cost']
            print(f"{order_datetime}: {order_type} {order_amount}")

asyncio.run(main())