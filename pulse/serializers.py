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
