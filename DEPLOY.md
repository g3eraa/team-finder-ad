# Выкладка на сервер

> **Для проверки проекта этот документ не нужен:** всё запускается локально по [README](readme.md).
> Здесь описано, как выложить проект на свой сервер с доменом.
> **Статус:** пайплайн собирает и публикует образы; шаг деплоя выключен, пока сервер не подключён.

## Как устроен CI/CD

```text
push в main → flake8 + тесты → сборка образов → ghcr.io → ssh: docker compose pull && up -d
```

| Задача в [`ci.yml`](.github/workflows/ci.yml) | Когда запускается | Что делает |
|---|---|---|
| `lint` | каждый push и pull request в `main`, `develop` | `flake8` |
| `tests` | там же | `manage.py check`, проверка миграций, тесты на PostgreSQL 16 |
| `build` | после `lint` и `tests` | собирает образы `web` и `gateway`; при push в `main` публикует их в `ghcr.io` с тегами `latest` и SHA коммита |
| `deploy` | push в `main`, если задана переменная `DEPLOY_ENABLED=true` | копирует `docker-compose.production.yml` на сервер, скачивает образы этого коммита и перезапускает контейнеры |

На сервере работают те же три контейнера, что и локально: `db`, `web` и `gateway`.
Caddy в `gateway` сам получает и продлевает HTTPS-сертификат Let's Encrypt для домена.

---

## 1. Сервер

Подойдёт любой VPS с Ubuntu 22.04/24.04, 1 CPU и 1 ГБ памяти.

```bash
# на сервере
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER        # перелогиниться, чтобы группа применилась
mkdir ~/team-finder
```

В файрволе откройте порты `22`, `80` и `443` (TCP), а также `443/udp` для HTTP/3.

## 2. Ключ для деплоя

На своём компьютере создайте отдельный ключ без пароля:

```bash
ssh-keygen -t ed25519 -f ~/.ssh/teamfinder_deploy -N "" -C "github-actions-deploy"
ssh-copy-id -i ~/.ssh/teamfinder_deploy.pub user@SERVER_IP
```

## 3. Файл `.env` на сервере

Создайте `~/team-finder/.env`. Сгенерировать секретный ключ:
`python3 -c "import secrets; print(secrets.token_urlsafe(50))"`.

**С доменом** (замените `teamfinder.ru` на свой):

```dotenv
DJANGO_SECRET_KEY=<сгенерированный ключ>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=teamfinder.ru,www.teamfinder.ru
DJANGO_CSRF_TRUSTED_ORIGINS=https://teamfinder.ru,https://www.teamfinder.ru
DJANGO_SECURE_COOKIES=True
SITE_ADDRESS=teamfinder.ru, www.teamfinder.ru

POSTGRES_DB=team_finder
POSTGRES_USER=team_finder
POSTGRES_PASSWORD=<длинный случайный пароль>
POSTGRES_HOST=db
POSTGRES_PORT=5432

TASK_VERSION=2
```

**Пока домена нет**, сайт можно открыть по IP по обычному HTTP. Отличия от варианта выше:

```dotenv
DJANGO_ALLOWED_HOSTS=SERVER_IP
DJANGO_CSRF_TRUSTED_ORIGINS=
DJANGO_SECURE_COOKIES=False
# SITE_ADDRESS не задавать — Caddy слушает порт 80 без HTTPS
```

## 4. Секреты и переменные в GitHub

Репозиторий → Settings → Secrets and variables → Actions.

| Тип      | Имя              | Значение                                                      |
|----------|------------------|---------------------------------------------------------------|
| Secret   | `SSH_HOST`       | IP сервера                                                    |
| Secret   | `SSH_USER`       | пользователь на сервере                                       |
| Secret   | `SSH_KEY`        | содержимое `~/.ssh/teamfinder_deploy` (приватный ключ целиком) |
| Secret   | `SSH_PORT`       | порт SSH, если не `22` (необязательно)                        |
| Variable | `DEPLOY_ENABLED` | `true` — включает шаг деплоя                                  |
| Variable | `DEPLOY_DIR`     | папка на сервере, если не `team-finder` (необязательно)       |

Публиковать образы в `ghcr.io` можно без настроек: используется встроенный `GITHUB_TOKEN`.

## 5. Первый деплой

Сделайте push или merge в `main`. После зелёного пайплайна на сервере:

```bash
cd ~/team-finder
docker compose -f docker-compose.production.yml exec web python manage.py createsuperuser
# при желании — тестовые пользователи и проекты:
docker compose -f docker-compose.production.yml exec web python manage.py loaddata test_data
```

Миграции и `collectstatic` выполняются сами при каждом старте контейнера `web`.

## 6. Когда появится домен

1. У регистратора добавьте DNS-записи `A` для `teamfinder.ru` и `www.teamfinder.ru` с IP сервера.
2. Дождитесь, пока `dig +short teamfinder.ru` вернёт IP сервера.
3. Замените `.env` на вариант «с доменом» из шага 3.
4. Перезапустите контейнеры:

   ```bash
   cd ~/team-finder && docker compose -f docker-compose.production.yml up -d
   ```

   Caddy получит сертификат за несколько секунд и начнёт перенаправлять HTTP на HTTPS.
   Логи: `docker compose -f docker-compose.production.yml logs gateway`.

## Полезные команды на сервере

```bash
cd ~/team-finder
docker compose -f docker-compose.production.yml ps          # состояние контейнеров
docker compose -f docker-compose.production.yml logs -f web # логи Django
IMAGE_TAG=<sha коммита> docker compose -f docker-compose.production.yml up -d   # откат на версию
docker compose -f docker-compose.production.yml exec db \
  pg_dump -U team_finder team_finder > backup.sql           # резервная копия базы
```
