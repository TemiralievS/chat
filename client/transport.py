import socket
import time
import logging
import json
import threading
import hashlib
import hmac
import binascii
import sys
from PyQt5.QtCore import pyqtSignal, QObject

from common.funcs import *
from common.vars import *
from common.errors import ServerError


logger = logging.getLogger('client')
socket_lock = threading.Lock()


class ClientTransport(threading.Thread, QObject):
    '''
    Класс реализующий транспортную подсистему клиентского
    модуля. Отвечает за взаимодействие с сервером.
    '''

    new_message = pyqtSignal(dict)
    message_205 = pyqtSignal()
    connection_lost = pyqtSignal()

    def __init__(self, port, ip_address, database, username, passwd, keys):
        threading.Thread.__init__(self)
        QObject.__init__(self)

        self.database = database

        self.username = username

        self.password = passwd

        self.transport = None

        self.keys = keys

        self.connection_init(port, ip_address)
        try:
            self.user_list_update()
            self.contacts_list_update()
        except OSError as err:
            if err.errno:
                logger.critical(f'Потеряно соединение с сервером.')
                raise ServerError('Потеряно соединение с сервером!')
            logger.error(
                'Timeout соединения при обновлении списков пользователей.')
        except json.JSONDecodeError:
            logger.critical(f'Потеряно соединение с сервером.')
            raise ServerError('Потеряно соединение с сервером!')
        self.running = True

    def connection_init(self, port, ip):
        '''Метод отвечающий за устанновку соединения с сервером.'''

        self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.transport.settimeout(5)

        connected = False
        for i in range(5):
            logger.info(f'Попытка подключения №{i + 1}')
            try:
                self.transport.connect((ip, port))
            except (OSError, ConnectionRefusedError):
                pass
            else:
                connected = True
                logger.debug("Connection established.")
                break
            time.sleep(1)

        if not connected:
            logger.critical('Не удалось установить соединение с сервером')
            raise ServerError('Не удалось установить соединение с сервером')

        logger.debug('Starting auth dialog.')

        passwd_bytes = self.password.encode('utf-8')
        salt = self.username.lower().encode('utf-8')
        passwd_hash = hashlib.pbkdf2_hmac('sha512', passwd_bytes, salt, 10000)
        passwd_hash_string = binascii.hexlify(passwd_hash)

        logger.debug(f'Passwd hash ready: {passwd_hash_string}')

        pubkey = self.keys.publickey().export_key().decode('ascii')

        with socket_lock:
            presense = {
                jim_action: jim_presence,
                jim_time: time.time(),
                jim_user: {
                    jim_account_name: self.username,
                    jim_public_key: pubkey
                }
            }
            logger.debug(f"Presense message = {presense}")

            try:
                send_message(self.transport, presense)
                ans = get_message(self.transport)
                logger.debug(f'Server response = {ans}.')

                if jim_response in ans:
                    if ans[jim_response] == 400:
                        raise ServerError(ans[jim_error])
                    elif ans[jim_response] == 511:
                        ans_data = ans[jim_data]
                        hash = hmac.new(
                            passwd_hash_string, ans_data.encode('utf-8'), 'MD5')
                        digest = hash.digest()
                        my_ans = {jim_response: 511, jim_data: None}
                        my_ans[jim_data] = binascii.b2a_base64(
                            digest).decode('ascii')
                        send_message(self.transport, my_ans)
                        self.process_server_ans(get_message(self.transport))
            except (OSError, json.JSONDecodeError) as err:
                logger.debug(f'Connection error.', exc_info=err)
                raise ServerError('Сбой соединения в процессе авторизации.')

    def process_server_ans(self, message):
        '''Метод обработчик поступающих сообщений с сервера.'''
        logger.debug(f'Разбор сообщения от сервера: {message}')

        if jim_response in message:
            if message[jim_response] == 200:
                return
            elif message[jim_response] == 400:
                raise ServerError(f'{message[jim_error]}')
            elif message[jim_response] == 205:
                self.user_list_update()
                self.contacts_list_update()
                self.message_205.emit()
            else:
                logger.error(
                    f'Принят неизвестный код подтверждения {message[jim_response]}')

        elif jim_action in message and message[jim_action] == jim_message and jim_sender in message and jim_waiter in message \
                and jim_message_txt in message and message[jim_waiter] == self.username:
            logger.debug(
                f'Получено сообщение от пользователя {message[jim_sender]}:{message[jim_message_txt]}')
            self.new_message.emit(message)

    def contacts_list_update(self):
        '''Метод обновляющий с сервера список контактов.'''
        self.database.contacts_clear()
        logger.debug(f'Запрос контакт листа для пользователся {self.name}')
        req = {
            jim_action: jim_get_cont,
            jim_time: time.time(),
            jim_user: self.username
        }
        logger.debug(f'Сформирован запрос {req}')
        with socket_lock:
            send_message(self.transport, req)
            ans = get_message(self.transport)
        logger.debug(f'Получен ответ {ans}')
        if jim_response in ans and ans[jim_response] == 202:
            for contact in ans[jim_list_info]:
                self.database.add_contact(contact)
        else:
            logger.error('Не удалось обновить список контактов.')

    def user_list_update(self):
        '''Метод обновляющий с сервера список пользователей.'''
        logger.debug(f'Запрос списка известных пользователей {self.username}')
        req = {
            jim_action: jim_get_users,
            jim_time: time.time(),
            jim_account_name: self.username
        }
        with socket_lock:
            send_message(self.transport, req)
            ans = get_message(self.transport)
        if jim_response in ans and ans[jim_response] == 202:
            self.database.add_users(ans[jim_list_info])
        else:
            logger.error('Не удалось обновить список известных пользователей.')

    def key_request(self, user):
        '''Метод запрашивающий с сервера публичный ключ пользователя.'''
        logger.debug(f'Запрос публичного ключа для {user}')
        req = {
            jim_action: jim_pubkey_req,
            jim_time: time.time(),
            jim_account_name: user
        }
        with socket_lock:
            send_message(self.transport, req)
            ans = get_message(self.transport)
        if jim_response in ans and ans[jim_response] == 511:
            return ans[jim_data]
        else:
            logger.error(f'Не удалось получить ключ собеседника{user}.')

    def add_contact(self, contact):
        '''Метод отправляющий на сервер сведения о добавлении контакта.'''
        logger.debug(f'Создание контакта {contact}')
        req = {
            jim_action: jim_add_cont,
            jim_time: time.time(),
            jim_user: self.username,
            jim_account_name: contact
        }
        with socket_lock:
            send_message(self.transport, req)
            self.process_server_ans(get_message(self.transport))

    def remove_contact(self, contact):
        '''Метод отправляющий на сервер сведения о удалении контакта.'''
        logger.debug(f'Удаление контакта {contact}')
        req = {
            jim_action: jim_remove_cont,
            jim_time: time.time(),
            jim_user: self.username,
            jim_account_name: contact
        }
        with socket_lock:
            send_message(self.transport, req)
            self.process_server_ans(get_message(self.transport))

    def transport_shutdown(self):
        '''Метод уведомляющий сервер о завершении работы клиента.'''
        self.running = False
        message = {
            jim_action: jim_exit,
            jim_time: time.time(),
            jim_account_name: self.username
        }
        with socket_lock:
            try:
                send_message(self.transport, message)
            except OSError:
                pass
        logger.debug('Транспорт завершает работу.')
        time.sleep(0.5)

    def send_message(self, to, message):
        '''Метод отправляющий на сервер сообщения для пользователя.'''
        message_dict = {
            jim_action: jim_message,
            jim_sender: self.username,
            jim_waiter: to,
            jim_time: time.time(),
            jim_message_txt: message
        }
        logger.debug(f'Сформирован словарь сообщения: {message_dict}')
        with socket_lock:
            send_message(self.transport, message_dict)
            self.process_server_ans(get_message(self.transport))
            logger.info(f'Отправлено сообщение для пользователя {to}')

    def run(self):
        '''Метод содержащий основной цикл работы транспортного потока.'''
        logger.debug('Запущен процесс - приёмник собщений с сервера.')
        while self.running:
            time.sleep(1)
            message = None
            with socket_lock:
                try:
                    self.transport.settimeout(0.5)
                    message = get_message(self.transport)
                except OSError as err:
                    if err.errno:
                        logger.critical(f'Потеряно соединение с сервером.')
                        self.running = False
                        self.connection_lost.emit()

                except (ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError, TypeError):
                    logger.debug(f'Потеряно соединение с сервером.')
                    self.running = False
                    self.connection_lost.emit()
                finally:
                    self.transport.settimeout(5)

            if message:
                logger.debug(f'Принято сообщение с сервера: {message}')
                self.process_server_ans(message)
