from rest_framework import serializers
from django.contrib.auth.models import User
from core.models import (
    Client, Project, Task, Invoice, InvoiceItem, Payment,
    Quote, QuoteItem, Document, ActivityLog
)
from .models import ProjectComment, ProjectUpdate, ClientNotification


# ─── Client Profile ─────────────────────────────────────────────

class ClientProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ['id', 'name', 'company_name', 'email', 'phone', 'whatsapp', 'address']
        read_only_fields = ['id']


# ─── Projects ────────────────────────────────────────────────────

class TaskSummarySerializer(serializers.ModelSerializer):
    """Lightweight task serializer for project detail view"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.name', read_only=True, default=None)
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'status', 'status_display', 'priority',
            'priority_display', 'assigned_to_name', 'due_date',
            'completed_date', 'is_overdue', 'created_at',
        ]


class ProjectListSerializer(serializers.ModelSerializer):
    """Project list — compact view"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    type_display = serializers.CharField(source='get_project_type_display', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    task_stats = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id', 'name', 'project_type', 'type_display', 'status',
            'status_display', 'start_date', 'deadline', 'completed_date',
            'is_overdue', 'task_stats', 'progress', 'created_at',
        ]

    def get_task_stats(self, obj):
        tasks = obj.tasks.all()
        total = tasks.count()
        completed = tasks.filter(status='completed').count()
        return {'total': total, 'completed': completed}

    def get_progress(self, obj):
        """Calculate progress from tasks or latest project update"""
        # Check if there's a manual progress update
        latest_update = obj.updates.filter(
            progress_percentage__isnull=False,
            is_visible_to_client=True
        ).first()
        if latest_update:
            return latest_update.progress_percentage

        # Otherwise calculate from tasks
        tasks = obj.tasks.all()
        total = tasks.count()
        if total == 0:
            return 0
        completed = tasks.filter(status='completed').count()
        return int((completed / total) * 100)


class ProjectDetailSerializer(serializers.ModelSerializer):
    """Full project detail with tasks, updates, and financials"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    type_display = serializers.CharField(source='get_project_type_display', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    tasks = TaskSummarySerializer(many=True, read_only=True)
    task_stats = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()
    team = serializers.SerializerMethodField()
    financial_summary = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id', 'name', 'description', 'project_type', 'type_display',
            'status', 'status_display', 'tech_stack', 'live_url',
            'start_date', 'deadline', 'completed_date', 'is_overdue',
            'tasks', 'task_stats', 'progress', 'team',
            'financial_summary', 'created_at', 'updated_at',
        ]

    def get_task_stats(self, obj):
        tasks = obj.tasks.all()
        total = tasks.count()
        by_status = {}
        for status, label in Task.STATUS_CHOICES:
            by_status[status] = tasks.filter(status=status).count()
        return {'total': total, **by_status}

    def get_progress(self, obj):
        latest_update = obj.updates.filter(
            progress_percentage__isnull=False,
            is_visible_to_client=True
        ).first()
        if latest_update:
            return latest_update.progress_percentage
        tasks = obj.tasks.all()
        total = tasks.count()
        if total == 0:
            return 0
        completed = tasks.filter(status='completed').count()
        return int((completed / total) * 100)

    def get_team(self, obj):
        return [
            {'name': m.name, 'role': m.get_role_display()}
            for m in obj.team_members.filter(is_active=True)
        ]

    def get_financial_summary(self, obj):
        invoices = obj.invoices.exclude(status='cancelled')
        from django.db.models import Sum
        total_invoiced = invoices.aggregate(t=Sum('total_amount'))['t'] or 0
        total_paid = invoices.aggregate(t=Sum('amount_paid'))['t'] or 0
        return {
            'total_invoiced': float(total_invoiced),
            'total_paid': float(total_paid),
            'balance_due': float(total_invoiced - total_paid),
        }


# ─── Task Board (Kanban) ────────────────────────────────────────

class TaskBoardSerializer(serializers.Serializer):
    """Returns tasks grouped by status for kanban view"""
    todo = TaskSummarySerializer(many=True)
    in_progress = TaskSummarySerializer(many=True)
    review = TaskSummarySerializer(many=True)
    completed = TaskSummarySerializer(many=True)


# ─── Invoices & Payments ────────────────────────────────────────

class InvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = ['id', 'description', 'details', 'quantity', 'unit_price', 'amount']


class PaymentSerializer(serializers.ModelSerializer):
    method_display = serializers.CharField(source='get_payment_method_display', read_only=True)

    class Meta:
        model = Payment
        fields = ['id', 'amount', 'payment_date', 'payment_method', 'method_display', 'transaction_id']


class InvoiceListSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True, default=None)
    balance_due = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'title', 'project_name', 'status',
            'status_display', 'total_amount', 'amount_paid', 'balance_due',
            'issue_date', 'due_date', 'is_overdue',
        ]


class InvoiceDetailSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True, default=None)
    balance_due = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    items = InvoiceItemSerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)

    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'title', 'description', 'project_name',
            'status', 'status_display', 'subtotal', 'discount', 'tax_rate',
            'tax_amount', 'total_amount', 'amount_paid', 'balance_due',
            'issue_date', 'due_date', 'is_overdue', 'terms', 'client_notes',
            'items', 'payments', 'created_at',
        ]


# ─── Quotes ──────────────────────────────────────────────────────

class QuoteItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuoteItem
        fields = ['id', 'description', 'details', 'quantity', 'unit_price', 'amount']


class QuoteListSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True, default=None)
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = Quote
        fields = [
            'id', 'quote_number', 'title', 'project_name', 'status',
            'status_display', 'total_amount', 'issue_date', 'valid_until',
            'is_expired',
        ]


class QuoteDetailSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True, default=None)
    is_expired = serializers.BooleanField(read_only=True)
    items = QuoteItemSerializer(many=True, read_only=True)

    class Meta:
        model = Quote
        fields = [
            'id', 'quote_number', 'title', 'description', 'project_name',
            'status', 'status_display', 'subtotal', 'discount', 'tax_rate',
            'tax_amount', 'total_amount', 'issue_date', 'valid_until',
            'is_expired', 'duration', 'start_date', 'deliverables',
            'payment_terms', 'terms', 'client_notes', 'items', 'created_at',
        ]


# ─── Comments ────────────────────────────────────────────────────

class CommentAuthorSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()
    is_team = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'display_name', 'is_team']

    def get_display_name(self, obj):
        return obj.get_full_name() or obj.username

    def get_is_team(self, obj):
        return obj.is_staff or obj.is_superuser or hasattr(obj, 'team_profile')


class ProjectCommentSerializer(serializers.ModelSerializer):
    author_info = CommentAuthorSerializer(source='author', read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = ProjectComment
        fields = [
            'id', 'project', 'message', 'author_info', 'parent',
            'replies', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'author_info', 'created_at', 'updated_at']

    def get_replies(self, obj):
        if obj.parent is not None:
            return []
        replies = obj.replies.filter(is_internal=False).order_by('created_at')
        return ProjectCommentSerializer(replies, many=True, context=self.context).data


class ProjectCommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectComment
        fields = ['project', 'message', 'parent']

    def validate_project(self, value):
        request = self.context['request']
        client = request.user.client_profile
        if value.client_id != client.id:
            raise serializers.ValidationError('You can only comment on your own projects.')
        return value

    def validate_parent(self, value):
        if value and value.is_internal:
            raise serializers.ValidationError('Cannot reply to this comment.')
        return value


# ─── Project Updates (Timeline) ─────────────────────────────────

class ProjectUpdateSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_update_type_display', read_only=True)
    author_name = serializers.SerializerMethodField()
    attachment_url = serializers.SerializerMethodField()

    class Meta:
        model = ProjectUpdate
        fields = [
            'id', 'title', 'description', 'update_type', 'type_display',
            'progress_percentage', 'author_name', 'attachment_url', 'created_at',
        ]

    def get_author_name(self, obj):
        return obj.author.get_full_name() or obj.author.username

    def get_attachment_url(self, obj):
        if obj.attachment:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.attachment.url)
        return None


# ─── Notifications ───────────────────────────────────────────────

class ClientNotificationSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True, default=None)

    class Meta:
        model = ClientNotification
        fields = [
            'id', 'title', 'message', 'notification_type', 'type_display',
            'project_name', 'is_read', 'created_at',
        ]


# ─── Documents ───────────────────────────────────────────────────

class DocumentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    file_extension = serializers.CharField(read_only=True)
    file_size = serializers.IntegerField(read_only=True)

    class Meta:
        model = Document
        fields = ['id', 'name', 'description', 'file_url', 'file_extension', 'file_size', 'created_at']

    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
        return None


# ─── Dashboard ───────────────────────────────────────────────────

class DashboardSerializer(serializers.Serializer):
    client = ClientProfileSerializer()
    stats = serializers.DictField()
    active_projects = ProjectListSerializer(many=True)
    recent_updates = ProjectUpdateSerializer(many=True)
    pending_invoices = InvoiceListSerializer(many=True)
    unread_notifications = serializers.IntegerField()


# ─── Password Change ────────────────────────────────────────────

class ClientChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Current password is incorrect.')
        return value

    def validate_new_password(self, value):
        from django.contrib.auth.password_validation import validate_password
        validate_password(value)
        return value
