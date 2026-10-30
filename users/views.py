import json
from http import HTTPStatus
from urllib.parse import urlencode

from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.core.paginator import Paginator
from django.db.models.functions import Lower
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from team_finder.constants import DEFAULT_PAGE_NUMBER

from .constants import SKILL_NAME_MAX_LENGTH, SKILL_SUGGESTIONS_LIMIT, USERS_PER_PAGE
from .forms import EditProfileForm, LoginForm, RegisterForm
from .models import Skill, User


def _json_error(message, status):
    return JsonResponse({"status": "error", "message": message}, status=status)


def _check_profile_owner(request, user_id):
    if not request.user.is_authenticated:
        return _json_error("Нужно войти в аккаунт.", HTTPStatus.UNAUTHORIZED)
    if request.user.pk != user_id:
        return _json_error("Можно изменять только свои навыки.", HTTPStatus.FORBIDDEN)
    return None


def _get_skill_by_id(value):
    try:
        skill_id = int(value)
    except (TypeError, ValueError):
        return None, False, _json_error("Некорректный skill_id.", HTTPStatus.BAD_REQUEST)
    skill = Skill.objects.filter(pk=skill_id).first()
    if skill is None:
        return None, False, _json_error("Навык не найден.", HTTPStatus.NOT_FOUND)
    return skill, False, None


def _resolve_skill(payload):
    if payload.get("skill_id") is not None:
        return _get_skill_by_id(payload["skill_id"])

    name = str(payload.get("name") or "").strip()
    if not name or len(name) > SKILL_NAME_MAX_LENGTH:
        message = f"Название навыка должно быть от 1 до {SKILL_NAME_MAX_LENGTH} символов."
        return None, False, _json_error(message, HTTPStatus.BAD_REQUEST)
    skill, created = Skill.objects.get_or_create(name__iexact=name, defaults={"name": name})
    return skill, created, None


def register(request):
    form = RegisterForm(request.POST if request.method == "POST" else None)
    if request.method != "POST" or not form.is_valid():
        return render(request, "users/register.html", {"form": form})
    form.save()
    return redirect("users:login")


def login_view(request):
    form = LoginForm(request, data=request.POST if request.method == "POST" else None)
    if request.method != "POST" or not form.is_valid():
        return render(request, "users/login.html", {"form": form})
    login(request, form.get_user())
    next_url = request.GET.get("next", "")
    if next_url and url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return redirect(next_url)
    return redirect("projects:list")


def logout_view(request):
    logout(request)
    return redirect("projects:list")


def user_list(request):
    users = User.objects.filter(is_active=True).order_by("-id")
    active_skill = request.GET.get("skill", "").strip()
    if active_skill:
        users = users.filter(skills__name=active_skill)
    page_obj = Paginator(users, USERS_PER_PAGE).get_page(
        request.GET.get("page", DEFAULT_PAGE_NUMBER)
    )
    context = {
        "participants": page_obj.object_list,
        "page_obj": page_obj,
        "all_skills": Skill.objects.values_list("name", flat=True),
        "active_skill": active_skill,
        "query_prefix": f"{urlencode({'skill': active_skill})}&" if active_skill else "",
    }
    return render(request, "users/participants.html", context)


@ensure_csrf_cookie
def user_detail(request, user_id):
    profile = get_object_or_404(
        User.objects.prefetch_related("skills", "owned_projects__participants"),
        pk=user_id,
    )
    return render(request, "users/user-details.html", {
        "user": profile,
        "skill_name_max_length": SKILL_NAME_MAX_LENGTH,
    })


@login_required
def edit_profile(request):
    profile = get_object_or_404(User, pk=request.user.pk)
    form = EditProfileForm(
        request.POST if request.method == "POST" else None,
        request.FILES if request.method == "POST" else None,
        instance=profile,
    )
    if request.method != "POST" or not form.is_valid():
        return render(request, "users/edit_profile.html", {"form": form})
    form.save()
    return redirect("users:detail", user_id=profile.pk)


@login_required
def change_password(request):
    form = PasswordChangeForm(
        request.user, request.POST if request.method == "POST" else None
    )
    if request.method != "POST" or not form.is_valid():
        return render(request, "users/change_password.html", {"form": form})
    user = form.save()
    update_session_auth_hash(request, user)
    return redirect("users:detail", user_id=user.pk)


@require_GET
def skill_search(request):
    query = request.GET.get("q", "").strip()
    if not query:
        return JsonResponse([], safe=False)
    skills = (
        Skill.objects.filter(name__istartswith=query)
        .order_by(Lower("name"))
        .values("id", "name")[:SKILL_SUGGESTIONS_LIMIT]
    )
    return JsonResponse(list(skills), safe=False)


@require_POST
def skill_add(request, user_id):
    error = _check_profile_owner(request, user_id)
    if error:
        return error
    try:
        payload = json.loads(request.body or b"{}")
    except ValueError:
        return _json_error("Некорректный JSON.", HTTPStatus.BAD_REQUEST)
    if not isinstance(payload, dict):
        return _json_error("Некорректный JSON.", HTTPStatus.BAD_REQUEST)

    skill, created, error = _resolve_skill(payload)
    if error:
        return error
    added = not request.user.skills.filter(pk=skill.pk).exists()
    if added:
        request.user.skills.add(skill)
    return JsonResponse({
        "id": skill.pk,
        "name": skill.name,
        "skill_id": skill.pk,
        "created": created,
        "added": added,
    })


@require_POST
def skill_remove(request, user_id, skill_id):
    error = _check_profile_owner(request, user_id)
    if error:
        return error
    skill = request.user.skills.filter(pk=skill_id).first()
    if skill is None:
        return _json_error("Такого навыка нет в профиле.", HTTPStatus.NOT_FOUND)
    request.user.skills.remove(skill)
    return JsonResponse({"status": "ok"})
