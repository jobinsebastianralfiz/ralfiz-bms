from django.contrib import admin

from .models import ShopLicense, ShopLicenseLog


class ShopLicenseLogInline(admin.TabularInline):
    model = ShopLicenseLog
    extra = 0
    readonly_fields = ('event', 'status', 'ip_address', 'domain', 'details', 'created_at')
    ordering = ('-created_at',)

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ShopLicense)
class ShopLicenseAdmin(admin.ModelAdmin):
    list_display = ('shop_name', 'license_key', 'api_domain', 'plan', 'status', 'valid_until', 'last_check_at')
    list_filter = ('status', 'plan', 'on_expiry')
    search_fields = ('shop_name', 'owner_name', 'shop_phone', 'license_key', 'api_domain')
    readonly_fields = ('license_key', 'created_at', 'updated_at', 'total_checks', 'last_check_at',
                       'last_check_ip', 'app_version')
    inlines = [ShopLicenseLogInline]
