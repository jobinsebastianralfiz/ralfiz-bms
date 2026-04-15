"""Task board APIs for the Flutter app.

Bridges core.Task (kanban tasks assigned to TeamMember) with JWT-authenticated
users coming from the mobile app. A User is eligible if they have either a
TeamMember or Employee profile.
"""
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema

from core.models import (
    Task, TeamMember, TaskComment, TaskIssue, TaskActivity, TaskAttachment
)
from .task_serializers import (
    TaskListSerializer, TaskDetailSerializer,
    TaskCommentSerializer, TaskIssueSerializer, TaskActivitySerializer,
)


def _log(task, actor, verb, from_value='', to_value='', message='', is_visible_to_client=False, related_comment=None, related_issue=None):
    TaskActivity.objects.create(
        task=task, actor=actor, verb=verb,
        from_value=str(from_value)[:255], to_value=str(to_value)[:255],
        message=message[:500], is_visible_to_client=is_visible_to_client,
        related_comment=related_comment, related_issue=related_issue,
    )


def _tasks_for(user):
    tm = getattr(user, 'team_profile', None)
    if tm:
        return Task.objects.filter(assigned_to=tm)
    # Employees without team_profile see everything assigned to them by user linkage isn't
    # modeled directly; fall back to none unless admin.
    if user.is_superuser or user.is_staff:
        return Task.objects.all()
    return Task.objects.none()


class MyTasksView(generics.ListAPIView):
    """List tasks assigned to the current user (kanban feed)."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TaskListSerializer

    def get_queryset(self):
        qs = _tasks_for(self.request.user).select_related('project', 'assigned_to')
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        project = self.request.query_params.get('project')
        if project:
            qs = qs.filter(project_id=project)
        return qs.order_by('-priority', 'due_date')


class TaskDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TaskDetailSerializer
    lookup_field = 'pk'

    def get_queryset(self):
        return _tasks_for(self.request.user).select_related('project', 'assigned_to')


class TaskStatusUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request={'application/json': {'type': 'object', 'properties': {'status': {'type': 'string'}}}})
    def post(self, request, pk):
        task = get_object_or_404(_tasks_for(request.user), pk=pk)
        new_status = request.data.get('status')
        if new_status not in dict(Task.STATUS_CHOICES):
            return Response({'detail': 'Invalid status'}, status=400)
        old = task.status
        task.status = new_status
        if new_status == 'completed':
            task.completed_date = timezone.now().date()
        else:
            task.completed_date = None
        task.save()
        if old != new_status:
            _log(task, request.user, 'status_changed', from_value=old, to_value=new_status, is_visible_to_client=True)
        return Response(TaskDetailSerializer(task, context={'request': request}).data)


class TaskCommentListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TaskCommentSerializer

    def get_queryset(self):
        task = get_object_or_404(_tasks_for(self.request.user), pk=self.kwargs['pk'])
        return task.comments.filter(is_deleted=False).select_related('author').order_by('created_at')

    def perform_create(self, serializer):
        task = get_object_or_404(_tasks_for(self.request.user), pk=self.kwargs['pk'])
        parent_id = self.request.data.get('parent')
        parent = TaskComment.objects.filter(pk=parent_id, task=task).first() if parent_id else None
        comment = serializer.save(task=task, author=self.request.user, parent=parent)
        _log(task, self.request.user, 'commented',
             message=comment.body[:140],
             is_visible_to_client=comment.is_visible_to_client, related_comment=comment)


class TaskCommentDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk, comment_id):
        task = get_object_or_404(_tasks_for(request.user), pk=pk)
        comment = get_object_or_404(TaskComment, pk=comment_id, task=task)
        if comment.author_id != request.user.id and not request.user.is_superuser:
            return Response({'detail': 'Forbidden'}, status=403)
        comment.is_deleted = True
        comment.body = '[deleted]'
        comment.save(update_fields=['is_deleted', 'body', 'updated_at'])
        return Response(status=204)


class TaskIssueListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TaskIssueSerializer

    def get_queryset(self):
        task = get_object_or_404(_tasks_for(self.request.user), pk=self.kwargs['pk'])
        return task.issues.select_related('reporter', 'assignee').all()

    def perform_create(self, serializer):
        task = get_object_or_404(_tasks_for(self.request.user), pk=self.kwargs['pk'])
        assignee_id = self.request.data.get('assignee_id')
        assignee = TeamMember.objects.filter(pk=assignee_id).first() if assignee_id else None
        issue = serializer.save(task=task, reporter=self.request.user, assignee=assignee)
        _log(task, self.request.user, 'issue_opened',
             to_value=issue.severity, message=issue.title[:140],
             is_visible_to_client=issue.is_visible_to_client, related_issue=issue)


class TaskIssueUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk, issue_id):
        task = get_object_or_404(_tasks_for(request.user), pk=pk)
        issue = get_object_or_404(TaskIssue, pk=issue_id, task=task)
        new_status = request.data.get('status')
        resolution = request.data.get('resolution', '').strip()
        if new_status and new_status in dict(TaskIssue.STATUS_CHOICES) and new_status != issue.status:
            old = issue.status
            issue.status = new_status
            if new_status in ('resolved', 'closed') and not issue.resolved_at:
                issue.resolved_at = timezone.now()
            if new_status in ('open', 'in_progress'):
                issue.resolved_at = None
            if resolution:
                issue.resolution = resolution
            issue.save()
            verb = 'issue_resolved' if new_status in ('resolved', 'closed') else 'issue_status_changed'
            _log(task, request.user, verb,
                 from_value=old, to_value=new_status, message=issue.title[:140],
                 is_visible_to_client=issue.is_visible_to_client, related_issue=issue)
        return Response(TaskIssueSerializer(issue).data)


class TaskActivityListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TaskActivitySerializer

    def get_queryset(self):
        task = get_object_or_404(_tasks_for(self.request.user), pk=self.kwargs['pk'])
        return task.activities.select_related('actor').all()[:100]
