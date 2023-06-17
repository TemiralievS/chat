import sys
import socket
import logging
import argparse
import select
import time
import json
import log.server_log_config
from log.decorator_log import *
from vars.vars import *
from funcJson.funcs import *
from meta import ServerCheck
from dscriptors import Port


server_logger = logging.getLogger('server')


@log
def arguments_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=7777, type=int, nargs='?')
    parser.add_argument('-a', default='', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p
    return listen_address, listen_port


class Server(metaclass=ServerCheck):
    port = Port()

    def __init__(self, listen_address, listen_port):
        self.addr = listen_address
        self.port = listen_port
        self.clients_lst = []
        self.messages_list = []
        self.names_dct = dict()


    def init_socket(self):
        server_logger.info(f'Запуск сервера. Порт {self.port}, адрес {self.addr}')
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.addr, self.port))
        s.settimeout(0.5)
        self.sock = s
        self.sock.listen()


    def main_alg(self):
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
            except OSError:
                pass

            if recv_lst:
                for sender in recv_lst:
                    try:
                        self.message_from_to_client(get_message(sender), sender)
                    except :
                        server_logger.info(f'{sender.getpeername()} отключился')
                        self.clients_lst.remove(sender)

            for messg in self.messages_list:
                try:
                    self.message_status(messg, send_lst)
                except :
                    server_logger.info(f'Разорвано соединение с {messg[jim_waiter]}')
                    self.clients_lst.remove(self.names_dct[messg[jim_waiter]])
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
        server_logger.debug(f'Клиент отправил сообщение {message}')

        if jim_action in message and message[jim_action] == jim_presence and jim_time in message \
                and jim_user in message:
            if message[jim_user][jim_account_name] not in self.names_dct.keys():
                self.names_dct[message[jim_user][jim_account_name]] = client
                send_message(client, {jim_response: 200})
            else:
                response = {jim_response: 400, jim_error: 'Пользователь с таким именем существует'}
                send_message(client, response)
                self.clients_lst.remove(client)
                client.close()
            return

        elif jim_action in message and message[jim_action] == jim_message and \
                jim_waiter in message and jim_time in message \
                and jim_sender in message and jim_message_txt in message:
            self.messages_list.append(message)
            return

        elif jim_action in message and message[jim_action] == jim_exit and \
                jim_account_name in message:
            self.clients_lst.remove(self.names_dct[jim_account_name])
            self.names_dct[jim_account_name].close()
            del self.names_dct[jim_account_name]
            return

        else:
            response = {jim_response: 400, jim_error: 'Ошибка запроса'}
            send_message(client, response)
            return


def main():
    listen_address, listen_port = arguments_parser()
    server = Server(listen_address, listen_port)
    server.main_alg()

    
if __name__ == '__main__':
    main()
