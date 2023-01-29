# crypto-bot-python-v2

## 개요

가상화폐 포지션 진입 시점이 다가왔다고 예상되었을 때 알림을 보내기 위한 파이썬 코드입니다.

**테스트 중인 코드이므로 정상적인 실행을 보장하지 않으며, 이 프로그램을 사용하여 발생하는 손해에 대한 책임은 사용자 본인에게 있습니다.**

## 사용한 주요 라이브러리
* ccxt: 바이낸스 API를 편하게 사용하기 위한 라이브러리
* python-telegram-bot: 텔레그램 메시지 전송을 위한 라이브러리
* numpy 및 pandas: 배열 처리를 쉽게 하기 위한 라이브러리
* python-dotenv: 환경변수(.env)를 사용하기 위한 라이브러리
* playsound: 사운드 재생을 위한 라이브러리

## 사용법(Binance)

우선 루트 경로에 `.env` 파일을 만듭니다. 이 파일에 텔레그램 API 키 값을 명시합니다. 텔레그램 API는 텔레그램 메시지를 전송할 때 사용됩니다.

```
TELEGRAM_TOKEN = "tElEgRaMtOkEn"  # 텔레그렘 봇 토큰
TELEGRAM_CHAT_ID = 12345678990    # 텔레그램 봇 아이디
```

### 차트 조사: alarm.py

`Binance/alarm.py` 파일을 열어 설정을 위한 상수 값을 입력합니다.

```python
TICKERS = ["BTC/USDT", "ETH/USDT"]  # 비트코인과 이더리움 조사
TICKER_INTERVAL = sys.argv[1]                           # 자동으로 입력되는 값
INTERVAL = int(re.sub(r'[^0-9]', '', TICKER_INTERVAL))  # 자동으로 입력되는 값

# 캔들 카운트(캔들 몇 개로 각 지표들을 조사할 것인가?)
COUNT_RSI = 200
COUNT_VOL = 70
COUNT_CANDLE_LEN = 70
COUNT_BB = 20
COUNT_MAX = max(COUNT_RSI, COUNT_VOL, COUNT_CANDLE_LEN, COUNT_BB)

# 알림 여부
IS_VOLUME_ALARM = True  # 거래량 알림 보내려면 True로...
IS_RSI_ALARM = True     # RSI 알림 보내려면 True로...
IS_CANDLE_ALARM = True  # 캔들크기 알림 보내려면 True로...
IS_BB_ALARM = True      # 볼린저 밴드 %B 알림 보내려면 True로...

# 알림 조건
ALERT_RSI_OVERBOUGHT = 75   # RSI 과매수 조건(RSI 값이 이 값보다 크면 과매수 알림)
ALERT_RSI_OVERSOLD = 25     # RSI 과매도 조건(RSI 값이 이 값보다 작으면 과매도 알림)
ALERT_VOL = 3               # 거래량 조건(현재 거래량이 평균 거래량보다 이 값의 배만큼 터졌을 때 알림)
ALERT_CANDLE_LEN = 3        # 캔들크기 조건(현재 캔들크기가 평균 캔들크기보다 이 값의 배만큼 터졌을 때 알림)
ALERT_BB_OVERBOUGHT = 1.1   # 볼린저 밴드 %B 과매수 조건(현재 %B 값이 이 값보다 크면 과매수 알림)
ALERT_BB_OVERSOLD = -0.1    # 볼린저 밴드 %B 과매도 조건(현재 %B 값이 이 값보다 작으면 과매도 알림)

# 알림 방법
IS_ALARM_SOUND = True     # 사운드 알림 보내려면 True로...
IS_ALARM_TELEGRAM = True  # 텔레그램 알림 보내려면 True로...
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")      # 텔레그렘 봇 토큰(자동으로 입력되는 값)
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")  # 텔레그램 봇 아이디(자동으로 입력되는 값)

# 한 ticker를 조사한 후 다음 ticker를 조사하기 전 쉴 시간(초)
SLEEP_TIME = 1
```

5분봉을 조사하려면 `python3 Binance/alert.py 5m` 명령어를 실행합니다. 5m 대신 1m, 3m, 15m, 30m, 1h, 4h, 12h를 입력할 수 있습니다.

5분봉을 백그라운드로 실행하여 조사하려면 `nohup python3 Binance/alert.py 5m &` 명령어를 실행하여 백그라운드로 작동시킵니다.

프로그램을 실행하면 logs 폴더에 프로그램 작동 및 알림 이력 로그를 기록합니다.

### 순간 거래량 탐지: vol_val_scan.py

`Binance/vol_val_scan.py` 파일을 열어 설정을 위한 상수 값을 입력합니다. SLEEP_TIME 값이 1이면 1초 간격으로 거래량이 얼마나 발생했는지 계산합니다. VOL_STANDARD 값이 100이면 거래량이 100 이상 발생 시 알림을 보냅니다.

```python
TICKER = "BTC/USDT"    # 거래량을 탐지할 바이낸스 거래소 Ticker
INTERVAL = "15m"       # 캔들 유형
SLEEP_TIME = 1         # 탐지 간격(초)
VOL_STANDARD = 100     # 거래량 기준치(거래량이 얼마 이상 발생했을 때 알림을 줄 것인가?)
IS_ALARMING = True     # 소리 알림 여부
IS_TELEGRAMING = True  # 텔레그램 알림 여부
IS_LOGGING = True      # 로그 기록 여부
```

상수 값을 입력한 후 `nohup python3 Binance/vol_val_scan.py &` 명령어를 실행하여 백그라운드로 작동시킵니다.

IS_LOGGING 값이 True이면 Binance 폴더에 logs 폴더를 만들어놔야 하며, logs 폴더에 거래량 알림 발생 로그를 기록합니다.


## 업비트 가상화폐 차트 조사

요즘 가상화폐 현물장은 단타 치기에 영 좋지 않기 때문에 나중에...