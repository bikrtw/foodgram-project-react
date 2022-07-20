# Foodgram

Сервис для сбора рецептов и удобного получения списка покупок

Дипломный проект Яндекс Практикума, 29 когорта.

## Тестовый сервер

Доступен по адресу: ```http://84.252.136.64```

### Как запустить проект в докере:

Клонировать репозиторий и перейти в него в командной строке:
```
git clone https://github.com/bikrtw/foodgram-project-react.git
cd foodgram-project-react
```

Перейти в директорию, содержащую файл docker-compose.yaml:
```
cd infra
```

Запустить docker-compose
```
sudo docker-compose up -d
```

Выполнить миграции и собрать статику:
```
sudo docker-compose exec web python manage.py migrate
sudo docker-compose exec web python manage.py collectstatic --no-input
```

(Опционально) Заполнить базу тестовыми данными и потестить функционал:

Тестовый пользователь: ```1@1.com``` Пароль: ```123```
```
sudo docker-compose exec web python manage.py load_csv
```

Для очистки базы:
```
sudo docker-compose exec web python manage.py clear_db
```

Создать админскую учетку:
```
sudo docker-compose exec web python manage.py createsuperuser
```

(Опционально) Восстановить базу из бекапа:
```
sudo docker-compose exec web python manage.py loaddata dump.json
```

Профит!

## Содержимое файла .env:
```
DB_ENGINE=django.db.backends.postgresql # указываем, что работаем с postgresql
DB_NAME=postgres # имя базы данных
POSTGRES_USER=postgres # логин для подключения к базе данных
POSTGRES_PASSWORD=password # пароль для подключения к БД (установите свой)
DB_HOST=db # название сервиса (контейнера)
DB_PORT=5432 # порт для подключения к БД 
```
