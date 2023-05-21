"""2. Задание на закрепление знаний по модулю json. Есть файл orders в формате JSON с информацией о заказах.
     Написать скрипт, автоматизирующий его заполнение данными. Для этого:

        2.1 Создать функцию write_order_to_json(), в которую передается 5 параметров — товар (item),
        количество (quantity), цена (price), покупатель (buyer), дата (date). Функция должна предусматривать запись
        данных в виде словаря в файл orders.json. При записи данных указать величину отступа в 4 пробельных символа;

        2.2 Проверить работу программы через вызов функции write_order_to_json() с передачей в нее значений каждого
        параметра."""

import json


def write_order_to_json(item, quantity, price, buyer, date):
    with open('orders.json', 'r', encoding='utf-8') as read_file:
        data = json.load(read_file)

    with open('orders.json', 'w', encoding='utf-8') as write_file:
        orders_list = data['orders']
        order_info = {'item': item, 'quantity': quantity,
                      'price': price, 'buyer': buyer, 'date': date}
        orders_list.append(order_info)
        json.dump(data, write_file, indent=4, ensure_ascii=False)


write_order_to_json('ПК', '1', '60000', 'Сергей', '21.05.2023')
write_order_to_json('Копир', '2', '6000', 'Олег', '20.05.2023')
