import json


def get_message(sock):
    '''
    Функция для приёма и декодирования сообщения в байтовом формате.
    Выдаёт словарь, если принятое сообщение не в байтовом формате, отдаёт ошибку значения
    :param sock:
    :return:
    '''

    encoded_response = sock.recv(1024)
    if isinstance(encoded_response, bytes):
        json_response = encoded_response.decode('utf-8')
        response = json.loads(json_response)
        if isinstance(response, dict):
            return response
        raise ValueError
    raise ValueError


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
