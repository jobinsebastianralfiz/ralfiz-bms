from django.contrib import admin
from .models import (
    Client, Project, Credential, Quote, QuoteItem,
    Invoice, InvoiceItem, Payment, CompanySettings,
    Expense, TeamMember, Task, TimeEntry, ActivityLog, Document
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
            'fields': ['gst_number', 'pan_number', 'hsn_code']
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


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['vendor', 'category', 'amount', 'date', 'project', 'is_billable', 'payment_method']
    list_filter = ['category', 'is_billable', 'payment_method', 'date']
    search_fields = ['vendor', 'description', 'project__name']
    ordering = ['-date']
    autocomplete_fields = ['project']


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ['name', 'role', 'email', 'phone', 'hourly_rate', 'is_active']
    list_filter = ['role', 'is_active']
    search_fields = ['name', 'email']
    ordering = ['name']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'assigned_to', 'status', 'priority', 'due_date']
    list_filter = ['status', 'priority', 'due_date']
    search_fields = ['title', 'description', 'project__name']
    ordering = ['-created_at']
    autocomplete_fields = ['project', 'assigned_to']


@admin.register(TimeEntry)
class TimeEntryAdmin(admin.ModelAdmin):
    list_display = ['project', 'task', 'user', 'hours', 'date', 'is_billable']
    list_filter = ['is_billable', 'date', 'project']
    search_fields = ['description', 'project__name', 'task__title']
    ordering = ['-date']
    autocomplete_fields = ['project', 'task', 'user']


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'model_name', 'object_repr', 'timestamp', 'ip_address']
    list_filter = ['action', 'model_name', 'timestamp']
    search_fields = ['object_repr', 'user__username']
    ordering = ['-timestamp']
    readonly_fields = ['user', 'action', 'model_name', 'object_id', 'object_repr', 'changes', 'ip_address', 'timestamp']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['name', 'content_type', 'uploaded_by', 'created_at']
    list_filter = ['content_type', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['-created_at']


# Customize admin site
admin.site.site_header = 'Ralfiz BMS Administration'
admin.site.site_title = 'Ralfiz BMS'
admin.site.index_title = 'Dashboard'
