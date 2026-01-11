from django.contrib import admin
from .models import (
    Client, Project, Credential, Quote, QuoteItem,
    Invoice, InvoiceItem, Payment, CompanySettings
)


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['name', 'company_name', 'email', 'phone', 'priority', 'is_active', 'created_at']
    list_filter = ['priority', 'is_active', 'created_at']
    search_fields = ['name', 'company_name', 'email', 'phone']
    ordering = ['-created_at']


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'client', 'project_type', 'status', 'estimated_budget', 'deadline', 'created_at']
    list_filter = ['status', 'project_type', 'created_at']
    search_fields = ['name', 'client__name', 'client__company_name']
    ordering = ['-created_at']
    autocomplete_fields = ['client']


@admin.register(Credential)
class CredentialAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'credential_type', 'provider', 'expiry_date', 'is_active']
    list_filter = ['credential_type', 'is_active', 'expiry_date']
    search_fields = ['name', 'provider', 'project__name']
    ordering = ['expiry_date']
    autocomplete_fields = ['project']


class QuoteItemInline(admin.TabularInline):
    model = QuoteItem
    extra = 1


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ['quote_number', 'client', 'title', 'status', 'total_amount', 'issue_date', 'valid_until']
    list_filter = ['status', 'issue_date']
    search_fields = ['quote_number', 'client__name', 'client__company_name', 'title']
    ordering = ['-created_at']
    autocomplete_fields = ['client', 'project']
    inlines = [QuoteItemInline]
    readonly_fields = ['quote_number']


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ['created_at']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'client', 'title', 'status', 'total_amount', 'amount_paid', 'due_date']
    list_filter = ['status', 'issue_date', 'due_date']
    search_fields = ['invoice_number', 'client__name', 'client__company_name', 'title']
    ordering = ['-created_at']
    autocomplete_fields = ['client', 'project', 'quote']
    inlines = [InvoiceItemInline, PaymentInline]
    readonly_fields = ['invoice_number']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'amount', 'payment_date', 'payment_method', 'transaction_id']
    list_filter = ['payment_method', 'payment_date']
    search_fields = ['invoice__invoice_number', 'transaction_id']
    ordering = ['-payment_date']
    autocomplete_fields = ['invoice']


@admin.register(CompanySettings)
class CompanySettingsAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Company Information', {
            'fields': ['company_name', 'tagline', 'email', 'phone', 'address', 'logo']
        }),
        ('Tax Information', {
            'fields': ['gst_number', 'pan_number']
        }),
        ('Bank Details', {
            'fields': ['bank_name', 'bank_account_number', 'bank_ifsc', 'bank_branch', 'upi_id']
        }),
        ('Default Settings', {
            'fields': ['invoice_prefix', 'quote_prefix', 'default_tax_rate', 'invoice_terms', 'quote_terms']
        }),
    ]

    def has_add_permission(self, request):
        # Only allow one instance
        return not CompanySettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


# Customize admin site
admin.site.site_header = 'Ralfiz BMS Administration'
admin.site.site_title = 'Ralfiz BMS'
admin.site.index_title = 'Dashboard'
