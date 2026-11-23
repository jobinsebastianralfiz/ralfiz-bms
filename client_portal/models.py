import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class ProjectComment(models.Model):
    """Comments on projects - enables client-team communication"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey('core.Project', on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='project_comments')
    message = models.TextField()
    is_internal = models.BooleanField(default=False, help_text='Internal notes not visible to clients')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Comment by {self.author.get_full_name() or self.author.username} on {self.project.name}"


class ProjectUpdate(models.Model):
    """Project milestone/progress updates visible to clients"""
    UPDATE_TYPE_CHOICES = [
        ('milestone', 'Milestone'),
        ('progress', 'Progress Update'),
        ('release', 'Release'),
        ('blocker', 'Blocker'),
        ('info', 'Information'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey('core.Project', on_delete=models.CASCADE, related_name='updates')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='project_updates')
    title = models.CharField(max_length=255)
    description = models.TextField()
    update_type = models.CharField(max_length=20, choices=UPDATE_TYPE_CHOICES, default='progress')
    progress_percentage = models.IntegerField(null=True, blank=True, help_text='Overall project progress 0-100')
    attachment = models.FileField(upload_to='project_updates/', blank=True)
    is_visible_to_client = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_update_type_display()}: {self.title}"


class ClientNotification(models.Model):
    """Notifications for clients about their projects"""
    NOTIFICATION_TYPE_CHOICES = [
        ('project_update', 'Project Update'),
        ('task_completed', 'Task Completed'),
        ('invoice_created', 'Invoice Created'),
        ('quote_sent', 'Quote Sent'),
        ('comment_reply', 'Comment Reply'),
        ('milestone', 'Milestone Reached'),
        ('general', 'General'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey('core.Client', on_delete=models.CASCADE, related_name='portal_notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES, default='general')
    project = models.ForeignKey('core.Project', on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.client}"


class SupportMessage(models.Model):
    """One line of the live support chat between a client and the Ralfiz team.

    One conversation per client. `read_at` is when the other side saw it:
    staff for a client's message, the client for a staff reply.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey('core.Client', on_delete=models.CASCADE, related_name='support_messages')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='support_messages')
    from_client = models.BooleanField(default=True)
    via = models.CharField(max_length=120, blank=True, default='',
                           help_text="Where a client's message came from when not the portal, e.g. 'Shop Manager · Anjali'.")
    body = models.TextField(max_length=4000)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['created_at']
        indexes = [models.Index(fields=['client', 'created_at'])]

    def __str__(self):
        return f"{'Client' if self.from_client else 'Team'} · {self.client} · {self.body[:40]}"

    @property
    def sender_name(self):
        if self.from_client:
            return f'{self.client.name} ({self.via})' if self.via else self.client.name
        u = self.sender
        return (u.get_full_name() or u.username) if u else 'Ralfiz team'

    def as_dict(self):
        return {
            'id': str(self.id), 'from_client': self.from_client, 'body': self.body,
            'sender': self.sender_name, 'at': self.created_at.isoformat(),
            'read': self.read_at is not None,
        }
