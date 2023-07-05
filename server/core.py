import threading
import logging
import select
import socket
import json
import hmac
import binascii
import os
from common.meta import ServerCheck
from common.dscriptors import Port
from common.vars import *
from common.funcs import send_message, get_message
from common.decors import login_required


logger = logging.getLogger('server')


class MessageProcessor(threading.Thread):
    '''
    Основной класс сервера. Принимает содинения, словари - пакеты
    от клиентов, обрабатывает поступающие сообщения.
    Работает в качестве отдельного потока.
    '''
    port = Port()


    def __init__(self, listen_address, listen_port, database):
        self.addr = listen_address
        self.port = listen_port

        self.database = database

        self.sock = None

        self.clients = []

        self.listen_sockets = None
        self.error_sockets = None

        self.running = True

        self.names = dict()

        super().__init__()

    def run(self):
        '''Метод основной цикл потока.'''
        self.init_socket()

        while self.running:

            try:
                client, client_address = self.sock.accept()
            except OSError:
                pass
            else:
                logger.info(f'Установлено соедение с ПК {client_address}')
                client.settimeout(5)
                self.clients.append(client)

            recv_data_lst = []
            send_data_lst = []
            err_lst = []

            try:
                if self.clients:
                    recv_data_lst, self.listen_sockets, self.error_sockets = select.select(
                        self.clients, self.clients, [], 0)
            except OSError as err:
                logger.error(f'Ошибка работы с сокетами: {err.errno}')

            if recv_data_lst:
                for client_with_message in recv_data_lst:
                    try:
                        self.process_client_message(
                            get_message(client_with_message), client_with_message)
                    except (OSError, json.JSONDecodeError, TypeError) as err:
                        logger.debug(
                            f'Getting data from client exception.', exc_info=err)
                        self.remove_client(client_with_message)

    def remove_client(self, client):
        '''
        Метод обработчик клиента с которым прервана связь.
        Ищет клиента и удаляет его из списков и базы:
        '''
        logger.info(f'Клиент {client.getpeername()} отключился от сервера.')
        for name in self.names:
            if self.names[name] == client:
                self.database.user_logout(name)
                del self.names[name]
                break
        self.clients.remove(client)
        client.close()

    def init_socket(self):
        '''Метод инициализатор сокета.'''
        logger.info(
            f'Запущен сервер, порт для подключений: {self.port} ,'
            f'адрес с которого принимаются подключения: {self.addr}.'
            f'Если адрес не указан, принимаются соединения с любых адресов.')

        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.bind((self.addr, self.port))
        transport.settimeout(0.5)

        self.sock = transport
        self.sock.listen(5)

    def process_message(self, message):
        '''
        Метод отправки сообщения клиенту.
        '''
        if message[jim_waiter] in self.names and self.names[message[jim_waiter]
                                                            ] in self.listen_sockets:
            try:
                send_message(self.names[message[jim_waiter]], message)
                logger.info(
                    f'Отправлено сообщение пользователю {message[jim_waiter]}' 
                    f'от пользователя {message[jim_sender]}.')
            except OSError:
                self.remove_client(message[jim_waiter])
        elif message[jim_waiter] in self.names and self.names[message[jim_waiter]] not in self.listen_sockets:
            logger.error(
                f'Связь с клиентом {message[jim_waiter]} была потеряна. Соединение закрыто, доставка невозможна.')
            self.remove_client(self.names[message[jim_waiter]])
        else:
            logger.error(
                f'Пользователь {message[jim_waiter]} не зарегистрирован на сервере, отправка сообщения невозможна.')

    @login_required
    def process_client_message(self, message, client):
        '''Метод отбработчик поступающих сообщений.'''
        logger.debug(f'Разбор сообщения от клиента : {message}')
        if jim_action in message and message[jim_action] == jim_presence and jim_time in message \
                and jim_user in message:
            self.autorize_user(message, client)

        elif jim_action in message and message[jim_action] == jim_message and jim_waiter in message \
            and jim_time in message and jim_sender in message \
                and jim_message_txt in message and self.names[message[jim_sender]] == client:
            if message[jim_waiter] in self.names:
                self.database.process_message(
                    message[jim_sender], message[jim_waiter])
                self.process_message(message)
                try:
                    send_message(client, {jim_response: 200})
                except OSError:
                    self.remove_client(client)
            else:
                response = {jim_response: 400, jim_error: None}
                response[jim_error] = 'Пользователь не зарегистрирован на сервере.'
                try:
                    send_message(client, response)
                except OSError:
                    pass
            return

        elif jim_action in message and message[jim_action] == jim_exit and jim_account_name in message \
                and self.names[message[jim_account_name]] == client:
            self.remove_client(client)

        elif jim_action in message and message[jim_action] == jim_get_cont and jim_user in message and \
                self.names[message[jim_user]] == client:
            response = {jim_response: 202, jim_list_info: None}
            response[jim_list_info] = self.database.get_contacts(
                message[jim_user])
            try:
                send_message(client, response)
            except OSError:
                self.remove_client(client)

        elif jim_action in message and message[jim_action] == jim_add_cont \
                and jim_account_name in message and jim_user in message and self.names[message[jim_user]] == client:
            self.database.add_contact(
                message[jim_user], message[jim_account_name])
            try:
                send_message(client, {jim_response: 200})
            except OSError:
                self.remove_client(client)

        elif jim_action in message and message[jim_action] == jim_remove_cont and \
                jim_account_name in message and jim_user in message and self.names[message[jim_user]] == client:
            self.database.remove_contact(
                message[jim_user], message[jim_account_name])
            try:
                send_message(client, {jim_response: 200})
            except OSError:
                self.remove_client(client)

        elif jim_action in message and message[jim_action] == jim_get_users and jim_account_name in message \
                and self.names[message[jim_account_name]] == client:
            response = {jim_response: 202, jim_list_info: None}
            response[jim_list_info] = [user[0]
                                       for user in self.database.users_list()]
            try:
                send_message(client, response)
            except OSError:
                self.remove_client(client)

        elif jim_action in message and message[jim_action] == jim_pubkey_req and jim_account_name in message:
            response = {jim_response: 511, jim_data: None}
            response[jim_data] = self.database.get_pubkey(
                message[jim_account_name])

            if response[jim_data]:
                try:
                    send_message(client, response)
                except OSError:
                    self.remove_client(client)
            else:
                response = {jim_response: 400, jim_error: None}
                response[jim_error] = 'Нет публичного ключа для данного пользователя'
                try:
                    send_message(client, response)
                except OSError:
                    self.remove_client(client)

        else:
            response = {jim_response: 400, jim_error: None}
            response[jim_error] = 'Запрос некорректен.'
            try:
                send_message(client, response)
            except OSError:
                self.remove_client(client)

    def autorize_user(self, message, sock):
        '''Метод реализующий авторизцию пользователей.'''
        logger.debug(f'Start auth process for {message[jim_user]}')
        if message[jim_user][jim_account_name] in self.names.keys():
            response = {jim_response: 400, jim_error: None}
            response[jim_error] = 'Имя пользователя уже занято.'
            try:
                logger.debug(f'Username busy, sending {response}')
                send_message(sock, response)
            except OSError:
                logger.debug('OS Error')
                pass
            self.clients.remove(sock)
            sock.close()
        elif not self.database.check_user(message[jim_user][jim_account_name]):
            response = {jim_response: 400, jim_error: None}
            response[jim_error] = 'Пользователь не зарегистрирован.'
            try:
                logger.debug(f'Unknown username, sending {response}')
                send_message(sock, response)
            except OSError:
                pass
            self.clients.remove(sock)
            sock.close()
        else:
            logger.debug('Correct username, starting passwd check.')
            message_auth = {jim_response: 511, jim_data: None}

            random_str = binascii.hexlify(os.urandom(64))
            message_auth[jim_data] = random_str.decode('ascii')
            hash = hmac.new(
                self.database.get_hash(
                    message[jim_user][jim_account_name]),
                random_str,
                'MD5')
            digest = hash.digest()
            logger.debug(f'Auth message = {message_auth}')
            try:

                send_message(sock, message_auth)
                ans = get_message(sock)
            except OSError as err:
                logger.debug('Error in auth, data:', exc_info=err)
                sock.close()
                return
            client_digest = binascii.a2b_base64(ans[jim_data])

            if jim_response in ans and ans[jim_response] == 511 and hmac.compare_digest(
                    digest, client_digest):
                self.names[message[jim_user][jim_account_name]] = sock
                client_ip, client_port = sock.getpeername()
                try:
                    send_message(sock, {jim_response: 200})
                except OSError:
                    self.remove_client(message[jim_user][jim_account_name])

                self.database.user_login(
                    message[jim_user][jim_account_name],
                    client_ip,
                    client_port,
                    message[jim_user][jim_public_key])
            else:
                response = {jim_response: 400, jim_error: None}
                response[jim_error] = 'Неверный пароль.'
                try:
                    send_message(sock, response)
                except OSError:
                    pass
                self.clients.remove(sock)
                sock.close()

    def service_update_lists(self):
        '''Метод реализующий отправки сервисного сообщения 205 клиентам.'''
        for client in self.names:
            try:
                send_message(self.names[client], {jim_response: 205})
            except OSError:
                self.remove_client(self.names[client])
