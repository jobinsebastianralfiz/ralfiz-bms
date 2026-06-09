from django.contrib import admin
from django.contrib.auth.models import User
from .models import InternProfile, Lead, LeadNote, LeadReferenceLink, LeadQuoteAttachment, DailyActivity, Demo, FollowUp, LeadActivity


class LeadNoteInline(admin.TabularInline):
    model = LeadNote
    extra = 0
    fields = ['note', 'created_by', 'created_at']
    readonly_fields = ['created_at']


class LeadReferenceLinkInline(admin.TabularInline):
    model = LeadReferenceLink
    extra = 0
    fields = ['title', 'url', 'created_by', 'created_at']
    readonly_fields = ['created_at']


class LeadQuoteAttachmentInline(admin.TabularInline):
    model = LeadQuoteAttachment
    extra = 0
    fields = ['title', 'file', 'amount', 'notes', 'created_by', 'created_at']
    readonly_fields = ['created_at']


class FollowUpInline(admin.TabularInline):
    model = FollowUp
    extra = 0
    fields = ['follow_up_type', 'scheduled_date', 'status', 'notes', 'created_by']


class DemoInline(admin.TabularInline):
    model = Demo
    extra = 0
    fields = ['scheduled_date', 'status', 'conducted_by', 'closing_probability']


@admin.register(InternProfile)
class InternProfileAdmin(admin.ModelAdmin):
    """DEPRECATED — use Employee model with employment_type='intern' instead."""
    list_display = [
        'user', 'intern_type', 'supervisor', 'default_commission_percentage',
        'status', 'joining_date', 'has_employee_profile', 'created_at'
    ]
    list_filter = ['intern_type', 'status', 'joining_date']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('⚠️ DEPRECATED — Intern data is now managed via Employee model', {
            'fields': ('user', 'intern_type', 'supervisor', 'status', 'joining_date'),
            'description': 'This model is deprecated. Use Employee with employment_type="intern" instead.',
        }),
        ('Commission', {
            'fields': ('default_commission_percentage',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def has_employee_profile(self, obj):
        return hasattr(obj.user, 'employee_profile')
    has_employee_profile.boolean = True
    has_employee_profile.short_description = 'Has Employee Record'


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = [
        'contact_person', 'company_name', 'phone', 'email',
        'status', 'source', 'assigned_to_name', 'closing_probability',
        'next_follow_up_date', 'demo_count', 'created_at'
    ]
    list_filter = ['status', 'source', 'assigned_to', 'created_at']
    search_fields = ['contact_person', 'company_name', 'phone', 'email']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['status']
    inlines = [LeadNoteInline, LeadReferenceLinkInline, LeadQuoteAttachmentInline, FollowUpInline, DemoInline]
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

    def assigned_to_name(self, obj):
        if obj.assigned_to:
            return obj.assigned_to.get_full_name() or obj.assigned_to.username
        return '-'
    assigned_to_name.short_description = 'Assigned To'

    def demo_count(self, obj):
        return obj.demos.count()
    demo_count.short_description = 'Demos'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'assigned_to':
            # Show employees (interns + staff) — not all users
            kwargs['queryset'] = User.objects.filter(
                employee_profile__status='active'
            ).select_related('employee_profile')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

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
        'intern_name', 'date', 'intern_type', 'activity_summary',
        'approval_status', 'approved_by', 'created_at'
    ]
    list_filter = ['intern_type', 'approval_status', 'date', 'intern']
    search_fields = ['intern__username', 'intern__first_name', 'intern__last_name']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['approval_status']
    date_hierarchy = 'date'
    actions = ['approve_selected', 'reject_selected']
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

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'intern':
            kwargs['queryset'] = User.objects.filter(
                employee_profile__employment_type='intern',
                employee_profile__status='active',
            ).select_related('employee_profile')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def intern_name(self, obj):
        return obj.intern.get_full_name() or obj.intern.username
    intern_name.short_description = 'Intern'

    def activity_summary(self, obj):
        if obj.intern_type == 'digital':
            return f"Posts:{obj.social_media_posts} Reels:{obj.reels_created} DMs:{obj.dms_sent} Leads:{obj.digital_leads_generated}"
        return f"Calls:{obj.calls_made} Visits:{obj.visits_done} Demos:{obj.demos_conducted} Leads:{obj.field_leads_generated}"
    activity_summary.short_description = 'Summary'

    @admin.action(description='Approve selected activities')
    def approve_selected(self, request, queryset):
        queryset.update(approval_status='approved', approved_by=request.user)

    @admin.action(description='Reject selected activities')
    def reject_selected(self, request, queryset):
        queryset.update(approval_status='rejected', approved_by=request.user)


@admin.register(Demo)
class DemoAdmin(admin.ModelAdmin):
    list_display = [
        'lead', 'scheduled_date', 'status', 'conducted_by_name',
        'closing_probability', 'location', 'created_at'
    ]
    list_filter = ['status', 'conducted_by', 'scheduled_date']
    search_fields = ['lead__contact_person', 'lead__company_name', 'outcome_notes']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['status']
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

    def conducted_by_name(self, obj):
        if obj.conducted_by:
            return obj.conducted_by.get_full_name() or obj.conducted_by.username
        return '-'
    conducted_by_name.short_description = 'Conducted By'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'conducted_by':
            kwargs['queryset'] = User.objects.filter(
                employee_profile__status='active'
            ).select_related('employee_profile')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(FollowUp)
class FollowUpAdmin(admin.ModelAdmin):
    list_display = ['lead', 'follow_up_type', 'scheduled_date', 'status', 'created_by', 'created_at']
    list_filter = ['follow_up_type', 'status', 'scheduled_date']
    search_fields = ['lead__contact_person', 'lead__company_name', 'notes', 'outcome']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(LeadActivity)
class LeadActivityAdmin(admin.ModelAdmin):
    list_display = ['lead', 'activity_type', 'description', 'created_by', 'created_at']
    list_filter = ['activity_type', 'created_at']
    search_fields = ['lead__contact_person', 'description']
    readonly_fields = ['created_at']
