# TeamFinder

Платформа для поиска команды на pet-проекты. Пользователи публикуют проекты,
присоединяются к командам, заполняют профиль и добавляют навыки. В списке участников
доступна фильтрация по навыкам.

Стек: Python, Django 5.2, PostgreSQL 16, Pillow, Gunicorn, Caddy, Docker Compose.
Интерфейс построен на Django Templates, CSS и JavaScript.

## Запуск в Docker

```bash
git clone git@github.com:g3eraa/team-finder-ad.git
cd team-finder-ad
cp .env_example .env
docker compose up -d --build
docker compose exec web python manage.py loaddata test_data
docker compose exec web python manage.py createsuperuser
```

Сайт доступен по адресу http://localhost/, админка — http://localhost/admin/.
Миграции и сборка статики выполняются автоматически при запуске контейнера `web`.
Применить миграции вручную:

```bash
docker compose exec web python manage.py migrate
```

Если порт 80 занят, укажите другой: `GATEWAY_PORT=8080 docker compose up -d`.
Для остановки выполните `docker compose down`. Данные хранятся в Docker volumes.

## Локальный запуск Django

Нужны Python 3.10–3.13 и Docker для PostgreSQL.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env_example .env
docker compose up -d db
python manage.py migrate
python manage.py loaddata test_data
python manage.py createsuperuser
python manage.py runserver
```

Сайт доступен по адресу http://127.0.0.1:8000/, админка — http://127.0.0.1:8000/admin/.

## Переменные окружения

Пример конфигурации — [.env_example](.env_example):

```dotenv
DJANGO_SECRET_KEY=change_for_safety
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DJANGO_CSRF_TRUSTED_ORIGINS=
DJANGO_SECURE_COOKIES=False

POSTGRES_DB=team_finder
POSTGRES_USER=team_finder
POSTGRES_PASSWORD=team_finder
POSTGRES_HOST=localhost
POSTGRES_PORT=5436

TASK_VERSION=2
```

Для локального запуска подходят значения из примера. `TASK_VERSION=2` выбирает
шаблоны из `templates_var2/`. В Docker адрес базы заменяется на `db`, порт — на `5432`,
а `DJANGO_DEBUG` устанавливается в `False`.

Для сервера задайте собственные секретный ключ и пароль базы, разрешённые домены
и параметры HTTPS. Порядок настройки описан в [DEPLOY.md](DEPLOY.md).

## Демонстрационные данные

Файл [fixtures/test_data.json](fixtures/test_data.json) содержит пять пользователей,
их навыки и шесть проектов. Команда `loaddata test_data` загружает эти данные после
миграций. Аватарки находятся в `media/avatars/`.

Аккаунты: `anna@example.com`, `maxim@example.com`, `katya@example.com`,
`dmitry@example.com`, `sofia@example.com`. Пароль для всех — `testpass123`.

## Проверки кода

```bash
pip install -r requirements-dev.txt
flake8 .
isort --check-only .
python manage.py check
python manage.py makemigrations --check --dry-run
```

Для сортировки импортов выполните `isort .`. Настройки flake8 и isort находятся
в `setup.cfg`. GitHub Actions запускает эти проверки, применяет миграции на
PostgreSQL и собирает Docker-образы.

## Автор

Yegor Gerasimov — [g3eraa](https://github.com/g3eraa).
