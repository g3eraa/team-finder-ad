from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.db.models.functions import Lower

from .avatars import generate_avatar


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Не указан email.")
        user = self.model(email=self.normalize_email(email).lower(), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if not (extra_fields["is_staff"] and extra_fields["is_superuser"]):
            raise ValueError("У суперпользователя должны быть is_staff=True и is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


class Skill(models.Model):
    name = models.CharField("название", max_length=124)

    class Meta:
        ordering = (Lower("name"),)
        verbose_name = "навык"
        verbose_name_plural = "навыки"
        constraints = (
            models.UniqueConstraint(
                Lower("name"),
                name="unique_skill_name_ci",
                violation_error_message="Такой навык уже существует.",
            ),
        )

    def __str__(self):
        return self.name


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField("email", unique=True)
    name = models.CharField("имя", max_length=124)
    surname = models.CharField("фамилия", max_length=124)
    avatar = models.ImageField("аватар", upload_to="avatars/")
    phone = models.CharField("телефон", max_length=12, unique=True, null=True, blank=True)
    github_url = models.URLField("ссылка на GitHub", blank=True)
    about = models.TextField("о себе", max_length=256, blank=True)
    skills = models.ManyToManyField(
        Skill, related_name="users", blank=True, verbose_name="навыки"
    )
    is_active = models.BooleanField("активен", default=True)
    is_staff = models.BooleanField("администратор", default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["name", "surname"]

    class Meta:
        verbose_name = "пользователь"
        verbose_name_plural = "пользователи"

    def __str__(self):
        return f"{self.name} {self.surname}"

    def save(self, *args, **kwargs):
        if not self.avatar:
            self.avatar = generate_avatar(self.name)
        super().save(*args, **kwargs)
