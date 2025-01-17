## Foodgram.

http://foodbammm.hopto.org развернул
 [Крамич Алексей Эдуардович ](https://github.com/kram1k)


---
## Backend stack:
- Python
	- Django rest-framework
	- django-filter
	- psycopg2-binary
	- reportlab
	- pytest
	- PyYAML
	- gunicorn
	- python-dotenv
- DB
	- PostgreSQL
	- SQLite
- Docker
- nginx


---
## CD/CI для развертывания

### Команды локального развертывания с Докером 
##### Клонирование репозитория.
`git clone https://github.com/kram1k/foodgram.git`
##### Переход в папку с `docker-compose.yml`.
`cd infra`
##### Создание .env файла
`SECRET_KEY=django-key...`\
`DEBUG=False`\
`ALLOWED_HOSTS=<ваш хост>,127.0.0.1,localhost`\
`POSTGRES_USER=<имя пользователя>`\
`POSTGRES_PASSWORD=<пароль>`\
`POSTGRES_DB=<имя базы данных>`\
`DB_HOST=<хост>`\
`DB_PORT=<порт>`
##### Подъем контейнераов в Докере.
`sudo docker compose -f docker-compose.production.yml pull`\
`sudo docker compose -f docker-compose.production.yml down`
##### Подготовка базы:
Миграции:
`sudo docker compose -f docker-compose.production.yml exec backend python manage.py makemigrations`\
`sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate`\
Создание супер-пользователя:
`sudo docker compose -f docker-compose.production.yml exec backend python manage.py createsuperuser`
##### Сборка статики.
`sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic --noinput`
##### Запуск сервера.

`sudo docker compose -f docker-compose.production.yml up -d`
## Команды локального развертывания без Докера

#### Клонирование репозитория.
`git clone https://github.com/kram1k/foodgram.git`
#### Настройка виртуального окружения
`cd backend`\
`py -3.9 -m venv venv`\
`. venv/Scripts/activate`\
`py -m pip install --upgrade pip`\
`pip install -r requirements.txt`\
#### Заполнение `.env`
`SECRET_KEY=django-key...`\
`DEBUG=True`\
`ALLOWED_HOSTS=<ваш хост>,127.0.0.1,localhost`

#### Миграция базы и создание супера.
`py manage.py createsuperuser`\
`py manage.py makemigrations`\
`py manage.py migrate`
#### Импорт продуктов JSON фикстур.
py manage.py loaddata <ваш файл JSON >  
#### Запуск сервера.
py manage.py runserver  

#### Ссылка (для локального сервера) для получения полной тех-доки к API.
Скачать schema.yaml: http://127.0.0.1:8000/schema/
Swagger:  http://127.0.0.1:8000/docs/swagger/
Redoc: http://127.0.0.1:8000/docs/redoc/