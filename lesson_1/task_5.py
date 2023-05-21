"""5. Выполнить пинг веб-ресурсов yandex.ru, youtube.com и преобразовать результаты из байтовового в строковый тип
    на кириллице."""

import subprocess
import chardet

args = ['ping', 'youtube.com']
ping = subprocess.Popen(args, stdout=subprocess.PIPE)
for line in ping.stdout:
    result = chardet.detect(line)
    line = line.decode(result['encoding']).encode('utf-8')
    print(line.decode('utf-8'))


