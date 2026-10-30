from django.contrib import admin

from .models import Template


@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    """Built-in note templates: hide them, change order/wording. Content is JSON (TipTap); the
    easiest way to change it is to edit doc_templates/builtin.py and run `sync_templates --force`.
    Templates people save from their own notes are private and not listed here."""

    list_display = ["name", "category", "is_active", "sort_order"]
    list_editable = ["is_active", "sort_order"]
    list_filter = ["category", "is_active"]
    search_fields = ["name", "slug"]
    readonly_fields = ["slug", "preview", "created_at", "updated_at"]
    fields = [
        "name", "description", "category", "note_title", "is_active", "sort_order",
        "content", "page_settings", "slug", "preview", "created_at", "updated_at",
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).filter(owner__isnull=True)

    def has_add_permission(self, request):
        return False
