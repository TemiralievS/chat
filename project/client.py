import sys
import json
import time
import logging
import log.client_log_config
from socket import *
from vars.vars import *
from funcJson.funcs import *


client_logger = logging.getLogger('client')


@log
def client_message_presence(account_name='user'):
    '''
    Функция формирует presence-сообщение со стороны клиента
    :param account_name:
    :return: dict
    '''

    message_dict = {
        jim_action: jim_presence,
        jim_time: time.time(),
        jim_user: {jim_account_name: account_name}
    }
    client_logger.info(f'{jim_presence} сообщение от {account_name}')
    return message_dict


@log
def server_message(answer):
    '''
    Функция принимает ответ от сервера
    :param answer:
    :return:
    '''
    client_logger.debug(f'Статус сообщения {answer}')
    if jim_response in answer:
        if answer[jim_response] == 200:
            return '200 — OK'
        else:
            return '4xx — client ERROR'
    raise ValueError


def main():
    try:
        server_address = sys.argv[1]
        server_port = int(sys.argv[2])
        if server_port < 1024 or server_port > 65535:
            client_logger.error('Неверный адрес')
            raise ValueError
    except IndexError:
        server_address = '127.0.0.1'
        server_port = 7777
    except ValueError:
        client_logger.error('The port must be in the range (1024:65535)')
        sys.exit(1)

    s = socket(AF_INET, SOCK_STREAM)
    s.connect((server_address, server_port))
    client_message = client_message_presence()
    send_message(s, client_message)

    try:
        server_answer = server_message(get_message(s))
        client_logger.debug(server_answer)
    except (ValueError, json.JSONDecodeError):
        client_logger.error('Структура сообщения не соответствует требованиям')


if __name__ == '__main__':
    main()

