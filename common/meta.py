import dis


class ServerCheck(type):
    '''
    Метакласс, проверяющий что в результирующем классе нет клиентских
    вызовов таких как: connect. Также проверяется, что серверный
    сокет является TCP и работает по IPv4 протоколу.
    '''
    def __init__(self, clsname, basecls, funcdict):
        methods = []
        attrs = []
        for func in funcdict:
            try:
                ret = dis.get_instructions(funcdict[func])
            except TypeError:
                pass
            else:
                for i in ret:
                    print(i)
                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval not in methods:
                            methods.append(i.argval)
                    elif i.opname == 'LOAD_ATTR':
                        if i.argval not in attrs:
                            attrs.append(i.argval)
        print(methods)
        if 'connect' in methods:
            raise TypeError('Недопустимый метод в серверном классе')
        if not ('SOCK_STREAM' in attrs and 'AF_INET' in attrs):
            raise TypeError('Некорректная инициализация сокета.')
        super().__init__(clsname, basecls, funcdict)


class ClientCheck(type):
    '''
    Метакласс, проверяющий что в результирующем классе нет серверных
    вызовов таких как: accept, listen. Также проверяется, что сокет не
    создаётся внутри конструктора класса.
    '''
    def __init__(self, clsname, basecls, funcdict):
        methods = []
        for func in funcdict:
            try:
                ret = dis.get_instructions(funcdict[func])
            except TypeError:
                pass
            else:
                for i in ret:
                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval not in methods:
                            methods.append(i.argval)
        for command in ('accept', 'listen', 'socket'):
            if command in methods:
                raise TypeError('Oбнаружено использование запрещённого метода')
            if 'get_message' in methods or 'send_message' in methods:
                pass
            else:
                raise TypeError(
                    'Отсутствуют вызовы функций, работающих с сокетами.')
            super().__init__(clsname, basecls, funcdict)
