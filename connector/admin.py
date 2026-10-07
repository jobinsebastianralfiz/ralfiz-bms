from django.contrib import admin

from .models import ConnectorCallLog


@admin.register(ConnectorCallLog)
class ConnectorCallLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'user', 'tool', 'is_write', 'ok', 'duration_ms', 'client_name')
    list_filter = ('ok', 'is_write', 'tool')
    search_fields = ('tool', 'user__username', 'error')
    readonly_fields = [f.name for f in ConnectorCallLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
