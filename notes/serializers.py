import json

from rest_framework import serializers

from .links import LINK_KINDS, link_payload
from .models import Folder, Note
from .pages import clean_page_settings

MAX_CONTENT_BYTES = 5 * 1024 * 1024


def validate_content(value):
    if value is None:
        return value
    if not isinstance(value, dict):
        raise serializers.ValidationError("Content must be a JSON object.")
    if len(json.dumps(value, separators=(",", ":"))) > MAX_CONTENT_BYTES:
        raise serializers.ValidationError("This note is too large to save (5 MB limit).")
    return value


def validate_page_settings(value):
    try:
        return clean_page_settings(value)
    except ValueError as exc:
        raise serializers.ValidationError(str(exc))


class OwnFolderField(serializers.PrimaryKeyRelatedField):
    """Only the requesting user's own folders can be chosen."""

    def get_queryset(self):
        return Folder.objects.filter(owner=self.context["user"])


class NoteSummarySerializer(serializers.ModelSerializer):
    link = serializers.SerializerMethodField()

    class Meta:
        model = Note
        fields = [
            "id", "kind", "title", "preview", "pinned", "folder", "version", "link",
            "created_at", "updated_at", "deleted_at",
        ]

    def get_link(self, note):
        return link_payload(note)


class NoteDetailSerializer(NoteSummarySerializer):
    class Meta(NoteSummarySerializer.Meta):
        fields = NoteSummarySerializer.Meta.fields + ["content", "page_settings"]

    def to_representation(self, note):
        data = super().to_representation(note)
        # Fill in defaults so clients always get a complete settings object.
        data["page_settings"] = clean_page_settings(note.page_settings or {})
        return data


class LinkField(serializers.Field):
    """`{"kind": "project"|"client"|"lead", "id": ...}`, or null to unlink."""

    def to_internal_value(self, data):
        if data is None:
            return None
        if not isinstance(data, dict) or data.get("kind") not in LINK_KINDS or data.get("id") in (None, ""):
            raise serializers.ValidationError("Link to a project, client or lead.")
        return {"kind": data["kind"], "id": data["id"]}


class NoteCreateSerializer(serializers.Serializer):
    kind = serializers.ChoiceField(choices=Note.KIND_CHOICES, default=Note.KIND_DOC)
    title = serializers.CharField(max_length=200, required=False, allow_blank=True, default="")
    content = serializers.JSONField(required=False, allow_null=True, default=None, validators=[validate_content])
    folder = OwnFolderField(required=False, allow_null=True, default=None)
    link = LinkField(required=False, allow_null=True, default=None)


class NoteUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200, required=False, allow_blank=True)
    content = serializers.JSONField(required=False, allow_null=True, validators=[validate_content])
    pinned = serializers.BooleanField(required=False)
    folder = OwnFolderField(required=False, allow_null=True)
    page_settings = serializers.JSONField(required=False, validators=[validate_page_settings])
    link = LinkField(required=False, allow_null=True)
    version = serializers.IntegerField(required=False, min_value=1)


class PdfExportSerializer(serializers.Serializer):
    """POST /notes/api/notes/export-pdf/: several notes combined into one PDF, in the given order."""

    notes = serializers.ListField(child=serializers.UUIDField(), min_length=1, max_length=50)


class FolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Folder
        fields = ["id", "name", "created_at"]
        read_only_fields = ["id", "created_at"]
