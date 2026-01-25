from django.contrib import admin
from django.utils.html import format_html
from .models import Business, Counter, Backup, SyncLog, APIToken


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ('name', 'license_customer', 'email', 'phone', 'gst_number', 'counters_count', 'created_at')
    list_filter = ('country', 'created_at')
    search_fields = ('name', 'email', 'gst_number', 'license__customer_name')
    readonly_fields = ('id', 'created_at', 'updated_at', 'last_synced_at')

    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'license', 'name', 'legal_name', 'business_type')
        }),
        ('Contact', {
            'fields': ('email', 'phone', 'website')
        }),
        ('Address', {
            'fields': ('address_line1', 'address_line2', 'city', 'state', 'country', 'postal_code')
        }),
        ('Tax Information', {
            'fields': ('gst_number', 'pan_number')
        }),
        ('Settings', {
            'fields': ('currency_code', 'currency_symbol', 'date_format', 'logo')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_synced_at'),
            'classes': ('collapse',)
        }),
    )

    def license_customer(self, obj):
        return obj.license.customer_name
    license_customer.short_description = 'License Customer'

    def counters_count(self, obj):
        return obj.counters.count()
    counters_count.short_description = 'Counters'


@admin.register(Counter)
class CounterAdmin(admin.ModelAdmin):
    list_display = ('name', 'business', 'device_type', 'status', 'is_primary', 'app_version', 'last_sync_at')
    list_filter = ('status', 'is_primary', 'device_type', 'sync_enabled')
    search_fields = ('name', 'business__name', 'device_name')
    readonly_fields = ('id', 'created_at', 'updated_at', 'last_sync_at')

    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'business', 'activation', 'name', 'description')
        }),
        ('Device Information', {
            'fields': ('device_name', 'device_type', 'os_info', 'app_version')
        }),
        ('Status', {
            'fields': ('status', 'is_primary', 'sync_enabled')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_sync_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Backup)
class BackupAdmin(admin.ModelAdmin):
    list_display = ('filename', 'business', 'counter', 'backup_type', 'status', 'file_size_display', 'created_at')
    list_filter = ('backup_type', 'status', 'is_encrypted', 'created_at')
    search_fields = ('filename', 'business__name', 'counter__name')
    readonly_fields = ('id', 'created_at', 'uploaded_at', 'checksum', 'file_size')
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'business', 'counter')
        }),
        ('File Information', {
            'fields': ('file', 'filename', 'file_size', 'checksum')
        }),
        ('Encryption', {
            'fields': ('is_encrypted', 'encryption_version')
        }),
        ('Metadata', {
            'fields': ('backup_type', 'status', 'app_version', 'db_version', 'record_counts')
        }),
        ('Notes', {
            'fields': ('notes', 'error_message'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'uploaded_at'),
            'classes': ('collapse',)
        }),
    )

    def file_size_display(self, obj):
        if obj.file_size < 1024:
            return f"{obj.file_size} B"
        elif obj.file_size < 1024 * 1024:
            return f"{obj.file_size / 1024:.1f} KB"
        else:
            return f"{obj.file_size / (1024 * 1024):.1f} MB"
    file_size_display.short_description = 'Size'


@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    list_display = ('business', 'counter', 'sync_type', 'sync_direction', 'status_badge', 'records_uploaded', 'records_downloaded', 'duration_display', 'started_at')
    list_filter = ('sync_type', 'sync_direction', 'status', 'started_at')
    search_fields = ('business__name', 'counter__name')
    readonly_fields = ('id', 'started_at', 'completed_at', 'duration_seconds')
    date_hierarchy = 'started_at'

    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'business', 'counter')
        }),
        ('Sync Details', {
            'fields': ('sync_type', 'sync_direction', 'status')
        }),
        ('Statistics', {
            'fields': ('records_uploaded', 'records_downloaded', 'conflicts_detected', 'conflicts_resolved')
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at', 'duration_seconds')
        }),
        ('Additional Information', {
            'fields': ('details', 'error_message'),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        colors = {
            'started': '#3498db',
            'in_progress': '#f39c12',
            'completed': '#27ae60',
            'failed': '#e74c3c',
            'partial': '#9b59b6',
        }
        color = colors.get(obj.status, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px;">{}</span>',
            color,
            obj.status.title()
        )
    status_badge.short_description = 'Status'

    def duration_display(self, obj):
        if obj.duration_seconds:
            if obj.duration_seconds < 60:
                return f"{obj.duration_seconds:.1f}s"
            else:
                return f"{obj.duration_seconds / 60:.1f}m"
        return '-'
    duration_display.short_description = 'Duration'


@admin.register(APIToken)
class APITokenAdmin(admin.ModelAdmin):
    list_display = ('license_customer', 'counter', 'name', 'is_active', 'token_preview', 'last_used_at', 'created_at')
    list_filter = ('is_active', 'created_at', 'last_used_at')
    search_fields = ('license__customer_name', 'name', 'token')
    readonly_fields = ('id', 'token', 'created_at', 'last_used_at')

    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'license', 'counter', 'name')
        }),
        ('Token', {
            'fields': ('token', 'is_active', 'expires_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'last_used_at'),
            'classes': ('collapse',)
        }),
    )

    def license_customer(self, obj):
        return obj.license.customer_name
    license_customer.short_description = 'Customer'

    def token_preview(self, obj):
        return f"{obj.token[:8]}...{obj.token[-8:]}" if obj.token else '-'
    token_preview.short_description = 'Token'