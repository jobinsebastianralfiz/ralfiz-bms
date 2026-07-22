from rest_framework import serializers


class AskRequestSerializer(serializers.Serializer):
    query = serializers.CharField(
        max_length=2000,
        trim_whitespace=True,
        help_text='A question about the business, typed or transcribed from speech.',
    )

    def validate_query(self, value):
        if not value.strip():
            raise serializers.ValidationError('Query cannot be empty.')
        return value


class DocumentIngestSerializer(serializers.Serializer):
    """Input for /api/pulse/documents/. Text or file, not neither."""

    project_id = serializers.UUIDField(
        help_text='Project this document belongs to.'
    )
    title = serializers.CharField(max_length=255)
    text = serializers.CharField(
        required=False,
        allow_blank=True,
        trim_whitespace=False,
        help_text='Document body as plain text. Alternative to file.',
    )
    file = serializers.FileField(
        required=False,
        help_text='Plain-text file (.txt, .md, .csv...). Alternative to text.',
    )
    source = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        help_text='Where this came from. Defaults to the filename or "pasted text".',
    )

    def validate(self, data):
        if not data.get('text', '').strip() and not data.get('file'):
            raise serializers.ValidationError(
                'Provide document text or upload a file.'
            )
        return data


class DocumentSerializer(serializers.Serializer):
    """Documentation shape for ingest/list responses."""

    id = serializers.UUIDField()
    project = serializers.CharField()
    title = serializers.CharField()
    source = serializers.CharField()
    chunks = serializers.IntegerField()
    created_at = serializers.DateTimeField()


class AskResponseSerializer(serializers.Serializer):
    """Documentation shape for /api/docs/. Responses are built as plain dicts."""

    answer = serializers.CharField(
        help_text='Natural-language answer, two or three sentences.'
    )
    intent = serializers.CharField(
        allow_null=True,
        help_text='Name of the whitelisted query function that was called.',
    )
    data = serializers.JSONField(
        allow_null=True,
        help_text='Structured result from that function, for rendering cards.',
    )
