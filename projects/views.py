from http import HTTPStatus

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from team_finder.constants import DEFAULT_PAGE_NUMBER

from .constants import PROJECTS_PER_PAGE
from .forms import ProjectForm
from .models import Project

PROJECT_FORM_TEMPLATE = "projects/create-project.html"


def _json_error(message, status):
    return JsonResponse({"status": "error", "message": message}, status=status)


def _get_project_for_ajax(request, project_id):
    if not request.user.is_authenticated:
        return None, _json_error("Нужно войти в аккаунт.", HTTPStatus.UNAUTHORIZED)
    project = Project.objects.filter(pk=project_id).first()
    if project is None:
        return None, _json_error("Проект не найден.", HTTPStatus.NOT_FOUND)
    return project, None


def project_list(request):
    projects = Project.objects.select_related("owner").prefetch_related("participants")
    page_obj = Paginator(projects, PROJECTS_PER_PAGE).get_page(
        request.GET.get("page", DEFAULT_PAGE_NUMBER)
    )
    context = {"projects": page_obj.object_list, "page_obj": page_obj, "query_prefix": ""}
    return render(request, "projects/project_list.html", context)


@ensure_csrf_cookie
def project_detail(request, project_id):
    project = get_object_or_404(
        Project.objects.select_related("owner").prefetch_related("participants"),
        pk=project_id,
    )
    return render(request, "projects/project-details.html", {"project": project})


@login_required
def project_create(request):
    form = ProjectForm(request.POST if request.method == "POST" else None)
    if request.method != "POST" or not form.is_valid():
        return render(request, PROJECT_FORM_TEMPLATE, {"form": form, "is_edit": False})
    project = form.save(commit=False)
    project.owner = request.user
    project.save()
    project.participants.add(request.user)
    return redirect("projects:detail", project_id=project.pk)


@login_required
def project_edit(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if project.owner_id != request.user.pk:
        raise PermissionDenied("Редактировать проект может только его автор.")
    form = ProjectForm(request.POST if request.method == "POST" else None, instance=project)
    if request.method != "POST" or not form.is_valid():
        return render(request, PROJECT_FORM_TEMPLATE, {"form": form, "is_edit": True})
    form.save()
    return redirect("projects:detail", project_id=project.pk)


@require_POST
def project_complete(request, project_id):
    project, error = _get_project_for_ajax(request, project_id)
    if error:
        return error
    if project.owner_id != request.user.pk:
        return _json_error("Завершить проект может только его автор.", HTTPStatus.FORBIDDEN)
    if project.status != Project.Status.OPEN:
        return _json_error("Проект уже завершён.", HTTPStatus.BAD_REQUEST)
    project.status = Project.Status.CLOSED
    project.save(update_fields=["status"])
    return JsonResponse({"status": "ok", "project_status": project.status})


@require_POST
def toggle_participate(request, project_id):
    project, error = _get_project_for_ajax(request, project_id)
    if error:
        return error
    if project.owner_id == request.user.pk:
        return _json_error("Автор не может покинуть свой проект.", HTTPStatus.BAD_REQUEST)
    is_participant = project.participants.filter(pk=request.user.pk).exists()
    if is_participant:
        project.participants.remove(request.user)
        return JsonResponse({"status": "ok", "participant": False})
    project.participants.add(request.user)
    return JsonResponse({"status": "ok", "participant": True})
