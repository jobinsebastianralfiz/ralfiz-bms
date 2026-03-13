from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Employee, DeviceToken, Attendance, LeaveType, LeaveRequest,
    WorkAssignment, WorkUpdate, Notification, QRCode, ScheduledClass
)
from .utils import generate_face_encoding


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'full_name', 'employment_type', 'department',
                    'designation', 'status', 'has_face_photo', 'joining_date']
    list_filter = ['employment_type', 'department', 'status']
    search_fields = ['employee_id', 'user__first_name', 'user__last_name', 'user__username']
    readonly_fields = ['id', 'created_at', 'updated_at', 'face_photo_preview']

    fieldsets = (
        ('Basic Info', {
            'fields': ('id', 'user', 'employee_id', 'employment_type', 'department',
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
    list_display = ['title', 'assigned_to', 'assigned_by', 'priority',
                    'status', 'due_date', 'is_overdue', 'has_attachment']
    list_filter = ['priority', 'status']
    search_fields = ['title', 'assigned_to__employee_id']
    readonly_fields = ['id', 'created_at', 'updated_at']

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
