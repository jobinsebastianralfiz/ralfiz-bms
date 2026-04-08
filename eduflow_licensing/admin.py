from django.contrib import admin
from .models import EduFlowLicense, EduFlowLicenseLog


class EduFlowLicenseLogInline(admin.TabularInline):
    model = EduFlowLicenseLog
    extra = 0
    readonly_fields = ('event', 'status', 'ip_address', 'domain', 'details', 'created_at')
    ordering = ('-created_at',)

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(EduFlowLicense)
class EduFlowLicenseAdmin(admin.ModelAdmin):
    list_display = (
        'institute_name', 'license_key', 'api_domain', 'license_type',
        'status', 'valid_until', 'days_remaining_display',
        'max_users', 'total_checks', 'last_check_at',
    )
    list_filter = ('status', 'license_type', 'billing_cycle')
    search_fields = ('institute_name', 'institute_email', 'license_key', 'api_domain')
    readonly_fields = (
        'license_key', 'issued_at', 'created_at', 'updated_at',
        'total_checks', 'last_check_at', 'last_check_ip',
    )
    inlines = [EduFlowLicenseLogInline]

    fieldsets = (
        ('Institute Identity', {
            'fields': ('client', 'institute_name', 'institute_owner_name', 'institute_email', 'institute_phone', 'institute_address'),
        }),
        ('License Key & Domain', {
            'fields': ('license_key', 'api_domain', 'landing_domain'),
        }),
        ('License Configuration', {
            'fields': ('license_type', 'status', 'billing_cycle', 'auto_renew', 'grace_period_days'),
        }),
        ('Validity', {
            'fields': ('valid_from', 'valid_until', 'last_renewed_at', 'renewal_count'),
        }),
        ('Module Control', {
            'fields': ('enabled_modules', 'max_users', 'max_batches'),
            'description': 'Leave enabled_modules empty to enable all modules.',
        }),
        ('Deployment', {
            'fields': ('server_ip', 'deployment_notes'),
            'classes': ('collapse',),
        }),
        ('Tracking', {
            'fields': ('last_check_at', 'last_check_ip', 'total_checks'),
            'classes': ('collapse',),
        }),
        ('Notes & Timestamps', {
            'fields': ('notes', 'issued_at', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def days_remaining_display(self, obj):
        days = obj.days_remaining()
        if days < 0:
            return f"⛔ {abs(days)}d overdue"
        if days < 7:
            return f"⚠️ {days}d"
        if days < 30:
            return f"🟡 {days}d"
        return f"✅ {days}d"
    days_remaining_display.short_description = 'Remaining'

    actions = ['mark_expired', 'mark_active', 'mark_suspended']

    @admin.action(description='Mark selected as Expired')
    def mark_expired(self, request, queryset):
        queryset.update(status='expired')

    @admin.action(description='Mark selected as Active')
    def mark_active(self, request, queryset):
        queryset.update(status='active')

    @admin.action(description='Mark selected as Suspended')
    def mark_suspended(self, request, queryset):
        queryset.update(status='suspended')


@admin.register(EduFlowLicenseLog)
class EduFlowLicenseLogAdmin(admin.ModelAdmin):
    list_display = ('license', 'event', 'status', 'ip_address', 'domain', 'created_at')
    list_filter = ('event', 'status')
    search_fields = ('license__institute_name', 'license__license_key', 'domain')
    readonly_fields = ('license', 'event', 'status', 'ip_address', 'domain', 'details', 'created_at')
    ordering = ('-created_at',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
