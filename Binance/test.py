import logging

logger = logging.getLogger(__name__)

# handler 생성 (stream, file) 및 logger instance에 handler 설정
streamHandler = logging.StreamHandler()
fileHandler = logging.FileHandler('./logs/test.log')
logger.addHandler(streamHandler)
logger.addHandler(fileHandler)

# logger level 설정
logger.setLevel(level=logging.INFO)

# log level 설정 및 log 남기기
logger.debug('my DEBUG log')
logger.info('my INFO log')
logger.warning('my WARNING log')
logger.error('my ERROR log')
logger.critical('my CRITICAL log')