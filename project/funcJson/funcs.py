import json
import sys
from project.log.decorator_log import log


@log
def get_message(client):
    '''
    Функция для приёма и декодирования сообщения в байтовом формате.
    Выдаёт словарь. если принятое сообщение не в байтовом формате, отдаёт ошибку значения
    :param client:
    :return:
    '''

    encoded_response = client.recv(1024)
    if isinstance(encoded_response, bytes):
        json_response = encoded_response.decode('utf-8')
        response = json.loads(json_response)
        if isinstance(response, dict):
            return response
        raise ValueError
    raise ValueError


@log
def send_message(sock, message):
    '''
    Функция кодирования и отправки сообщения
    принимает словарь и отправляет его
    :param sock:
    :param message:
    :return:
    '''

    js_message = json.dumps(message)
    encoded_message = js_message.encode('utf-8')
    sock.send(encoded_message)
