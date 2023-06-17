from collections.abc import Callable, Iterable, Mapping
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
from vars.vars import *
from funcJson.funcs import *
from meta import ClientCheck

client_logger = logging.getLogger('client')


class ClientSend(threading.Thread, metaclass=ClientCheck):
    def __init__(self, account_name, sock):
        self.account_name = account_name
        self.sock = sock
        super().__init__()
        

    # Функция словарь-сообщение о выходе.
    def bye_bye_message(self):
        return {
            jim_action: jim_exit,
            jim_time: time.time(),
            jim_account_name: self.account_name
    }


    # Функция запрашивает адресата и само сообщение аресату, затем отправляет сообщение на сервер.    
    def client_message_message(self):
        waiter = input('Кому отправить сообщение: ')
        message = input('Введите сообщениe: ')

        message_dict = {
            jim_action: jim_message,
            jim_sender: self.account_name,
            jim_waiter: waiter,
            jim_time: time.time(),
            jim_message_txt: message
        }
        client_logger.debug(f'Сообщение {message_dict}')
        try:
            send_message(self.sock, message_dict)
            client_logger.info(f'Пользователь {waiter} скоро получит ваше сообщение')
        except:
            client_logger.critical('Сервер не отвечает')
            sys.exit(1)


    
    # Функция запрашивает-получает команды от пользователя, отправляет сообщения
    def run(self):
        self.print_info()
        while True:
            command = input('Что тебе нужно? :')
            if command == 'message':
                self.client_message_message()
            elif command == 'help':
                self.print_info()
            elif command == 'exit':
                try:
                    send_message(self.sock, self.bye_bye_message())
                except:
                    pass
                print('reservuar')
                client_logger.info(f'Пользователь покинул чат')
                time.sleep(1)
                break
            else:
                print('Прочтите еще раз список команд')


    # Функция показывающая список команд доступных пользователю.
    def print_info(self):
        print('Список команд:    ')
        print('  message - отправить сообщение\n  help - список команд\n  exit-выход')


class ClientWait(threading.Thread, metaclass=ClientCheck):
    def __init__(self, account_name, sock):
        self.account_name = account_name
        self.sock = sock
        super().__init__()

    
    # Функция принимает сообщение, выводит его в консоль.
    def run(self):
        while True:
            try:
                message = get_message(self.sock)
                if jim_action in message and message[jim_action] == jim_message and \
                        jim_sender in message and jim_waiter in message and jim_message_txt in message\
                        and message[jim_waiter] == self.account_name:
                    print(f'Входящее сообщение от {message[jim_sender]}: {message[jim_message_txt]}')
                    client_logger.info(f'Входящее сообщение от {message[jim_sender]}: {message[jim_message_txt]}')
                else:
                    client_logger.error(f'Ошибка чтения сообщения: {message}')
            except IncorrectDataRecivedError:
                client_logger.error(f'DECODING ERROR!')
            except (OSError, ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError):
                client_logger.critical(f'Разорвано соединение с сервером')
                break




# Функция формирует presence-сообщение со стороны клиента
@log
def client_message_presence(account_name):
    out = {
        jim_action: jim_presence,
        jim_time: time.time(),
        jim_user: {
            jim_account_name: account_name
        }
    }
    client_logger.info(f'{jim_presence} сообщение от {account_name}')
    return out


# Функция принимает-разбирает ответ от сервера 
@log
def server_message(answer):
    client_logger.debug(f'Статус сообщения {answer}')
    if jim_response in answer:
        if answer[jim_response] == 200:
            return '200 : OK'
        elif answer[jim_response] == 400:
            raise ServerError(f'400 : {answer[jim_error]}')
    raise ReqFieldMissingError(jim_response)


# Функция, которая забирает(парсит) аргументы из командной строки
@log
def arguments_parser():
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
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
        module_receiver = ClientWait(client_name, s)
        module_receiver.daemon = True
        module_receiver.start()

        module_sender = ClientSend(client_name, s)
        module_sender.daemon = True
        module_sender.start()
        client_logger.debug('Запущено')
        
        while True:
            time.sleep(1)
            if module_receiver.is_alive() and module_sender.is_alive():
                continue
            break


if __name__ == '__main__':
    main()
