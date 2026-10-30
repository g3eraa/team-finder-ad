# TeamFinder

Сервис для поиска команды на pet-проекты. Можно опубликовать свою идею,
присоединиться к чужому проекту и найти участников с нужными навыками.
Это вариант 2 задания: навыки в профиле и фильтрация пользователей по ним.

Проект написан на Django 5.2, база — PostgreSQL 16. Для аватарок используется Pillow.
На сервере Django работает через Gunicorn, а Caddy отдаёт статику и медиа и принимает
HTTPS-запросы. Всё это запускается через Docker Compose.

## Как запустить

Сначала склонируйте репозиторий и создайте `.env` из примера:

```bash
git clone git@github.com:g3eraa/team-finder-ad.git
cd team-finder-ad
cp .env_example .env
```

Для локального запуска подходят значения из `.env_example`.

### Весь проект в Docker

```bash
docker compose up -d --build
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
Остановить проект — `docker compose down`. База, аватарки и собранная статика
сохраняются в volumes.

### Django локально, PostgreSQL в Docker

Для этого способа нужен Python 3.10–3.13. Команды ниже — для macOS и Linux.

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

## Переменные окружения

Пример настроек находится в [.env_example](.env_example). При локальном запуске
PostgreSQL доступна на порту `5436`. `TASK_VERSION=2` выбирает шаблоны из `templates_var2`.
При запуске всего проекта в Docker адрес базы заменяется на `db`, порт — на `5432`,
а `DJANGO_DEBUG` устанавливается в `False`.

Для сервера задайте собственные секретный ключ и пароль базы, разрешённые домены
и параметры HTTPS. Порядок настройки описан в [разделе «Деплой»](#деплой) ниже.

## Данные для проверки

Команда `loaddata test_data` загружает пять пользователей, их навыки и шесть
проектов из [fixtures/test_data.json](fixtures/test_data.json). У каждого пользователя
есть свой проект. Аватарки лежат в `media/avatars/`.

Для входа можно использовать любой из аккаунтов:

- `anna@example.com`
- `maxim@example.com`
- `katya@example.com`
- `dmitry@example.com`
- `sofia@example.com`

Пароль у всех — `testpass123`.

## Проверка кода

```bash
pip install -r requirements-dev.txt
flake8 .
isort --check-only .
python manage.py check
python manage.py makemigrations --check --dry-run
```

Чтобы исправить порядок импортов, выполните `isort .`. Настройки flake8 и isort
лежат в `setup.cfg`.

В [GitHub Actions](.github/workflows/ci.yml) эти проверки запускаются при push
и pull request в `main` и `develop`. Там же миграции применяются к отдельной
PostgreSQL и собираются Docker-образы. При push в `main` образы публикуются в GHCR
с тегами `latest` и SHA коммита.

## Деплой

Для сервера используется [docker-compose.production.yml](docker-compose.production.yml).
Он запускает PostgreSQL, Django и Caddy из готовых образов. Деплой из GitHub Actions
включается переменной `DEPLOY_ENABLED=true`.

### Подготовка сервера

На сервере должны быть установлены Docker и Docker Compose. Пользователю,
под которым будет выполняться деплой, нужен доступ к Docker без `sudo`.
Создайте папку проекта в его домашней директории:

```bash
mkdir -p ~/team-finder
```

Откройте порты SSH, `80` и `443` по TCP. Для HTTP/3 нужен ещё `443/udp`.
Если есть домен, добавьте DNS-записи `A`, указывающие на IP сервера.

На своём компьютере создайте отдельный SSH-ключ и добавьте его на сервер.
Вместо `user@SERVER_IP` укажите своего пользователя и адрес:

```bash
ssh-keygen -t ed25519 -f ~/.ssh/teamfinder_deploy -N "" -C "github-actions-deploy"
ssh-copy-id -i ~/.ssh/teamfinder_deploy.pub user@SERVER_IP
```

### Настройки на сервере

Создайте файл `~/team-finder/.env` на основе `.env_example`. Задайте собственные
пароль базы и секретный ключ, установите `DJANGO_DEBUG=False`, `POSTGRES_HOST=db`
и `POSTGRES_PORT=5432`. Ключ можно сгенерировать локально:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

Для доступа по IP укажите адрес сервера в `DJANGO_ALLOWED_HOSTS`, оставьте
`DJANGO_CSRF_TRUSTED_ORIGINS` пустым, поставьте `DJANGO_SECURE_COOKIES=False`
и не задавайте `SITE_ADDRESS`. Сайт будет доступен по HTTP на порту 80.

### Настройки GitHub Actions

В репозитории откройте Settings → Secrets and variables → Actions.

| Тип | Имя | Значение |
|---|---|---|
| Secret | `SSH_HOST` | IP или адрес сервера |
| Secret | `SSH_USER` | Пользователь на сервере |
| Secret | `SSH_KEY` | Содержимое приватного ключа `~/.ssh/teamfinder_deploy` |
| Secret | `SSH_PORT` | Порт SSH, если отличается от `22` |
| Variable | `DEPLOY_ENABLED` | `true` |
| Variable | `DEPLOY_DIR` | Папка проекта, если отличается от `team-finder` |

Для публикации образов используется встроенный `GITHUB_TOKEN`.
После push в `main` workflow проверит код, соберёт образы, скопирует Compose-файл
на сервер и перезапустит контейнеры с новой версией.

После первого деплоя подключитесь к серверу и создайте суперпользователя:

```bash
cd ~/team-finder
docker compose -f docker-compose.production.yml exec web python manage.py createsuperuser
```

При необходимости загрузите демонстрационные данные:

```bash
docker compose -f docker-compose.production.yml exec web python manage.py loaddata test_data
```

Миграции и сборка статики выполняются при старте `web`. Если указан домен,
Caddy получает и продлевает HTTPS-сертификат автоматически.

После изменения `.env` выполните `docker compose -f docker-compose.production.yml up -d`.

### Команды на сервере

Состояние контейнеров и логи Django:

```bash
cd ~/team-finder
docker compose -f docker-compose.production.yml ps
docker compose -f docker-compose.production.yml logs -f web
```

Логи HTTPS и прокси можно посмотреть той же командой, заменив `web` на `gateway`.

Резервная копия базы:

```bash
docker compose -f docker-compose.production.yml exec -T db \
  pg_dump -U team_finder team_finder > backup.sql
```

Чтобы запустить образы другого коммита, замените `commit_sha` на его SHA:

```bash
export IMAGE_TAG=commit_sha
docker compose -f docker-compose.production.yml pull web gateway
docker compose -f docker-compose.production.yml up -d
```

## Автор

Yegor Gerasimov — [g3eraa](https://github.com/g3eraa).
