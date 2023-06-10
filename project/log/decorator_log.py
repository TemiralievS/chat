import sys
import logging
import project.log.client_log_config
import project.log.server_log_config
import traceback
import inspect
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
                     f'Вызов из модуля {log_func.__module__}. Вызов из'
                     f' функции {traceback.format_stack()[0].strip().split()[-1]}.'
                     f'Вызов из функции {inspect.stack()[1][3]}', stacklevel=2)
        return logs
    return wrapper
