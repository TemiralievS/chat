import unittest
import json
import time
from vars.vars import *
from funcJson.funcs import get_message, send_message


class TestSocket:

    def __init__(self, test_dict):
        self.test_dict = test_dict
        self.encoded_message = None
        self.receved_message = None

    def send(self, message_to_send):
        """
        Тестовая функция отправки, корретно  кодирует сообщение,
        так-же сохраняет что должно было отправлено в сокет.
        message_to_send - то, что отправляем в сокет
        :param message_to_send:
        :return:
        """
        json_test_message = json.dumps(self.test_dict)
        # кодирует сообщение
        self.encoded_message = json_test_message.encode('utf-8')
        # сохраняем что должно было отправлено в сокет
        self.receved_message = message_to_send

    def recv(self, max_len):
        """
        Получаем данные из сокета
        :param max_len:
        :return:
        """
        json_test_message = json.dumps(self.test_dict)
        return json_test_message.encode('utf-8')


class TestGetSendMessage(unittest.TestCase):
    # пример правильного сообщения
    client_message = {
        'action': 'presence',
        'time': 1685125876.2628665,
        'user': {'account_name': 'user'}
    }

    def test_get_message_type_dict(self):
        '''
        Возвращает ли словарь
        :return:
        '''
        test_socket = TestSocket(self.client_message)
        self.assertIsInstance(get_message(test_socket), dict)

    def test_get_message_presence(self):
        '''
        Корректно ли расшифровывает сообщение
        :return:
        '''
        test_socket = TestSocket(self.client_message)
        self.assertEqual(get_message(test_socket), self.client_message)


    def test_send_message_byte(self):
        '''
        Отдаёт ли функция сообщение в байтовом виде
        :return:
        '''
        test_socket = TestSocket(self.client_message)
        send_message(test_socket, self.client_message)
        self.assertIsInstance(test_socket.encoded_message, bytes)


if __name__ == '__main__':
    unittest.main()