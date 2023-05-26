import unittest
from server import message_from_to_client
import time


class TestMessageFromToClient(unittest.TestCase):
    # пример правильного сообщения
    client_message = {
        'action': 'presence',
        'time': time.time(),
        'user': {'account_name': 'user'}
    }
    # примеры возвратов
    correct_answer = {'response': 200}
    bad_request_answer = {'response': 400, 'error': 'Bad request'}

    def test_message_from_server_type_dict(self):
        '''
        Возвращает ли словарь
        :return:
        '''
        self.assertIsInstance(message_from_to_client(self.client_message), dict)

    def test_message_from_server(self):
        '''
        Корректно ли срабатывает с правильным сообщением
        :return:
        '''
        self.assertEqual(message_from_to_client(self.client_message), self.correct_answer)


    def test_message_from_server_action(self):
        '''
        Ошибка при отсутствии поля action
        :return:
        '''
        self.assertEqual(message_from_to_client({'time': time.time(), 'user': {'account_name': 'user'}}),
                         self.bad_request_answer)


if __name__ == '__main__':
    unittest.main()
