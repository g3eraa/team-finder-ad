import json
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

from .forms import EditProfileForm, LoginForm, RegisterForm
from .models import Skill, User

USERS_PER_PAGE = 12
SKILL_SUGGESTIONS_LIMIT = 10
SKILL_NAME_MAX_LENGTH = Skill._meta.get_field("name").max_length


def _json_error(message, status):
    return JsonResponse({"status": "error", "message": message}, status=status)


def _check_profile_owner(request, user_id):
    """Возвращает JSON-ошибку, если навыки пытается менять не владелец профиля."""
    if not request.user.is_authenticated:
        return _json_error("Нужно войти в аккаунт.", 401)
    if request.user.pk != user_id:
        return _json_error("Можно изменять только свои навыки.", 403)
    return None


def _resolve_skill(payload):
    """Находит навык по skill_id или находит/создаёт по name.

    Возвращает кортеж (skill, created, error_response).
    """
    if payload.get("skill_id") is not None:
        try:
            skill_id = int(payload["skill_id"])
        except (TypeError, ValueError):
            return None, False, _json_error("Некорректный skill_id.", 400)
        skill = Skill.objects.filter(pk=skill_id).first()
        if skill is None:
            return None, False, _json_error("Навык не найден.", 404)
        return skill, False, None

    name = str(payload.get("name") or "").strip()
    if not name or len(name) > SKILL_NAME_MAX_LENGTH:
        message = f"Название навыка должно быть от 1 до {SKILL_NAME_MAX_LENGTH} символов."
        return None, False, _json_error(message, 400)
    skill, created = Skill.objects.get_or_create(name__iexact=name, defaults={"name": name})
    return skill, created, None


def register(request):
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("users:login")
    return render(request, "users/register.html", {"form": form})


def login_view(request):
    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        next_url = request.GET.get("next")
        if next_url and url_has_allowed_host_and_scheme(
            next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
        ):
            return redirect(next_url)
        return redirect("projects:list")
    return render(request, "users/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("projects:list")


def user_list(request):
    users = User.objects.filter(is_active=True).order_by("-id")
    active_skill = request.GET.get("skill", "").strip()
    if active_skill:
        users = users.filter(skills__name=active_skill)
    page_obj = Paginator(users, USERS_PER_PAGE).get_page(request.GET.get("page"))
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
    # Шаблон ждёт просматриваемый профиль под именем user.
    return render(request, "users/user-details.html", {"user": profile})


@login_required
def edit_profile(request):
    # Отдельный экземпляр, чтобы невалидные данные не попали в request.user в шапке.
    profile = get_object_or_404(User, pk=request.user.pk)
    form = EditProfileForm(request.POST or None, request.FILES or None, instance=profile)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("users:detail", user_id=profile.pk)
    return render(request, "users/edit_profile.html", {"form": form})


@login_required
def change_password(request):
    form = PasswordChangeForm(request.user, request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        return redirect("users:detail", user_id=user.pk)
    return render(request, "users/change_password.html", {"form": form})


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
        return _json_error("Некорректный JSON.", 400)
    if not isinstance(payload, dict):
        return _json_error("Некорректный JSON.", 400)

    skill, created, error = _resolve_skill(payload)
    if error:
        return error
    added = not request.user.skills.filter(pk=skill.pk).exists()
    if added:
        request.user.skills.add(skill)
    # id и name нужны skills.js, остальные поля описаны в рекомендациях к заданию.
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
        return _json_error("Такого навыка нет в профиле.", 404)
    request.user.skills.remove(skill)
    return JsonResponse({"status": "ok"})
