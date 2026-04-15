from rest_framework import serializers
from core.models import Task, TaskComment, TaskIssue, TaskActivity, TaskAttachment


class TaskAttachmentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = TaskAttachment
        fields = ['id', 'name', 'file_url', 'created_at']

    def get_file_url(self, obj):
        req = self.context.get('request')
        url = obj.file.url if obj.file else ''
        return req.build_absolute_uri(url) if req and url else url


class _AuthorMixin(serializers.Serializer):
    author_name = serializers.SerializerMethodField()
    author_initial = serializers.SerializerMethodField()

    def get_author_name(self, obj):
        a = getattr(obj, 'author', None) or getattr(obj, 'actor', None) or getattr(obj, 'reporter', None)
        if not a:
            return 'System'
        return a.get_full_name() or a.username

    def get_author_initial(self, obj):
        name = self.get_author_name(obj)
        return (name[:1] or '?').upper()


class TaskCommentSerializer(_AuthorMixin, serializers.ModelSerializer):
    attachment_url = serializers.SerializerMethodField()
    reply_count = serializers.IntegerField(source='replies.count', read_only=True)

    class Meta:
        model = TaskComment
        fields = ['id', 'body', 'parent', 'attachment', 'attachment_url',
                  'is_visible_to_client', 'is_deleted', 'reply_count',
                  'author_name', 'author_initial', 'created_at', 'updated_at']
        read_only_fields = ['is_deleted', 'attachment_url', 'author_name', 'author_initial', 'created_at', 'updated_at']
        extra_kwargs = {'attachment': {'write_only': True, 'required': False}}

    def get_attachment_url(self, obj):
        if not obj.attachment:
            return None
        req = self.context.get('request')
        url = obj.attachment.url
        return req.build_absolute_uri(url) if req else url


class TaskIssueSerializer(_AuthorMixin, serializers.ModelSerializer):
    assignee_name = serializers.SerializerMethodField()
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = TaskIssue
        fields = ['id', 'title', 'description', 'severity', 'severity_display',
                  'status', 'status_display', 'is_visible_to_client',
                  'resolution', 'resolved_at', 'assignee_name',
                  'author_name', 'author_initial', 'created_at', 'updated_at']
        read_only_fields = ['resolved_at', 'severity_display', 'status_display',
                            'assignee_name', 'author_name', 'author_initial',
                            'created_at', 'updated_at']

    def get_assignee_name(self, obj):
        return obj.assignee.name if obj.assignee else None


class TaskActivitySerializer(_AuthorMixin, serializers.ModelSerializer):
    verb_display = serializers.CharField(source='get_verb_display', read_only=True)

    class Meta:
        model = TaskActivity
        fields = ['id', 'verb', 'verb_display', 'from_value', 'to_value',
                  'message', 'is_visible_to_client',
                  'author_name', 'author_initial', 'created_at']


class TaskListSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)
    assignee_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    comment_count = serializers.IntegerField(source='comments.count', read_only=True)
    open_issue_count = serializers.IntegerField(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = Task
        fields = ['id', 'title', 'project_name', 'assignee_name', 'status',
                  'status_display', 'priority', 'priority_display', 'due_date',
                  'is_overdue', 'comment_count', 'open_issue_count', 'created_at']

    def get_assignee_name(self, obj):
        return obj.assigned_to.name if obj.assigned_to else None


class TaskDetailSerializer(TaskListSerializer):
    description = serializers.CharField()
    notes = serializers.CharField()
    attachments = TaskAttachmentSerializer(many=True, read_only=True)
    comments = serializers.SerializerMethodField()
    issues = serializers.SerializerMethodField()
    activities = serializers.SerializerMethodField()

    class Meta(TaskListSerializer.Meta):
        fields = TaskListSerializer.Meta.fields + [
            'description', 'notes', 'attachments', 'comments', 'issues', 'activities'
        ]

    def get_comments(self, obj):
        qs = obj.comments.filter(is_deleted=False).select_related('author').order_by('created_at')
        return TaskCommentSerializer(qs, many=True, context=self.context).data

    def get_issues(self, obj):
        qs = obj.issues.select_related('reporter', 'assignee').all()
        return TaskIssueSerializer(qs, many=True, context=self.context).data

    def get_activities(self, obj):
        qs = obj.activities.select_related('actor').all()[:50]
        return TaskActivitySerializer(qs, many=True, context=self.context).data
