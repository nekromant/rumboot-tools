Регистрация тестов
------------------

Класс теста может быть зарегистрирован следующим способами:
- декоратор:
```
@rtest()
class TestClass(RumbootBaseTest):

@rtest(name = "TestWithName")
class TestClass(RumbootBaseTest):

@rtest(params = { "key": "value1" }, name = "TestWithParameter")
class TestClass(RumbootBaseTest):

@rtest(params = [ { "key": "value1" }, { "key": "value2" }, { "key": "value3" } ], name = "TestWithParameter2")
class TestClass(RumbootBaseTest):
```
- вызов функции регистрации:
```
register_test(TestClass)
register_test(TestClass, name = "TestWithName")
register_test(TestClass, params = { "key": "value", "timeout": 180 }, name = "TestWithParameter")
register_test(TestClass, params = [ { "key": "value1" }, { "key": "value2" }, { "key": "value3" } ], name = "TestsWithParameter")
```
Значения params может быть словарем или массивом словарей (в этом случае регистрируется несколько тестов, к имени теста прибавляется суффикс :<номер_теста>)


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

Параметры environment хранятся в yaml файле. Путь к файлу может быть задан через командную строку (параметр --env).
Если путь не задан, делается попытка прочитать параметры из файла env.yaml в текущем каталоге.

Параметры из файла environment могут быть перекрыты параметрами командной строки. Параметры environment дополняться, например, списком найденных тестов.


Основные параметры environment
------------------------------

chip:
        name: <имя_чипа> ("mm7705"/"oi10"/"basis"/...)

connection:
        port: <имя_порта> (/dev/ttyUSB0/...)
        baud: <скорость> (115200/1000000/...)
        transport: <транспорт> ("xmodem"/"edcl")
        force_static_arp: <установка_маршрутизации_edcl_вручную> (True/False)
        edcl_ip: <IP_адрес_для_edcl> (None/"192.168.1.2"/...)
        edcl_mac: <MAC_адрес_для_edcl> (None/"ec:17:66:00:00:02"/...)
        edcl_timeout: <таймаут_для_edcl> (None/7.0/...)

reset:
        name: <метод_ресета> ("none"/"pl2303"/...)
        <опции_reset> (например, "pl2303-invert")
        port: <имя_порта> (копия connection/port, для совместимости с reset_seq)

gui: <признак_запуска_gui> (True/False)

root_path: <путь_к_артефактам>

report_file_path: <путь_к_отчету_в_формате_JUnit>

tests:
        enabled:
                - <шаблоны_тестов_для_исполнения> (по умолчанию все)
        disabled:
                - <шаблоны_тестов_для_исключения> (по умолчанию нет исключенных тестов)

uboot:
        active: <признак_наличия_uboot> (True/False)
        path_base: <путь_к_каталогу_uboot> (относительно root_path)
        spl_path: <путь_к_образу_spl> (относительно path_base)
        uboot_path: <путь_к_образу_uboot> (относительно path_base)
        mem_setup_cmd: <команда_инициализации_памяти> (например, run setmem)
        mem_ram_addr: <адрес_ОЗУ_для_тестов>
        mem_ram_size: <размер_ОЗУ_длф_тестов>
        sd_card_active: <признак_наличия_sd_card> (True/False)
        sd_card_count: <количество_sd_card>
        sf_probe_active: <признак_наличия_spi_flash> (True/False)
        sf_probe_list:
                - addr: <адрес_на_шине> (0:0/...)
                  detect_name: <строка_определения> ("SF: Detected m25p32 with page size 256 Bytes, erase size 64 KiB, total 4 MiB")
        sram_active: <признак_наличия_SRAM> (True/False)
        nor_active: <признак_наличия_NOR> (True/False)

kernel:
        active: <признак_наличия_linux_kernel> (True/False)
        path_base: <путь_к_каталогу_kernel> (относительно root_path)
        uimage_path: <путь_к_образу_uimage> (относительно path_base)
        dtb_path: <путь_к_образу_device_tree> (относительно path_base)
        bootargs: <опции_запуска>
        user: <имя_пользователя>
        password: <пароль>

openocd:
        active: <признак_наличия_openocd> (True/False)
        path_base: <путь_к_файлам_конфигураций_openocd> (относительно root_path)
        config_path: <путь_к_файлу_конфигурации_openocd> (относительно path_base)
        targets: [<список_целей_targets>]
        jtag_init: [<список_jtag_соединений>]


Таймаут на исполнение теста
---------------------------

Таймаут на выполнение всего теста задается статической переменной тестового класса timeout:
```
class RumbootHelloWorldTest(RumbootTestBase):
    timeout = 30
...
```


Проверка на возможности исполнения теста
----------------------------------------

Перед запуском тест проверяется статическим методом suitable тестового класс. Реализация метода
по умолчанию сравнивает значение словаря requested (статическая переменная класса) со словарем environment.
Все значения из словаря requested должны совпадать со значения из словаря environment.
