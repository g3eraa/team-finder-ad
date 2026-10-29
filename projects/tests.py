import json
import shutil
import tempfile

from django.test import Client, TestCase, override_settings

from users.models import User

from .models import Project

TEMP_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(
    MEDIA_ROOT=TEMP_MEDIA_ROOT,
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
)
class ProjectTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.alice = User.objects.create_user(
            email="alice@example.com", password="Team-Finder-2026",
            name="Алиса", surname="Смирнова",
        )
        self.bob = User.objects.create_user(
            email="bob@example.com", password="Team-Finder-2026",
            name="Боб", surname="Иванов",
        )
        self.client_alice = Client()
        self.client_alice.force_login(self.alice)
        self.client_bob = Client()
        self.client_bob.force_login(self.bob)

    def post_json(self, client, url):
        return client.post(url, data=json.dumps({}), content_type="application/json")

    def test_list_pagination_and_order(self):
        for i in range(13):
            Project.objects.create(name=f"P{i}", owner=self.alice)
        response = self.client.get("/projects/list/")
        page = response.context["page_obj"]
        self.assertEqual(len(page.object_list), 12)
        self.assertEqual(page.object_list[0].name, "P12")
        self.assertContains(response, f'href="/users/{self.alice.pk}"')
        response = self.client.get("/projects/list/?page=2")
        self.assertEqual(len(response.context["page_obj"].object_list), 1)
        self.assertEqual(self.client.get("/projects/list/?page=999").status_code, 200)

    def test_create_requires_login(self):
        response = self.client.get("/projects/create-project/")
        self.assertRedirects(response, "/users/login/?next=/projects/create-project/")

    def test_create_button_only_for_authenticated(self):
        Project.objects.create(name="P", owner=self.alice)
        self.assertNotContains(self.client.get("/projects/list/"), "+ Создать проект")
        self.assertContains(self.client_alice.get("/projects/list/"), "+ Создать проект")

    def test_create_project(self):
        self.assertContains(self.client_alice.get("/projects/create-project/"), "Опубликовать")
        response = self.client_alice.post(
            "/projects/create-project/", {"name": "", "status": "open"}
        )
        self.assertEqual(response.status_code, 200)
        response = self.client_alice.post("/projects/create-project/", {
            "name": "X", "status": "open", "github_url": "https://gitlab.com/x",
        })
        self.assertContains(response, "GitHub")
        self.assertFalse(Project.objects.exists())
        response = self.client_alice.post("/projects/create-project/", {
            "name": "TeamFinder", "description": "d", "status": "open",
            "github_url": "https://github.com/a/b",
        })
        project = Project.objects.get()
        self.assertRedirects(response, f"/projects/{project.pk}/")
        self.assertEqual(project.owner, self.alice)
        self.assertEqual(list(project.participants.all()), [self.alice])

    def test_edit_project(self):
        project = Project.objects.create(name="Old", owner=self.alice)
        url = f"/projects/{project.pk}/edit/"
        self.assertContains(
            self.client_bob.get(url), "Редактировать проект может только его автор.",
            status_code=403,
        )
        response = self.client_alice.get(url)
        self.assertContains(response, 'value="Old"')
        self.assertContains(response, "Сохранить")
        response = self.client_alice.post(url, {"name": "New", "status": "closed"})
        self.assertRedirects(response, f"/projects/{project.pk}/")
        project.refresh_from_db()
        self.assertEqual((project.name, project.status), ("New", "closed"))

    def test_detail_buttons_by_role(self):
        project = Project.objects.create(name="Pr", owner=self.alice)
        project.participants.add(self.alice)
        url = f"/projects/{project.pk}/"
        response = self.client_alice.get(url)
        self.assertContains(response, "complete-project-btn")
        self.assertNotContains(response, "participate-btn")
        response = self.client_bob.get(url)
        self.assertContains(response, "participate-btn")
        self.assertContains(response, "Участвовать")
        response = self.client.get(url)
        self.assertNotContains(response, "participate-btn")
        self.assertContains(response, "Автор проекта")
        self.assertContains(response, f'href="/users/login/?next=/projects/{project.pk}/"')
        self.assertEqual(self.client.get("/projects/999/").status_code, 404)

    def test_complete_project(self):
        project = Project.objects.create(name="Pr", owner=self.alice)
        url = f"/projects/{project.pk}/complete/"
        self.assertEqual(self.post_json(self.client, url).status_code, 401)
        self.assertEqual(self.post_json(self.client_bob, url).status_code, 403)
        self.assertEqual(
            self.post_json(self.client_alice, url).json(),
            {"status": "ok", "project_status": "closed"},
        )
        self.assertEqual(self.post_json(self.client_alice, url).status_code, 400)
        self.assertEqual(self.client_alice.get(url).status_code, 405)

    def test_toggle_participate(self):
        project = Project.objects.create(name="Pr", owner=self.alice)
        project.participants.add(self.alice)
        url = f"/projects/{project.pk}/toggle-participate/"
        self.assertEqual(self.post_json(self.client, url).status_code, 401)
        self.assertEqual(
            self.post_json(self.client_bob, url).json(), {"status": "ok", "participant": True}
        )
        self.assertIn(self.bob, project.participants.all())
        self.assertContains(
            self.client_bob.get(f"/projects/{project.pk}/"), "Отказаться от участия"
        )
        self.assertFalse(self.post_json(self.client_bob, url).json()["participant"])
        self.assertEqual(self.post_json(self.client_alice, url).status_code, 400)
