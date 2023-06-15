"""
2. Написать функцию host_range_ping() для перебора ip-адресов из 
заданного диапазона. Меняться должен только последний октет каждого 
адреса. По результатам проверки должно выводиться соответствующее 
сообщение.
"""

from ipaddress import ip_address
from task_1 import host_ping


def host_range_ping():
    while True:
        ip_addr = input('Введите стартовый ip-адрес для перебора: ')
        fin_oct = int(ip_addr.split('.')[-1])
        quantity = int(input('Введите диапазон перебора: '))
        if fin_oct > 255:
            print('Неправильно введен ip-адрес')
        elif (fin_oct + quantity) > 254:
            print('Превышено максимально количество хостов')
        else:
            break

    ip_addresses_list = [str(ip_address(ip_addr)+x) for x in range(quantity)]
    return host_ping(ip_addresses_list)


if __name__== "__main__":
    host_range_ping()

"""
Введите стартовый ip-адрес для перебора: 77.88.55.88
Введите диапазон перебора: 4 
Узел 77.88.55.88 - доступен
Узел 77.88.55.89 - недоступен
Узел 77.88.55.90 - недоступен
Узел 77.88.55.91 - недоступен
"""