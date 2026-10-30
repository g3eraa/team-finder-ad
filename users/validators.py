import re
from urllib.parse import urlparse

from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError

from .constants import PHONE_NATIONAL_NUMBER_LENGTH

PHONE_PATTERN = re.compile(rf"(?:\+7|8)\d{{{PHONE_NATIONAL_NUMBER_LENGTH}}}")
PHONE_SEPARATORS = re.compile(r"[\s()-]")
GITHUB_HOSTS = {"github.com", "www.github.com"}


def normalize_phone(value):
    phone = PHONE_SEPARATORS.sub("", value)
    if not PHONE_PATTERN.fullmatch(phone):
        raise ValidationError(
            "Номер телефона должен быть в формате 8XXXXXXXXXX или +7XXXXXXXXXX."
        )
    return f"+7{phone[-PHONE_NATIONAL_NUMBER_LENGTH:]}"


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

    def _min_length_text(self):
        symbols = _plural_ru(self.min_length, "символ", "символа", "символов")
        return f"{self.min_length} {symbols}"

    def get_error_message(self):
        return f"Пароль слишком короткий: нужно не меньше {self._min_length_text()}."

    def get_help_text(self):
        return f"Пароль должен содержать не меньше {self._min_length_text()}."
