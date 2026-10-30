import uuid

from django.conf import settings
from django.db import models


class Template(models.Model):
    """A starting point for a new note.

    Built-in templates have a `slug` and no owner; they come from doc_templates/builtin.py
    (`manage.py sync_templates`) and can be hidden or reordered in the Django admin.
    Custom templates are saved from a note and are private to the user who saved them."""

    CATEGORIES = [
        ("resume", "Resumes & CVs"),
        ("business", "Business"),
        ("letters", "Letters"),
        ("personal", "Personal"),
        ("education", "Education"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(max_length=60, unique=True, null=True, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name="note_templates"
    )
    name = models.CharField(max_length=120)
    description = models.CharField(max_length=240, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORIES, default="personal")
    # Title given to notes created from this template.
    note_title = models.CharField(max_length=200, blank=True)
    content = models.JSONField(default=dict)
    page_settings = models.JSONField(default=dict, blank=True)
    preview = models.CharField(max_length=240, blank=True, editable=False)
    # Kept from Noetsa's plans; in the BMS every template is available to everyone.
    premium = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name

    @property
    def builtin(self):
        return self.owner_id is None

    def save(self, *args, **kwargs):
        from notes.text import extract_text, make_preview

        self.preview = make_preview(extract_text("doc", self.content))
        super().save(*args, **kwargs)
