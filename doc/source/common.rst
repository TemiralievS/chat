Common package
=================================================

Пакет общих утилит, использующихся в разных модулях проекта.

Скрипт decors.py
---------------

.. automodule:: common.decors
	:members:
	
Скрипт dscriptors.py
---------------------

.. autoclass:: common.dscriptors.Port
    :members:
   
Скрипт errors.py
---------------------
   
.. autoclass:: common.errors.ServerError
   :members:
   
Скрипт metaclasses.py
-----------------------

.. autoclass:: common.meta.ServerCheck
   :members:
   
.. autoclass:: common.meta.ClientCheck
   :members:
   
Скрипт funcs.py
---------------------

common.utils. **get_message** (client)


	Функция приёма сообщений от удалённых компьютеров. Принимает сообщения JSON,
	декодирует полученное сообщение и проверяет что получен словарь.

common.utils. **send_message** (sock, message)


	Функция отправки словарей через сокет. Кодирует словарь в формат JSON и отправляет через сокет.


Скрипт vars.py
---------------------

Содержит разные глобальные переменные проекта.