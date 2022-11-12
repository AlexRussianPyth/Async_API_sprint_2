# Шаги для запуска этого проекта

1. Создайте свой собственный '.env' файл, или используйте '.env_example'
2. Запустите:
```
    $ docker-compose up --build
```
3. Схема "content" в нашей БД будет создана автоматически при первом запуске docker-compose.
4. Мигрируйте модели в Джанго:
```
    $ docker exec web-container python3 manage.py migrate
```
5. Создайте суперюзера для админки в Джанго (Login: admin, pass: 123):
```
    $ docker exec web-container make superuser
```
6. Соберите файлы статики, которые будут отдаваться сервером Nginx:
```
    $ docker exec -it web-container bash
    $ python3 manage.py collectstatic
```
7. Опционально: Перелейте данные о фильмах из Sqlite3 в Postgre. 
Для этого вам потребуется файл "docker-compose.dev.yml"
```
    $ docker-compose -f docker-compose.dev.yml up --build
```
Далее используйте скрипт load_data.py из модуля db_loader. Нам понадобится создать виртуальное 
окружение перед использованием загрузчика: 
```
    $ python3 -m venv venv
    $ source venv/bin/activate
    $ pip install -r service/requirements.txt
```
Затем на время поменяем значение переменной DB_HOST с 'db' на 0.0.0.0 (так как наш скрипт
не работает с DNS Докера). Переменная находится в файле '.env'.
```
    $ python3 db_loader/load_data.py
```
Возвратите переменную обратно к значению 'db'.

Установка проекта завершена!


Проект полностью контейнеризован, поэтому для его запуска всегда достаточно набрать
```
    $ docker-compose up
```

## Тесты
Чтобы запустить тесты, наберите следующую команду из директории, в которой находится Makefile:
```
    $ make test-compose
```
