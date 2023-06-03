import sys
import logging
import project.log.client_log_config
import project.log.server_log_config
import traceback
import inspect


if sys.argv[0].find('client') == -1:
    logger = logging.getLogger('server')
else:
    logger = logging.getLogger('client')


def log(log_func):
    def for_logs(*args, **kwargs):
        logs = log_func(*args, **kwargs)
        logger.debug(f'Была вызвана функция {log_func.__name__} c параметрами {args}, {kwargs}. '
                     f'Вызов из модуля {log_func.__module__}. Вызов из'
                     f' функции {traceback.format_stack()[0].strip().split()[-1]}.'
                     f'Вызов из функции {inspect.stack()[1][3]}')
        return logs
    return for_logs
