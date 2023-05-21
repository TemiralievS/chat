"""6. Создать текстовый файл test_file.txt, заполнить его тремя строками: «сетевое программирование», «сокет»,
    «декоратор». Проверить кодировку файла по умолчанию. Принудительно открыть файл в формате Unicode и вывести
    его содержимое."""

# 6.1 Создание файла и запись в него строк: «сетевое программирование», «сокет», «декоратор»

"""new_file = open("test_file.txt", "w")
new_file.write("сетевое программирование\nсокет\nдекоратор")
new_file.close()"""

# 6.2 Проверка кодировки файла по умолчанию

with open('test_file.txt') as new_file:
    print(new_file)
# <_io.TextIOWrapper name='test_file.txt' mode='r' encoding='UTF-8'>
    for string in new_file:
        print(string, end='')
new_file.close()

# 6.3 Принудительно открыть файл в формате Unicode и вывести его содержимое

new_file_2 = open('test_file.txt', 'rb')
for string in new_file_2:
    print(string.decode(encoding='utf-8'))


