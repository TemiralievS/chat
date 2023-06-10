import socket
import sys
import json
import time
import logging
import argparse
import log.client_log_config
from log.decorator_log import *
from errs.errors import *
from socket import *
from vars.vars import *
from funcJson.funcs import *

client_logger = logging.getLogger('client')


@log
def message_from_another_client(message):
    if jim_action in message and message[jim_action] == jim_message and \
            jim_sender in message and jim_message_txt in message:
        print(f'Входящее сообщение от {message[jim_sender]}: {message[jim_message_txt]}')
        client_logger.info(f'Входящее сообщение от {message[jim_sender]}: {message[jim_message_txt]}')
    else:
        client_logger.error(f'Ошибка чтения сообщения: {message}')


@log
def client_message_message(sock, account_name='user'):
    message = input('Введите сообщени, exit для выхода: ')
    if message == 'exit':
        sock.close()
        client_logger.info('Выход')
        print('exit from chat')
        sys.exit(0)
    message_dict = {
        jim_action: jim_message,
        jim_time: time.time(),
        jim_user: account_name,
        jim_message_txt: message
    }
    client_logger.debug(f'Сообщение {message_dict} от {account_name}')
    return message_dict


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


@log
def arguments_parser():
    '''
    Функция, которая забирает аргументы из командной строки
    :return:
    server_address - ip-адрес сервера
    server_port  - порт сервера
    client_mode - режим, в котором работает клиент
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default='127.0.0.1', nargs='?')
    parser.add_argument('port', default=7777, type=int, nargs='?')
    parser.add_argument('-m', '--mode', default='listen', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.addr
    server_port = namespace.port
    client_mode = namespace.mode

    if not 1023 < server_port < 65536:
        client_logger.critical(
            f'Попытка запуска клиента с неподходящим номером порта: {server_port}. '
            f'Допустимы адреса с 1024 до 65535. Клиент завершается.')
        sys.exit(1)
    if client_mode not in ('listen', 'send'):
        client_logger.critical(f'Указан недопустимый режим работы {client_mode}, '
                        f'допустимые режимы: listen , send')
        sys.exit(1)

    return server_address, server_port, client_mode


def main():
    server_address, server_port, client_mode = arguments_parser()

    client_logger.info('адрес сервера: {server_address}, порт: {server_port}, режим работы: {client_mode}')

    try:
        s = socket(AF_INET, SOCK_STREAM)
        s.connect((server_address, server_port))
        send_message(s, client_message_presence())
        answer = server_message(get_message(s))
        client_logger.info(f'Соединение с сервером. Ответ сервера: {answer}')
        print(f'Соединение с сервером')
    except json.JSONDecodeError:  # - блок ошибок, при соединении с сервером -
        client_logger.error('Ошибка декодирования строки')
        sys.exit(1)
    except ServerError as errr:
        client_logger.error(f'Ошибка при соединении с сервером: {errr.text}')
        sys.exit(1)
    except ReqFieldMissingError as missing_error:
        client_logger.error(f'Пропущено необходимое поле: {missing_error.missing_field}')
        sys.exit(1)
    except ConnectionRefusedError:
        client_logger.error('Отсутствует разрешение на присоединение')
        sys.exit(1)
    else:
        if client_mode == 'send':
            try:
                send_message(s, client_message_message(s))
            except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
                client_logger.error(f'{server_address} - соединение разорвано')
                sys.exit(1)

        if client_mode == 'listen':
            try:
                message_from_another_client(get_message(s))
            except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
                client_logger.error(f'{server_address} - соединение разорвано')
                sys.exit(1)


if __name__ == '__main__':
    main()

