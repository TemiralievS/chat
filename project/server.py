import socket
import sys
import os
import logging
import argparse
import select
import time
import json
import threading
import configparser
from errs.errors import *
import log.server_log_config
from log.decorator_log import *
from vars.vars import *
from funcJson.funcs import *
from meta import ServerCheck
from dscriptors import Port
from server_db import ServerStorage
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer
from server_gui import MainWindow, gui_create_model, HistoryWindow, create_stat_model, ConfigWindow
from PyQt5.QtGui import QStandardItemModel, QStandardItem


server_logger = logging.getLogger('server')
new_connection = False
conflag_lock = threading.Lock()


@log
def arguments_parser(default_port, default_address):
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=7777, type=int, nargs='?')
    parser.add_argument('-a', default='', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p
    return listen_address, listen_port


class Server(threading.Thread, metaclass=ServerCheck):
    port = Port()

    def __init__(self, listen_address, listen_port, database):
        self.addr = listen_address
        self.port = listen_port

        self.database = database

        self.clients = []
        self.messages = []
        self.names = dict()

        super().__init__()

    def init_socket(self):
        server_logger.info(
            f'Запущен сервер, порт для подключений: {self.port} , адрес с которого принимаются подключения: {self.addr}. Если адрес не указан, принимаются соединения с любых адресов.')
       
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.bind((self.addr, self.port))
        transport.settimeout(0.5)

        
        self.sock = transport
        self.sock.listen()

    def run(self):
        global new_connection
        self.init_socket()

        while True:
            try:
                client, client_address = self.sock.accept()
            except OSError:
                pass
            else:
                server_logger.info(f'Установлено соедение с ПК {client_address}')
                self.clients.append(client)

            recv_data_lst = []
            send_data_lst = []
            err_lst = []
            try:
                if self.clients:
                    recv_data_lst, send_data_lst, err_lst = select.select(self.clients, self.clients, [], 0)
            except OSError as err:
                server_logger.error(f'Ошибка работы с сокетами: {err}')

            if recv_data_lst:
                for client_with_message in recv_data_lst:
                    try:
                        self.process_client_message(get_message(client_with_message), client_with_message)
                    except (OSError):
                        server_logger.info(f'Клиент {client_with_message.getpeername()} отключился от сервера.')
                        for name in self.names:
                            if self.names[name] == client_with_message:
                                self.database.user_logout(name)
                                del self.names[name]
                                break
                        self.clients.remove(client_with_message)
                        with conflag_lock:
                            new_connection = True

            for message in self.messages:
                try:
                    self.process_message(message, send_data_lst)
                except (ConnectionAbortedError, ConnectionError, ConnectionResetError, ConnectionRefusedError):
                    server_logger.info(f'Связь с клиентом с именем {message[jim_waiter]} была потеряна')
                    self.clients.remove(self.names[message[jim_waiter]])
                    self.database.user_logout(message[jim_waiter])
                    del self.names[message[jim_waiter]]
                    with conflag_lock:
                        new_connection = True
            self.messages.clear()


    def process_message(self, message, listen_socks):
        if message[jim_waiter] in self.names and self.names[message[jim_waiter]] in listen_socks:
            send_message(self.names[message[jim_waiter]], message)
            server_logger.info(f'Отправлено сообщение пользователю {message[jim_waiter]} от пользователя {message[jim_sender]}.')
        elif message[jim_waiter] in self.names and self.names[message[jim_waiter]] not in listen_socks:
            raise ConnectionError
        else:
            server_logger.error(
                f'Пользователь {message[jim_waiter]} не зарегистрирован на сервере, отправка сообщения невозможна.')


    def process_client_message(self, message, client):
        global new_connection
        server_logger.debug(f'Разбор сообщения от клиента : {message}')

        if jim_action in message and message[jim_action] == jim_presence and jim_time in message and jim_user in message:
            if message[jim_user][jim_account_name] not in self.names.keys():
                self.names[message[jim_user][jim_account_name]] = client
                client_ip, client_port = client.getpeername()
                self.database.user_login(message[jim_user][jim_account_name], client_ip, client_port)
                send_message(client, {jim_response: 200})
                with conflag_lock:
                    new_connection = True
            else:
                response = {jim_response: 400, jim_error: None}
                response[jim_error] = 'Имя пользователя уже занято.'
                send_message(client, response)
                self.clients.remove(client)
                client.close()
            return

        elif jim_action in message and message[jim_action] == jim_message and jim_waiter in message and jim_time in message \
                and jim_sender in message and jim_message_txt in message and self.names[message[jim_sender]] == client:
            if message[jim_waiter] in self.names:
                self.messages.append(message)
                self.database.process_message(message[jim_sender], message[jim_waiter])
                send_message(client, {jim_response: 200})
            else:
                response = {jim_response: 400, jim_error: None}
                response[jim_error] = 'Пользователь не зарегистрирован на сервере.'
                send_message(client, response)
            return

        elif jim_action in message and message[jim_action] == jim_exit and jim_account_name in message \
                and self.names[message[jim_account_name]] == client:
            self.database.user_logout(message[jim_account_name])
            server_logger.info(f'Клиент {message[jim_account_name]} корректно отключился от сервера.')
            self.clients.remove(self.names[message[jim_account_name]])
            self.names[message[jim_account_name]].close()
            del self.names[message[jim_account_name]]
            with conflag_lock:
                new_connection = True
            return

        elif jim_action in message and message[jim_action] == jim_get_cont and jim_user in message and \
                self.names[message[jim_user]] == client:
            response = {jim_response: 202, jim_list_info:None}
            response[jim_list_info] = self.database.get_contacts(message[jim_user])
            send_message(client, response)

        elif jim_action in message and message[jim_action] == jim_add_cont and jim_account_name in message and jim_user in message \
                and self.names[message[jim_user]] == client:
            self.database.add_contact(message[jim_user], message[jim_account_name])
            send_message(client, {jim_response: 200})

        elif jim_action in message and message[jim_action] == jim_remove_cont and jim_account_name in message and jim_user in message \
                and self.names[message[jim_user]] == client:
            self.database.remove_contact(message[jim_user], message[jim_account_name])
            send_message(client, {jim_response: 200})

        elif jim_action in message and message[jim_action] == jim_get_users and jim_account_name in message \
                and self.names[message[jim_account_name]] == client:
            response = {jim_response: 202, jim_list_info:None}
            response[jim_list_info] = [user[0] for user in self.database.users_list()]
            send_message(client, response)

        else:
            response = {jim_response: 400, jim_error: None}
            response[jim_error] = 'Запрос некорректен.'
            send_message(client, response)
            return


def config_load():
    config = configparser.ConfigParser()
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f"{dir_path}/{'server.ini'}")
    if 'SETTINGS' in config:
        return config
    else:
        config.add_section('SETTINGS')
        config.set('SETTINGS', 'Default_port', str(7777))
        config.set('SETTINGS', 'Listen_Address', '')
        config.set('SETTINGS', 'Database_path', '')
        config.set('SETTINGS', 'Database_file', 'server_database.db3')
        return config
        

def load_conf():
    config = configparser.ConfigParser()
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f"{dir_path}/{'server.ini'}")
    if 'SETTINGS' in config:
        return config
    else:
        config.add_section('SETTINGS')
        config.set('SETTINGS', 'Default_port', str(7777))
        config.set('SETTINGS', 'Listen_Address', '')
        config.set('SETTINGS', 'Database_path', '')
        config.set('SETTINGS', 'Database_file', 'server_database.db3')
        return config


def main():
    
    config = load_conf()

    listen_address, listen_port = arguments_parser(
        config['SETTINGS']['Default_port'], config['SETTINGS']['Listen_Address'])

    database = ServerStorage(
        os.path.join(config['SETTINGS']['Database_path'], config['SETTINGS']['Database_file']))

    server = Server(listen_address, listen_port, database)
    server.daemon = True
    server.start()

    server_app = QApplication(sys.argv)
    main_window = MainWindow()

    main_window.statusBar().showMessage('Server Working')
    main_window.active_clients_table.setModel(gui_create_model(database))
    main_window.active_clients_table.resizeColumnsToContents()
    main_window.active_clients_table.resizeRowsToContents()


    def list_update():
        global new_connection
        if new_connection:
            main_window.active_clients_table.setModel(
                gui_create_model(database))
            main_window.active_clients_table.resizeColumnsToContents()
            main_window.active_clients_table.resizeRowsToContents()
            with conflag_lock:
                new_connection = False
    

    def show_statistics():
        global stat_window
        stat_window = HistoryWindow()
        stat_window.history_table.setModel(create_stat_model(database))
        stat_window.history_table.resizeColumnsToContents()
        stat_window.history_table.resizeRowsToContents()
        stat_window.show()


    def server_config():
        global config_window
        config_window = ConfigWindow()
        config_window.db_path.insert(config['SETTINGS']['Database_path'])
        config_window.db_file.insert(config['SETTINGS']['Database_file'])
        config_window.port.insert(config['SETTINGS']['Default_port'])
        config_window.ip.insert(config['SETTINGS']['Listen_Address'])
        config_window.save_btn.clicked.connect(save_server_config)


    def save_server_config():
        global config_window
        message = QMessageBox()
        config['SETTINGS']['Database_path'] = config_window.db_path.text()
        config['SETTINGS']['Database_file'] = config_window.db_file.text()
        try:
            port = int(config_window.port.text())
        except ValueError:
            message.warning(config_window, 'Ошибка', 'Порт должен быть числом')
        else:
            config['SETTINGS']['Listen_Address'] = config_window.ip.text()
            if 1023 < port < 65536:
                config['SETTINGS']['Default_port'] = str(port)
                dir_path = os.path.dirname(os.path.realpath(__file__))
                with open(f"{dir_path}/{'server.ini'}", 'w') as conf:
                    config.write(conf)
                    message.information(config_window, 'OK', 'Настройки успешно сохранены!')
            else:
                message.warning(config_window, 'Ошибка', 'Порт должен быть от 1024 до 65536')



    timer = QTimer()
    timer.timeout.connect(list_update)
    timer.start(1000)

    main_window.refresh_button.triggered.connect(list_update)
    main_window.show_history_button.triggered.connect(show_statistics)
    main_window.config_btn.triggered.connect(server_config)

    server_app.exec_()
 
    
if __name__ == '__main__':
    main()
