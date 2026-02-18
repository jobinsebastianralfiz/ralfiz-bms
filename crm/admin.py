from django.contrib import admin
from .models import InternProfile, Lead, LeadNote, DailyActivity, Demo


class LeadNoteInline(admin.TabularInline):
    model = LeadNote
    extra = 0
    fields = ['note', 'created_by', 'created_at']
    readonly_fields = ['created_at']


class DemoInline(admin.TabularInline):
    model = Demo
    extra = 0
    fields = ['scheduled_date', 'status', 'conducted_by', 'closing_probability']


@admin.register(InternProfile)
class InternProfileAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'intern_type', 'supervisor', 'default_commission_percentage',
        'status', 'joining_date', 'created_at'
    ]
    list_filter = ['intern_type', 'status', 'joining_date']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Intern Information', {
            'fields': ('user', 'intern_type', 'supervisor', 'status', 'joining_date')
        }),
        ('Commission', {
            'fields': ('default_commission_percentage',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = [
        'contact_person', 'company_name', 'phone', 'email',
        'status', 'source', 'assigned_to', 'closing_probability', 'created_at'
    ]
    list_filter = ['status', 'source', 'assigned_to', 'created_at']
    search_fields = ['contact_person', 'company_name', 'phone', 'email']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [LeadNoteInline, DemoInline]
    fieldsets = (
        ('Contact Information', {
            'fields': ('contact_person', 'company_name', 'phone', 'email')
        }),
        ('Lead Details', {
            'fields': ('status', 'source', 'closing_probability', 'notes')
        }),
        ('Assignment & Follow-up', {
            'fields': ('assigned_to', 'next_follow_up_date')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(LeadNote)
class LeadNoteAdmin(admin.ModelAdmin):
    list_display = ['lead', 'created_by', 'created_at']
    list_filter = ['created_at', 'created_by']
    search_fields = ['note', 'lead__contact_person']
    readonly_fields = ['created_at']


@admin.register(DailyActivity)
class DailyActivityAdmin(admin.ModelAdmin):
    list_display = [
        'intern', 'date', 'intern_type', 'approval_status', 'approved_by', 'created_at'
    ]
    list_filter = ['intern_type', 'approval_status', 'date', 'intern']
    search_fields = ['intern__username', 'intern__first_name', 'intern__last_name']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Info', {
            'fields': ('intern', 'date', 'intern_type')
        }),
        ('Digital Marketing Metrics', {
            'fields': ('social_media_posts', 'reels_created', 'dms_sent', 'digital_leads_generated'),
            'classes': ('collapse',),
        }),
        ('Field Marketing Metrics', {
            'fields': ('calls_made', 'visits_done', 'demos_conducted', 'field_leads_generated'),
            'classes': ('collapse',),
        }),
        ('Approval', {
            'fields': ('remarks', 'approval_status', 'approved_by')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Demo)
class DemoAdmin(admin.ModelAdmin):
    list_display = [
        'lead', 'scheduled_date', 'status', 'conducted_by',
        'closing_probability', 'location', 'created_at'
    ]
    list_filter = ['status', 'conducted_by', 'scheduled_date']
    search_fields = ['lead__contact_person', 'lead__company_name', 'outcome_notes']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Demo Information', {
            'fields': ('lead', 'scheduled_date', 'status', 'conducted_by', 'location')
        }),
        ('Outcome', {
            'fields': ('closing_probability', 'outcome_notes')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
