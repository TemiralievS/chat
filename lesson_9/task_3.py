"""
3. Написать функцию host_range_ping_tab(), возможности которой основаны 
на функции из примера 2. Но в данном случае результат должен быть 
итоговым по всем ip-адресам, представленным в табличном формате
(использовать модуль tabulate). 
Таблица должна состоять из двух колонок
"""

from tabulate import tabulate
from task_2 import host_range_ping


def host_range_ping_tab():
    host_range_dict = host_range_ping()
    print('\n \n')
    print(tabulate([host_range_dict], headers='keys', tablefmt='grid', stralign='center'))


if __name__ == "__main__":
    host_range_ping_tab()


"""
Введите стартовый ip-адрес для перебора: 77.88.55.88
Введите диапазон перебора: 3
Узел 77.88.55.88 - доступен
Узел 77.88.55.89 - недоступен
Узел 77.88.55.90 - недоступен
{'Доступные узлы': '77.88.55.88\n',
 'Недоступные узлы': '77.88.55.89\n77.88.55.90\n'}



+------------------+--------------------+
|  Доступные узлы  |  Недоступные узлы  |
+==================+====================+
|   77.88.55.88    |    77.88.55.89     |
|                  |    77.88.55.90     |
+------------------+--------------------+
"""