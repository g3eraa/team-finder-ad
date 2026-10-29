import re
from urllib.parse import urlparse

from django.core.exceptions import ValidationError

PHONE_PATTERN = re.compile(r"(?:\+7|8)\d{10}")
PHONE_SEPARATORS = re.compile(r"[\s()-]")
GITHUB_HOSTS = {"github.com", "www.github.com"}


def normalize_phone(value):
    """Проверяет номер телефона и приводит его к формату +7XXXXXXXXXX."""
    phone = PHONE_SEPARATORS.sub("", value)
    if not PHONE_PATTERN.fullmatch(phone):
        raise ValidationError(
            "Номер телефона должен быть в формате 8XXXXXXXXXX или +7XXXXXXXXXX."
        )
    return f"+7{phone[-10:]}"


def validate_github_url(value):
    if urlparse(value).hostname not in GITHUB_HOSTS:
        raise ValidationError("Ссылка должна вести на GitHub.")
