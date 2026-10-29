FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN useradd --create-home --uid 1000 app \
    && mkdir -p staticfiles media \
    && chown -R app:app staticfiles media

USER app

EXPOSE 8000

# Миграции и сборка статики выполняются при старте контейнера, см. entrypoint.sh.
ENTRYPOINT ["./entrypoint.sh"]
CMD ["gunicorn", "team_finder.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--access-logfile", "-"]
