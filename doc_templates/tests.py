from types import SimpleNamespace

from django.test import TestCase

from notes.models import Note
from notes.pdf import note_html
from notes.tests import doc, make_user, weasyprint_available

from .builtin import BUILTIN, sync
from .models import Template


class TemplateApiTests(TestCase):
    def setUp(self):
        self.user, self.client = make_user("ann")

    def builtin(self, slug):
        return Template.objects.get(slug=slug)

    def test_builtins_are_seeded_and_listed(self):
        res = self.client.get("/notes/api/templates/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), len(BUILTIN))
        self.assertNotIn("content", res.data[0])
        detail = self.client.get(f"/notes/api/templates/{res.data[0]['id']}/").data
        self.assertEqual(detail["content"]["type"], "doc")
        self.assertIn("margins", detail["page_settings"])

    def test_use_free_template_creates_note(self):
        template = self.builtin("meeting-notes")
        res = self.client.post(f"/notes/api/templates/{template.id}/use/")
        self.assertEqual(res.status_code, 201)
        note = Note.objects.get(pk=res.data["id"])
        self.assertEqual(note.owner, self.user)
        self.assertEqual(note.title, "Meeting notes")
        self.assertIn("Action items", note.search_text)
        self.assertTrue(note.page_settings["show_title"])

    def test_premium_templates_are_free_for_everyone(self):
        template = self.builtin("gst-invoice")
        self.assertTrue(template.premium)
        self.assertEqual(self.client.post(f"/notes/api/templates/{template.id}/use/").status_code, 201)

    def test_hidden_template_is_not_available(self):
        template = self.builtin("todo-list")
        template.is_active = False
        template.save()
        self.assertEqual(self.client.post(f"/notes/api/templates/{template.id}/use/").status_code, 404)

    def test_saved_templates_are_unlimited_and_private(self):
        note_id = self.client.post("/notes/api/notes/", {"title": "My format", "content": doc("hello")}, format="json").data["id"]
        for i in range(3):
            res = self.client.post("/notes/api/templates/", {"note": note_id, "name": f"Mine {i}"}, format="json")
            self.assertEqual(res.status_code, 201)
            self.assertFalse(res.data["builtin"])

        mine = Template.objects.filter(owner=self.user).first()
        _, other = make_user("eve")
        other_ids = [t["id"] for t in other.get("/notes/api/templates/").data]
        self.assertNotIn(str(mine.id), other_ids)
        self.assertEqual(other.post(f"/notes/api/templates/{mine.id}/use/").status_code, 404)
        self.assertEqual(other.delete(f"/notes/api/templates/{mine.id}/").status_code, 404)
        self.assertEqual(other.post("/notes/api/templates/", {"note": note_id, "name": "x"}, format="json").status_code, 400)

        res = self.client.post(f"/notes/api/templates/{mine.id}/use/")
        self.assertEqual(res.data["title"], "My format")
        self.assertEqual(self.client.delete(f"/notes/api/templates/{mine.id}/").status_code, 204)

    def test_builtins_cannot_be_deleted(self):
        template = self.builtin("todo-list")
        self.assertEqual(self.client.delete(f"/notes/api/templates/{template.id}/").status_code, 404)

    def test_sync_keeps_admin_edits_unless_forced(self):
        template = self.builtin("todo-list")
        template.name = "Edited"
        template.save()
        self.assertEqual(sync(Template), (0, 0))
        self.assertEqual(self.builtin("todo-list").name, "Edited")
        sync(Template, force=True)
        self.assertEqual(self.builtin("todo-list").name, "To-do list")


class BuiltinRenderTests(TestCase):
    def test_every_builtin_renders(self):
        for template in Template.objects.filter(slug__isnull=False):
            note = SimpleNamespace(title=template.note_title, content=template.content, page_settings=template.page_settings)
            html = note_html(note, set())
            body = html.split("<body>", 1)[1]
            self.assertGreater(len(body), 300, template.slug)
            self.assertGreater(len(template.preview), 10, template.slug)

    def test_every_builtin_makes_a_pdf(self):
        if not weasyprint_available():
            self.skipTest("WeasyPrint system libraries are not installed")
        from notes.pdf import build_pdf

        user, _ = make_user("pdf")
        for template in Template.objects.filter(slug__isnull=False):
            note = Note(owner=user, title=template.note_title, content=template.content, page_settings=template.page_settings)
            self.assertTrue(build_pdf([note], user).startswith(b"%PDF"), template.slug)
