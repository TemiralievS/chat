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
from client_db import ClientDatabase


client_logger = logging.getLogger('client')

sock_lock = threading.Lock()
database_lock = threading.Lock()


class ClientSend(threading.Thread, metaclass=ClientCheck):
    def __init__(self, account_name, sock, database):
        self.account_name = account_name
        self.sock = sock
        self.database = database
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

        with database_lock:
            if not self.database.check_user(waiter):
                client_logger.error(f'Попытка отправить сообщение незарегистрированому получателю: {waiter}')
                return

        message_dict = {
            jim_action: jim_message,
            jim_sender: self.account_name,
            jim_waiter: waiter,
            jim_time: time.time(),
            jim_message_txt: message
        }
        client_logger.debug(f'Сообщение {message_dict}')

        with database_lock:
            self.database.save_message(self.account_name , waiter , message)

        with sock_lock:
            try:
                send_message(self.sock, message_dict)
                client_logger.info(f'Пользователь {waiter} скоро получит ваше сообщение')
            except OSError as err:
                if err.errno: 
                    client_logger.critical('Сервер не отвечает')
                    sys.exit(1)
                else:
                    client_logger.error('Не удалось передать сообщение. Таймаут соединения')


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
                with sock_lock:
                    try:
                        send_message(self.sock, self.bye_bye_message())
                    except:
                        pass
                    print('reservuar')
                    client_logger.info(f'Пользователь покинул чат')
                time.sleep(1)
                break

            elif command == 'contacts':
                with database_lock:
                    contacts_list = self.database.get_contacts()
                for contact in contacts_list:
                    print(contact)

            elif command == 'edit':
                self.edit_contacts()

            elif command == 'history':
                self.print_history()

            else:
                print('Прочтите еще раз список команд')


    # Функция показывающая список команд доступных пользователю.
    def print_info(self):
        print('Список команд:    ')
        print('message - отправить сообщение.')
        print('history - история сообщений')
        print('contacts - список контактов')
        print('edit - редактирование списка контактов')
        print('help - вывести подсказки по командам')
        print('exit - выход')

    
    def print_history(self):
        ask = input('Показать входящие сообщения - in, исходящие - out, все - просто Enter: ')
        with database_lock:
            if ask == 'in':
                history_list = self.database.get_history(to_who=self.account_name)
                for message in history_list:
                    print(f'\nСообщение от пользователя: {message[0]} от {message[3]}:\n{message[2]}')
            elif ask == 'out':
                history_list = self.database.get_history(from_who=self.account_name)
                for message in history_list:
                    print(f'\nСообщение пользователю: {message[1]} от {message[3]}:\n{message[2]}')
            else:
                history_list = self.database.get_history()
                for message in history_list:
                    print(f'\nСообщение от пользователя: {message[0]}, пользователю {message[1]} от {message[3]}\n{message[2]}')

    # Функция изменеия контактов
    def edit_contacts(self):
        ans = input('Для удаления введите del, для добавления add: ')
        if ans == 'del':
            edit = input('Введите имя удаляемного контакта: ')
            with database_lock:
                if self.database.check_contact(edit):
                    self.database.del_contact(edit)
                else:
                    client_logger.error('Попытка удаления несуществующего контакта.')
        elif ans == 'add':
            # Проверка на возможность такого контакта
            edit = input('Введите имя создаваемого контакта: ')
            if self.database.check_user(edit):
                with database_lock:
                    self.database.add_contact(edit)
                with sock_lock:
                    try:
                        add_contact(self.sock , self.account_name, edit)
                    except ServerError:
                        client_logger.error('Не удалось отправить информацию на сервер.')


class ClientWait(threading.Thread, metaclass=ClientCheck):
    def __init__(self, account_name, sock, database):
        self.account_name = account_name
        self.sock = sock
        self.database = database
        super().__init__()

    
    # Функция принимает сообщение, выводит его в консоль.
    def run(self):
        while True:
            time.sleep(1)
            with sock_lock:
                try:
                    message = get_message(self.sock)
                except IncorrectDataRecivedError:
                    client_logger.error(f'DECODING ERROR!')
                except OSError as err:
                    if err.errno:
                        client_logger.critical(f'Разорвано соединение с сервером')
                        time.sleep(10)
                        break
                except (ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError):
                    client_logger.critical(f'Потеряно соединение с сервером.')
                    break
                else:
                    if jim_action in message and message[jim_action] == jim_message and \
                            jim_sender in message and jim_waiter in message and jim_message_txt in message\
                            and message[jim_waiter] == self.account_name:
                        print(f'Входящее сообщение от {message[jim_sender]}: {message[jim_message_txt]}')
                        with database_lock:
                            try:
                                self.database.save_message(message[jim_sender], self.account_name, message[jim_message_txt])
                            except:
                                client_logger.error('Ошибка взаимодействия с базой данных')
                        
                        client_logger.info(f'Входящее сообщение от {message[jim_sender]}: {message[jim_message_txt]}')
                    else:
                        client_logger.error(f'Ошибка чтения сообщения: {message}')
                

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


def contacts_list_request(sock, name):
    client_logger.debug(f'Запрос контакт листа для пользователся {name}')
    req = {
        jim_action: jim_get_cont,
        jim_time: time.time(),
        jim_user: name
    }
    client_logger.debug(f'Сформирован запрос {req}')
    send_message(sock, req)
    ans = get_message(sock)
    client_logger.debug(f'Получен ответ {ans}')
    if jim_response in ans and ans[jim_response] == 202:
        return ans[jim_list_info]
    else:
        raise ServerError


# Функция добавления пользователя в контакт лист
def add_contact(sock, username, contact):
    client_logger.debug(f'Создание контакта {contact}')
    req = {
        jim_action: jim_add_cont,
        jim_time: time.time(),
        jim_user: username,
        jim_account_name: contact
    }
    send_message(sock, req)
    ans = get_message(sock)
    if jim_response in ans and ans[jim_response] == 200:
        pass
    else:
        raise ServerError('Ошибка создания контакта')
    print('Удачное создание контакта.')


# Функция запроса списка известных пользователей
def user_list_request(sock, username):
    client_logger.debug(f'Запрос списка известных пользователей {username}')
    req = {
        jim_action: jim_get_users,
        jim_time: time.time(),
        jim_account_name: username
    }
    send_message(sock, req)
    ans = get_message(sock)
    if jim_response in ans and ans[jim_response] == 202:
        return ans[jim_list_info]
    else:
        raise ServerError


# Функция удаления пользователя из контакт листа
def remove_contact(sock, username, contact):
    client_logger.debug(f'Создание контакта {contact}')
    req = {
        jim_action: jim_remove_cont,
        jim_time: time.time(),
        jim_user: username,
        jim_account_name: contact
    }
    send_message(sock, req)
    ans = get_message(sock)
    if jim_response in ans and ans[jim_response] == 200:
        pass
    else:
        raise ServerError('Ошибка удаления клиента')
    print('Удачное удаление')


# Функция инициализатор базы данных. Запускается при запуске, загружает данные в базу с сервера.
def database_load(sock, database, username):
    try:
        users_list = user_list_request(sock, username)
    except ServerError:
        client_logger.error('Ошибка запроса списка известных пользователей.')
    else:
        database.add_users(users_list)

    try:
        contacts_list = contacts_list_request(sock, username)
    except ServerError:
        client_logger.error('Ошибка запроса списка контактов.')
    else:
        for contact in contacts_list:
            database.add_contact(contact)


def main():
    print('Client running')
    server_address, server_port, client_name = arguments_parser()

    if not client_name:
        client_name = input('Имя пользователя: ')
    else:
        print(f'Клиентский модуль запущен с именем: {client_name}')

    client_logger.info(f'Запущен клиент с парамeтpами: адрес сервера: {server_address}, '
        f'порт: {server_port}, имя пользователя: {client_name}')

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)

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
        database = ClientDatabase(client_name)
        database_load(s, database, client_name)

        module_sender = ClientSend(client_name, s, database)
        module_sender.daemon = True
        module_sender.start()
        client_logger.debug('Запущено')

        module_receiver = ClientWait(client_name, s, database)
        module_receiver.daemon = True
        module_receiver.start()
        
        
        while True:
            time.sleep(1)
            if module_receiver.is_alive() and module_sender.is_alive():
                continue
            break


if __name__ == '__main__':
    main()
