"""3. Задание на закрепление знаний по модулю yaml. Написать скрипт, автоматизирующий сохранение данных в файле
     YAML-формата. Для этого:

        3.1 Подготовить данные для записи в виде словаря, в котором первому ключу соответствует список,
        второму — целое число, третьему — вложенный словарь, где значение каждого ключа — это целое число с
        юникод-символом, отсутствующим в кодировке ASCII (например, €);

        3.2 Реализовать сохранение данных в файл формата YAML — например, в файл file.yaml.
        При этом обеспечить стилизацию файла с помощью параметра default_flow_style, а также установить
        возможность работы с юникодом: allow_unicode = True;

        3.3 Реализовать считывание данных из созданного файла и проверить, совпадают ли они с исходными."""

import yaml

data_for_yaml = {'name': ['PC', 'laptop', 'processor', 'video card'], 'name_quantity': 4,
                 'price': {'PC': '1000€', 'laptop': '1500€', 'processor': '250€', 'video card': '500€'}}

with open('file.yaml', 'w', encoding='utf-8') as file_write:
    yaml.dump(data_for_yaml, file_write, default_flow_style=False, allow_unicode=True, sort_keys=False)

with open('file.yaml', 'r', encoding='utf-8') as file_read:
    data_from_yaml = yaml.load(file_read, Loader=yaml.SafeLoader)

print(data_for_yaml == data_from_yaml)
