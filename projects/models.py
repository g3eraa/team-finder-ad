from django.conf import settings
from django.db import models


class Project(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Открыт"
        CLOSED = "closed", "Закрыт"

    name = models.CharField("название проекта", max_length=200)
    description = models.TextField("описание проекта", blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_projects",
        verbose_name="автор",
    )
    created_at = models.DateTimeField("дата создания", auto_now_add=True)
    github_url = models.URLField("ссылка на GitHub", blank=True)
    status = models.CharField(
        "статус", max_length=6, choices=Status.choices, default=Status.OPEN
    )
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="participated_projects",
        blank=True,
        verbose_name="участники",
    )

    class Meta:
        ordering = ("-created_at", "-id")
        verbose_name = "проект"
        verbose_name_plural = "проекты"

    def __str__(self):
        return self.name
