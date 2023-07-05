from collections.abc import Callable, Iterable, Mapping
import logging
import log_main.client_log_config
import argparse
import sys
import os
from Cryptodome.PublicKey import RSA
from PyQt5.QtWidgets import QApplication, QMessageBox

from common.vars import *
from common.errors import *
from common.decors import log
from client.database import ClientDatabase
from client.transport import ClientTransport
from client.main_window import ClientMainWindow
from client.start_dialog import UserNameDialog


client_logger = logging.getLogger('client')


@log
def arguments_parser():
    '''Парсер аргументов коммандной строки.'''
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default='127.0.0.1', nargs='?')
    parser.add_argument('port', default=7777, type=int, nargs='?')
    parser.add_argument('-n', '--name', default=None, nargs='?')
    parser.add_argument('-p', '--password', default='', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.addr
    server_port = namespace.port
    client_name = namespace.name
    client_passwd = namespace.password

    if not 1023 < server_port < 65536:
        client_logger.critical(
            f'Попытка запуска клиента с неподходящим номером порта: {server_port}. '
            f'Допустимы адреса с 1024 до 65535. Клиент завершается.')
        sys.exit(1)

    return server_address, server_port, client_name, client_passwd


if __name__ == '__main__':

    server_address, server_port, client_name, client_passwd = arguments_parser()

    client_app = QApplication(sys.argv)

    start_dialog = UserNameDialog()

    if not client_name or not client_passwd:
        client_app.exec_()
        if start_dialog.ok_pressed:
            client_name = start_dialog.client_name.text()
            client_passwd = start_dialog.client_passwd.text()
            client_logger.debug(
                f'Имя пользователя = {client_name}, пароль = {client_passwd}')
        else:
            exit(0)

    client_logger.info(f'Запущен клиент с параметрами: адрес сервера:\
                        {server_address} , порт: {server_port}, имя пользователя: {client_name}')

    dir_path = os.path.dirname(os.path.realpath(__file__))
    key_file = os.path.join(dir_path, f'{client_name}.key')
    if not os.path.exists(key_file):
        keys = RSA.generate(2048, os.urandom)
        with open(key_file, 'wb') as key:
            key.write(keys.export_key())
    else:
        with open(key_file, 'rb') as key:
            keys = RSA.import_key(key.read())

    keys.publickey().export_key()
    client_logger.debug("Keys sucsessfully loaded.")

    database = ClientDatabase(client_name)

    try:
        transport = ClientTransport(
            server_port,
            server_address,
            database,
            client_name,
            client_passwd,
            keys)
    except ServerError as error:
        message = QMessageBox()
        message.critical(start_dialog, 'Server error', error.text)
        exit(1)
    transport.daemon = True
    transport.start()

    main_window = ClientMainWindow(database, transport, keys)
    main_window.make_connection(transport)
    main_window.setWindowTitle(f'Чат Программа alpha release - {client_name}')
    client_app.exec_()

    transport.transport_shutdown()
    transport.join()
