import sys
import os
import logging
sys.path.append('../')

CLIENT_FORMATTER = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s')

PATH = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(f'{PATH}/logs/client_logs', 'client.log')

err_hand = logging.StreamHandler(sys.stderr)
err_hand.setFormatter(CLIENT_FORMATTER)
err_hand.setLevel(logging.ERROR)
LOG_FILE = logging.FileHandler(PATH, encoding='utf8')
LOG_FILE.setFormatter(CLIENT_FORMATTER)

logger = logging.getLogger('client')
logger.addHandler(err_hand)
logger.addHandler(LOG_FILE)
logger.setLevel(logging.DEBUG)


if __name__ == '__main__':
    logger.critical('Критическая ошибка')
    logger.error('Ошибка')
    logger.debug('Отладочная информация')
    logger.info('Информационное сообщение')

