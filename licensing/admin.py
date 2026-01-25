from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import LicenseKey, License, LicenseActivation


@admin.register(LicenseKey)
class LicenseKeyAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at', 'license_count']
    list_filter = ['is_active']
    readonly_fields = ['id', 'created_at', 'public_key_display']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'is_active')
        }),
        ('Keys', {
            'fields': ('public_key_display', 'private_key'),
            'description': 'NEVER share the private key. The public key should be embedded in your app.'
        }),
        ('Info', {
            'fields': ('id', 'created_at'),
        }),
    )
    
    def license_count(self, obj):
        return obj.licenses.count()
    license_count.short_description = 'Licenses Issued'
    
    def public_key_display(self, obj):
        if obj.public_key:
            return format_html('<pre style="white-space: pre-wrap; word-wrap: break-word; max-width: 600px;">{}</pre>', obj.public_key)
        return '-'
    public_key_display.short_description = 'Public Key (embed in app)'
    
    actions = ['generate_new_keypair']
    
    def generate_new_keypair(self, request, queryset):
        key_pair = LicenseKey.generate_key_pair()
        self.message_user(request, f'Generated new key pair: {key_pair.name} (ID: {key_pair.id})')
    generate_new_keypair.short_description = 'Generate new RSA key pair'


class LicenseActivationInline(admin.TabularInline):
    model = LicenseActivation
    extra = 0
    readonly_fields = ['machine_id', 'machine_name', 'activated_at', 'last_check', 'ip_address']
    can_delete = True


@admin.register(License)
class LicenseAdmin(admin.ModelAdmin):
    list_display = ['customer_name', 'client_name', 'customer_email', 'license_type', 'status_badge', 'valid_until', 'days_left', 'activations_display']
    list_filter = ['license_type', 'status', 'key_pair', 'client']
    search_fields = ['customer_name', 'customer_email', 'customer_company', 'id', 'client__name', 'client__company_name']
    readonly_fields = ['id', 'license_code_display', 'created_at', 'updated_at', 'current_activations']
    date_hierarchy = 'created_at'
    inlines = [LicenseActivationInline]
    autocomplete_fields = ['client']  # For easier client selection

    fieldsets = (
        ('Link to Client', {
            'fields': ('client',),
            'description': 'Link this license to an existing client for RetailEase app configuration.'
        }),
        ('Customer Information', {
            'fields': ('customer_name', 'customer_email', 'customer_company', 'customer_phone')
        }),
        ('License Configuration', {
            'fields': ('key_pair', 'license_type', 'max_activations', 'current_activations')
        }),
        ('Validity', {
            'fields': ('status', 'valid_from', 'valid_until')
        }),
        ('License Code', {
            'fields': ('license_code_display',),
            'description': 'This is the code to provide to the customer.'
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('System Info', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def client_name(self, obj):
        if obj.client:
            return obj.client.company_name or obj.client.name
        return '-'
    client_name.short_description = 'Linked Client'
    
    def status_badge(self, obj):
        colors = {
            'active': '#28a745',
            'expired': '#dc3545',
            'revoked': '#6c757d',
            'suspended': '#ffc107',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def days_left(self, obj):
        if obj.status != 'active':
            return '-'
        days = obj.days_remaining()
        if days <= 0:
            return format_html('<span style="color: red;">Expired</span>')
        elif days <= 30:
            return format_html('<span style="color: orange;">{} days</span>', days)
        return f'{days} days'
    days_left.short_description = 'Days Remaining'
    
    def activations_display(self, obj):
        return f'{obj.current_activations}/{obj.max_activations}'
    activations_display.short_description = 'Activations'
    
    def license_code_display(self, obj):
        if obj.license_code:
            return format_html(
                '<textarea readonly style="width: 100%; height: 100px; font-family: monospace; font-size: 11px;">{}</textarea>'
                '<br><button type="button" onclick="navigator.clipboard.writeText(this.previousElementSibling.previousElementSibling.value); alert(\'Copied!\');" '
                'style="margin-top: 5px; padding: 5px 15px; cursor: pointer;">Copy to Clipboard</button>',
                obj.license_code
            )
        return 'Will be generated on save'
    license_code_display.short_description = 'License Code'
    
    def save_model(self, request, obj, form, change):
        # Regenerate license code if key fields changed
        if change:
            old_obj = License.objects.filter(pk=obj.pk).first()
            if old_obj:
                fields_to_check = ['license_type', 'valid_from', 'valid_until', 'max_activations']
                for field in fields_to_check:
                    if getattr(old_obj, field) != getattr(obj, field):
                        obj.license_code = obj.generate_license_code()
                        break
        super().save_model(request, obj, form, change)
    
    actions = ['mark_expired', 'mark_revoked', 'regenerate_codes']
    
    def mark_expired(self, request, queryset):
        queryset.update(status='expired')
        self.message_user(request, f'{queryset.count()} licenses marked as expired.')
    mark_expired.short_description = 'Mark selected as expired'
    
    def mark_revoked(self, request, queryset):
        queryset.update(status='revoked')
        self.message_user(request, f'{queryset.count()} licenses revoked.')
    mark_revoked.short_description = 'Revoke selected licenses'
    
    def regenerate_codes(self, request, queryset):
        for license in queryset:
            license.license_code = license.generate_license_code()
            license.save()
        self.message_user(request, f'{queryset.count()} license codes regenerated.')
    regenerate_codes.short_description = 'Regenerate license codes'


@admin.register(LicenseActivation)
class LicenseActivationAdmin(admin.ModelAdmin):
    list_display = ['license', 'machine_id_short', 'machine_name', 'activated_at', 'last_check', 'is_active']
    list_filter = ['is_active', 'activated_at']
    search_fields = ['license__customer_name', 'machine_id', 'machine_name']
    readonly_fields = ['license', 'machine_id', 'activated_at', 'last_check', 'ip_address']
    
    def machine_id_short(self, obj):
        return f'{obj.machine_id[:16]}...'
    machine_id_short.short_description = 'Machine ID'
