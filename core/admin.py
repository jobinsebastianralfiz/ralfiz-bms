from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import (
    Client, Project, Credential, Quote, QuoteItem,
    Invoice, InvoiceItem, Payment, CompanySettings,
    Expense, TeamMember, Task, TimeEntry, ActivityLog, Document
)
from licensing.models import License


class ClientLicenseInline(admin.StackedInline):
    """Inline to manage licenses from the Client detail page"""
    model = License
    extra = 0
    can_delete = False
    show_change_link = True
    verbose_name = "License"
    verbose_name_plural = "Licenses"

    fields = [
        'license_status_display',
        ('license_type', 'status'),
        ('valid_from', 'valid_until'),
        ('billing_cycle', 'auto_renew'),
        ('current_activations', 'max_activations'),
        'renewal_info',
    ]
    readonly_fields = ['license_status_display', 'current_activations', 'renewal_info']

    def license_status_display(self, obj):
        """Show license status with visual indicators"""
        if not obj.pk:
            return '-'

        days = obj.days_remaining()
        valid_until = obj.valid_until.strftime('%Y-%m-%d') if obj.valid_until else '-'

        if obj.status == 'revoked':
            return format_html(
                '<div style="padding: 10px; background: #f8d7da; border-radius: 5px; margin-bottom: 10px;">'
                '<span style="color: #721c24; font-size: 14px;">&#10006; <strong>REVOKED</strong></span>'
                '</div>'
            )
        elif obj.status == 'suspended':
            return format_html(
                '<div style="padding: 10px; background: #fff3cd; border-radius: 5px; margin-bottom: 10px;">'
                '<span style="color: #856404; font-size: 14px;">&#9888; <strong>SUSPENDED</strong></span>'
                '</div>'
            )
        elif days <= 0:
            return format_html(
                '<div style="padding: 10px; background: #f8d7da; border-radius: 5px; margin-bottom: 10px;">'
                '<span style="color: #721c24; font-size: 14px;">&#10006; <strong>EXPIRED</strong></span> '
                '<span style="color: #666;">(expired on {})</span><br>'
                '<small style="color: #721c24;">Update the "Valid until" date below and save to renew.</small>'
                '</div>',
                valid_until
            )
        elif days <= 7:
            return format_html(
                '<div style="padding: 10px; background: #f8d7da; border-radius: 5px; margin-bottom: 10px;">'
                '<span style="color: #721c24; font-size: 14px;">&#9888; <strong>{} days remaining</strong></span> '
                '<span style="color: #666;">(expires {})</span><br>'
                '<small style="color: #721c24;">License expiring soon! Update "Valid until" date to extend.</small>'
                '</div>',
                days, valid_until
            )
        elif days <= 30:
            return format_html(
                '<div style="padding: 10px; background: #fff3cd; border-radius: 5px; margin-bottom: 10px;">'
                '<span style="color: #856404; font-size: 14px;">&#9888; <strong>{} days remaining</strong></span> '
                '<span style="color: #666;">(expires {})</span>'
                '</div>',
                days, valid_until
            )
        else:
            return format_html(
                '<div style="padding: 10px; background: #d4edda; border-radius: 5px; margin-bottom: 10px;">'
                '<span style="color: #155724; font-size: 14px;">&#10004; <strong>{} days remaining</strong></span> '
                '<span style="color: #666;">(expires {})</span>'
                '</div>',
                days, valid_until
            )
    license_status_display.short_description = 'Status Overview'

    def renewal_info(self, obj):
        """Show renewal history"""
        if not obj.pk:
            return '-'

        info_parts = []
        if obj.renewal_count > 0:
            info_parts.append(f'Renewed {obj.renewal_count} time(s)')
        if obj.last_renewed_at:
            info_parts.append(f'Last renewed: {obj.last_renewed_at.strftime("%Y-%m-%d %H:%M")}')

        if info_parts:
            return ' | '.join(info_parts)
        return 'Never renewed'
    renewal_info.short_description = 'Renewal History'


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['name', 'company_name', 'email', 'phone', 'priority', 'license_status', 'is_active', 'created_at']
    list_filter = ['priority', 'is_active', 'created_at']
    search_fields = ['name', 'company_name', 'email', 'phone']
    ordering = ['-created_at']
    inlines = [ClientLicenseInline]

    def license_status(self, obj):
        """Show license status in list view"""
        license = obj.licenses.first()
        if not license:
            return format_html('<span style="color: #999;">No License</span>')

        days = license.days_remaining()
        if license.status in ['revoked', 'suspended']:
            return format_html('<span style="color: #6c757d;">{}</span>', license.status.title())
        elif days <= 0:
            return format_html('<span style="color: #dc3545; font-weight: bold;">Expired</span>')
        elif days <= 7:
            return format_html('<span style="color: #dc3545;">{} days</span>', days)
        elif days <= 30:
            return format_html('<span style="color: #ffc107;">{} days</span>', days)
        else:
            return format_html('<span style="color: #28a745;">{} days</span>', days)
    license_status.short_description = 'License'

    def save_formset(self, request, form, formset, change):
        """Handle license updates including renewal tracking"""
        if formset.model == License:
            instances = formset.save(commit=False)
            for instance in instances:
                # Check if valid_until was extended (renewal)
                if instance.pk:
                    old_instance = License.objects.get(pk=instance.pk)
                    if instance.valid_until > old_instance.valid_until:
                        # License was extended - track as renewal
                        instance.renewal_count += 1
                        instance.last_renewed_at = timezone.now()
                        instance.status = 'active'  # Reactivate if was expired

                        # Add renewal note
                        renewal_note = f"\n[{timezone.now().isoformat()}] Renewed via admin from {old_instance.valid_until.date()} to {instance.valid_until.date()}"
                        instance.notes = (instance.notes or '') + renewal_note

                        # Regenerate license code with new expiry
                        instance.license_code = instance.generate_license_code()

                instance.save()

            for obj in formset.deleted_objects:
                obj.delete()
        else:
            formset.save()


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
