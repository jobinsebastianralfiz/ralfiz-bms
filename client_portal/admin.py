from django.contrib import admin
from .models import ProjectComment, ProjectUpdate, ClientNotification


@admin.register(ProjectComment)
class ProjectCommentAdmin(admin.ModelAdmin):
    list_display = ['project', 'author', 'message_preview', 'is_internal', 'created_at']
    list_filter = ['is_internal', 'created_at']
    search_fields = ['message', 'project__name']

    def message_preview(self, obj):
        return obj.message[:80] + '...' if len(obj.message) > 80 else obj.message
    message_preview.short_description = 'Message'


@admin.register(ProjectUpdate)
class ProjectUpdateAdmin(admin.ModelAdmin):
    list_display = ['project', 'title', 'update_type', 'progress_percentage', 'is_visible_to_client', 'created_at']
    list_filter = ['update_type', 'is_visible_to_client', 'created_at']
    search_fields = ['title', 'description', 'project__name']


@admin.register(ClientNotification)
class ClientNotificationAdmin(admin.ModelAdmin):
    list_display = ['client', 'title', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['title', 'message']
