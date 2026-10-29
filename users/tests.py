import json
import shutil
import tempfile
from io import BytesIO

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from PIL import Image

from projects.models import Project

from .models import Skill, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp()
PASSWORD = "Team-Finder-2026"
TEST_DATA_PASSWORD = "testpass123"


def make_user(email, name="Иван", surname="Петров", **extra):
    return User.objects.create_user(
        email=email, password=PASSWORD, name=name, surname=surname, **extra
    )


@override_settings(
    MEDIA_ROOT=TEMP_MEDIA_ROOT,
    PASSWORD_HASHERS=[
        "django.contrib.auth.hashers.MD5PasswordHasher",
        "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    ],
)
class BaseTestCase(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.alice = make_user("alice@example.com", "Алиса", "Смирнова")
        self.bob = make_user("bob@example.com", "Боб", "Иванов")
        self.client_alice = Client()
        self.client_alice.force_login(self.alice)
        self.client_bob = Client()
        self.client_bob.force_login(self.bob)

    def post_json(self, client, url, data=None):
        return client.post(url, data=json.dumps(data or {}), content_type="application/json")


class AuthTests(BaseTestCase):
    def test_root_redirects_to_projects(self):
        self.assertRedirects(self.client.get("/"), "/projects/list/")

    def test_register_creates_user_with_avatar(self):
        self.assertEqual(self.client.get("/users/register/").status_code, 200)
        response = self.client.post("/users/register/", {
            "name": "Егор", "surname": "Тестов", "email": "Egor@Example.COM",
            "password": PASSWORD,
        })
        self.assertRedirects(response, "/users/login/")
        user = User.objects.get(email="egor@example.com")
        self.assertTrue(user.check_password(PASSWORD))
        self.assertTrue(user.avatar.name.startswith("avatars/avatar_"))
        with Image.open(user.avatar.path) as image:
            self.assertEqual(image.size, (256, 256))

    @override_settings(AUTH_PASSWORD_VALIDATORS=[
        {"NAME": "users.validators.MinimumLengthValidator"},
    ])
    def test_register_password_errors_in_russian_next_to_field(self):
        response = self.client.get("/users/register/")
        self.assertContains(response, "Пароль должен содержать не меньше 8 символов.")
        response = self.client.post("/users/register/", {
            "name": "Егор", "surname": "Тестов", "email": "egor@example.com",
            "password": "short",
        })
        self.assertContains(response, "Пароль слишком короткий: нужно не меньше 8 символов.")
        self.assertContains(response, 'aria-describedby="id_password_helptext id_password_error"')
        self.assertContains(response, '<ul class="errorlist" id="id_password_error">')
        self.assertFalse(User.objects.filter(email="egor@example.com").exists())

    def test_register_rejects_duplicate_and_empty_fields(self):
        response = self.client.post("/users/register/", {
            "name": "Алиса", "surname": "Смирнова", "email": "ALICE@example.com",
            "password": PASSWORD,
        })
        self.assertContains(response, "уже существует")
        response = self.client.post("/users/register/", {"name": "", "email": "bad"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), 2)

    def test_login_and_logout(self):
        response = self.client.post(
            "/users/login/", {"email": "alice@example.com", "password": "wrong"}
        )
        self.assertContains(response, "Неверный email или пароль")
        response = self.client.post(
            "/users/login/", {"email": "ALICE@example.com", "password": PASSWORD}
        )
        self.assertRedirects(response, "/projects/list/")
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.alice.pk)
        self.assertRedirects(self.client.get("/users/logout/"), "/projects/list/")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_login_follows_only_safe_next(self):
        response = self.client.post(
            "/users/login/?next=/projects/create-project/",
            {"email": "alice@example.com", "password": PASSWORD},
        )
        self.assertRedirects(response, "/projects/create-project/")
        response = Client().post(
            "/users/login/?next=https://evil.com/",
            {"email": "alice@example.com", "password": PASSWORD},
        )
        self.assertRedirects(response, "/projects/list/")

    def test_blocked_user_cannot_login(self):
        make_user("blocked@example.com", is_active=False)
        response = self.client.post(
            "/users/login/", {"email": "blocked@example.com", "password": PASSWORD}
        )
        self.assertContains(response, "Неверный email или пароль")

    def test_change_password_keeps_session(self):
        response = self.client.get("/users/change-password/")
        self.assertRedirects(response, "/users/login/?next=/users/change-password/")
        response = self.client_alice.post("/users/change-password/", {
            "old_password": "wrong", "new_password1": "n1", "new_password2": "n1",
        })
        self.assertEqual(response.status_code, 200)
        new_password = "Another-Strong-2026"
        response = self.client_alice.post("/users/change-password/", {
            "old_password": PASSWORD,
            "new_password1": new_password,
            "new_password2": new_password,
        })
        self.assertRedirects(response, f"/users/{self.alice.pk}/")
        self.alice.refresh_from_db()
        self.assertTrue(self.alice.check_password(new_password))
        self.assertEqual(self.client_alice.get("/users/edit-profile/").status_code, 200)


class LayoutTests(BaseTestCase):
    def test_guest_has_no_user_menu(self):
        response = self.client.get("/projects/list/")
        self.assertNotContains(response, 'id="userSidebar"')
        self.assertNotContains(response, "/users/None/")
        self.assertContains(response, 'name="viewport"')

    def test_user_menu_is_a_button(self):
        response = self.client_alice.get("/projects/list/")
        self.assertContains(response, 'id="userSidebar"')
        self.assertContains(response, 'aria-controls="userSidebar"')

    def test_not_found_page(self):
        response = self.client.get("/users/999/")
        self.assertContains(response, "Страница не найдена", status_code=404)


class ProfileTests(BaseTestCase):
    def test_profile_page(self):
        Project.objects.create(name="AliceProj", owner=self.alice)
        self.alice.skills.add(Skill.objects.create(name="Python"))
        response = self.client.get(f"/users/{self.alice.pk}/")
        self.assertContains(response, "Алиса Смирнова")
        self.assertContains(response, "AliceProj")
        self.assertContains(response, "Python")
        self.assertNotContains(response, "add-skill-btn")
        response = self.client_alice.get(f"/users/{self.alice.pk}/")
        self.assertContains(response, "add-skill-btn")
        self.assertContains(response, "remove-skill-btn")
        self.assertContains(response, "Добавить проект")
        response = self.client_bob.get(f"/users/{self.alice.pk}/")
        self.assertNotContains(response, "add-skill-btn")
        self.assertContains(response, "Боб Иванов")
        self.assertEqual(self.client.get("/users/999/").status_code, 404)

    def test_edit_profile(self):
        self.assertEqual(self.client.get("/users/edit-profile/").status_code, 302)
        buffer = BytesIO()
        Image.new("RGB", (10, 10), "red").save(buffer, "PNG")
        avatar = SimpleUploadedFile("a.png", buffer.getvalue(), content_type="image/png")
        response = self.client_alice.post("/users/edit-profile/", {
            "name": "Алиса", "surname": "Новая", "about": "hi",
            "phone": "8 (999) 123-45-67", "github_url": "https://github.com/alice",
            "avatar": avatar,
        })
        self.assertRedirects(response, f"/users/{self.alice.pk}/")
        self.alice.refresh_from_db()
        self.assertEqual(self.alice.phone, "+79991234567")
        self.assertEqual(self.alice.surname, "Новая")
        self.assertTrue(self.alice.avatar.name.startswith("avatars/a"))

    def test_edit_profile_validation(self):
        self.alice.phone = "+79991234567"
        self.alice.save()
        profile = {"name": "Боб", "surname": "Иванов"}
        response = self.client_bob.post(
            "/users/edit-profile/", {**profile, "phone": "89991234567"}
        )
        self.assertContains(response, "уже используется")
        response = self.client_bob.post("/users/edit-profile/", {**profile, "phone": "12345"})
        self.assertContains(response, "8XXXXXXXXXX")
        response = self.client_bob.post(
            "/users/edit-profile/", {**profile, "github_url": "https://notgithub.com/bob"}
        )
        self.assertContains(response, "GitHub")
        response = self.client_bob.post(
            "/users/edit-profile/", {"name": "Хакер", "surname": "Иванов", "phone": "bad"}
        )
        self.assertContains(response, "Боб Иванов")
        response = self.client_bob.post("/users/edit-profile/", {**profile, "phone": ""})
        self.assertEqual(response.status_code, 302)
        self.bob.refresh_from_db()
        self.assertIsNone(self.bob.phone)


class SkillTests(BaseTestCase):
    def test_search(self):
        names = ["Python", "PyTorch", "Postgres", "Go"] + [f"Pz{i}" for i in range(12)]
        Skill.objects.bulk_create(Skill(name=name) for name in names)
        response = self.client.get("/users/skills/?q=py")
        self.assertEqual([skill["name"] for skill in response.json()], ["Python", "PyTorch"])
        self.assertEqual(set(response.json()[0]), {"id", "name"})
        self.assertEqual(len(self.client.get("/users/skills/?q=P").json()), 10)
        self.assertEqual(self.client.get("/users/skills/?q=").json(), [])

    def test_add_skill(self):
        url = f"/users/{self.alice.pk}/skills/add/"
        self.assertEqual(self.post_json(self.client, url, {"name": "Go"}).status_code, 401)
        self.assertEqual(self.post_json(self.client_bob, url, {"name": "Go"}).status_code, 403)
        data = self.post_json(self.client_alice, url, {"name": "Django"}).json()
        self.assertEqual((data["name"], data["created"], data["added"]), ("Django", True, True))
        self.assertEqual(data["id"], data["skill_id"])
        data = self.post_json(self.client_alice, url, {"name": "django"}).json()
        self.assertEqual((data["created"], data["added"]), (False, False))
        go = Skill.objects.create(name="Go")
        data = self.post_json(self.client_alice, url, {"skill_id": str(go.pk)}).json()
        self.assertTrue(data["added"])
        self.assertEqual(Skill.objects.count(), 2)
        self.assertEqual(
            set(self.alice.skills.values_list("name", flat=True)), {"Django", "Go"}
        )

    def test_add_skill_bad_requests(self):
        url = f"/users/{self.alice.pk}/skills/add/"
        response = self.post_json(self.client_alice, url, {"skill_id": 999})
        self.assertEqual(response.status_code, 404)
        response = self.post_json(self.client_alice, url, {"skill_id": "x"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.post_json(self.client_alice, url, {}).status_code, 400)
        response = self.client_alice.post(url, data="{", content_type="application/json")
        self.assertEqual(response.status_code, 400)

    def test_remove_skill(self):
        go = Skill.objects.create(name="Go")
        self.alice.skills.add(go)
        url = f"/users/{self.alice.pk}/skills/{go.pk}/remove/"
        self.assertEqual(self.client_bob.post(url).status_code, 403)
        self.assertEqual(self.client_alice.post(url).json(), {"status": "ok"})
        self.assertEqual(self.client_alice.post(url).status_code, 404)
        self.assertTrue(Skill.objects.filter(pk=go.pk).exists())

    def test_csrf_token_from_profile_page(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.alice)
        token = client.get(f"/users/{self.alice.pk}/").cookies["csrftoken"].value
        url = f"/users/{self.alice.pk}/skills/add/"
        payload = json.dumps({"name": "Rust"})
        response = client.post(url, data=payload, content_type="application/json")
        self.assertEqual(response.status_code, 403)
        response = client.post(
            url, data=payload, content_type="application/json",
            headers={"X-CSRFToken": token},
        )
        self.assertEqual(response.status_code, 200)


class UserListTests(BaseTestCase):
    def test_pagination_and_order(self):
        for i in range(14):
            make_user(f"u{i}@example.com", f"U{i}")
        make_user("blocked@example.com", is_active=False)
        response = self.client.get("/users/list/")
        page = response.context["page_obj"]
        self.assertEqual(len(page.object_list), 12)
        self.assertEqual(page.object_list[0].email, "u13@example.com")
        self.assertEqual(page.paginator.count, 16)

    def test_skill_filter(self):
        python = Skill.objects.create(name="Python")
        cpp = Skill.objects.create(name="C++")
        self.alice.skills.add(python, cpp)
        self.bob.skills.add(python)
        response = self.client.get("/users/list/")
        self.assertEqual(list(response.context["all_skills"]), ["C++", "Python"])
        self.assertContains(response, 'href="?skill=C%2B%2B"')
        response = self.client.get("/users/list/?skill=C%2B%2B")
        self.assertEqual([u.email for u in response.context["page_obj"]], ["alice@example.com"])
        self.assertContains(response, "filter-chip active")
        self.assertContains(response, "Сбросить")
        response = self.client.get("/users/list/?skill=Python")
        self.assertEqual(len(response.context["page_obj"].object_list), 2)
        self.assertEqual(response.context["query_prefix"], "skill=Python&")
        response = self.client.get("/users/list/?skill=Nope")
        self.assertContains(response, "Пока нет участников")


class AdminTests(BaseTestCase):
    def test_admin_pages(self):
        admin = User.objects.create_superuser(
            "admin@example.com", PASSWORD, name="Админ", surname="Сайта"
        )
        client = Client()
        client.force_login(admin)
        project = Project.objects.create(name="Pr", owner=self.alice)
        urls = [
            "/admin/",
            "/admin/users/user/",
            "/admin/users/user/add/",
            f"/admin/users/user/{self.alice.pk}/change/",
            f"/admin/users/user/{self.alice.pk}/password/",
            "/admin/users/skill/",
            f"/admin/projects/project/{project.pk}/change/",
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(client.get(url).status_code, 200)

    def test_admin_creates_user_and_changes_password(self):
        admin = User.objects.create_superuser(
            "admin@example.com", PASSWORD, name="Админ", surname="Сайта"
        )
        client = Client()
        client.force_login(admin)
        new_password = "Another-Strong-2026"
        response = client.post("/admin/users/user/add/", {
            "email": "new@example.com", "name": "N", "surname": "S",
            "password1": new_password, "password2": new_password,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.get(email="new@example.com").avatar)
        response = client.post(f"/admin/users/user/{self.alice.pk}/password/", {
            "password1": new_password, "password2": new_password,
        })
        self.assertEqual(response.status_code, 302)
        self.alice.refresh_from_db()
        self.assertTrue(self.alice.check_password(new_password))


class TestDataFixtureTests(BaseTestCase):
    def test_loaddata_keeps_existing_users(self):
        call_command("loaddata", "test_data", verbosity=0)
        call_command("loaddata", "test_data", verbosity=0)
        self.assertTrue(User.objects.filter(pk=self.alice.pk, email="alice@example.com").exists())
        test_users = User.objects.exclude(pk__in=[self.alice.pk, self.bob.pk])
        self.assertEqual(test_users.count(), 5)
        for user in test_users:
            with self.subTest(email=user.email):
                self.assertTrue(user.owned_projects.exists())
                self.assertTrue(user.skills.exists())
                self.assertTrue(user.check_password(TEST_DATA_PASSWORD))
                self.assertTrue((settings.BASE_DIR / "media" / user.avatar.name).exists())
