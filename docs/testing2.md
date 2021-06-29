Регистрация тестов
------------------

ToDo: ???


Формирование полного имени теста
--------------------------------

Полное имя теста формируется следующим образом: <каталог1>.<каталог2>.<имя_теста>[:<номер_теста>] . Имя модуля в формировании полного имени теста не участвует.
Примеры:
```
        TestHellowWord
        root_package.TestHellowWord:1
        root_package.TestHellowWord:2
        root_package.TestHellowWord:3
        root_package.subpackage.TestHellowWord
```


Чтение environment
------------------

ToDo: ????


Основные параметры environment
------------------------------

chip:
        name: <имя_чипа>

connection:
        port: <имя_порта>
        baud: <скорость>
        reset: <метод_ресета>

runlist:
        - каталог всех тестов <полное_имя_теста>: <описание_теста> (объект TestDesc)

