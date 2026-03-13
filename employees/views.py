import uuid
import math
from datetime import date

from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from .models import (
    Employee, DeviceToken, Attendance, LeaveType, LeaveRequest,
    WorkAssignment, WorkUpdate, Notification, QRCode
)
from .serializers import (
    EmployeeProfileSerializer, EmployeeListSerializer,
    DeviceTokenSerializer, AttendanceSerializer,
    CheckInSerializer, CheckOutSerializer,
    LeaveTypeSerializer, LeaveRequestSerializer, LeaveRequestCreateSerializer,
    WorkAssignmentSerializer, WorkUpdateSerializer, WorkStatusUpdateSerializer,
    NotificationSerializer, ChangePasswordSerializer,
)
from django.shortcuts import render

from .utils import send_push_notification, compare_faces, generate_face_encoding


def get_employee(user):
    """Get employee profile for the authenticated user"""
    try:
        return Employee.objects.get(user=user, status='active')
    except Employee.DoesNotExist:
        return None


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two GPS coordinates in meters"""
    R = 6371000  # Earth's radius in meters
    phi1, phi2 = math.radians(float(lat1)), math.radians(float(lat2))
    dphi = math.radians(float(lat2) - float(lat1))
    dlambda = math.radians(float(lon2) - float(lon1))
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ============================================================
# Employee App APIs (for mobile app)
# ============================================================

@extend_schema(tags=['Profile'])
class DashboardView(APIView):
    """Employee dashboard - overview of today's status"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        employee = get_employee(request.user)
        if not employee:
            return Response({'error': 'Employee profile not found'}, status=status.HTTP_404_NOT_FOUND)

        today = date.today()
        today_attendance = Attendance.objects.filter(employee=employee, date=today).first()

        data = {
            'employee': EmployeeProfileSerializer(employee, context={'request': request}).data,
            'today_attendance': AttendanceSerializer(today_attendance).data if today_attendance else None,
            'pending_leaves': LeaveRequest.objects.filter(employee=employee, status='pending').count(),
            'active_assignments': WorkAssignment.objects.filter(
                assigned_to=employee, status__in=['assigned', 'in_progress']
            ).count(),
            'unread_notifications': Notification.objects.filter(employee=employee, is_read=False).count(),
            'recent_assignments': WorkAssignmentSerializer(
                WorkAssignment.objects.filter(assigned_to=employee).exclude(status='cancelled')[:5],
                many=True
            ).data,
        }
        return Response(data)


@extend_schema(tags=['Profile'])
class ProfileView(APIView):
    """View and update own profile"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        employee = get_employee(request.user)
        if not employee:
            return Response({'error': 'Employee profile not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(EmployeeProfileSerializer(employee, context={'request': request}).data)

    def patch(self, request):
        employee = get_employee(request.user)
        if not employee:
            return Response({'error': 'Employee profile not found'}, status=status.HTTP_404_NOT_FOUND)

        allowed_fields = ['phone', 'emergency_contact', 'address', 'profile_photo']
        data = {k: v for k, v in request.data.items() if k in allowed_fields}

        serializer = EmployeeProfileSerializer(employee, data=data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=['Profile'])
class FacePhotoUploadView(APIView):
    """Upload/update reference face photo for face recognition. The app uses Google ML Kit on-device for matching."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        employee = get_employee(request.user)
        if not employee:
            return Response({'error': 'Employee profile not found'}, status=status.HTTP_404_NOT_FOUND)

        face_photo = request.FILES.get('face_photo')
        face_encoding = request.data.get('face_encoding')

        if not face_photo:
            return Response({'error': 'face_photo is required'}, status=status.HTTP_400_BAD_REQUEST)

        employee.face_photo = face_photo
        employee.save()

        # Auto-generate face encoding from the uploaded photo
        encoding = generate_face_encoding(employee.face_photo.path)
        if encoding is None:
            employee.face_photo = None
            employee.save()
            return Response({'error': 'No face detected in the uploaded photo. Please upload a clear face photo.'},
                            status=status.HTTP_400_BAD_REQUEST)
        employee.face_encoding = encoding
        employee.save()

        return Response({
            'message': 'Face photo updated successfully',
            'face_photo': request.build_absolute_uri(employee.face_photo.url) if employee.face_photo else None,
        })

    def get(self, request):
        """Get reference face photo URL and encoding for on-device matching"""
        employee = get_employee(request.user)
        if not employee:
            return Response({'error': 'Employee profile not found'}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'face_photo': request.build_absolute_uri(employee.face_photo.url) if employee.face_photo else None,
            'face_encoding': employee.face_encoding,
            'has_face_registered': bool(employee.face_photo),
        })


@extend_schema(tags=['Auth'])
class ChangePasswordView(APIView):
    """Change password"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if not request.user.check_password(serializer.validated_data['old_password']):
            return Response({'error': 'Current password is incorrect'}, status=status.HTTP_400_BAD_REQUEST)

        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response({'message': 'Password changed successfully'})


# ---- Attendance APIs ----

@extend_schema(tags=['Attendance'], request=CheckInSerializer)
class CheckInView(APIView):
    """Mark attendance check-in with face/QR/location verification."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f'Check-in request from {request.user.username}, method: {request.data.get("verification_method")}, '
                     f'has_face_photo: {"face_photo" in request.FILES}, has_qr: {bool(request.data.get("qr_code"))}, '
                     f'has_lat: {bool(request.data.get("latitude"))}')

        employee = get_employee(request.user)
        if not employee:
            return Response({'error': 'Employee profile not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = CheckInSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        today = date.today()
        if Attendance.objects.filter(employee=employee, date=today).exists():
            return Response({'error': 'Already checked in today'}, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        method = data.get('verification_method', 'face')

        # Verify location - required for all methods to prevent remote check-in
        location_verified = False
        if not data.get('latitude') or not data.get('longitude'):
            return Response({'error': 'Location is required for check-in.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if employee.office_latitude and employee.office_longitude:
            distance = haversine_distance(
                data['latitude'], data['longitude'],
                employee.office_latitude, employee.office_longitude
            )
            location_verified = distance <= employee.allowed_radius_meters
            if not location_verified:
                return Response({
                    'error': f'You are {int(distance)}m away from office. Must be within {employee.allowed_radius_meters}m.',
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            # No office location configured for this employee, skip location check
            location_verified = True

        # Verify QR code - supports static office QR sticker or daily QR
        qr_verified = False
        if data.get('qr_code') and method in ['qr', 'face_qr', 'face_local']:
            # Check static office QR sticker
            from .models import OfficeConfig
            if OfficeConfig.objects.filter(qr_code=data['qr_code']).exists():
                qr_verified = True
            else:
                # Check daily QR codes
                qr = QRCode.objects.filter(code=data['qr_code'], is_active=True, date=today).first()
                if qr and not qr.is_expired:
                    qr_verified = True
            if not qr_verified:
                return Response({'error': 'Invalid QR code. Please scan the office QR sticker.'}, status=status.HTTP_400_BAD_REQUEST)

        # Face verification
        face_verified = False
        face_confidence = None

        # On-device face verification (ML Kit on mobile) - QR + location still verified server-side
        if method == 'face_local':
            face_photo = data.get('face_photo')
            if not face_photo:
                return Response({'error': 'Face photo (selfie) is required.'},
                                status=status.HTTP_400_BAD_REQUEST)
            if not qr_verified:
                return Response({'error': 'QR verification is required with face_local method.'},
                                status=status.HTTP_400_BAD_REQUEST)
            # Trust on-device face detection - app already verified face presence via ML Kit
            face_verified = True
            face_confidence = float(data.get('face_confidence', 0.8))

        # Server-side face comparison against reference photo
        elif method in ['face', 'face_qr', 'face_location']:
            face_photo = data.get('face_photo')
            if not face_photo:
                return Response({'error': 'Face photo (selfie) is required for face verification.'},
                                status=status.HTTP_400_BAD_REQUEST)
            if not employee.face_photo:
                return Response({'error': 'No reference face photo registered. Please register your face first.'},
                                status=status.HTTP_400_BAD_REQUEST)

            is_match, face_confidence, error_msg = compare_faces(
                employee.face_photo.path, face_photo
            )
            if error_msg:
                return Response({'error': error_msg}, status=status.HTTP_400_BAD_REQUEST)
            if not is_match:
                return Response({
                    'error': 'Face verification failed. The selfie does not match your registered face.',
                    'confidence': face_confidence,
                }, status=status.HTTP_403_FORBIDDEN)
            face_verified = True

        attendance = Attendance.objects.create(
            employee=employee,
            date=today,
            check_in=timezone.now(),
            status='present',
            verification_method=method,
            check_in_latitude=data.get('latitude'),
            check_in_longitude=data.get('longitude'),
            face_verified=face_verified,
            face_confidence=face_confidence,
            face_photo=data.get('face_photo'),
            qr_verified=qr_verified,
        )

        return Response({
            'message': 'Checked in successfully',
            'attendance': AttendanceSerializer(attendance).data,
        }, status=status.HTTP_201_CREATED)


@extend_schema(tags=['Attendance'], request=CheckOutSerializer)
class CheckOutView(APIView):
    """Mark attendance check-out"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        employee = get_employee(request.user)
        if not employee:
            return Response({'error': 'Employee profile not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = CheckOutSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        today = date.today()
        attendance = Attendance.objects.filter(employee=employee, date=today).first()
        if not attendance:
            return Response({'error': 'No check-in record found for today'}, status=status.HTTP_400_BAD_REQUEST)
        if attendance.check_out:
            return Response({'error': 'Already checked out today'}, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        attendance.check_out = timezone.now()
        attendance.check_out_latitude = data.get('latitude')
        attendance.check_out_longitude = data.get('longitude')
        attendance.save()

        return Response({
            'message': 'Checked out successfully',
            'attendance': AttendanceSerializer(attendance).data,
        })


@extend_schema(tags=['Attendance'], parameters=[
    OpenApiParameter(name='month', type=int, required=False),
    OpenApiParameter(name='year', type=int, required=False),
])
class AttendanceHistoryView(generics.ListAPIView):
    """View attendance history. Filter by month/year."""
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        employee = get_employee(self.request.user)
        if not employee:
            return Attendance.objects.none()

        qs = Attendance.objects.filter(employee=employee)

        # Filter by month/year
        month = self.request.query_params.get('month')
        year = self.request.query_params.get('year')
        if year:
            qs = qs.filter(date__year=int(year))
        if month:
            qs = qs.filter(date__month=int(month))

        return qs


@extend_schema(tags=['Attendance'])
class TodayAttendanceView(APIView):
    """Get today's attendance status"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        employee = get_employee(request.user)
        if not employee:
            return Response({'error': 'Employee profile not found'}, status=status.HTTP_404_NOT_FOUND)

        attendance = Attendance.objects.filter(employee=employee, date=date.today()).first()
        return Response({
            'checked_in': attendance is not None,
            'checked_out': attendance.check_out is not None if attendance else False,
            'attendance': AttendanceSerializer(attendance).data if attendance else None,
        })


# ---- Leave APIs ----

@extend_schema(tags=['Leave'])
class LeaveTypeListView(generics.ListAPIView):
    """List available leave types"""
    serializer_class = LeaveTypeSerializer
    permission_classes = [IsAuthenticated]
    queryset = LeaveType.objects.filter(is_active=True)


@extend_schema(tags=['Leave'])
class LeaveRequestListCreateView(APIView):
    """List own leave requests or create new one"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        employee = get_employee(request.user)
        if not employee:
            return Response({'error': 'Employee profile not found'}, status=status.HTTP_404_NOT_FOUND)

        qs = LeaveRequest.objects.filter(employee=employee)
        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        serializer = LeaveRequestSerializer(qs, many=True)
        return Response(serializer.data)

    def post(self, request):
        employee = get_employee(request.user)
        if not employee:
            return Response({'error': 'Employee profile not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = LeaveRequestCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        leave = serializer.save(employee=employee)

        # Notify admins
        admin_employees = Employee.objects.filter(user__is_staff=True).exclude(pk=employee.pk)
        for admin_emp in admin_employees:
            Notification.objects.create(
                employee=admin_emp,
                title='New Leave Request',
                body=f'{employee.full_name} requested {leave.total_days} day(s) leave from {leave.start_date} to {leave.end_date}',
                notification_type='leave',
                data={'leave_request_id': str(leave.id)},
            )
            send_push_notification(
                admin_emp,
                'New Leave Request',
                f'{employee.full_name} requested {leave.total_days} day(s) leave',
            )

        return Response(LeaveRequestSerializer(leave).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=['Leave'])
class LeaveRequestCancelView(APIView):
    """Cancel own leave request (only if still pending)"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        employee = get_employee(request.user)
        if not employee:
            return Response({'error': 'Employee profile not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            leave = LeaveRequest.objects.get(pk=pk, employee=employee)
        except LeaveRequest.DoesNotExist:
            return Response({'error': 'Leave request not found'}, status=status.HTTP_404_NOT_FOUND)

        if leave.status != 'pending':
            return Response({'error': 'Only pending requests can be cancelled'}, status=status.HTTP_400_BAD_REQUEST)

        leave.status = 'cancelled'
        leave.save()
        return Response({'message': 'Leave request cancelled'})


@extend_schema(tags=['Leave'])
class LeaveBalanceView(APIView):
    """Get leave balance for the current year"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        employee = get_employee(request.user)
        if not employee:
            return Response({'error': 'Employee profile not found'}, status=status.HTTP_404_NOT_FOUND)

        year = timezone.now().year
        leave_types = LeaveType.objects.filter(is_active=True)
        balances = []

        for lt in leave_types:
            used = LeaveRequest.objects.filter(
                employee=employee, leave_type=lt, status='approved',
                start_date__year=year,
            ).count()
            # Sum actual days
            used_days = 0
            for lr in LeaveRequest.objects.filter(
                employee=employee, leave_type=lt, status='approved',
                start_date__year=year,
            ):
                used_days += lr.total_days

            balances.append({
                'leave_type': lt.name,
                'total_allowed': lt.days_allowed,
                'used': used_days,
                'remaining': max(0, lt.days_allowed - used_days),
            })

        return Response(balances)


# ---- Work Assignment APIs ----

@extend_schema(tags=['Work'])
class WorkAssignmentListView(generics.ListAPIView):
    """List work assignments for the employee"""
    serializer_class = WorkAssignmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        employee = get_employee(self.request.user)
        if not employee:
            return WorkAssignment.objects.none()

        qs = WorkAssignment.objects.filter(assigned_to=employee)
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs


@extend_schema(tags=['Work'])
class WorkAssignmentDetailView(APIView):
    """View work assignment details"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        employee = get_employee(request.user)
        if not employee:
            return Response({'error': 'Employee profile not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            assignment = WorkAssignment.objects.get(pk=pk, assigned_to=employee)
        except WorkAssignment.DoesNotExist:
            return Response({'error': 'Assignment not found'}, status=status.HTTP_404_NOT_FOUND)

        return Response(WorkAssignmentSerializer(assignment).data)


@extend_schema(tags=['Work'], request=WorkStatusUpdateSerializer)
class WorkStatusUpdateView(APIView):
    """Update status of a work assignment"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        employee = get_employee(request.user)
        if not employee:
            return Response({'error': 'Employee profile not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            assignment = WorkAssignment.objects.get(pk=pk, assigned_to=employee)
        except WorkAssignment.DoesNotExist:
            return Response({'error': 'Assignment not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = WorkStatusUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        assignment.status = data['status']
        if data['status'] == 'completed':
            assignment.completed_at = timezone.now()
        assignment.save()

        # Create work update log
        if data.get('message'):
            WorkUpdate.objects.create(
                assignment=assignment,
                employee=employee,
                message=data['message'],
                attachment=data.get('attachment'),
            )

        # Notify the assigner
        if assignment.assigned_by:
            assigner_employee = Employee.objects.filter(user=assignment.assigned_by).first()
            if assigner_employee:
                Notification.objects.create(
                    employee=assigner_employee,
                    title=f'Work Update: {assignment.title}',
                    body=f'{employee.full_name} updated status to {assignment.get_status_display()}',
                    notification_type='work',
                    data={'assignment_id': str(assignment.id)},
                )
                send_push_notification(
                    assigner_employee,
                    f'Work Update: {assignment.title}',
                    f'{employee.full_name} updated status to {assignment.get_status_display()}',
                )

        return Response({
            'message': 'Status updated',
            'assignment': WorkAssignmentSerializer(assignment).data,
        })


@extend_schema(tags=['Work'])
class WorkUpdateCreateView(APIView):
    """Add an update/note to a work assignment"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        employee = get_employee(request.user)
        if not employee:
            return Response({'error': 'Employee profile not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            assignment = WorkAssignment.objects.get(pk=pk, assigned_to=employee)
        except WorkAssignment.DoesNotExist:
            return Response({'error': 'Assignment not found'}, status=status.HTTP_404_NOT_FOUND)

        message = request.data.get('message')
        if not message:
            return Response({'error': 'message is required'}, status=status.HTTP_400_BAD_REQUEST)

        update = WorkUpdate.objects.create(
            assignment=assignment,
            employee=employee,
            message=message,
            attachment=request.FILES.get('attachment'),
        )

        return Response(WorkUpdateSerializer(update).data, status=status.HTTP_201_CREATED)


# ---- Notification APIs ----

@extend_schema(tags=['Notifications'])
class NotificationListView(generics.ListAPIView):
    """List notifications for the employee"""
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        employee = get_employee(self.request.user)
        if not employee:
            return Notification.objects.none()

        return Notification.objects.filter(
            Q(employee=employee) | Q(employee__isnull=True)
        )


@extend_schema(tags=['Notifications'])
class NotificationMarkReadView(APIView):
    """Mark notification(s) as read"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk=None):
        employee = get_employee(request.user)
        if not employee:
            return Response({'error': 'Employee profile not found'}, status=status.HTTP_404_NOT_FOUND)

        if pk:
            Notification.objects.filter(pk=pk, employee=employee).update(is_read=True)
        else:
            # Mark all as read
            Notification.objects.filter(employee=employee, is_read=False).update(is_read=True)

        return Response({'message': 'Marked as read'})


@extend_schema(tags=['Notifications'], request=DeviceTokenSerializer)
class RegisterDeviceTokenView(APIView):
    """Register FCM device token for push notifications"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        employee = get_employee(request.user)
        if not employee:
            return Response({'error': 'Employee profile not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = DeviceTokenSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Deactivate old tokens with same value
        DeviceToken.objects.filter(token=serializer.validated_data['token']).delete()

        token = serializer.save(employee=employee)
        return Response({'message': 'Device registered', 'id': str(token.id)}, status=status.HTTP_201_CREATED)


# ============================================================
# Admin APIs (for managing employees from backend/admin panel)
# ============================================================

@extend_schema(tags=['Admin'])
class AdminEmployeeListView(generics.ListCreateAPIView):
    """Admin: List all employees or create new"""
    permission_classes = [IsAdminUser]
    queryset = Employee.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return EmployeeListSerializer
        return EmployeeProfileSerializer

    def create(self, request, *args, **kwargs):
        data = request.data
        # Create Django user
        username = data.get('username')
        password = data.get('password', 'changeme123')
        email = data.get('email', '')
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')

        if not username:
            return Response({'error': 'username is required'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(
            username=username, password=password, email=email,
            first_name=first_name, last_name=last_name,
        )

        employee = Employee.objects.create(
            user=user,
            employee_id=data.get('employee_id', f'EMP{user.pk:04d}'),
            employment_type=data.get('employment_type', 'fulltime'),
            department=data.get('department', 'engineering'),
            designation=data.get('designation', ''),
            phone=data.get('phone', ''),
            address=data.get('address', ''),
            monthly_salary=data.get('monthly_salary'),
            hourly_rate=data.get('hourly_rate'),
            office_latitude=data.get('office_latitude'),
            office_longitude=data.get('office_longitude'),
            allowed_radius_meters=data.get('allowed_radius_meters', 100),
        )

        return Response(EmployeeProfileSerializer(employee, context={'request': request}).data,
                        status=status.HTTP_201_CREATED)


@extend_schema(tags=['Admin'])
class AdminEmployeeDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Admin: View/update/delete employee"""
    serializer_class = EmployeeProfileSerializer
    permission_classes = [IsAdminUser]
    queryset = Employee.objects.all()


@extend_schema(tags=['Admin'])
class AdminLeaveReviewView(APIView):
    """Admin: Approve/reject leave requests"""
    permission_classes = [IsAdminUser]

    def get(self, request):
        """List pending leave requests"""
        qs = LeaveRequest.objects.filter(status='pending')
        return Response(LeaveRequestSerializer(qs, many=True).data)

    def post(self, request, pk):
        """Approve or reject a leave request"""
        try:
            leave = LeaveRequest.objects.get(pk=pk)
        except LeaveRequest.DoesNotExist:
            return Response({'error': 'Leave request not found'}, status=status.HTTP_404_NOT_FOUND)

        action = request.data.get('action')  # 'approve' or 'reject'
        if action not in ['approve', 'reject']:
            return Response({'error': 'action must be approve or reject'}, status=status.HTTP_400_BAD_REQUEST)

        leave.status = 'approved' if action == 'approve' else 'rejected'
        leave.reviewed_by = request.user
        leave.review_notes = request.data.get('notes', '')
        leave.reviewed_at = timezone.now()
        leave.save()

        # Notify employee
        Notification.objects.create(
            employee=leave.employee,
            title=f'Leave {leave.get_status_display()}',
            body=f'Your leave request from {leave.start_date} to {leave.end_date} has been {leave.get_status_display().lower()}.',
            notification_type='leave',
            data={'leave_request_id': str(leave.id)},
        )
        send_push_notification(
            leave.employee,
            f'Leave {leave.get_status_display()}',
            f'Your leave from {leave.start_date} to {leave.end_date} has been {leave.get_status_display().lower()}.',
        )

        return Response({'message': f'Leave {leave.get_status_display().lower()}'})


@extend_schema(tags=['Admin'])
class AdminWorkAssignView(APIView):
    """Admin: Create work assignments for employees"""
    permission_classes = [IsAdminUser]

    def post(self, request):
        data = request.data
        try:
            employee = Employee.objects.get(pk=data.get('employee_id'))
        except Employee.DoesNotExist:
            return Response({'error': 'Employee not found'}, status=status.HTTP_404_NOT_FOUND)

        assignment = WorkAssignment.objects.create(
            title=data.get('title', ''),
            description=data.get('description', ''),
            assigned_to=employee,
            assigned_by=request.user,
            project_id=data.get('project_id'),
            priority=data.get('priority', 'medium'),
            due_date=data.get('due_date'),
            attachment=request.FILES.get('attachment'),
        )

        # Notify employee
        Notification.objects.create(
            employee=employee,
            title='New Work Assignment',
            body=f'You have been assigned: {assignment.title}',
            notification_type='work',
            data={'assignment_id': str(assignment.id)},
        )
        send_push_notification(
            employee,
            'New Work Assignment',
            f'You have been assigned: {assignment.title}',
        )

        return Response(WorkAssignmentSerializer(assignment).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=['Admin'])
class AdminWorkAssignDetailView(APIView):
    """Admin: View, update, or delete a work assignment"""
    permission_classes = [IsAdminUser]

    def get(self, request, pk):
        try:
            assignment = WorkAssignment.objects.get(pk=pk)
        except WorkAssignment.DoesNotExist:
            return Response({'error': 'Assignment not found'}, status=status.HTTP_404_NOT_FOUND)

        return Response(WorkAssignmentSerializer(assignment).data)

    def patch(self, request, pk):
        try:
            assignment = WorkAssignment.objects.get(pk=pk)
        except WorkAssignment.DoesNotExist:
            return Response({'error': 'Assignment not found'}, status=status.HTTP_404_NOT_FOUND)

        data = request.data
        allowed_fields = ['title', 'description', 'priority', 'status', 'due_date', 'notes']
        for field in allowed_fields:
            if field in data:
                setattr(assignment, field, data[field])

        # Handle employee reassignment
        if 'employee_id' in data:
            try:
                assignment.assigned_to = Employee.objects.get(pk=data['employee_id'])
            except Employee.DoesNotExist:
                return Response({'error': 'Employee not found'}, status=status.HTTP_404_NOT_FOUND)

        # Handle project change
        if 'project_id' in data:
            assignment.project_id = data['project_id'] or None

        # Handle attachment
        if 'attachment' in request.FILES:
            assignment.attachment = request.FILES['attachment']
        elif data.get('remove_attachment'):
            assignment.attachment = None

        if data.get('status') == 'completed' and not assignment.completed_at:
            assignment.completed_at = timezone.now()

        assignment.save()

        return Response(WorkAssignmentSerializer(assignment).data)

    def delete(self, request, pk):
        try:
            assignment = WorkAssignment.objects.get(pk=pk)
        except WorkAssignment.DoesNotExist:
            return Response({'error': 'Assignment not found'}, status=status.HTTP_404_NOT_FOUND)

        assignment.delete()
        return Response({'message': 'Assignment deleted'}, status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=['Admin'])
class AdminAttendanceReportView(APIView):
    """Admin: View attendance report"""
    permission_classes = [IsAdminUser]

    def get(self, request):
        month = int(request.query_params.get('month', timezone.now().month))
        year = int(request.query_params.get('year', timezone.now().year))
        employee_id = request.query_params.get('employee_id')

        qs = Attendance.objects.filter(date__month=month, date__year=year)
        if employee_id:
            qs = qs.filter(employee__pk=employee_id)

        data = []
        employees = Employee.objects.filter(status='active')
        if employee_id:
            employees = employees.filter(pk=employee_id)

        for emp in employees:
            emp_attendance = qs.filter(employee=emp)
            data.append({
                'employee_id': emp.employee_id,
                'name': emp.full_name,
                'total_present': emp_attendance.filter(status='present').count(),
                'total_late': emp_attendance.filter(status='late').count(),
                'total_absent': emp_attendance.filter(status='absent').count(),
                'total_half_day': emp_attendance.filter(status='half_day').count(),
                'total_wfh': emp_attendance.filter(status='work_from_home').count(),
                'records': AttendanceSerializer(emp_attendance, many=True).data,
            })

        return Response(data)


@extend_schema(tags=['Admin'])
class AdminGenerateQRView(APIView):
    """Admin: Generate daily QR code for attendance"""
    permission_classes = [IsAdminUser]

    def post(self, request):
        today = date.today()
        expires_hours = int(request.data.get('expires_hours', 12))

        # Deactivate old QR codes
        QRCode.objects.filter(date=today).update(is_active=False)

        code = f"ATT-{today.isoformat()}-{uuid.uuid4().hex[:8]}"
        qr = QRCode.objects.create(
            code=code,
            date=today,
            expires_at=timezone.now() + timezone.timedelta(hours=expires_hours),
        )

        return Response({
            'code': qr.code,
            'date': qr.date,
            'expires_at': qr.expires_at,
        }, status=status.HTTP_201_CREATED)


@extend_schema(tags=['Admin'])
class AdminSendNotificationView(APIView):
    """Admin: Send push notification to employee(s)"""
    permission_classes = [IsAdminUser]

    def post(self, request):
        title = request.data.get('title')
        body = request.data.get('body')
        employee_id = request.data.get('employee_id')  # None = broadcast
        notification_type = request.data.get('type', 'general')

        if not title or not body:
            return Response({'error': 'title and body are required'}, status=status.HTTP_400_BAD_REQUEST)

        if employee_id:
            try:
                employee = Employee.objects.get(pk=employee_id)
            except Employee.DoesNotExist:
                return Response({'error': 'Employee not found'}, status=status.HTTP_404_NOT_FOUND)

            notif = Notification.objects.create(
                employee=employee, title=title, body=body,
                notification_type=notification_type,
            )
            send_push_notification(employee, title, body)
            return Response({'message': 'Notification sent', 'id': str(notif.id)})
        else:
            # Broadcast to all active employees
            notif = Notification.objects.create(
                employee=None, title=title, body=body,
                notification_type=notification_type,
            )
            for emp in Employee.objects.filter(status='active'):
                send_push_notification(emp, title, body)
            return Response({'message': 'Broadcast sent', 'id': str(notif.id)})


# ============================================================
# Account Deletion (for App Store / Play Store compliance)
# ============================================================

@extend_schema(tags=['Auth'])
class DeleteAccountView(APIView):
    """
    Delete own employee account and all associated data.
    Required by Apple App Store and Google Play Store policies.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        employee = get_employee(request.user)
        if not employee:
            return Response({'error': 'Employee profile not found'}, status=status.HTTP_404_NOT_FOUND)

        password = request.data.get('password')
        if not password:
            return Response({'error': 'Password is required to confirm account deletion'},
                            status=status.HTTP_400_BAD_REQUEST)

        if not request.user.check_password(password):
            return Response({'error': 'Incorrect password'}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user

        # Delete all employee-related data
        DeviceToken.objects.filter(employee=employee).delete()
        Notification.objects.filter(employee=employee).delete()
        WorkUpdate.objects.filter(employee=employee).delete()
        Attendance.objects.filter(employee=employee).delete()
        LeaveRequest.objects.filter(employee=employee).delete()

        # Delete employee profile and user account
        employee.delete()
        user.delete()

        return Response({'message': 'Your account and all associated data have been permanently deleted.'})


# ============================================================
# Public Pages (Privacy Policy, Data Retention)
# ============================================================

def privacy_policy(request):
    """Public privacy policy page for App Store / Play Store"""
    return render(request, 'employees/privacy_policy.html')


def data_retention_policy(request):
    """Public data retention policy page for App Store / Play Store"""
    return render(request, 'employees/data_retention_policy.html')


