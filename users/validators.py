import re
from urllib.parse import urlparse

from django.contrib.auth import password_validation
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


def _plural_ru(number, one, few, many):
    if number % 10 == 1 and number % 100 != 11:
        return one
    if 2 <= number % 10 <= 4 and not 12 <= number % 100 <= 14:
        return few
    return many


class MinimumLengthValidator(password_validation.MinimumLengthValidator):
    """Стандартный валидатор с русским текстом: в переводе Django 5.2 его нет."""

    def _min_length_text(self):
        symbols = _plural_ru(self.min_length, "символ", "символа", "символов")
        return f"{self.min_length} {symbols}"

    def get_error_message(self):
        return f"Пароль слишком короткий: нужно не меньше {self._min_length_text()}."

    def get_help_text(self):
        return f"Пароль должен содержать не меньше {self._min_length_text()}."
