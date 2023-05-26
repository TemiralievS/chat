from socket import *
import sys
import json

from vars.vars import *
from funcJson.funcs import *


def message_from_to_client(message):
    '''
    Функция принимает сообщение от клиента в виде словаря,
    проверяет правильность структуры сообщения,
    возвращает ответ клиенту в виде словаря
    '''
    if jim_action in message and message[jim_action] == jim_presence and jim_time in message and jim_user in message \
            and message[jim_user][jim_account_name] == 'user':
        return {jim_response: 200}
    else:
        return {jim_response: 400,
                jim_error: 'Bad request'}


def main():
    '''
    Запуск с параметрами командной строки
    Без параметров используются значения по умолчанию
    :return:
    '''
    try:
        if '-p' in sys.argv:
            port = int(sys.argv[sys.argv.index('-p') + 1])
        else:
            port = 7777
        if port < 1024 or port > 65535:
            raise ValueError

    except IndexError:
        print('Not a port')
        sys.exit(1)
    except ValueError:
        print('The port must be in the range (1024:65535)')
        sys.exit(1)

    try:
        if '-a' in sys.argv:
            address = sys.argv[sys.argv.index('-a')+1]
        else:
            address = ''

    except IndexError:
        print(
            'После параметра \'a\'- укажите адрес, который будет слушать сервер.')
        sys.exit(1)

    s = socket(AF_INET, SOCK_STREAM)
    s.bind((address, port))
    s.listen(5)

    while True:
        client, addr = s.accept()
        print('получаем запрос на соединение:', addr)
        try:
            client_message = get_message(client)
            print(client_message)
            check = message_from_to_client(client_message)
            send_message(client, check)
            client.close()
        except (ValueError, json.JSONDecodeError):
            print('Структура сообщения не соответствует требованиям')
            client.close()


if __name__ == '__main__':
    main()
