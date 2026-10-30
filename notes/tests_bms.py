"""The Notes app inside the BMS: who can open it, privacy, and links to projects/clients/leads."""
import shutil
import tempfile
from pathlib import Path

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from core.models import Client, Project
from crm.models import Lead
from employees.models import Employee

from .models import Asset, Note
from .tests import doc, make_user, png_file

TEMP_MEDIA = tempfile.mkdtemp()


def make_intern(username="intern1"):
    user, client = make_user(username)
    Employee.objects.create(
        user=user, employee_id=f"EMP-{username}", employment_type="intern", role="intern", status="active")
    return user, client


class AccessTests(TestCase):
    def test_signed_out_api_gets_noetsa_error_shape(self):
        res = APIClient().get("/notes/api/notes/")
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.json()["code"], "not_authenticated")

    def test_me_returns_bms_user_or_null(self):
        self.assertEqual(APIClient().get("/notes/api/auth/me/").json(), {"user": None})
        user, client = make_user("ann", first_name="Ann", last_name="Mary")
        data = client.get("/notes/api/auth/me/").json()
        self.assertEqual(data["user"]["full_name"], "Ann Mary")
        self.assertEqual(data["home_url"], "/")
        self.assertEqual(data["logout_url"], "/logout/")

    def test_validation_errors_carry_fields(self):
        _, client = make_user("ann")
        res = client.post("/notes/api/notes/", {"kind": "poem"}, format="json")
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], "invalid")
        self.assertIn("kind", res.json()["fields"])

    def test_list_is_limit_offset_paginated(self):
        _, client = make_user("ann")
        for i in range(3):
            client.post("/notes/api/notes/", {"title": f"n{i}"}, format="json")
        data = client.get("/notes/api/notes/?limit=2&offset=0").json()
        self.assertEqual(data["count"], 3)
        self.assertEqual(len(data["results"]), 2)
        self.assertIsNotNone(data["next"])

    def test_spa_requires_login(self):
        res = self.client.get("/notes/n/abc")
        self.assertEqual(res.status_code, 302)
        self.assertTrue(res["Location"].startswith("/login/?next=/notes/n/abc"))

    def test_spa_serves_the_built_index_for_every_route(self):
        dist = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, dist, True)
        (dist / "index.html").write_text("<div id=root></div>")
        make_user("ann")
        self.client.login(username="ann", password="pw-long-enough-1")
        with self.settings(NOTES_FRONTEND_DIST=dist):
            for path in ["/notes/", "/notes/docs", "/notes/n/123", "/notes/templates"]:
                res = self.client.get(path)
                self.assertEqual(res.status_code, 200, path)
                self.assertContains(res, "<div id=root>")
        self.assertIn("csrftoken", res.cookies)
        # Unknown API paths are a 404, not the app shell.
        self.assertEqual(self.client.get("/notes/api/nope/").status_code, 404)

    def test_intern_can_use_notes(self):
        _, client = make_intern()
        self.assertTrue(client.get("/notes/").status_code in (200, 503))  # 503 only when the app isn't built
        self.assertEqual(client.post("/notes/api/notes/", {"title": "Mine"}, format="json").status_code, 201)
        # The rest of the business side stays closed to them.
        self.assertRedirects(client.get("/clients/"), "/staff/", fetch_redirect_response=False)

    def test_client_portal_login_is_kept_out(self):
        user, client = make_user("buyer")
        Client.objects.create(name="Buyer", email="b@example.com", user=user)
        self.assertEqual(client.get("/notes/api/notes/").status_code, 403)
        res = client.get("/notes/")
        self.assertEqual(res.status_code, 302)
        self.assertTrue(res["Location"].startswith("/portal/"))
        self.assertEqual(client.get("/notes/api/auth/me/").status_code, 403)


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class PrivacyTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)

    def test_even_superusers_only_see_their_own_notes(self):
        _, ann = make_user("ann")
        note_id = ann.post("/notes/api/notes/", {"title": "Ann's"}, format="json").data["id"]
        _, boss = make_user("boss", is_staff=True, is_superuser=True)
        self.assertEqual(boss.get(f"/notes/api/notes/{note_id}/").status_code, 404)
        self.assertEqual(boss.get("/notes/api/notes/").data["count"], 0)
        _, intern = make_intern()
        self.assertEqual(intern.get(f"/notes/api/notes/{note_id}/").status_code, 404)

    def test_assets_are_stored_outside_public_media(self):
        _, ann = make_user("ann")
        url = ann.post("/notes/api/assets/", {"file": png_file()}, format="multipart").data["url"]
        self.assertTrue(url.startswith("/notes/api/assets/"))
        asset = Asset.objects.get()
        self.assertTrue(asset.file.name.startswith("private/notes/"))
        # config.urls refuses media/private/, so the file is only reachable through the API.
        self.assertEqual(ann.get(f"/media/{asset.file.name}").status_code, 404)


class LinkTests(TestCase):
    def setUp(self):
        self.owner, self.api = make_user("boss", is_staff=True)
        self.client.force_login(self.owner)
        self.biz = Client.objects.create(name="Asha", company_name="Perfect Institutions", email="a@example.com")
        self.project = Project.objects.create(client=self.biz, name="Fee Management")

    def test_note_links_to_a_project_and_shows_the_chip(self):
        res = self.api.post("/notes/api/notes/", {"title": "Kickoff", "link": {"kind": "project", "id": str(self.project.pk)}}, format="json")
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data["link"], {
            "kind": "project", "id": str(self.project.pk), "label": "Fee Management",
            "url": f"/projects/{self.project.pk}/",
        })
        note_id = res.data["id"]
        res = self.api.patch(f"/notes/api/notes/{note_id}/", {"link": {"kind": "client", "id": str(self.biz.pk)}}, format="json")
        self.assertEqual(res.data["link"]["label"], "Perfect Institutions")
        note = Note.objects.get(pk=note_id)
        self.assertIsNone(note.project_id)  # one link at a time
        res = self.api.patch(f"/notes/api/notes/{note_id}/", {"link": None}, format="json")
        self.assertIsNone(res.data["link"])

    def test_unknown_record_is_rejected(self):
        res = self.api.post("/notes/api/notes/", {"link": {"kind": "project", "id": "not-a-uuid"}}, format="json")
        self.assertEqual(res.status_code, 400)
        self.assertIn("link", res.json()["fields"])

    def test_new_note_button_on_project_page(self):
        page = self.client.get(f"/projects/{self.project.pk}/")
        self.assertContains(page, 'action="/notes/new/"')
        self.assertContains(page, "My Notes")
        res = self.client.post("/notes/new/", {"kind": "project", "id": str(self.project.pk)})
        note = Note.objects.get()
        self.assertRedirects(res, f"/notes/n/{note.pk}", fetch_redirect_response=False)
        self.assertEqual((note.owner, note.project, note.kind), (self.owner, self.project, "doc"))
        note.title = "Scope call"
        note.save()
        self.assertContains(self.client.get(f"/projects/{self.project.pk}/"), "Scope call")

    def test_card_lists_only_the_viewers_notes(self):
        other, _ = make_user("partner", is_staff=True)
        Note.objects.create(owner=other, title="Partner secret", project=self.project)
        Note.objects.create(owner=self.owner, title="Mine on it", project=self.project)
        page = self.client.get(f"/projects/{self.project.pk}/")
        self.assertContains(page, "Mine on it")
        self.assertNotContains(page, "Partner secret")

    def test_client_and_lead_pages_have_the_card(self):
        self.assertContains(self.client.get(f"/clients/{self.biz.pk}/"), 'name="kind" value="client"')
        lead = Lead.objects.create(contact_person="Ravi", phone="9999999999", created_by=self.owner)
        self.assertContains(self.client.get(f"/crm/leads/{lead.pk}/"), 'name="kind" value="lead"')
        self.client.post("/notes/new/", {"kind": "lead", "id": lead.pk})
        self.assertEqual(Note.objects.get().lead, lead)

    def test_intern_links_only_their_own_leads(self):
        intern, intern_api = make_intern()
        mine = Lead.objects.create(contact_person="Mine", phone="1", assigned_to=intern, created_by=self.owner)
        theirs = Lead.objects.create(contact_person="Theirs", phone="2", created_by=self.owner)
        ok = intern_api.post("/notes/api/notes/", {"link": {"kind": "lead", "id": mine.pk}}, format="json")
        self.assertEqual(ok.status_code, 201)
        for kind, pk in [("lead", theirs.pk), ("project", str(self.project.pk)), ("client", str(self.biz.pk))]:
            res = intern_api.post("/notes/api/notes/", {"link": {"kind": kind, "id": pk}}, format="json")
            self.assertEqual(res.status_code, 400, kind)
        res = intern_api.post("/notes/new/", {"kind": "project", "id": str(self.project.pk)})
        self.assertEqual(res.status_code, 302)
        self.assertEqual(Note.objects.filter(owner=intern).count(), 1)


class DashboardTests(TestCase):
    def setUp(self):
        self.owner, _ = make_user("chief", is_staff=True, is_superuser=True)
        self.client.force_login(self.owner)

    def test_dashboard_lists_only_my_notes(self):
        other, _ = make_user("partner", is_staff=True)
        Note.objects.create(owner=self.owner, title="Roadmap ideas")
        Note.objects.create(owner=other, title="Their secret")
        page = self.client.get("/")
        self.assertContains(page, "My Notes")
        self.assertContains(page, "Roadmap ideas")
        self.assertNotContains(page, "Their secret")

    def test_new_note_and_board_from_dashboard(self):
        res = self.client.post("/notes/new/")
        note = Note.objects.get()
        self.assertRedirects(res, f"/notes/n/{note.pk}", fetch_redirect_response=False)
        self.assertEqual((note.owner, note.kind, note.project, note.client, note.lead), (self.owner, "doc", None, None, None))
        self.client.post("/notes/new/", {"note_kind": "board"})
        self.assertEqual(Note.objects.filter(kind="board", owner=self.owner).count(), 1)
