from playsound import playsound
import time
import datetime
"""
Alarm/alarm.py
* Date: 2022. 9. 10.
* Author: Jeon Won
* Func: 비트코인 차트 5분봉, 15분봉 및 1시간봉이 갱신되기 30초 전에 알림음 재생
* Usage: `python3 alarm.py` 명령어 실행
"""

while True:
    # 현재 시간 가져오기
    now = datetime.datetime.now()

    # 각각 5분봉, 15분봉 및 1시간봉 갱신 직전 여부 플래그
    is_5m = False
    is_15m = False
    is_1h = False

    # 5분봉, 15분봉 또는 1시간봉 갱신 30초 전인지 판단
    if(divmod(now.minute, 5)[1] == 4 and now.second > 30):
        is_5m = True    
    if(divmod(now.minute, 15)[1] == 14 and now.second > 30):
        is_5m = False
        is_15m = True    
    if(divmod(now.minute, 60)[1] == 59 and now.second > 30):
        is_5m = False
        is_15m = False
        is_1h = True

    # 5분봉, 15분봉 및 1시간봉 갱신 30초 전에 사운드 재생 후 1분 쉼
    is_alarm_timing = is_5m or is_15m or is_1h
    if(is_alarm_timing):
        if(is_1h): 
            playsound('alarm_1h.mp3')
        if(is_15m): 
            playsound('alarm_15m.mp3')
        if(is_5m): 
            playsound('alarm_5m.mp3')
        time.sleep(60)

    # 이 작업을 1초 간격으로 수행
    time.sleep(1)