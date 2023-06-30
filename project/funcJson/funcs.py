import json
import sys
sys.path.append('../')
from log.decorator_log import log


@log
def get_message(client):
    encoded_response = client.recv(1024)
    json_response = encoded_response.decode('utf-8')
    response = json.loads(json_response)
    if isinstance(response, dict):
        return response
    else:
        raise TypeError


@log
def send_message(sock, message):
    js_message = json.dumps(message)
    encoded_message = js_message.encode('utf-8')
    sock.send(encoded_message)