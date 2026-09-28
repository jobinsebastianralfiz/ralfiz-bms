from django.contrib import admin

from .models import RalfPOSLicense, RalfPOSLicenseLog


class RalfPOSLicenseLogInline(admin.TabularInline):
    model = RalfPOSLicenseLog
    extra = 0
    readonly_fields = ('event', 'status', 'ip_address', 'domain', 'details', 'created_at')
    ordering = ('-created_at',)

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(RalfPOSLicense)
class RalfPOSLicenseAdmin(admin.ModelAdmin):
    list_display = ('shop_name', 'license_key', 'api_domain', 'status', 'valid_until', 'max_counters', 'last_check_at')
    list_filter = ('status', 'license_type', 'billing_cycle')
    search_fields = ('shop_name', 'shop_email', 'license_key', 'api_domain')
    readonly_fields = ('license_key', 'issued_at', 'created_at', 'updated_at', 'total_checks', 'last_check_at',
                       'last_check_ip', 'app_version')
    inlines = [RalfPOSLicenseLogInline]
