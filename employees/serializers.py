from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Employee, DeviceToken, Attendance, LeaveType, LeaveRequest,
    WorkAssignment, WorkUpdate, Notification, QRCode, ScheduledClass, Payroll,
    CertificateTemplate, Certificate
)
from crm.models import Lead, LeadNote, DailyActivity, Demo, FollowUp, LeadActivity
from core.models import Client, Project


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        read_only_fields = ['id', 'username']


class EmployeeProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    full_name = serializers.ReadOnlyField()
    profile_photo = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = [
            'id', 'user', 'employee_id', 'employment_type', 'role', 'department',
            'designation', 'phone', 'emergency_contact', 'address',
            'date_of_birth', 'joining_date', 'status', 'profile_photo',
            'face_photo', 'office_latitude', 'office_longitude',
            'allowed_radius_meters', 'work_mode', 'full_name', 'created_at',
        ]

    def get_profile_photo(self, obj):
        photo = obj.profile_photo or obj.face_photo
        if photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(photo.url)
            return photo.url
        return None
        read_only_fields = [
            'id', 'employee_id', 'employment_type', 'department',
            'designation', 'joining_date', 'status', 'office_latitude',
            'office_longitude', 'allowed_radius_meters', 'created_at',
        ]


class EmployeeListSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    profile_photo = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = ['id', 'employee_id', 'full_name', 'employment_type', 'role',
                  'department', 'designation', 'status', 'profile_photo']

    def get_profile_photo(self, obj):
        photo = obj.profile_photo or obj.face_photo
        if photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(photo.url)
            return photo.url
        return None


class DeviceTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceToken
        fields = ['id', 'token', 'platform']


class AttendanceSerializer(serializers.ModelSerializer):
    working_hours = serializers.ReadOnlyField()
    minimum_checkout_time = serializers.SerializerMethodField()
    is_checkout_allowed = serializers.SerializerMethodField()
    seconds_until_eligible = serializers.SerializerMethodField()

    class Meta:
        model = Attendance
        fields = [
            'id', 'date', 'check_in', 'check_out', 'status',
            'verification_method', 'check_in_latitude', 'check_in_longitude',
            'check_out_latitude', 'check_out_longitude', 'face_verified',
            'face_confidence', 'qr_verified', 'working_hours', 'notes',
            'required_hours', 'worked_hours', 'pending_hours',
            'is_force_checkout', 'is_remote',
            'minimum_checkout_time', 'is_checkout_allowed', 'seconds_until_eligible',
        ]
        read_only_fields = ['id', 'date', 'status', 'verification_method']

    def get_minimum_checkout_time(self, obj):
        dt = obj.minimum_checkout_time() if obj.check_in else None
        return dt.isoformat() if dt else None

    def get_is_checkout_allowed(self, obj):
        if not obj.check_in or obj.check_out:
            return False
        return obj.is_checkout_allowed()

    def get_seconds_until_eligible(self, obj):
        if not obj.check_in or obj.check_out:
            return 0
        return obj.seconds_until_eligible()


class CheckInSerializer(serializers.Serializer):
    latitude = serializers.DecimalField(max_digits=10, decimal_places=7, required=False)
    longitude = serializers.DecimalField(max_digits=10, decimal_places=7, required=False)
    face_confidence = serializers.FloatField(required=False, help_text='Face match confidence from ML Kit (0-1)')
    face_photo = serializers.ImageField(required=False, help_text='Selfie for verification')
    qr_code = serializers.CharField(required=False, help_text='Scanned QR code value')
    verification_method = serializers.ChoiceField(
        choices=['face', 'qr', 'location', 'face_qr', 'face_location', 'face_local', 'remote'],
        default='face'
    )
    is_remote = serializers.BooleanField(required=False, default=False,
                                         help_text='Hybrid/remote employees can set true to skip QR + geo-fence')


class CheckOutSerializer(serializers.Serializer):
    latitude = serializers.DecimalField(max_digits=10, decimal_places=7, required=False)
    longitude = serializers.DecimalField(max_digits=10, decimal_places=7, required=False)
    qr_code = serializers.CharField(required=False, help_text='Scanned office QR. Required unless is_remote attendance.')
    force = serializers.BooleanField(required=False, default=False,
                                     help_text='Force check-out before 6h / 4PM. Shortfall recorded as pending_hours.')


class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = ['id', 'name', 'days_allowed', 'is_paid']


class LeaveRequestSerializer(serializers.ModelSerializer):
    leave_type_name = serializers.CharField(source='leave_type.name', read_only=True)
    total_days = serializers.ReadOnlyField()
    reviewed_by_name = serializers.CharField(source='reviewed_by.get_full_name', read_only=True, default='')

    class Meta:
        model = LeaveRequest
        fields = [
            'id', 'leave_type', 'leave_type_name', 'start_date', 'end_date',
            'reason', 'status', 'total_days', 'reviewed_by_name',
            'review_notes', 'reviewed_at', 'created_at',
        ]
        read_only_fields = ['id', 'status', 'reviewed_by_name', 'review_notes', 'reviewed_at', 'created_at']


class LeaveRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveRequest
        fields = ['leave_type', 'start_date', 'end_date', 'reason']

    def validate(self, data):
        if data['start_date'] > data['end_date']:
            raise serializers.ValidationError('End date must be after start date.')
        return data


class WorkAssignmentSerializer(serializers.ModelSerializer):
    is_overdue = serializers.ReadOnlyField()
    assigned_by_name = serializers.CharField(source='assigned_by.get_full_name', read_only=True, default='')
    project_name = serializers.CharField(source='project.name', read_only=True, default='')
    assigned_to_names = serializers.SerializerMethodField()
    updates = serializers.SerializerMethodField()

    class Meta:
        model = WorkAssignment
        fields = [
            'id', 'title', 'description', 'priority', 'status',
            'due_date', 'completed_at', 'assigned_by_name', 'project_name',
            'assigned_to_names', 'is_overdue', 'attachment', 'notes', 'confidentiality_disclaimer', 'updates', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'title', 'description', 'priority', 'due_date',
            'assigned_by_name', 'project_name', 'attachment', 'created_at', 'updated_at',
        ]

    def get_assigned_to_names(self, obj):
        return [{'id': str(e.pk), 'name': e.full_name, 'employee_id': e.employee_id} for e in obj.assigned_to.all()]

    def get_updates(self, obj):
        updates = obj.updates.all()[:10]
        return WorkUpdateSerializer(updates, many=True).data


class WorkUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkUpdate
        fields = ['id', 'message', 'attachment', 'created_at']
        read_only_fields = ['id', 'created_at']


class WorkStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['in_progress', 'on_hold', 'completed'])
    message = serializers.CharField(required=False, allow_blank=True)
    attachment = serializers.FileField(required=False)


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'body', 'notification_type', 'data',
                  'is_read', 'created_at']
        read_only_fields = ['id', 'title', 'body', 'notification_type', 'data', 'created_at']


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=6)


class ClassParticipantSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    profile_photo = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = ['id', 'employee_id', 'full_name', 'department', 'designation', 'profile_photo']

    def get_profile_photo(self, obj):
        photo = obj.profile_photo or obj.face_photo
        if photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(photo.url)
            return photo.url
        return None


class ScheduledClassSerializer(serializers.ModelSerializer):
    is_upcoming = serializers.ReadOnlyField()
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True, default='')
    intern_count = serializers.SerializerMethodField()
    participants = serializers.SerializerMethodField()

    class Meta:
        model = ScheduledClass
        fields = [
            'id', 'title', 'description', 'date', 'start_time', 'end_time',
            'instructor', 'location', 'status', 'attachment', 'notes',
            'is_upcoming', 'created_by_name', 'intern_count', 'participants',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_by_name', 'created_at', 'updated_at']

    def get_intern_count(self, obj):
        return obj.interns.count()

    def get_participants(self, obj):
        interns = obj.interns.all()
        if not interns.exists():
            # Empty means all interns
            interns = Employee.objects.filter(employment_type='intern', status='active')
        return ClassParticipantSerializer(interns, many=True, context=self.context).data


class PayrollSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    employee_id_display = serializers.CharField(source='employee.employee_id', read_only=True)
    month_name = serializers.SerializerMethodField()

    class Meta:
        model = Payroll
        fields = [
            'id', 'employee', 'employee_name', 'employee_id_display',
            'month', 'year', 'month_name', 'base_salary',
            'working_days', 'days_present', 'days_absent',
            'paid_leave_days', 'unpaid_leave_days', 'leave_deduction',
            'bonus', 'deductions', 'net_pay', 'status', 'notes',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'employee_name', 'employee_id_display', 'created_at', 'updated_at']

    def get_month_name(self, obj):
        import calendar
        return calendar.month_name[obj.month]


class DashboardSerializer(serializers.Serializer):
    employee = EmployeeProfileSerializer()
    today_attendance = AttendanceSerializer(allow_null=True)
    pending_leaves = serializers.IntegerField()
    active_assignments = serializers.IntegerField()
    unread_notifications = serializers.IntegerField()
    recent_assignments = WorkAssignmentSerializer(many=True)


# ---- Owner/Partner Serializers ----

class OwnerClientSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    company_name = serializers.CharField()
    email = serializers.EmailField()
    phone = serializers.CharField()
    is_active = serializers.BooleanField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    pending_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    project_count = serializers.IntegerField()


class OwnerProjectSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    client_name = serializers.CharField()
    status = serializers.CharField()
    project_type = serializers.CharField()
    estimated_budget = serializers.DecimalField(max_digits=12, decimal_places=2)
    final_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    invoiced_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    paid_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    start_date = serializers.DateField()
    deadline = serializers.DateField()


class CertificateTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CertificateTemplate
        fields = ['id', 'name', 'certificate_type', 'title', 'body_text', 'wish_text', 'is_active']


class CertificateSerializer(serializers.ModelSerializer):
    verification_url = serializers.SerializerMethodField()
    pdf_url = serializers.SerializerMethodField()
    template_name = serializers.CharField(source='template.name', read_only=True, default=None)

    class Meta:
        model = Certificate
        fields = [
            'id', 'certificate_number', 'verification_id', 'template', 'template_name',
            'certificate_type', 'status', 'title',
            'salutation', 'student_name', 'gender', 'college_name',
            'course_name', 'start_date', 'end_date', 'duration_days', 'mode',
            'body_text', 'skills', 'wish_text',
            'date_of_issuance', 'verification_url', 'pdf_url',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'certificate_number', 'verification_id', 'created_at', 'updated_at']

    def validate(self, data):
        instance = self.instance
        if instance and instance.status == 'published':
            # Published certificates can only change status to cancelled
            allowed_fields = {'status'}
            changed_fields = set(data.keys()) - allowed_fields
            if changed_fields:
                if data.get('status') == 'cancelled':
                    # Allow cancelling - ignore other fields
                    return {'status': 'cancelled'}
                raise serializers.ValidationError('Published certificates cannot be edited. You can only cancel them.')
        if instance and instance.status == 'cancelled':
            raise serializers.ValidationError('Cancelled certificates cannot be edited.')
        return data

    def get_verification_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/api/employees/certificates/verify/{obj.verification_id}/')
        return None

    def get_pdf_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/api/employees/certificates/{obj.id}/pdf/')
        return None


class CertificateCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certificate
        fields = [
            'template', 'certificate_type', 'status', 'title',
            'salutation', 'student_name', 'gender', 'college_name',
            'course_name', 'start_date', 'end_date', 'duration_days', 'mode',
            'body_text', 'skills', 'wish_text', 'date_of_issuance',
        ]

    def validate(self, data):
        # If template is provided, copy body_text/wish_text/title/type from template
        template = data.get('template')
        if template:
            if not data.get('body_text'):
                data['body_text'] = template.body_text
            if not data.get('wish_text'):
                data['wish_text'] = template.wish_text
            if not data.get('title'):
                data['title'] = template.title
            if not data.get('certificate_type'):
                data['certificate_type'] = template.certificate_type
        return data


class OwnerAttendanceEmployeeSerializer(serializers.Serializer):
    employee_id = serializers.CharField()
    name = serializers.CharField()
    department = serializers.CharField()
    records = AttendanceSerializer(many=True)


# ---- CRM Serializers ----

class LeadNoteSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True, default='')

    class Meta:
        model = LeadNote
        fields = ['id', 'note', 'created_by_name', 'created_at']
        read_only_fields = ['id', 'created_by_name', 'created_at']


class FollowUpSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True, default='')
    type_display = serializers.CharField(source='get_follow_up_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = FollowUp
        fields = [
            'id', 'lead', 'follow_up_type', 'type_display', 'scheduled_date',
            'status', 'status_display', 'notes', 'outcome', 'is_overdue',
            'created_by_name', 'completed_at', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'lead', 'created_by_name', 'created_at', 'updated_at']


class FollowUpCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FollowUp
        fields = ['follow_up_type', 'scheduled_date', 'notes']


class LeadActivitySerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True, default='')
    type_display = serializers.CharField(source='get_activity_type_display', read_only=True)

    class Meta:
        model = LeadActivity
        fields = ['id', 'activity_type', 'type_display', 'description', 'metadata', 'created_by_name', 'created_at']
        read_only_fields = ['id', 'created_at']


class LeadSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True, default='')
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True, default='')
    notes_list = LeadNoteSerializer(source='lead_notes', many=True, read_only=True)
    demo_count = serializers.SerializerMethodField()
    upcoming_follow_ups = serializers.SerializerMethodField()
    overdue_follow_ups = serializers.SerializerMethodField()
    last_activity = serializers.SerializerMethodField()
    client_id = serializers.UUIDField(source='client.id', read_only=True, default=None)
    client_name = serializers.CharField(source='client.name', read_only=True, default='')
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    source_display = serializers.CharField(source='get_source_display', read_only=True)
    lost_reason_display = serializers.CharField(source='get_lost_reason_display', read_only=True, default='')

    class Meta:
        model = Lead
        fields = [
            'id', 'contact_person', 'company_name', 'phone', 'email',
            'status', 'status_display', 'source', 'source_display',
            'assigned_to', 'assigned_to_name',
            'next_follow_up_date', 'closing_probability', 'notes',
            'lost_reason', 'lost_reason_display',
            'created_by_name', 'notes_list', 'demo_count',
            'upcoming_follow_ups', 'overdue_follow_ups', 'last_activity',
            'client_id', 'client_name',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'status_display', 'source_display', 'lost_reason_display',
            'created_by_name', 'client_id', 'client_name', 'created_at', 'updated_at',
        ]

    def get_demo_count(self, obj):
        return obj.demos.count()

    def get_upcoming_follow_ups(self, obj):
        from django.utils import timezone
        fups = obj.follow_ups.filter(status='scheduled', scheduled_date__gte=timezone.now()).order_by('scheduled_date')[:3]
        return FollowUpSerializer(fups, many=True).data

    def get_overdue_follow_ups(self, obj):
        from django.utils import timezone
        return obj.follow_ups.filter(status='scheduled', scheduled_date__lt=timezone.now()).count()

    def get_last_activity(self, obj):
        activity = obj.activities.first()
        if activity:
            return {'type': activity.activity_type, 'description': activity.description, 'created_at': activity.created_at}
        return None


class LeadCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = [
            'contact_person', 'company_name', 'phone', 'email',
            'status', 'source', 'next_follow_up_date', 'closing_probability',
            'notes', 'lost_reason',
        ]


class DailyActivitySerializer(serializers.ModelSerializer):
    intern_name = serializers.CharField(source='intern.get_full_name', read_only=True, default='')
    is_editable = serializers.ReadOnlyField()

    class Meta:
        model = DailyActivity
        fields = [
            'id', 'intern_name', 'date', 'intern_type',
            'social_media_posts', 'reels_created', 'dms_sent', 'digital_leads_generated',
            'calls_made', 'visits_done', 'demos_conducted', 'field_leads_generated',
            'remarks', 'approval_status', 'is_editable',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'intern_name', 'approval_status', 'created_at', 'updated_at']


class DailyActivityCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyActivity
        fields = [
            'date', 'social_media_posts', 'reels_created', 'dms_sent',
            'digital_leads_generated', 'calls_made', 'visits_done',
            'demos_conducted', 'field_leads_generated', 'remarks',
        ]


class DemoSerializer(serializers.ModelSerializer):
    lead_name = serializers.CharField(source='lead.contact_person', read_only=True, default='')
    lead_company = serializers.CharField(source='lead.company_name', read_only=True, default='')
    conducted_by_name = serializers.CharField(source='conducted_by.get_full_name', read_only=True, default='')

    class Meta:
        model = Demo
        fields = [
            'id', 'lead', 'lead_name', 'lead_company',
            'scheduled_date', 'status', 'conducted_by', 'conducted_by_name',
            'closing_probability', 'outcome_notes', 'location',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'conducted_by', 'created_at', 'updated_at']


class DemoCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Demo
        fields = ['lead', 'scheduled_date', 'closing_probability', 'location', 'outcome_notes']

    def validate_lead(self, value):
        user = self.context['request'].user
        employee = getattr(user, 'employee_profile', None)
        # Interns can only schedule demos for their assigned leads
        if employee and employee.role == 'intern':
            if value.assigned_to != user:
                raise serializers.ValidationError('You can only schedule demos for leads assigned to you.')
        return value


class CRMDashboardSerializer(serializers.Serializer):
    total_leads = serializers.IntegerField()
    new_leads = serializers.IntegerField()
    converted_leads = serializers.IntegerField()
    upcoming_demos = serializers.IntegerField()
    pending_activities = serializers.IntegerField()
    recent_leads = LeadSerializer(many=True)
    upcoming_demos_list = DemoSerializer(many=True)
    active_assignments = WorkAssignmentSerializer(many=True)
