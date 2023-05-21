"""3. Определить, какие из слов «attribute», «класс», «функция», «type» невозможно записать в байтовом типе."""

var_attribute = "attribute"
var_clss = "класс"
var_func = "функция"
var_type = "type"
var_list = [var_attribute, var_clss, var_func, var_type]

for elem in var_list:
    try:
        bytes(elem, 'ascii')
    except UnicodeEncodeError:
        print(f'{elem} невозможно перевести в байтовый тип')

# либо можно проверить переменные из списка var_list с помощью .isascii, тогда при значении False, переменную нельзя
# записать в байтовом типе

not_bytes_list = [var for var in var_list if var.isascii() is False]
print(f'Слова {not_bytes_list} невозможно записать в виде байтовой строки')