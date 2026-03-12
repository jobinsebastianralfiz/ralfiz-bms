from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Employee, DeviceToken, Attendance, LeaveType, LeaveRequest,
    WorkAssignment, WorkUpdate, Notification, QRCode
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        read_only_fields = ['id', 'username']


class EmployeeProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = Employee
        fields = [
            'id', 'user', 'employee_id', 'employment_type', 'department',
            'designation', 'phone', 'emergency_contact', 'address',
            'date_of_birth', 'joining_date', 'status', 'profile_photo',
            'face_photo', 'office_latitude', 'office_longitude',
            'allowed_radius_meters', 'full_name', 'created_at',
        ]
        read_only_fields = [
            'id', 'employee_id', 'employment_type', 'department',
            'designation', 'joining_date', 'status', 'office_latitude',
            'office_longitude', 'allowed_radius_meters', 'created_at',
        ]


class EmployeeListSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = Employee
        fields = ['id', 'employee_id', 'full_name', 'employment_type',
                  'department', 'designation', 'status', 'profile_photo']


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
            'is_overdue', 'notes', 'updates', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'title', 'description', 'priority', 'due_date',
            'assigned_by_name', 'project_name', 'created_at', 'updated_at',
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


class DashboardSerializer(serializers.Serializer):
    employee = EmployeeProfileSerializer()
    today_attendance = AttendanceSerializer(allow_null=True)
    pending_leaves = serializers.IntegerField()
    active_assignments = serializers.IntegerField()
    unread_notifications = serializers.IntegerField()
    recent_assignments = WorkAssignmentSerializer(many=True)
