import logging.handlers
import logging
import os
import sys

sys.path.append('../')


SERVER_FORMATTER = logging.Formatter('%(asctime)s %(levelname)s %(filename)s %(message)s')

PATH = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(f'{PATH}/logs/server_logs', 'server.log')

err_hand = logging.StreamHandler(sys.stderr)
err_hand.setFormatter(SERVER_FORMATTER)
err_hand.setLevel(logging.ERROR)
LOG_FILE = logging.handlers.TimedRotatingFileHandler(PATH, encoding='utf8', interval=1, when='D')
LOG_FILE.setFormatter(SERVER_FORMATTER)

logger = logging.getLogger('server')
logger.addHandler(err_hand)
logger.addHandler(LOG_FILE)
logger.setLevel(logging.DEBUG)


if __name__ == '__main__':
    logger.critical('Критическая ошибка')
    logger.error('Ошибка')
    logger.debug('Отладочная информация')
    logger.info('Информационное сообщение')


