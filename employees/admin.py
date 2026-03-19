from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Employee, DeviceToken, Attendance, LeaveType, LeaveRequest,
    WorkAssignment, WorkUpdate, Notification, QRCode, ScheduledClass, Payroll,
    CertificateTemplate, Certificate
)
from .utils import generate_face_encoding


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'full_name', 'employment_type', 'role', 'department',
                    'designation', 'status', 'has_face_photo', 'joining_date']
    list_filter = ['employment_type', 'role', 'department', 'status']
    search_fields = ['employee_id', 'user__first_name', 'user__last_name', 'user__username']
    readonly_fields = ['id', 'created_at', 'updated_at', 'face_photo_preview']

    fieldsets = (
        ('Basic Info', {
            'fields': ('id', 'user', 'employee_id', 'employment_type', 'role', 'department',
                       'designation', 'status', 'joining_date'),
        }),
        ('Contact', {
            'fields': ('phone', 'emergency_contact', 'address', 'date_of_birth'),
        }),
        ('Photos & Face Recognition', {
            'fields': ('profile_photo', 'face_photo', 'face_photo_preview'),
            'description': 'Upload a clear face photo for attendance verification. '
                           'Face encoding is auto-generated on save.',
        }),
        ('Compensation', {
            'fields': ('monthly_salary', 'hourly_rate'),
        }),
        ('Intern Fields', {
            'fields': ('intern_type', 'commission_percentage', 'supervisor'),
            'classes': ('collapse',),
            'description': 'Only applicable for interns (employment_type=intern).',
        }),
        ('Office Location', {
            'fields': ('office_latitude', 'office_longitude', 'allowed_radius_meters'),
        }),
        ('Metadata', {
            'fields': ('notes', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def has_face_photo(self, obj):
        return bool(obj.face_photo)
    has_face_photo.boolean = True
    has_face_photo.short_description = 'Face Photo'

    def face_photo_preview(self, obj):
        if obj.face_photo:
            return format_html('<img src="{}" width="150" style="border-radius: 8px;" />', obj.face_photo.url)
        return 'No face photo uploaded'
    face_photo_preview.short_description = 'Face Photo Preview'

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Auto-generate face encoding when face_photo is uploaded/changed
        if obj.face_photo and 'face_photo' in form.changed_data:
            encoding = generate_face_encoding(obj.face_photo.path)
            if encoding:
                obj.face_encoding = encoding
                obj.save(update_fields=['face_encoding'])
            else:
                self.message_user(
                    request,
                    'Warning: No face detected in the uploaded photo. '
                    'Please upload a clear face photo.',
                    level='warning',
                )


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['employee', 'date', 'check_in', 'check_out', 'status',
                    'verification_method', 'face_verified', 'qr_verified']
    list_filter = ['status', 'verification_method', 'date', 'face_verified']
    search_fields = ['employee__employee_id', 'employee__user__first_name']
    date_hierarchy = 'date'


@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'days_allowed', 'is_paid', 'is_active']


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ['employee', 'leave_type', 'start_date', 'end_date',
                    'total_days', 'status', 'created_at']
    list_filter = ['status', 'leave_type']
    search_fields = ['employee__employee_id', 'employee__user__first_name']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(WorkAssignment)
class WorkAssignmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'get_assigned_to', 'assigned_by', 'priority',
                    'status', 'due_date', 'is_overdue', 'has_attachment']
    list_filter = ['priority', 'status']
    search_fields = ['title', 'assigned_to__employee_id']
    readonly_fields = ['id', 'created_at', 'updated_at']
    filter_horizontal = ['assigned_to']

    def get_assigned_to(self, obj):
        return ', '.join(e.full_name for e in obj.assigned_to.all())
    get_assigned_to.short_description = 'Assigned To'

    def has_attachment(self, obj):
        return bool(obj.attachment)
    has_attachment.boolean = True
    has_attachment.short_description = 'Attachment'


@admin.register(WorkUpdate)
class WorkUpdateAdmin(admin.ModelAdmin):
    list_display = ['assignment', 'employee', 'created_at']
    readonly_fields = ['id', 'created_at']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'employee', 'notification_type', 'is_read', 'is_sent', 'created_at']
    list_filter = ['notification_type', 'is_read', 'is_sent']


@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = ['employee', 'platform', 'is_active', 'updated_at']
    list_filter = ['platform', 'is_active']


@admin.register(QRCode)
class QRCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'date', 'is_active', 'expires_at']
    list_filter = ['is_active', 'date']


@admin.register(ScheduledClass)
class ScheduledClassAdmin(admin.ModelAdmin):
    list_display = ['title', 'date', 'start_time', 'end_time', 'instructor', 'status']
    list_filter = ['status', 'date']
    search_fields = ['title', 'instructor']
    filter_horizontal = ['interns']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Payroll)
class PayrollAdmin(admin.ModelAdmin):
    list_display = ['employee', 'month', 'year', 'base_salary', 'leave_deduction',
                    'bonus', 'deductions', 'net_pay', 'status']
    list_filter = ['status', 'year', 'month']
    search_fields = ['employee__employee_id', 'employee__user__first_name']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(CertificateTemplate)
class CertificateTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'certificate_type', 'title', 'is_active', 'updated_at']
    list_filter = ['certificate_type', 'is_active']
    search_fields = ['name', 'title']
    readonly_fields = ['id', 'created_at', 'updated_at']
    fieldsets = (
        (None, {
            'fields': ('id', 'name', 'certificate_type', 'title', 'is_active'),
        }),
        ('Content', {
            'fields': ('body_text', 'wish_text'),
            'description': 'Placeholders: {salutation}, {student_name}, {college_name}, {course_name}, '
                           '{start_date}, {end_date}, {duration_days}, {mode}, {skills}, '
                           '{pronoun}, {pronoun_cap}, {possessive}, {object_pronoun}',
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ['certificate_number', 'student_name', 'certificate_type', 'status', 'course_name',
                    'date_of_issuance', 'download_pdf_link', 'verify_link']
    list_filter = ['certificate_type', 'status', 'mode', 'date_of_issuance']
    search_fields = ['student_name', 'certificate_number', 'course_name', 'college_name']
    readonly_fields = ['id', 'certificate_number', 'verification_id', 'created_at', 'updated_at',
                       'download_pdf_link', 'verify_link']
    fieldsets = (
        ('Certificate Info', {
            'fields': ('id', 'certificate_number', 'verification_id', 'template',
                       'certificate_type', 'status', 'title', 'download_pdf_link', 'verify_link'),
        }),
        ('Student Info', {
            'fields': ('salutation', 'student_name', 'gender', 'college_name'),
        }),
        ('Course Info', {
            'fields': ('course_name', 'start_date', 'end_date', 'duration_days', 'mode'),
        }),
        ('Content', {
            'fields': ('body_text', 'skills', 'wish_text'),
        }),
        ('Issuance', {
            'fields': ('date_of_issuance', 'issued_by', 'created_at', 'updated_at'),
        }),
    )

    def download_pdf_link(self, obj):
        if obj.pk:
            url = f'/api/employees/certificates/{obj.pk}/pdf/?download=1'
            return format_html('<a href="{}" target="_blank">Download PDF</a>', url)
        return '-'
    download_pdf_link.short_description = 'PDF'

    def verify_link(self, obj):
        if obj.pk:
            url = f'/api/employees/certificates/verify/{obj.verification_id}/'
            return format_html('<a href="{}" target="_blank">Verify</a>', url)
        return '-'
    verify_link.short_description = 'Verify'

    def save_model(self, request, obj, form, change):
        if not obj.issued_by:
            obj.issued_by = request.user
        super().save_model(request, obj, form, change)
