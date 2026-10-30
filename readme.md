# TeamFinder

TeamFinder помогает найти команду для pet-проекта. Пользователь может опубликовать
идею, присоединиться к чужой команде или найти человека с нужными навыками.
В профилях видны описание, контакты и проекты участников.

Учебный проект, вариант 2 — навыки пользователей и фильтрация участников по навыкам.

## Возможности

- Регистрация и вход по email, редактирование профиля и смена пароля.
- Загрузка аватара. Если его нет, при создании аккаунта генерируется картинка с первой буквой имени.
- Создание и редактирование своих проектов, завершение проекта со сменой статуса на «Закрыт».
- Присоединение к чужому проекту и выход из его участников.
- Добавление и удаление навыков в профиле, подсказки при вводе и создание новых навыков.
- Поиск участников по выбранному навыку. Проекты и участники выводятся по 12 на странице.
- Управление пользователями и проектами через админку Django.

Гости могут просматривать проекты и профили. Для создания проекта, участия в команде
и изменения своих данных нужно войти в аккаунт.

## Технологии

Python, Django 5.2, PostgreSQL 16, Pillow, HTML, CSS и JavaScript.
Страницы собираются на сервере через Django Templates.

Для запуска используется Docker Compose. Caddy принимает запросы,
отдаёт статику и загруженные файлы.

## Как запустить

Сначала склонируйте репозиторий и создайте `.env` из примера:

```bash
git clone git@github.com:g3eraa/team-finder-ad.git
cd team-finder-ad
cp .env_example .env
```

Для локального запуска подходят значения из `.env_example`.

### Весь проект в Docker

Для этого способа достаточно Docker с Docker Compose. Python и PostgreSQL
на компьютер устанавливать не нужно.

```bash
docker compose up -d --build
```

Загрузите данные для проверки и создайте администратора:

```bash
docker compose exec web python manage.py loaddata test_data
docker compose exec web python manage.py createsuperuser
```

Сайт откроется на http://localhost/, админка — на http://localhost/admin/.
При создании суперпользователя нужно указать email, имя, фамилию и пароль.

Миграции и сборка статики выполняются при старте `web`. Если нужно применить
миграции отдельно:

```bash
docker compose exec web python manage.py migrate
```

Если порт 80 занят, можно выбрать другой: `GATEWAY_PORT=8080 docker compose up -d`.
В этом случае сайт будет доступен на http://localhost:8080/.
Остановить проект — `docker compose down`. База, аватарки и собранная статика
сохраняются в volumes.

### Django локально, PostgreSQL в Docker

Нужны Python 3.10–3.13 и Docker Compose. Команды ниже — для macOS и Linux;
`python3` должен указывать
на одну из поддерживаемых версий Python.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
docker compose up -d db
python manage.py migrate
python manage.py loaddata test_data
python manage.py createsuperuser
python manage.py runserver
```

Сайт откроется на http://localhost:8000/, админка — на http://localhost:8000/admin/.
Настройки подключения к базе берутся из `.env`.

## Деплой

Деплой запускается через [GitHub Actions](.github/workflows/ci.yml).
На сервере используется [docker-compose.production.yml](docker-compose.production.yml).

1. Подготовьте сервер с Docker, Docker Compose и доступом по SSH. Создайте папку
   `~/team-finder` и откройте порт 80. Пользователь для деплоя должен иметь доступ
   к Docker без `sudo`.
2. Создайте в этой папке `.env` на основе `.env_example`. Укажите собственные
   секретный ключ и пароль базы, установите `DJANGO_DEBUG=False` и добавьте адрес
   сервера в `DJANGO_ALLOWED_HOSTS`.
3. В настройках репозитория GitHub добавьте секреты `SSH_HOST`, `SSH_USER`, `SSH_KEY`
   и переменную `DEPLOY_ENABLED=true`. Если порт SSH отличается от 22, задайте
   секрет `SSH_PORT`. Для другой папки проекта укажите переменную `DEPLOY_DIR`.
4. Сделайте push или merge в `main`. Workflow проверит код, соберёт и опубликует
   образы в GHCR, скопирует Compose-файл на сервер и запустит новую версию проекта.

Миграции и сборка статики выполняются при запуске приложения. Следующие изменения
в `main` выкладываются тем же workflow автоматически.

## Автор

Yegor Gerasimov — [g3eraa](https://github.com/g3eraa).
