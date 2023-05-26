import unittest
from client import client_message_presence, server_message
from vars.vars import *


class TestClientMessagePresence(unittest.TestCase):

    def test_client_message_presence_type_dict(self):
        '''
        Проверяет, является ли сообщение клиента словарём
        :return:
        '''
        self.assertIsInstance(client_message_presence(), dict)


    def test_client_message_is_presence(self):
        '''
        Проверяет, является ли в сообщении клиента значение (ключа) поля action - presence
        :return:
        '''
        self.assertEqual(client_message_presence()[jim_action], 'presence')


class TestServerMessage(unittest.TestCase):
    #примеры для проверки
    correct_answer = {'response': 200}
    bad_request_answer = {'response': 400, 'error': 'Bad request'}

    def test_server_correct(self):
        '''
        Проверяет, корректность ответа
        :return:
        '''
        self.assertEqual(server_message(self.correct_answer), '200 — OK')

    def test_server_type_dict(self):
        '''
        Проверяет содержится ли 'ERROR' в ответе
        :return:
        '''
        self.assertIn('ERROR', server_message(self.bad_request_answer))


if __name__ == '__main__':
    unittest.main()
