import socket
import sys
import json
import time
import logging
import argparse
import threading
import log.client_log_config
from log.decorator_log import *
from errs.errors import *
from socket import *
from vars.vars import *
from funcJson.funcs import *

client_logger = logging.getLogger('client')


@log
def bye_bye_message(account_name):
    return {
        jim_action: jim_exit,
        jim_time: time.time(),
        jim_account_name: account_name
    }


@log
def message_from_another_client(sock, my_name):
    while True:
        try:
            message = get_message(sock)
            if jim_action in message and message[jim_action] == jim_message and \
                    jim_sender in message and jim_waiter in message and jim_message_txt in message\
                    and message[jim_waiter] == my_name:
                print(f'Входящее сообщение от {message[jim_sender]}: {message[jim_message_txt]}')
                client_logger.info(f'Входящее сообщение от {message[jim_sender]}: {message[jim_message_txt]}')
            else:
                client_logger.error(f'Ошибка чтения сообщения: {message}')
        except IncorrectDataRecivedError:
            client_logger.error(f'DECODING ERROR!')
        except (OSError, ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError):
            client_logger.critical(f'Разорвано соединение с сервером')
            break


@log
def client_message_message(sock, account_name='user'):
    waiter = input('Кому отправить сообщение: ')
    message = input('Введите сообщениe: ')

    message_dict = {
        jim_action: jim_message,
        jim_sender: account_name,
        jim_waiter: waiter,
        jim_time: time.time(),
        jim_message_txt: message
    }
    client_logger.debug(f'Сообщение {message_dict} от {account_name}')
    try:
        send_message(sock, message_dict)
        client_logger.info(f'Пользователь {waiter} скоро получит ваше сообщение')
    except:
        client_logger.critical('Сервер не отвечает')
        sys.exit(1)


@log
def client_message_presence(account_name):
    '''
    Функция формирует presence-сообщение со стороны клиента
    :param account_name:
    :return: dict
    '''

    out = {
        jim_action: jim_presence,
        jim_time: time.time(),
        jim_user: {
            jim_account_name: account_name
        }
    }
    client_logger.info(f'{jim_presence} сообщение от {account_name}')
    return out


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
            return '200 : OK'
        elif answer[jim_response] == 400:
            raise ServerError(f'400 : {answer[jim_error]}')
    raise ReqFieldMissingError(jim_response)


@log
def user_commands(sock, user):
    print_info()
    while True:
        command = input('Что тебе нужно? :')
        if command == 'message':
            client_message_message(sock, user)
        elif command == 'help':
            print_info()
        elif command == 'exit':
            send_message(sock, bye_bye_message(user))
            print('reservuar')
            client_logger.info(f'Пользователь {user} покинул чат')
            time.sleep(1)
            break
        else:
            print('Прочтите еще раз список команд')


def print_info():
    print('Список команд:    ')
    print('  message - отправить сообщение\n  help - список команд\n  exit-выход')



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
    parser.add_argument('-n', '--name', default=None, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.addr
    server_port = namespace.port
    client_name = namespace.name

    if not 1023 < server_port < 65536:
        client_logger.critical(
            f'Попытка запуска клиента с неподходящим номером порта: {server_port}. '
            f'Допустимы адреса с 1024 до 65535. Клиент завершается.')
        sys.exit(1)

    return server_address, server_port, client_name


def main():
    print('Client running')
    server_address, server_port, client_name = arguments_parser()

    if not client_name:
        client_name = input('Имя пользователя: ')

    client_logger.info(f'Запущен клиент с парамeтpами: адрес сервера: {server_address}, '
        f'порт: {server_port}, имя пользователя: {client_name}')

    try:
        s = socket(AF_INET, SOCK_STREAM)
        s.connect((server_address, server_port))
        send_message(s, client_message_presence(client_name))
        answer = server_message(get_message(s))
        client_logger.info(f'Соединение с сервером. Ответ сервера: {answer}')
        print(f'Соединение с сервером выполнено')
    except json.JSONDecodeError:  # - блок ошибок, при соединении с сервером -
        client_logger.error('Ошибка декодирования строки')
        sys.exit(1)
    except ServerError as errr:
        client_logger.error(f'Ошибка при соединении с сервером: {errr.text}')
        sys.exit(1)
    except ReqFieldMissingError as missing_error:
        client_logger.error(f'Пропущено необходимое поле: {missing_error.missing_field}')
        sys.exit(1)
    except (ConnectionRefusedError, ConnectionError):
        client_logger.critical('Отсутствует разрешение на присоединение')
        sys.exit(1)
    else:
        receiver = threading.Thread(target=message_from_another_client, args=(s, client_name))
        receiver.daemon = True
        receiver.start()

        user_interface = threading.Thread(target=user_commands, args=(s, client_name))
        user_interface.daemon = True
        user_interface.start()
        client_logger.debug('Запущены процессы')

        while True:
            time.sleep(1)
            if receiver.is_alive() and user_interface.is_alive():
                continue
            break


if __name__ == '__main__':
    main()

