"""2. Каждое из слов «class», «function», «method» записать в байтовом типе без преобразования в последовательность
    кодов (не используя методы encode и decode) и определить тип, содержимое и длину соответствующих переменных."""

var_class = "class"
var_function = "function"
var_method = "method"
var_list = [var_class, var_function, var_method]
bytes_list = [bytes(elem, 'ascii') for elem in var_list]
print(f'Список переменных{bytes_list}\n')


for var in bytes_list:
    print(f'Переменная: {var}, тип: {type(var)}, длина: {len(var)}\n')

