# crypto-bot-python-v2

## 개요
가상화폐 롱숏 포지션 진입 시점이 다가왔다고 예상되었을 때 알림을 보내기 위한 파이썬 코드입니다.

**테스트 중인 코드이므로 정상적인 실행을 보장하지 않으며, 이 프로그램을 사용하여 발생하는 손해에 대한 책임은 사용자 본인에게 있습니다.**

## 사용한 주요 라이브러리
* ccxt: 바이낸스 API를 편하게 사용하기 위한 라이브러리
* python-telegram-bot: 텔레그램 메시지 전송을 위한 라이브러리
* numpy 및 pandas: 배열 처리를 쉽게 하기 위한 라이브러리
* python-dotenv: 환경변수(.env)를 사용하기 위한 라이브러리
* playsound: 사운드 재생을 위한 라이브러리

## 사용법
우선 루트 경로에 .env 파일을 만듭니다. 이 파일에 API 키 값을 명시합니다.

```
TELEGRAM_TOKEN = "tElEgRaMtOkEn"  # 텔레그렘 봇 토큰
TELEGRAM_CHAT_ID = 12345678990    # 텔레그램 봇 아이디
```

아직 미완성...