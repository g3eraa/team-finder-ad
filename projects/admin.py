from django.contrib import admin

from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "status", "created_at")
    list_filter = ("status",)
    list_select_related = ("owner",)
    search_fields = ("name", "description", "owner__email")
    filter_horizontal = ("participants",)
