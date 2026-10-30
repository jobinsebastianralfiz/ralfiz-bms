from rest_framework import serializers

from notes.pages import clean_page_settings

from .models import Template


class TemplateSummarySerializer(serializers.ModelSerializer):
    builtin = serializers.BooleanField(read_only=True)

    class Meta:
        model = Template
        fields = ["id", "slug", "name", "description", "category", "premium", "builtin", "preview", "created_at"]


class TemplateDetailSerializer(TemplateSummarySerializer):
    page_settings = serializers.SerializerMethodField()

    class Meta(TemplateSummarySerializer.Meta):
        fields = TemplateSummarySerializer.Meta.fields + ["note_title", "content", "page_settings"]

    def get_page_settings(self, obj):
        return clean_page_settings(obj.page_settings or {})


class SaveTemplateSerializer(serializers.Serializer):
    """Save an existing note as a custom template."""

    note = serializers.UUIDField()
    name = serializers.CharField(max_length=120)
    description = serializers.CharField(max_length=240, required=False, allow_blank=True, default="")
    category = serializers.ChoiceField(choices=Template.CATEGORIES, default="personal")
