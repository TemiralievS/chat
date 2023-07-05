import sys
import logging
import socket

sys.path.append('../')


if sys.argv[0].find('client') == -1:
    logger = logging.getLogger('server')
else:
    logger = logging.getLogger('client')


def log(func_to_log):
    def log_saver(*args, **kwargs):
        logger.debug(
            f'Была вызвана функция {func_to_log.__name__} c параметрами {args} , {kwargs}.'
            f'Вызов из модуля {func_to_log.__module__}')
        ret = func_to_log(*args, **kwargs)
        return ret
    return log_saver


def login_required(func):

    def checker(*args, **kwargs):
        from server.core import MessageProcessor
        from common.vars import jim_action, jim_presence
        if isinstance(args[0], MessageProcessor):
            found = False
            for arg in args:
                if isinstance(arg, socket.socket):
                    for client in args[0].names:
                        if args[0].names[client] == arg:
                            found = True
            for arg in args:
                if isinstance(arg, dict):
                    if jim_action in arg and arg[jim_action] == jim_presence:
                        found = True
            if not found:
                raise TypeError
        return func(*args, **kwargs)

    return checker
