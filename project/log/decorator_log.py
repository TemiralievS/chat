import sys
import logging
from functools import wraps


if sys.argv[0].find('client') == -1:
    logger = logging.getLogger('server')
else:
    logger = logging.getLogger('client')


def log(log_func):
    @wraps(log_func)
    def wrapper(*args, **kwargs):
        logs = log_func(*args, **kwargs)
        logger.debug(f'Была вызвана функция {log_func.__name__} c параметрами {args}, {kwargs}. '
                     f'Вызов из модуля {log_func.__module__}.', stacklevel=2)
        return logs
    return wrapper
