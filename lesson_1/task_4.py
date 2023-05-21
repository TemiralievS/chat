"""4. Преобразовать слова «разработка», «администрирование», «protocol», «standard» из строкового представления в
    байтовое и выполнить обратное преобразование (используя методы encode и decode)."""

var_dev = "разработка"
var_admin = "администрирование"
var_protocol = "protocol"
var_standard = "standard"
var_list = [var_dev, var_admin, var_protocol, var_standard]

var_ecode_list = [var.encode('utf-8') for var in var_list]
var_decode_list = [var.decode('utf-8') for var in var_ecode_list]

print(var_ecode_list)
print(var_decode_list)


# либо можно сделать преобразования с помощью циклов
new_encode_list = []
for elem in var_list:
    new_encode_list.append(elem.encode('utf-8'))
print(new_encode_list)

# решил вспомнить while :D
new_decode_list = []
i = 0
while i in range(len(new_encode_list)):
    new_decode_list.append(new_encode_list[i].decode('utf-8'))
    i+=1
print(new_decode_list)    
