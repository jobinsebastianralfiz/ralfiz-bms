import io
import re
import shutil
import tempfile
import zlib
from unittest import skipUnless

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image
from rest_framework.test import APIClient

from .models import Note
from .pages import clean_page_settings
from .pdf import note_html
from .render import referenced_asset_ids, render_doc
from .text import extract_text

User = get_user_model()
TEMP_MEDIA = tempfile.mkdtemp()


def doc(text):
    return {"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": text}]}]}


def png_file(name="pic.png"):
    buf = io.BytesIO()
    Image.new("RGB", (4, 4), "red").save(buf, "PNG")
    return SimpleUploadedFile(name, buf.getvalue(), content_type="image/png")


def make_user(username, **extra):
    user = User.objects.create_user(username, f"{username}@example.com", "pw-long-enough-1", **extra)
    client = APIClient()
    client.force_login(user)
    return user, client


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class NotesApiTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)

    def setUp(self):
        self.user, self.client = make_user("ann")

    def create(self, **data):
        return self.client.post("/notes/api/notes/", data, format="json")

    def test_create_read_update_with_derived_preview(self):
        res = self.create(title="Groceries", content=doc("Milk and eggs"))
        self.assertEqual(res.status_code, 201)
        note_id = res.data["id"]
        self.assertEqual(res.data["preview"], "Milk and eggs")
        self.assertEqual(res.data["version"], 1)

        res = self.client.patch(f"/notes/api/notes/{note_id}/", {"content": doc("Bread"), "version": 1}, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["version"], 2)
        self.assertEqual(res.data["preview"], "Bread")

    def test_stale_version_conflicts(self):
        note_id = self.create(title="A").data["id"]
        self.client.patch(f"/notes/api/notes/{note_id}/", {"title": "B", "version": 1}, format="json")
        res = self.client.patch(f"/notes/api/notes/{note_id}/", {"title": "C", "version": 1}, format="json")
        self.assertEqual(res.status_code, 409)
        self.assertEqual(res.data["note"]["title"], "B")

    def test_pinning_does_not_bump_version(self):
        note_id = self.create(title="A").data["id"]
        res = self.client.patch(f"/notes/api/notes/{note_id}/", {"pinned": True}, format="json")
        self.assertTrue(res.data["pinned"])
        self.assertEqual(res.data["version"], 1)

    def test_search_matches_title_and_body(self):
        self.create(title="Trip plan", content=doc("Book train to Kochi"))
        self.create(title="Work", content=doc("Quarterly report"))
        res = self.client.get("/notes/api/notes/?q=kochi")
        self.assertEqual([n["title"] for n in res.data["results"]], ["Trip plan"])
        res = self.client.get("/notes/api/notes/?q=work")
        self.assertEqual([n["title"] for n in res.data["results"]], ["Work"])

    def test_other_users_cannot_see_or_edit_notes(self):
        note_id = self.create(title="Private").data["id"]
        _, other = make_user("eve")
        self.assertEqual(other.get(f"/notes/api/notes/{note_id}/").status_code, 404)
        self.assertEqual(other.patch(f"/notes/api/notes/{note_id}/", {"title": "x"}, format="json").status_code, 404)
        self.assertEqual(other.delete(f"/notes/api/notes/{note_id}/").status_code, 404)
        self.assertEqual(other.get("/notes/api/notes/").data["count"], 0)

    def test_trash_restore_and_permanent_delete(self):
        note_id = self.create(title="Old").data["id"]
        self.client.delete(f"/notes/api/notes/{note_id}/")
        self.assertEqual(self.client.get("/notes/api/notes/").data["count"], 0)
        self.assertEqual(self.client.get("/notes/api/notes/?trash=1").data["count"], 1)
        res = self.client.patch(f"/notes/api/notes/{note_id}/", {"title": "x"}, format="json")
        self.assertEqual(res.status_code, 400)

        self.client.post(f"/notes/api/notes/{note_id}/restore/")
        self.assertEqual(self.client.get("/notes/api/notes/").data["count"], 1)

        self.client.delete(f"/notes/api/notes/{note_id}/")
        self.client.delete(f"/notes/api/notes/{note_id}/")
        self.assertFalse(Note.objects.filter(pk=note_id).exists())

    def test_folder_of_another_user_rejected(self):
        _, other = make_user("eve")
        folder_id = other.post("/notes/api/folders/", {"name": "Eve's"}, format="json").data["id"]
        res = self.create(title="x", folder=folder_id)
        self.assertEqual(res.status_code, 400)

    def test_image_upload_and_private_serving(self):
        res = self.client.post("/notes/api/assets/", {"file": png_file()}, format="multipart")
        self.assertEqual(res.status_code, 201)
        url = res.data["url"]
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res["Content-Type"], "image/png")
        _, other = make_user("eve")
        self.assertEqual(other.get(url).status_code, 404)

    def test_non_image_upload_rejected(self):
        fake = SimpleUploadedFile("x.png", b"<svg onload=alert(1)>", content_type="image/png")
        res = self.client.post("/notes/api/assets/", {"file": fake}, format="multipart")
        self.assertEqual(res.status_code, 400)


class BoardContentTests(TestCase):
    def setUp(self):
        self.user, self.client = make_user("ann")

    def test_board_scene_saved_and_searchable(self):
        scene = {"elements": [
            {"type": "rectangle", "id": "r"},
            # Excalidraw stores wrapped lines in `text` and the typed text in `originalText`.
            {"type": "text", "id": "t", "text": "Approve\nbudget", "originalText": "Approve budget"},
        ], "files": {}}
        res = self.client.post("/notes/api/notes/", {"kind": "board", "content": scene}, format="json")
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data["preview"], "Approve budget")
        board_id = res.data["id"]
        self.assertEqual(self.client.get("/notes/api/notes/?q=budget").data["count"], 1)
        res = self.client.patch(f"/notes/api/notes/{board_id}/", {"content": doc("not a scene"), "version": 1}, format="json")
        self.assertEqual(res.status_code, 400)

    def test_doc_rejects_scene(self):
        res = self.client.post("/notes/api/notes/", {"kind": "doc", "content": {"elements": []}}, format="json")
        self.assertEqual(res.status_code, 400)


class TextExtractionTests(TestCase):
    def test_tables_and_checklists_are_searchable(self):
        from .text import extract_text

        def cell(kind, text):
            return {"type": kind, "content": [{"type": "paragraph", "content": [{"type": "text", "text": text}]}]}

        content = {
            "type": "doc",
            "content": [
                {"type": "table", "content": [
                    {"type": "tableRow", "content": [cell("tableHeader", "Item"), cell("tableHeader", "Price")]},
                    {"type": "tableRow", "content": [cell("tableCell", "Laptop"), cell("tableCell", "₹55,000")]},
                ]},
                {"type": "taskList", "content": [
                    {"type": "taskItem", "attrs": {"checked": True}, "content": [
                        {"type": "paragraph", "content": [{"type": "text", "text": "Pay invoice"}]}]},
                ]},
                {"type": "image", "attrs": {"src": "/notes/api/assets/x/"}},
            ],
        }
        text = extract_text("doc", content)
        for word in ["Item", "Price", "Laptop", "₹55,000", "Pay invoice"]:
            self.assertIn(word, text)
        self.assertNotIn("ItemPrice", text)  # cells are separated


def weasyprint_available():
    try:
        import weasyprint  # noqa: F401
    except (ImportError, OSError):
        return False
    return True


def pdf_page_count(data):
    """Count page objects, looking inside WeasyPrint's compressed object streams too."""
    text = data
    for stream in re.findall(rb"stream\r?\n(.*?)endstream", data, re.S):
        try:
            text += zlib.decompress(stream)
        except zlib.error:
            pass
    return len(re.findall(rb"/Type\s*/Page\b(?!s)", text))


class RenderTests(TestCase):
    def test_marks_styles_and_tables_render_escaped(self):
        content = {"type": "doc", "content": [
            {"type": "paragraph", "attrs": {"textAlign": "center"}, "content": [
                {"type": "text", "text": "<b>hi</b>", "marks": [{"type": "bold"}]},
                {"type": "text", "text": "red", "marks": [{"type": "textStyle", "attrs": {"color": "#ff0000"}}]},
            ]},
            {"type": "table", "content": [{"type": "tableRow", "content": [
                {"type": "tableCell", "attrs": {"colspan": 2, "backgroundColor": "#eeeeee"}, "content": [doc("cell")["content"][0]]},
            ]}]},
        ]}
        html = render_doc(content, set())
        self.assertIn('<p style="text-align: center"><strong>&lt;b&gt;hi&lt;/b&gt;</strong>', html)
        self.assertIn('<span style="color: #ff0000">red</span>', html)
        self.assertIn('<td colspan="2" style="background-color: #eeeeee"><p>cell</p></td>', html)

    def test_unsafe_values_are_dropped(self):
        content = {"type": "doc", "content": [{"type": "paragraph", "content": [
            {"type": "text", "text": "x", "marks": [
                {"type": "link", "attrs": {"href": "javascript:alert(1)"}},
                {"type": "textStyle", "attrs": {"color": "red; background: url(http://evil)"}},
            ]},
        ]}, {"type": "image", "attrs": {"src": "http://evil.example/a.png"}},
            {"type": "image", "attrs": {"src": "/notes/api/assets/00000000-0000-0000-0000-000000000000/"}}]}
        html = render_doc(content, set())
        self.assertNotIn("javascript", html)
        self.assertNotIn("evil", html)
        self.assertNotIn("<img", html)

    def test_callouts_columns_toggles_and_drawings(self):
        asset_id = "11111111-1111-1111-1111-111111111111"
        para = lambda text: {"type": "paragraph", "content": [{"type": "text", "text": text}]}
        content = {"type": "doc", "content": [
            {"type": "callout", "attrs": {"variant": "warning"}, "content": [para("Careful")]},
            {"type": "callout", "attrs": {"variant": "<script>"}, "content": [para("Odd variant")]},
            {"type": "columns", "content": [
                {"type": "column", "content": [para("Left")]},
                {"type": "column", "content": [para("Right")]},
            ]},
            {"type": "details", "content": [
                {"type": "detailsSummary", "content": [{"type": "text", "text": "More"}]},
                {"type": "detailsContent", "content": [para("Hidden text")]},
            ]},
            {"type": "drawing", "attrs": {"src": f"/notes/api/assets/{asset_id}/", "width": 320, "scene": {"elements": []}}},
            {"type": "drawing", "attrs": {"src": "/notes/api/assets/22222222-2222-2222-2222-222222222222/"}},
        ]}
        html = render_doc(content, {asset_id})
        self.assertIn('<div class="callout callout-warning"><span class="callout-icon">⚠️</span>', html)
        self.assertIn('<div class="callout callout-info">', html)  # unknown variants fall back
        self.assertNotIn("<script>", html)
        self.assertIn('<table class="columns"><tr><td><p>Left</p></td><td><p>Right</p></td></tr></table>', html)
        self.assertIn('<p class="toggle-title">More</p><div class="toggle-body"><p>Hidden text</p></div>', html)
        self.assertIn(f'<div class="drawing"><img src="asset:{asset_id}" alt="" style="width: 320px"></div>', html)
        self.assertEqual(html.count("<img"), 1)  # another user's drawing is dropped
        self.assertEqual(referenced_asset_ids(content), {asset_id, "22222222-2222-2222-2222-222222222222"})

        text = extract_text("doc", content)
        self.assertIn("Careful", text)
        self.assertRegex(text, r"Left\s+Right")
        self.assertRegex(text, r"More\s+Hidden text")

    def test_page_settings_validation(self):
        self.assertEqual(clean_page_settings({})["size"], "A4")
        with self.assertRaises(ValueError):
            clean_page_settings({"margins": {"top": 99}})
        with self.assertRaises(ValueError):
            clean_page_settings({"size": "A0"})


@skipUnless(weasyprint_available(), "WeasyPrint system libraries are not installed")
@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class PdfExportTests(TestCase):
    def setUp(self):
        self.user, self.client = make_user("ann")

    def create(self, **data):
        return self.client.post("/notes/api/notes/", data, format="json").data["id"]

    def test_page_settings_saved_without_version_bump(self):
        note_id = self.create(title="A")
        res = self.client.patch(
            f"/notes/api/notes/{note_id}/", {"page_settings": {"size": "Letter", "orientation": "landscape"}}, format="json"
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["page_settings"]["size"], "Letter")
        self.assertEqual(res.data["page_settings"]["margins"]["top"], 20)
        self.assertEqual(res.data["version"], 1)
        res = self.client.patch(f"/notes/api/notes/{note_id}/", {"page_settings": {"size": "A0"}}, format="json")
        self.assertEqual(res.status_code, 400)

    def test_single_pdf_with_page_break_and_image(self):
        asset_url = self.client.post("/notes/api/assets/", {"file": png_file()}, format="multipart").data["url"]
        content = {"type": "doc", "content": [
            doc("Page one")["content"][0],
            {"type": "image", "attrs": {"src": asset_url, "width": 100}},
            {"type": "pageBreak"},
            doc("Page two")["content"][0],
        ]}
        note_id = self.create(title="Report", content=content)
        res = self.client.get(f"/notes/api/notes/{note_id}/pdf/?inline=1")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res["Content-Type"], "application/pdf")
        self.assertTrue(res["Content-Disposition"].startswith('inline; filename="report.pdf"'))
        self.assertEqual(res["X-Frame-Options"], "SAMEORIGIN")
        self.assertTrue(res.content.startswith(b"%PDF"))
        self.assertEqual(pdf_page_count(res.content), 2)
        self.assertIn(b"/Subtype /Image", res.content)

    def test_no_noetsa_branding(self):
        note = Note.objects.get(pk=self.create(title="A", content=doc("x")))
        self.assertNotIn("Noetsa", note_html(note, set()))

    def test_combined_export_keeps_order_and_scope(self):
        a = self.create(title="A", content=doc("first"))
        b = self.create(title="B", content=doc("second"))
        res = self.client.post("/notes/api/notes/export-pdf/", {"notes": [b, a]}, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(pdf_page_count(res.content), 2)
        self.assertIn('filename="b.pdf"', res["Content-Disposition"])

        _, other = make_user("eve")
        self.assertEqual(other.get(f"/notes/api/notes/{a}/pdf/").status_code, 404)
        self.assertEqual(other.post("/notes/api/notes/export-pdf/", {"notes": [a]}, format="json").status_code, 400)

    def test_boards_and_trashed_notes_are_not_exported(self):
        board = self.create(kind="board")
        self.assertEqual(self.client.get(f"/notes/api/notes/{board}/pdf/").status_code, 400)
        note = self.create(title="gone")
        self.client.delete(f"/notes/api/notes/{note}/")
        self.assertEqual(self.client.get(f"/notes/api/notes/{note}/pdf/").status_code, 404)
