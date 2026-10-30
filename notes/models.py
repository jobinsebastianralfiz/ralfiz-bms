import uuid

from django.conf import settings
from django.db import models


class Folder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="note_folders")
    name = models.CharField(max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Note(models.Model):
    """A rich-text note (`doc`, TipTap JSON) or a canvas (`board`, Excalidraw scene JSON).

    Notes are private: every query goes through `owner`, and no one else can read them.
    A note may be linked to one BMS record (project, client or lead), see notes.links."""

    KIND_DOC = "doc"
    KIND_BOARD = "board"
    KIND_CHOICES = [(KIND_DOC, "Note"), (KIND_BOARD, "Board")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notes")
    folder = models.ForeignKey(Folder, on_delete=models.SET_NULL, null=True, blank=True, related_name="notes")
    kind = models.CharField(max_length=10, choices=KIND_CHOICES, default=KIND_DOC)
    title = models.CharField(max_length=200, blank=True, default="")
    content = models.JSONField(null=True, blank=True)
    # Derived from content on save (notes.text): plain text for search and the list snippet.
    search_text = models.TextField(blank=True, default="")
    preview = models.CharField(max_length=240, blank=True, default="")
    pinned = models.BooleanField(default=False)
    # Page size, orientation, margins, header/footer for page view and PDF export (notes.pages).
    page_settings = models.JSONField(default=dict, blank=True)
    # Bumped on every title/content change; clients send the version they edited so a save
    # from a stale tab or device is rejected instead of overwriting newer work.
    version = models.PositiveIntegerField(default=1)
    # At most one of these is set (notes.links.set_link keeps it that way).
    project = models.ForeignKey("core.Project", on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    client = models.ForeignKey("core.Client", on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    lead = models.ForeignKey("crm.Lead", on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-pinned", "-updated_at"]
        indexes = [models.Index(fields=["owner", "deleted_at", "-updated_at"])]

    def __str__(self):
        return self.title or "Untitled"


def asset_path(instance, filename):
    # Under media/private/, which config.urls never serves; AssetFileView checks the owner.
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
    return f"private/notes/{instance.owner_id}/{instance.id}.{ext}"


class Asset(models.Model):
    """An uploaded image. Served only to its owner."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="note_assets")
    file = models.FileField(upload_to=asset_path)
    original_name = models.CharField(max_length=255, blank=True)
    content_type = models.CharField(max_length=100)
    size = models.PositiveBigIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.original_name or str(self.id)
