import socket
import sys
import time
import logging
import json
import threading
from PyQt5.QtCore import pyqtSignal, QObject

sys.path.append('../')
from funcJson.funcs import *
from vars.vars import *
from errs.errors import ServerError


logger = logging.getLogger('client')
socket_lock = threading.Lock()


class ClientTransport(threading.Thread, QObject):
    new_message = pyqtSignal(str)
    connection_lost = pyqtSignal()


    def __init__(self, port, ip_address, database, username):
        threading.Thread.__init__(self)
        QObject.__init__(self)
        self.database = database
        self.username = username
        self.transport = None
        self.connection_init(port, ip_address)
        try:
            self.user_list_update()
            self.contacts_list_update()
        except OSError as err:
            if err.errno:
                logger.critical(f'Потеряно соединение с сервером.')
                raise ServerError('Потеряно соединение с сервером!')
            logger.error('Timeout соединения при обновлении списков пользователей.')
        except json.JSONDecodeError:
            logger.critical(f'Потеряно соединение с сервером.')
            raise ServerError('Потеряно соединение с сервером!')
            
        self.running = True

    
    def connection_init(self, port, ip):
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
                break
            time.sleep(1)
        if not connected:
            logger.critical('Не удалось установить соединение с сервером')
            raise ServerError('Не удалось установить соединение с сервером')
        logger.debug('Установлено соединение с сервером')
        try:
            with socket_lock:
                send_message(self.transport, self.create_presence())
                self.process_server_ans(get_message(self.transport))
        except (OSError, json.JSONDecodeError):
            logger.critical('Потеряно соединение с сервером!')
            raise ServerError('Потеряно соединение с сервером!')
        logger.info('Соединение с сервером успешно установлено.')

    
    def create_presence(self):
        out = {
            jim_action: jim_presence,
            jim_time: time.time(),
            jim_user: {
                jim_account_name: self.username
            }
        }
        logger.debug(f'Сформировано {jim_presence} сообщение для пользователя {self.username}')
        return out

    
    def process_server_ans(self, message):
        logger.debug(f'Разбор сообщения от сервера: {message}')
        if jim_response in message:
            if message[jim_response] == 200:
                return
            elif message[jim_response] == 400:
                raise ServerError(f'{message[jim_error]}')
            else:
                logger.debug(f'Принят неизвестный код подтверждения {message[jim_response]}')
        elif jim_action in message and message[jim_action] == jim_message and jim_sender in message and jim_waiter in message \
                and jim_message_txt in message and message[jim_waiter] == self.username:
            logger.debug(f'Получено сообщение от пользователя {message[jim_sender]}:{message[jim_message_txt]}')
            self.database.save_message(message[jim_sender] , 'in' , message[jim_message_txt])
            self.new_message.emit(message[jim_sender])

    
    def contacts_list_update(self):
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

    
    def add_contact(self, contact):
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
        logger.debug('Запущен процесс - приёмник собщений с сервера.')
        while self.running:
            time.sleep(1)
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
                else:
                    logger.debug(f'Принято сообщение с сервера: {message}')
                    self.process_server_ans(message)
                finally:
                    self.transport.settimeout(5)