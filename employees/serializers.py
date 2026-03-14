from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Employee, DeviceToken, Attendance, LeaveType, LeaveRequest,
    WorkAssignment, WorkUpdate, Notification, QRCode, ScheduledClass, Payroll
)


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
            'allowed_radius_meters', 'full_name', 'created_at',
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

    class Meta:
        model = Attendance
        fields = [
            'id', 'date', 'check_in', 'check_out', 'status',
            'verification_method', 'check_in_latitude', 'check_in_longitude',
            'check_out_latitude', 'check_out_longitude', 'face_verified',
            'face_confidence', 'qr_verified', 'working_hours', 'notes',
        ]
        read_only_fields = ['id', 'date', 'status', 'verification_method']


class CheckInSerializer(serializers.Serializer):
    latitude = serializers.DecimalField(max_digits=10, decimal_places=7, required=False)
    longitude = serializers.DecimalField(max_digits=10, decimal_places=7, required=False)
    face_confidence = serializers.FloatField(required=False, help_text='Face match confidence from ML Kit (0-1)')
    face_photo = serializers.ImageField(required=False, help_text='Selfie for verification')
    qr_code = serializers.CharField(required=False, help_text='Scanned QR code value')
    verification_method = serializers.ChoiceField(
        choices=['face', 'qr', 'location', 'face_qr', 'face_location', 'face_local'],
        default='face'
    )


class CheckOutSerializer(serializers.Serializer):
    latitude = serializers.DecimalField(max_digits=10, decimal_places=7, required=False)
    longitude = serializers.DecimalField(max_digits=10, decimal_places=7, required=False)


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
    updates = serializers.SerializerMethodField()

    class Meta:
        model = WorkAssignment
        fields = [
            'id', 'title', 'description', 'priority', 'status',
            'due_date', 'completed_at', 'assigned_by_name', 'project_name',
            'is_overdue', 'attachment', 'notes', 'updates', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'title', 'description', 'priority', 'due_date',
            'assigned_by_name', 'project_name', 'attachment', 'created_at', 'updated_at',
        ]

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


class OwnerAttendanceEmployeeSerializer(serializers.Serializer):
    employee_id = serializers.CharField()
    name = serializers.CharField()
    department = serializers.CharField()
    records = AttendanceSerializer(many=True)
