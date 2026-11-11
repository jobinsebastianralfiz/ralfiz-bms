from django.contrib import admin

from .models import XPEntry, XPPayout, XPSettings


@admin.register(XPSettings)
class XPSettingsAdmin(admin.ModelAdmin):
    list_display = ('rate_paise', 'monthly_cap', 'include_employees', 'updated_at')


@admin.register(XPEntry)
class XPEntryAdmin(admin.ModelAdmin):
    list_display = ('employee', 'xp', 'kind', 'status', 'source_kind', 'title', 'created_at')
    list_filter = ('kind', 'status', 'source_kind')
    search_fields = ('employee__employee_id', 'employee__user__first_name', 'title')

    # The ledger is append-only: fix mistakes with a correcting row from HR > XP Wallets.
    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(XPPayout)
class XPPayoutAdmin(admin.ModelAdmin):
    list_display = ('employee', 'xp', 'amount', 'method', 'status', 'paid_on')
    list_filter = ('method', 'status')

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
