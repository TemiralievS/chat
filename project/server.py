import sys
import os
import socket
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

        self.clients_lst = []
        self.messages_list = []
        self.names_dct = dict()

        super().__init__()


    def init_socket(self):
        server_logger.info(f'Запуск сервера. Порт {self.port}, адрес {self.addr}')
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.addr, self.port))
        s.settimeout(0.5)
        self.sock = s
        self.sock.listen()


    def run(self):
        self.init_socket()
        while True:
            try:
                client, client_address = self.sock.accept()
            except OSError:
                pass
            else:
                server_logger.info(f'Соединение с {client_address}')
                self.clients_lst.append(client)

            recv_lst = []
            send_lst = []
            errors_lst = []

            try:
                if self.clients_lst:
                    recv_lst, send_lst, errors_lst = select.select(self.clients_lst, self.clients_lst, [], 0)
            except OSError as err:
                server_logger.error(f'Ошибка работы с сокетами: {err}')

            if recv_lst:
                for sender in recv_lst:
                    try:
                        self.message_from_to_client(get_message(sender), sender)
                    except (OSError) :
                        server_logger.info(f'{sender.getpeername()} отключился')
                        for name in self.names_dct:
                            if self.names_dct[name] == sender:
                                self.database.user_logout(name)
                                del self.names_dct[name]
                                break
                        self.clients_lst.remove(sender)

            for messg in self.messages_list:
                try:
                    self.message_status(messg, send_lst)
                except (ConnectionAbortedError, ConnectionError, ConnectionResetError, ConnectionRefusedError):
                    server_logger.info(f'Разорвано соединение с {messg[jim_waiter]}')
                    self.clients_lst.remove(self.names_dct[messg[jim_waiter]])
                    self.database.user_logout(messg[jim_waiter])
                    del self.names_dct[messg[jim_waiter]]
            self.messages_list.clear()



    def message_status(self, message, listen_socks):
        if message[jim_waiter] in self.names_dct and self.names_dct[message[jim_waiter]] in listen_socks:
            send_message(self.names_dct[message[jim_waiter]], message)
            server_logger.info(f'Пользователь {message[jim_sender]} отправил сообщение пользователю {message[jim_waiter]}')
        elif message[jim_waiter] in self.names_dct and self.names_dct[message[jim_waiter]] not in listen_socks:
            raise ConnectionError
        else:
            server_logger.error(f'Пользователя с именем {message[jim_waiter]} не существует')


    def message_from_to_client(self, message, client):
        global new_connection
        server_logger.debug(f'Клиент отправил сообщение {message}')

        # presence?
        if jim_action in message and message[jim_action] == jim_presence and jim_time in message \
                and jim_user in message:
            if message[jim_user][jim_account_name] not in self.names_dct.keys():
                self.names_dct[message[jim_user][jim_account_name]] = client
                client_ip, client_port = client.getpeername()
                self.database.user_login(message[jim_user][jim_account_name], client_ip, client_port)
                send_message(client, {jim_response: 200})
                with conflag_lock:
                    new_connection = True
            else:
                response = {jim_response: 400, jim_error: 'Пользователь с таким именем существует'}
                send_message(client, response)
                self.clients_lst.remove(client)
                client.close()
            return


        # message?
        elif jim_action in message and message[jim_action] == jim_message and \
                jim_waiter in message and jim_time in message \
                and jim_sender in message and jim_message_txt in message \
                    and self.names_dct[message[jim_sender]] == client:
            self.messages_list.append(message)
            self.database.process_message(message[jim_sender], message[jim_waiter])
            return

        # client exit
        elif jim_action in message and message[jim_action] == jim_exit and \
                jim_account_name in message and self.names_dct[message[jim_account_name]] == client:
            self.database.user_logout(message[jim_account_name])
            
            server_logger.info(f'Клиент {message[jim_account_name]} отключился от сервера')
            self.clients_lst.remove(self.names_dct[message[jim_account_name]])
            self.names_dct[message[jim_account_name]].close()
            del self.names_dct[message[jim_account_name]]
            with conflag_lock:
                new_connection = True
            return
        
        # get cont lst
        elif jim_action in message and message[jim_action] == jim_get_cont and \
                jim_user in message and self.names_dct[message[jim_user]] == client:
            response = {jim_response: 202, jim_list_info: None}
            response[jim_list_info] = self.database.get_contacts(message[jim_user])
            send_message(client, response)

        # add cont
        elif jim_action in message and message[jim_action] == jim_add_cont \
            and jim_account_name in message and jim_user in message \
                and self.names_dct[message[jim_user]] == client:
            self.database.add_contact(message[jim_user], message[jim_account_name])
            send_message(client, {jim_response: 200})

        # del cont
        elif jim_action in message and message[jim_action] == jim_remove_cont and jim_account_name in message \
              and jim_user in message and self.names_dct[message[jim_user]] == client:
            self.database.remove_contact(message[jim_user], message[jim_account_name])
            send_message(client, {jim_response: 200})

        # user req
        elif jim_action in message and message[jim_action] == jim_get_users and \
            jim_account_name in message and self.names_dct[message[jim_account_name]] == client:
            response = {jim_response: 202, jim_list_info: None}
            response[jim_list_info] = [user[0] for user in self.database.users_list()]
            send_message(client, response)

        else:
            response = {jim_response: 400, jim_error: 'Ошибка запроса'}
            send_message(client, response)
            return


def main():
    
    config = configparser.ConfigParser()
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f"{dir_path}/{'server.ini'}")

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
                print(port)
                with open('server.ini', 'w') as conf:
                    config.write(conf)
                    message.information(
                        config_window, 'OK', 'Настройки успешно сохранены!')
            else:
                message.warning(
                    config_window,
                    'Ошибка',
                    'Порт должен быть от 1024 до 65536')


    timer = QTimer()
    timer.timeout.connect(list_update)
    timer.start(1000)


    main_window.refresh_button.triggered.connect(list_update)
    main_window.show_history_button.triggered.connect(show_statistics)
    main_window.config_btn.triggered.connect(server_config)

    server_app.exec_()
 
    
if __name__ == '__main__':
    main()
