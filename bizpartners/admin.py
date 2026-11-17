from django.contrib import admin

from .models import BusinessPartner, JointExpense, JointPayment, JointProject, JointQuote, JointUpdate


class _Inline(admin.TabularInline):
    extra = 0


class QuoteInline(_Inline):
    model = JointQuote


class PaymentInline(_Inline):
    model = JointPayment


class ExpenseInline(_Inline):
    model = JointExpense


@admin.register(BusinessPartner)
class BusinessPartnerAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'name', 'country', 'currency', 'default_partner_share', 'is_active')
    search_fields = ('name', 'company_name', 'email', 'phone')


@admin.register(JointProject)
class JointProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'partner', 'status', 'contract_value', 'partner_share_percent')
    list_filter = ('status', 'partner')
    search_fields = ('title', 'client_name')
    inlines = [QuoteInline, PaymentInline, ExpenseInline]


admin.site.register(JointUpdate)
