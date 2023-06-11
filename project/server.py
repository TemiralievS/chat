import sys
import logging
import argparse
import select
import time
import log.server_log_config
from log.decorator_log import *
from socket import *
from vars.vars import *
from funcJson.funcs import *


server_logger = logging.getLogger('server')


@log
def message_from_to_client(message, messages_list, client, clients_lst, names):
    '''
    Функция принимает сообщение от клиента в виде словаря,
    проверяет правильность структуры сообщения,
    возвращает ответ клиенту в виде словаря
    '''
    server_logger.debug(f'Клиент отправил сообщение {message}')

    if jim_action in message and message[jim_action] == jim_presence and jim_time in message \
            and jim_user in message:
        if message[jim_user][jim_account_name] not in names.keys():
            names[message[jim_user][jim_account_name]] = client
            send_message(client, {jim_response: 200})
        else:
            response = {jim_response: 400, jim_error: 'Пользователь с таким именем существует'}
            send_message(client, response)
            clients_lst.remove(client)
            client.close()
        return

    elif jim_action in message and message[jim_action] == jim_message and \
            jim_waiter in message and jim_time in message \
            and jim_sender in message and jim_message_txt in message:
        messages_list.append(message)
        return

    elif jim_action in message and message[jim_action] == jim_exit and \
            jim_account_name in message:
        clients_lst.remove(names[message[jim_account_name]])
        names[message[jim_account_name]].close()
        del names[message[jim_account_name]]
        return

    else:
        response = {jim_response: 400, jim_error: 'Ошибка запроса'}
        send_message(client, response)
        return


@log
def message_status(message, names, listen_socks):
    if message[jim_waiter] in names and names[message[jim_waiter]] in listen_socks:
        send_message(names[message[jim_waiter]], message)
        server_logger.info(f'Пользователь {message[jim_sender]} отправил сообщение пользователю {message[jim_waiter]}')
    elif message[jim_waiter] in names and names[message[jim_waiter]] not in listen_socks:
        raise ConnectionError
    else:
        server_logger.error(f'Пользователя с именем {message[jim_waiter]} не существует')


@log
def arguments_parser():
    '''
    Функция, которая забирает аргументы из командной строки
    :return:
    listen_address - ip-адрес сервера
    listen_port  - порт сервера
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=7777, type=int, nargs='?')
    parser.add_argument('-a', default='', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p

    if not 1023 < listen_port < 65536:
        server_logger.critical(
            f'Попытка запуска клиента с неподходящим номером порта: {listen_port}. '
            f'Допустимы адреса с 1024 до 65535. Клиент завершается.')
        sys.exit(1)
    return listen_address, listen_port


def main():
    '''
    Запуск с параметрами командной строки
    Без параметров используются значения по умолчанию
    :return:
    '''

    listen_address, listen_port = arguments_parser()
    server_logger.info(f'Запуск сервера. Порт {listen_port}, адрес {listen_address}')

    s = socket(AF_INET, SOCK_STREAM)
    s.bind((listen_address, listen_port))
    s.settimeout(0.5)

    clients_lst = []
    messages_list = []
    names_dct = dict()

    s.listen(5)

    while True:
        try:
            client, addr = s.accept()
        except OSError:
            pass
        else:
            server_logger.info(f'Соединение с {addr}')
            clients_lst.append(client)

        recv_lst = []
        send_lst = []
        errors_lst = []

        try:
            if clients_lst:
                recv_lst, send_lst, errors_lst = select.select(clients_lst, clients_lst, [], 0)
        except OSError:
            pass

        if recv_lst:
            for sender in recv_lst:
                try:
                    message_from_to_client(get_message(sender), messages_list, sender, clients_lst, names_dct)

                except Exception:
                    server_logger.info(f'{sender.getpeername()} отключился')
                    clients_lst.remove(sender)

        for messg in messages_list:
            try:
                message_status(messg, names_dct, send_lst)
            except Exception:
                server_logger.info(f'Разорвано соединение с {messg[jim_waiter]}')
                clients_lst.remove(names_dct[messg[jim_waiter]])
                del names_dct[messg[jim_waiter]]
        messages_list.clear()


if __name__ == '__main__':
    main()
