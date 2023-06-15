"""
1. Написать функцию host_ping(), в которой с помощью утилиты ping
будет проверяться доступность сетевых узлов.
Аргументом функции является список, в котором каждый сетевой узел
должен быть представлен именем хоста или ip-адресом.
В функции необходимо перебирать ip-адреса и проверять
их доступность с выводом соответствующего сообщения
(«Узел доступен», «Узел недоступен»). При этом ip-адрес
сетевого узла должен создаваться с помощью функции ip_address().
"""

import subprocess
from ipaddress import ip_address
from pprint import pprint

def host_ping(ping_addr_list: list):
    available_list = []
    unavailable_list = []
    addresses_status = {'Доступные узлы': "", 'Недоступные узлы': ""}
    for addr in ping_addr_list:
        ip_addr = ip_address(addr)
        ping = subprocess.Popen(f"ping {addr} -w {500} -n {1}", shell=False, stdout=subprocess.PIPE)
        ping.wait()
        if ping.returncode == 0:
            print(f'Узел {str(addr)} - доступен')
            addresses_status['Доступные узлы'] += f'{str(addr)}\n'
            available_list.append(str(addr))
        else:
            unavailable_list.append(str(addr))
            addresses_status['Недоступные узлы'] += f'{str(addr)}\n'
            print(f'Узел {str(addr)} - недоступен')
    pprint(addresses_status)
    return addresses_status


if __name__ == '__main__':
 ip_addrs = ['77.88.55.88', '192.168.0.101','5.255.255.70', '192.168.0.5']
 host_ping(ip_addrs)


 """
Узел 77.88.55.88 - доступен
Узел 192.168.0.101 - недоступен
Узел 5.255.255.70 - доступен
Узел 192.168.0.5 - недоступен
 """