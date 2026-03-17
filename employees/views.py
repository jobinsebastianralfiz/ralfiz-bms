import uuid
import math
from datetime import date

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q, Sum
from django.utils import timezone
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from .models import (
    Employee, DeviceToken, Attendance, LeaveType, LeaveRequest,
    WorkAssignment, WorkUpdate, Notification, QRCode, ScheduledClass, Payroll,
    Certificate
)
from .serializers import (
    EmployeeProfileSerializer, EmployeeListSerializer,
    DeviceTokenSerializer, AttendanceSerializer,
    CheckInSerializer, CheckOutSerializer,
    LeaveTypeSerializer, LeaveRequestSerializer, LeaveRequestCreateSerializer,
    WorkAssignmentSerializer, WorkUpdateSerializer, WorkStatusUpdateSerializer,
    NotificationSerializer, ChangePasswordSerializer, ScheduledClassSerializer,
    PayrollSerializer, OwnerClientSerializer, OwnerProjectSerializer,
    OwnerAttendanceEmployeeSerializer,
    CertificateSerializer, CertificateCreateSerializer,
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
                many=True, context={'request': request}
            ).data,
        }

        # Include class-related data only for interns
        if employee.role == 'intern':
            upcoming_classes = ScheduledClass.objects.filter(
                Q(interns=employee) | Q(interns__isnull=True),
                date__gte=today,
                status__in=['scheduled', 'in_progress'],
            ).distinct()[:5]
            data['upcoming_classes'] = ScheduledClassSerializer(
                upcoming_classes, many=True, context={'request': request}
            ).data

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
        # Files come via request.FILES, not request.data
        if 'profile_photo' in request.FILES:
            data['profile_photo'] = request.FILES['profile_photo']

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
            if not employee.face_photo:
                return Response({'error': 'No reference face photo registered. Please register your face first.'},
                                status=status.HTTP_400_BAD_REQUEST)
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


# ---- Scheduled Classes APIs (for interns) ----

@extend_schema(tags=['Classes'], parameters=[
    OpenApiParameter(name='status', type=str, required=False),
    OpenApiParameter(name='upcoming', type=bool, required=False),
])
class ScheduledClassListView(generics.ListAPIView):
    """List scheduled classes for the logged-in intern"""
    serializer_class = ScheduledClassSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        employee = get_employee(self.request.user)
        if not employee:
            return ScheduledClass.objects.none()

        # Only interns can see scheduled classes
        if employee.role != 'intern':
            return ScheduledClass.objects.none()

        # Classes where this intern is assigned, or all-intern classes (empty interns list)
        qs = ScheduledClass.objects.filter(
            Q(interns=employee) | Q(interns__isnull=True)
        ).distinct()

        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        if self.request.query_params.get('upcoming') == 'true':
            from datetime import date as dt_date
            qs = qs.filter(date__gte=dt_date.today(), status__in=['scheduled', 'in_progress'])

        return qs


@extend_schema(tags=['Classes'])
class ScheduledClassDetailView(APIView):
    """View scheduled class details"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        employee = get_employee(request.user)
        if not employee:
            return Response({'error': 'Employee profile not found'}, status=status.HTTP_404_NOT_FOUND)

        if employee.role != 'intern':
            return Response({'error': 'Scheduled classes are only available for interns.'},
                            status=status.HTTP_403_FORBIDDEN)

        try:
            scheduled_class = ScheduledClass.objects.filter(
                Q(interns=employee) | Q(interns__isnull=True)
            ).distinct().get(pk=pk)
        except ScheduledClass.DoesNotExist:
            return Response({'error': 'Class not found'}, status=status.HTTP_404_NOT_FOUND)

        return Response(ScheduledClassSerializer(scheduled_class, context={'request': request}).data)


# ---- Payroll/Salary APIs (for employee app) ----

@extend_schema(tags=['Payroll'], parameters=[
    OpenApiParameter(name='year', type=int, required=False),
])
class PayslipListView(generics.ListAPIView):
    """List own payslips/salary records"""
    serializer_class = PayrollSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        employee = get_employee(self.request.user)
        if not employee:
            return Payroll.objects.none()

        qs = Payroll.objects.filter(employee=employee).exclude(status='draft')
        year = self.request.query_params.get('year')
        if year:
            qs = qs.filter(year=int(year))
        return qs


@extend_schema(tags=['Payroll'])
class PayslipDetailView(APIView):
    """View a specific payslip"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        employee = get_employee(request.user)
        if not employee:
            return Response({'error': 'Employee profile not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            payroll = Payroll.objects.exclude(status='draft').get(pk=pk, employee=employee)
        except Payroll.DoesNotExist:
            return Response({'error': 'Payslip not found'}, status=status.HTTP_404_NOT_FOUND)

        return Response(PayrollSerializer(payroll).data)


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
# Owner/Partner APIs (business-level data)
# ============================================================

class IsOwnerOrPartner(permissions.BasePermission):
    """Only allow owners or partners to access these views"""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        employee = get_employee(request.user)
        return employee is not None and employee.role in ('owner', 'partner')


class IsAdminOrOwner(permissions.BasePermission):
    """Allow admin (is_staff) or owner/partner role employees"""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_staff:
            return True
        employee = get_employee(request.user)
        return employee is not None and employee.role in ('owner', 'partner')


@extend_schema(tags=['Owner'])
class OwnerDashboardView(APIView):
    """Owner/Partner dashboard with business-level data"""
    permission_classes = [IsAuthenticated, IsOwnerOrPartner]

    def get(self, request):
        from core.models import Client, Project, Invoice, Payment, Expense
        from django.db.models import Sum, Count, Q
        from decimal import Decimal

        today = date.today()
        current_month_start = today.replace(day=1)

        # Client stats
        total_clients = Client.objects.count()
        active_clients = Client.objects.filter(is_active=True).count()

        # Project stats
        active_projects = Project.objects.filter(
            status__in=['confirmed', 'in_progress', 'review']
        ).count()

        # Revenue
        total_revenue = Invoice.objects.filter(
            status='paid'
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')

        month_revenue = Payment.objects.filter(
            payment_date__gte=current_month_start,
            payment_date__lte=today,
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        outstanding = Invoice.objects.filter(
            status__in=['sent', 'viewed', 'partial', 'overdue']
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
        outstanding_paid = Invoice.objects.filter(
            status__in=['sent', 'viewed', 'partial', 'overdue']
        ).aggregate(paid=Sum('amount_paid'))['paid'] or Decimal('0')
        outstanding_amount = outstanding - outstanding_paid

        # Recent payments
        recent_payments = Payment.objects.select_related(
            'invoice', 'invoice__client'
        ).order_by('-payment_date')[:10]
        recent_payments_data = [{
            'amount': str(p.amount),
            'payment_date': str(p.payment_date),
            'payment_method': p.payment_method,
            'client_name': p.invoice.client.name if p.invoice and p.invoice.client else '',
            'invoice_number': p.invoice.invoice_number if p.invoice else '',
        } for p in recent_payments]

        # Expenses
        total_expenses = Expense.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0')
        month_expenses = Expense.objects.filter(
            date__gte=current_month_start, date__lte=today
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        # Employee counts
        employees = Employee.objects.filter(status='active')
        employee_counts = {
            'total': employees.count(),
            'fulltime': employees.filter(employment_type='fulltime').count(),
            'parttime': employees.filter(employment_type='parttime').count(),
            'intern': employees.filter(employment_type='intern').count(),
        }

        return Response({
            'clients': {
                'total': total_clients,
                'active': active_clients,
            },
            'projects': {
                'active': active_projects,
                'total': Project.objects.count(),
            },
            'revenue': {
                'total': str(total_revenue),
                'this_month': str(month_revenue),
                'outstanding': str(outstanding_amount),
            },
            'expenses': {
                'total': str(total_expenses),
                'this_month': str(month_expenses),
            },
            'recent_payments': recent_payments_data,
            'employees': employee_counts,
        })


@extend_schema(tags=['Owner'])
class OwnerClientListView(APIView):
    """Owner/Partner: List all clients with revenue data"""
    permission_classes = [IsAuthenticated, IsOwnerOrPartner]

    def get(self, request):
        from core.models import Client, Invoice, Project
        from django.db.models import Sum, Count, Q
        from decimal import Decimal

        clients = Client.objects.all()
        search = request.query_params.get('search')
        if search:
            clients = clients.filter(
                Q(name__icontains=search) | Q(company_name__icontains=search)
            )

        data = []
        for client in clients:
            invoices = Invoice.objects.filter(client=client)
            total_revenue = invoices.filter(status='paid').aggregate(
                total=Sum('total_amount'))['total'] or Decimal('0')
            total_paid = invoices.exclude(status__in=['draft', 'cancelled']).aggregate(
                paid=Sum('amount_paid'))['paid'] or Decimal('0')
            total_invoiced = invoices.exclude(status__in=['draft', 'cancelled']).aggregate(
                total=Sum('total_amount'))['total'] or Decimal('0')
            pending = total_invoiced - total_paid

            data.append({
                'id': str(client.id),
                'name': client.name,
                'company_name': client.company_name,
                'email': client.email,
                'phone': client.phone,
                'is_active': client.is_active,
                'total_revenue': str(total_revenue),
                'pending_amount': str(pending),
                'project_count': Project.objects.filter(client=client).count(),
            })

        return Response(data)


@extend_schema(tags=['Owner'])
class OwnerProjectListView(APIView):
    """Owner/Partner: List all projects with financial data"""
    permission_classes = [IsAuthenticated, IsOwnerOrPartner]

    def get(self, request):
        from core.models import Project, Invoice
        from django.db.models import Sum, Q
        from decimal import Decimal

        projects = Project.objects.select_related('client').all()

        status_filter = request.query_params.get('status')
        if status_filter:
            projects = projects.filter(status=status_filter)

        search = request.query_params.get('search')
        if search:
            projects = projects.filter(
                Q(name__icontains=search) | Q(client__name__icontains=search)
            )

        data = []
        for project in projects:
            invoices = Invoice.objects.filter(project=project).exclude(status__in=['draft', 'cancelled'])
            invoiced = invoices.aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
            paid = invoices.aggregate(paid=Sum('amount_paid'))['paid'] or Decimal('0')

            data.append({
                'id': str(project.id),
                'name': project.name,
                'client_name': project.client.name if project.client else '',
                'status': project.status,
                'project_type': project.project_type,
                'estimated_budget': str(project.estimated_budget or 0),
                'final_amount': str(project.final_amount or 0),
                'invoiced_amount': str(invoiced),
                'paid_amount': str(paid),
                'start_date': str(project.start_date) if project.start_date else None,
                'deadline': str(project.deadline) if project.deadline else None,
            })

        return Response(data)


@extend_schema(tags=['Owner'])
class OwnerFinancialReportView(APIView):
    """Owner/Partner: Financial report with trends"""
    permission_classes = [IsAuthenticated, IsOwnerOrPartner]

    def get(self, request):
        from core.models import Client, Invoice, Payment, Expense
        from django.db.models import Sum, Q
        from decimal import Decimal
        import calendar

        today = date.today()

        # Monthly trends for last 12 months
        monthly_data = []
        for i in range(11, -1, -1):
            month = today.month - i
            year = today.year
            while month <= 0:
                month += 12
                year -= 1

            month_payments = Payment.objects.filter(
                payment_date__month=month, payment_date__year=year
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

            month_expenses = Expense.objects.filter(
                date__month=month, date__year=year
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

            monthly_data.append({
                'month': calendar.month_abbr[month],
                'year': year,
                'income': str(month_payments),
                'expenses': str(month_expenses),
                'profit': str(month_payments - month_expenses),
            })

        # Revenue by client (top 10)
        revenue_by_client = []
        for client in Client.objects.all():
            paid = Invoice.objects.filter(
                client=client, status='paid'
            ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
            if paid > 0:
                revenue_by_client.append({
                    'client': client.name,
                    'revenue': str(paid),
                })
        revenue_by_client.sort(key=lambda x: float(x['revenue']), reverse=True)
        revenue_by_client = revenue_by_client[:10]

        # Collection rate
        total_invoiced = Invoice.objects.exclude(
            status__in=['draft', 'cancelled']
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
        total_collected = Invoice.objects.exclude(
            status__in=['draft', 'cancelled']
        ).aggregate(paid=Sum('amount_paid'))['paid'] or Decimal('0')
        collection_rate = (float(total_collected) / float(total_invoiced) * 100) if total_invoiced else 0

        # Total income vs expenses
        total_income = Payment.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0')
        total_expenses = Expense.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0')

        return Response({
            'summary': {
                'total_income': str(total_income),
                'total_expenses': str(total_expenses),
                'net_profit': str(total_income - total_expenses),
                'collection_rate': round(collection_rate, 1),
            },
            'monthly_trends': monthly_data,
            'revenue_by_client': revenue_by_client,
        })


@extend_schema(tags=['Owner'], parameters=[
    OpenApiParameter(name='start_date', type=str, required=False, description='YYYY-MM-DD'),
    OpenApiParameter(name='end_date', type=str, required=False, description='YYYY-MM-DD'),
    OpenApiParameter(name='employee_id', type=str, required=False),
])
class OwnerAttendanceView(APIView):
    """Owner/Partner: View all employees' attendance"""
    permission_classes = [IsAuthenticated, IsOwnerOrPartner]

    def get(self, request):
        from datetime import datetime

        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        employee_id = request.query_params.get('employee_id')

        today = date.today()
        start = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else today.replace(day=1)
        end = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else today

        employees = Employee.objects.filter(status='active')
        if employee_id:
            employees = employees.filter(pk=employee_id)

        data = []
        for emp in employees:
            records = Attendance.objects.filter(
                employee=emp, date__gte=start, date__lte=end
            )
            data.append({
                'employee_id': emp.employee_id,
                'name': emp.full_name,
                'department': emp.department,
                'records': AttendanceSerializer(records, many=True).data,
            })

        return Response(data)


@extend_schema(tags=['Owner'])
class OwnerClientDetailView(APIView):
    """Owner/Partner: View single client with projects, invoices, quotes"""
    permission_classes = [IsAuthenticated, IsOwnerOrPartner]

    def get(self, request, pk):
        from core.models import Client, Project, Invoice, Quote
        from decimal import Decimal

        try:
            client = Client.objects.get(pk=pk)
        except Client.DoesNotExist:
            return Response({'error': 'Client not found'}, status=status.HTTP_404_NOT_FOUND)

        # Projects
        projects = Project.objects.filter(client=client)
        projects_data = [{
            'id': str(p.id),
            'name': p.name,
            'status': p.status,
            'project_type': p.project_type,
            'estimated_budget': str(p.estimated_budget or 0),
            'final_amount': str(p.final_amount or 0),
            'start_date': str(p.start_date) if p.start_date else None,
            'deadline': str(p.deadline) if p.deadline else None,
        } for p in projects]

        # Invoices
        invoices = Invoice.objects.filter(client=client).exclude(status='draft')
        invoices_data = [{
            'id': str(inv.id),
            'invoice_number': inv.invoice_number,
            'title': inv.title,
            'status': inv.status,
            'total_amount': str(inv.total_amount),
            'amount_paid': str(inv.amount_paid),
            'balance_due': str(inv.balance_due),
            'issue_date': str(inv.issue_date),
            'due_date': str(inv.due_date) if inv.due_date else None,
        } for inv in invoices]

        # Quotes
        quotes = Quote.objects.filter(client=client)
        quotes_data = [{
            'id': str(q.id),
            'quote_number': q.quote_number,
            'title': q.title,
            'status': q.status,
            'total_amount': str(q.total_amount),
            'issue_date': str(q.issue_date),
            'valid_until': str(q.valid_until),
        } for q in quotes]

        # Revenue stats
        total_invoiced = invoices.aggregate(
            total=models.Sum('total_amount'))['total'] or Decimal('0')
        total_paid = invoices.aggregate(
            paid=models.Sum('amount_paid'))['paid'] or Decimal('0')

        return Response({
            'id': str(client.id),
            'name': client.name,
            'company_name': client.company_name,
            'email': client.email,
            'phone': client.phone,
            'whatsapp': client.whatsapp,
            'address': client.address,
            'gst_number': client.gst_number,
            'priority': client.priority,
            'is_active': client.is_active,
            'total_invoiced': str(total_invoiced),
            'total_paid': str(total_paid),
            'balance_due': str(total_invoiced - total_paid),
            'projects': projects_data,
            'invoices': invoices_data,
            'quotes': quotes_data,
        })


@extend_schema(tags=['Owner'])
class OwnerProjectDetailView(APIView):
    """Owner/Partner: View single project with credentials, invoices, expenses"""
    permission_classes = [IsAuthenticated, IsOwnerOrPartner]

    def get(self, request, pk):
        from core.models import Project, Credential, Invoice, Expense
        from decimal import Decimal

        try:
            project = Project.objects.select_related('client').get(pk=pk)
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)

        # Credentials
        credentials = Credential.objects.filter(project=project)
        credentials_data = [{
            'id': str(c.id),
            'credential_type': c.credential_type,
            'name': c.name,
            'provider': c.provider,
            'url': c.url,
            'ip_address': c.ip_address,
            'username': c.username,
            'password': c.password,
            'ssh_key': c.ssh_key,
            'port': c.port,
            'purchase_date': str(c.purchase_date) if c.purchase_date else None,
            'expiry_date': str(c.expiry_date) if c.expiry_date else None,
            'auto_renew': c.auto_renew,
            'renewal_cost': str(c.renewal_cost) if c.renewal_cost else None,
            'is_active': c.is_active,
            'is_expired': c.is_expired,
            'is_expiring_soon': c.is_expiring_soon,
            'days_until_expiry': c.days_until_expiry,
        } for c in credentials]

        # Invoices
        invoices = Invoice.objects.filter(project=project).exclude(status='draft')
        invoices_data = [{
            'id': str(inv.id),
            'invoice_number': inv.invoice_number,
            'title': inv.title,
            'status': inv.status,
            'total_amount': str(inv.total_amount),
            'amount_paid': str(inv.amount_paid),
            'balance_due': str(inv.balance_due),
            'issue_date': str(inv.issue_date),
            'due_date': str(inv.due_date) if inv.due_date else None,
        } for inv in invoices]

        # Expenses
        expenses = Expense.objects.filter(project=project)
        expenses_data = [{
            'id': str(e.id),
            'category': e.category,
            'amount': str(e.amount),
            'date': str(e.date),
            'vendor': e.vendor,
            'description': e.description,
            'is_billable': e.is_billable,
            'payment_method': e.payment_method,
        } for e in expenses]

        # Financial summary
        total_invoiced = invoices.aggregate(
            total=models.Sum('total_amount'))['total'] or Decimal('0')
        total_paid = invoices.aggregate(
            paid=models.Sum('amount_paid'))['paid'] or Decimal('0')
        total_expenses = expenses.aggregate(
            total=models.Sum('amount'))['total'] or Decimal('0')

        return Response({
            'id': str(project.id),
            'name': project.name,
            'client_name': project.client.name if project.client else '',
            'client_id': str(project.client.id) if project.client else None,
            'project_type': project.project_type,
            'status': project.status,
            'description': project.description,
            'estimated_budget': str(project.estimated_budget or 0),
            'final_amount': str(project.final_amount or 0),
            'start_date': str(project.start_date) if project.start_date else None,
            'deadline': str(project.deadline) if project.deadline else None,
            'completed_date': str(project.completed_date) if project.completed_date else None,
            'tech_stack': project.tech_stack,
            'github_repo': project.github_repo,
            'live_url': project.live_url,
            'is_overdue': project.is_overdue,
            'financial_summary': {
                'total_invoiced': str(total_invoiced),
                'total_paid': str(total_paid),
                'balance_due': str(total_invoiced - total_paid),
                'total_expenses': str(total_expenses),
            },
            'credentials': credentials_data,
            'invoices': invoices_data,
            'expenses': expenses_data,
        })


@extend_schema(tags=['Owner'])
class OwnerInvoiceListView(APIView):
    """Owner/Partner: List all invoices"""
    permission_classes = [IsAuthenticated, IsOwnerOrPartner]

    def get(self, request):
        from core.models import Invoice

        invoices = Invoice.objects.select_related('client', 'project').all()

        status_filter = request.query_params.get('status')
        if status_filter:
            invoices = invoices.filter(status=status_filter)

        client_id = request.query_params.get('client_id')
        if client_id:
            invoices = invoices.filter(client_id=client_id)

        search = request.query_params.get('search')
        if search:
            invoices = invoices.filter(
                models.Q(invoice_number__icontains=search) |
                models.Q(title__icontains=search) |
                models.Q(client__name__icontains=search)
            )

        data = [{
            'id': str(inv.id),
            'invoice_number': inv.invoice_number,
            'title': inv.title,
            'client_name': inv.client.name if inv.client else '',
            'project_name': inv.project.name if inv.project else '',
            'status': inv.status,
            'total_amount': str(inv.total_amount),
            'amount_paid': str(inv.amount_paid),
            'balance_due': str(inv.balance_due),
            'issue_date': str(inv.issue_date),
            'due_date': str(inv.due_date) if inv.due_date else None,
            'is_overdue': inv.is_overdue,
        } for inv in invoices]

        return Response(data)


@extend_schema(tags=['Owner'])
class OwnerInvoiceDetailView(APIView):
    """Owner/Partner: View single invoice with line items and payments"""
    permission_classes = [IsAuthenticated, IsOwnerOrPartner]

    def get(self, request, pk):
        from core.models import Invoice

        try:
            inv = Invoice.objects.select_related('client', 'project', 'quote').get(pk=pk)
        except Invoice.DoesNotExist:
            return Response({'error': 'Invoice not found'}, status=status.HTTP_404_NOT_FOUND)

        items = [{
            'description': item.description,
            'details': item.details,
            'quantity': str(item.quantity),
            'unit_price': str(item.unit_price),
            'amount': str(item.amount),
        } for item in inv.items.all()]

        payments = [{
            'id': str(p.id),
            'amount': str(p.amount),
            'payment_date': str(p.payment_date),
            'payment_method': p.payment_method,
            'transaction_id': p.transaction_id,
            'notes': p.notes,
        } for p in inv.payments.all()]

        return Response({
            'id': str(inv.id),
            'invoice_number': inv.invoice_number,
            'title': inv.title,
            'description': inv.description,
            'client_name': inv.client.name if inv.client else '',
            'client_id': str(inv.client.id) if inv.client else None,
            'project_name': inv.project.name if inv.project else '',
            'project_id': str(inv.project.id) if inv.project else None,
            'quote_number': inv.quote.quote_number if inv.quote else None,
            'status': inv.status,
            'subtotal': str(inv.subtotal),
            'discount': str(inv.discount),
            'tax_rate': str(inv.tax_rate),
            'tax_amount': str(inv.tax_amount),
            'total_amount': str(inv.total_amount),
            'amount_paid': str(inv.amount_paid),
            'balance_due': str(inv.balance_due),
            'issue_date': str(inv.issue_date),
            'due_date': str(inv.due_date) if inv.due_date else None,
            'is_overdue': inv.is_overdue,
            'items': items,
            'payments': payments,
        })


@extend_schema(tags=['Owner'])
class OwnerQuoteListView(APIView):
    """Owner/Partner: List all quotes"""
    permission_classes = [IsAuthenticated, IsOwnerOrPartner]

    def get(self, request):
        from core.models import Quote

        quotes = Quote.objects.select_related('client', 'project').all()

        status_filter = request.query_params.get('status')
        if status_filter:
            quotes = quotes.filter(status=status_filter)

        client_id = request.query_params.get('client_id')
        if client_id:
            quotes = quotes.filter(client_id=client_id)

        data = [{
            'id': str(q.id),
            'quote_number': q.quote_number,
            'title': q.title,
            'client_name': q.client.name if q.client else '',
            'project_name': q.project.name if q.project else '',
            'status': q.status,
            'total_amount': str(q.total_amount),
            'issue_date': str(q.issue_date),
            'valid_until': str(q.valid_until),
            'is_expired': q.is_expired,
        } for q in quotes]

        return Response(data)


@extend_schema(tags=['Owner'])
class OwnerExpenseListView(APIView):
    """Owner/Partner: List all expenses"""
    permission_classes = [IsAuthenticated, IsOwnerOrPartner]

    def get(self, request):
        from core.models import Expense
        from decimal import Decimal

        expenses = Expense.objects.select_related('project').all()

        category = request.query_params.get('category')
        if category:
            expenses = expenses.filter(category=category)

        project_id = request.query_params.get('project_id')
        if project_id:
            expenses = expenses.filter(project_id=project_id)

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        if start_date:
            expenses = expenses.filter(date__gte=start_date)
        if end_date:
            expenses = expenses.filter(date__lte=end_date)

        total = expenses.aggregate(total=models.Sum('amount'))['total'] or Decimal('0')

        data = [{
            'id': str(e.id),
            'category': e.category,
            'amount': str(e.amount),
            'date': str(e.date),
            'vendor': e.vendor,
            'description': e.description,
            'project_name': e.project.name if e.project else '',
            'is_billable': e.is_billable,
            'payment_method': e.payment_method,
        } for e in expenses]

        return Response({
            'total': str(total),
            'count': len(data),
            'expenses': data,
        })


# ---- Owner: Employee List & Detail ----

@extend_schema(tags=['Owner'], parameters=[
    OpenApiParameter(name='status', type=str, required=False, description='active|inactive|terminated|on_leave'),
    OpenApiParameter(name='department', type=str, required=False),
    OpenApiParameter(name='role', type=str, required=False, description='employee|intern|owner|partner'),
    OpenApiParameter(name='search', type=str, required=False),
])
class OwnerEmployeeListView(APIView):
    """Owner/Partner: List all employees"""
    permission_classes = [IsAuthenticated, IsOwnerOrPartner]

    def get(self, request):
        employees = Employee.objects.select_related('user').all()

        status_filter = request.query_params.get('status')
        if status_filter:
            employees = employees.filter(status=status_filter)

        dept = request.query_params.get('department')
        if dept:
            employees = employees.filter(department=dept)

        role = request.query_params.get('role')
        if role:
            employees = employees.filter(role=role)

        search = request.query_params.get('search')
        if search:
            employees = employees.filter(
                models.Q(user__first_name__icontains=search) |
                models.Q(user__last_name__icontains=search) |
                models.Q(employee_id__icontains=search) |
                models.Q(user__email__icontains=search)
            )

        data = []
        for emp in employees:
            photo = emp.profile_photo or emp.face_photo
            photo_url = request.build_absolute_uri(photo.url) if photo else None
            data.append({
                'id': str(emp.id),
                'employee_id': emp.employee_id,
                'name': emp.full_name,
                'email': emp.user.email,
                'phone': emp.phone,
                'department': emp.department,
                'department_display': emp.get_department_display(),
                'designation': emp.designation,
                'employment_type': emp.employment_type,
                'employment_type_display': emp.get_employment_type_display(),
                'role': emp.role,
                'role_display': emp.get_role_display(),
                'status': emp.status,
                'status_display': emp.get_status_display(),
                'joining_date': str(emp.joining_date) if emp.joining_date else None,
                'profile_photo': photo_url,
            })

        return Response(data)


@extend_schema(tags=['Owner'])
class OwnerEmployeeDetailView(APIView):
    """Owner/Partner: View single employee with attendance summary and leave info"""
    permission_classes = [IsAuthenticated, IsOwnerOrPartner]

    def get(self, request, pk):
        from datetime import datetime
        from decimal import Decimal

        try:
            emp = Employee.objects.select_related('user', 'supervisor').get(pk=pk)
        except Employee.DoesNotExist:
            return Response({'error': 'Employee not found'}, status=status.HTTP_404_NOT_FOUND)

        today = date.today()
        current_month_start = today.replace(day=1)

        # Attendance stats for current month
        month_attendance = Attendance.objects.filter(
            employee=emp, date__gte=current_month_start, date__lte=today
        )
        total_present = month_attendance.filter(status='present').count()
        total_absent = month_attendance.filter(status='absent').count()
        total_late = month_attendance.filter(status='late').count()
        total_hours = sum(
            float(a.working_hours or 0) for a in month_attendance
        )

        # Recent attendance (last 10)
        recent_attendance = Attendance.objects.filter(employee=emp).order_by('-date')[:10]
        attendance_data = [{
            'date': str(a.date),
            'check_in': a.check_in.strftime('%H:%M') if a.check_in else None,
            'check_out': a.check_out.strftime('%H:%M') if a.check_out else None,
            'working_hours': str(a.working_hours) if a.working_hours else None,
            'status': a.status,
            'status_display': a.get_status_display(),
            'verification_method': a.verification_method,
        } for a in recent_attendance]

        # Leave summary for current year
        leave_data = []
        leave_types = LeaveType.objects.filter(is_active=True)
        for lt in leave_types:
            used_days = 0
            for lr in LeaveRequest.objects.filter(
                employee=emp, leave_type=lt, status='approved',
                start_date__year=today.year,
            ):
                used_days += lr.total_days
            leave_data.append({
                'leave_type': lt.name,
                'total_allowed': lt.days_allowed,
                'used': used_days,
                'remaining': max(0, lt.days_allowed - used_days),
            })

        # Pending leave requests
        pending_leaves = LeaveRequest.objects.filter(employee=emp, status='pending')
        pending_leaves_data = [{
            'id': str(l.id),
            'leave_type': l.leave_type.name if l.leave_type else '',
            'start_date': str(l.start_date),
            'end_date': str(l.end_date),
            'total_days': l.total_days,
            'reason': l.reason,
        } for l in pending_leaves]

        # Active work assignments
        assignments = WorkAssignment.objects.filter(
            assigned_to=emp, status__in=['assigned', 'in_progress']
        )
        assignments_data = [{
            'id': str(w.id),
            'title': w.title,
            'priority': w.priority,
            'status': w.status,
            'due_date': str(w.due_date) if w.due_date else None,
        } for w in assignments]

        photo = emp.profile_photo or emp.face_photo
        photo_url = request.build_absolute_uri(photo.url) if photo else None

        return Response({
            'id': str(emp.id),
            'employee_id': emp.employee_id,
            'name': emp.full_name,
            'first_name': emp.user.first_name,
            'last_name': emp.user.last_name,
            'email': emp.user.email,
            'phone': emp.phone,
            'emergency_contact': emp.emergency_contact,
            'address': emp.address,
            'date_of_birth': str(emp.date_of_birth) if emp.date_of_birth else None,
            'joining_date': str(emp.joining_date) if emp.joining_date else None,
            'department': emp.department,
            'department_display': emp.get_department_display(),
            'designation': emp.designation,
            'employment_type': emp.employment_type,
            'employment_type_display': emp.get_employment_type_display(),
            'role': emp.role,
            'role_display': emp.get_role_display(),
            'status': emp.status,
            'status_display': emp.get_status_display(),
            'monthly_salary': str(emp.monthly_salary) if emp.monthly_salary else None,
            'hourly_rate': str(emp.hourly_rate) if emp.hourly_rate else None,
            'profile_photo': photo_url,
            'has_face_registered': bool(emp.face_photo),
            'supervisor': emp.supervisor.get_full_name() if emp.supervisor else None,
            'attendance_summary': {
                'month': today.strftime('%B %Y'),
                'present': total_present,
                'absent': total_absent,
                'late': total_late,
                'total_hours': round(total_hours, 1),
            },
            'recent_attendance': attendance_data,
            'leave_balance': leave_data,
            'pending_leaves': pending_leaves_data,
            'active_assignments': assignments_data,
        })


# ---- Owner: Client CRUD ----

@extend_schema(tags=['Owner'])
class OwnerClientCreateView(APIView):
    """Owner/Partner: Create a new client"""
    permission_classes = [IsAuthenticated, IsOwnerOrPartner]

    def post(self, request):
        from core.models import Client
        data = request.data
        if not data.get('name'):
            return Response({'error': 'Client name is required'}, status=status.HTTP_400_BAD_REQUEST)

        client = Client.objects.create(
            name=data.get('name', ''),
            company_name=data.get('company_name', ''),
            email=data.get('email', ''),
            phone=data.get('phone', ''),
            whatsapp=data.get('whatsapp', ''),
            address=data.get('address', ''),
            gst_number=data.get('gst_number', ''),
            priority=data.get('priority', 'medium'),
            notes=data.get('notes', ''),
        )
        return Response({'id': str(client.id), 'message': 'Client created'}, status=status.HTTP_201_CREATED)


@extend_schema(tags=['Owner'])
class OwnerClientUpdateDeleteView(APIView):
    """Owner/Partner: Update or delete a client"""
    permission_classes = [IsAuthenticated, IsOwnerOrPartner]

    def patch(self, request, pk):
        from core.models import Client
        try:
            client = Client.objects.get(pk=pk)
        except Client.DoesNotExist:
            return Response({'error': 'Client not found'}, status=status.HTTP_404_NOT_FOUND)

        fields = ['name', 'company_name', 'email', 'phone', 'whatsapp', 'address',
                  'gst_number', 'priority', 'notes', 'is_active']
        for field in fields:
            if field in request.data:
                setattr(client, field, request.data[field])
        client.save()
        return Response({'message': 'Client updated'})

    def delete(self, request, pk):
        from core.models import Client
        try:
            client = Client.objects.get(pk=pk)
        except Client.DoesNotExist:
            return Response({'error': 'Client not found'}, status=status.HTTP_404_NOT_FOUND)
        client.delete()
        return Response({'message': 'Client deleted'}, status=status.HTTP_204_NO_CONTENT)


# ---- Owner: Project CRUD ----

@extend_schema(tags=['Owner'])
class OwnerProjectCreateView(APIView):
    """Owner/Partner: Create a new project"""
    permission_classes = [IsAuthenticated, IsOwnerOrPartner]

    def post(self, request):
        from core.models import Project, Client
        data = request.data
        if not data.get('name') or not data.get('client_id'):
            return Response({'error': 'Project name and client_id are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            client = Client.objects.get(pk=data['client_id'])
        except Client.DoesNotExist:
            return Response({'error': 'Client not found'}, status=status.HTTP_404_NOT_FOUND)

        project = Project.objects.create(
            client=client,
            name=data.get('name', ''),
            project_type=data.get('project_type', 'web_app'),
            description=data.get('description', ''),
            status=data.get('status', 'lead'),
            estimated_budget=data.get('estimated_budget'),
            final_amount=data.get('final_amount'),
            start_date=data.get('start_date') or None,
            deadline=data.get('deadline') or None,
            tech_stack=data.get('tech_stack', ''),
            github_repo=data.get('github_repo', ''),
            live_url=data.get('live_url', ''),
            notes=data.get('notes', ''),
        )
        return Response({'id': str(project.id), 'message': 'Project created'}, status=status.HTTP_201_CREATED)


@extend_schema(tags=['Owner'])
class OwnerProjectUpdateDeleteView(APIView):
    """Owner/Partner: Update or delete a project"""
    permission_classes = [IsAuthenticated, IsOwnerOrPartner]

    def patch(self, request, pk):
        from core.models import Project
        try:
            project = Project.objects.get(pk=pk)
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)

        fields = ['name', 'project_type', 'description', 'status', 'estimated_budget',
                  'final_amount', 'start_date', 'deadline', 'completed_date', 'tech_stack',
                  'github_repo', 'live_url', 'notes']
        for field in fields:
            if field in request.data:
                val = request.data[field]
                if field in ('start_date', 'deadline', 'completed_date') and val == '':
                    val = None
                setattr(project, field, val)

        if 'client_id' in request.data:
            project.client_id = request.data['client_id']

        project.save()
        return Response({'message': 'Project updated'})

    def delete(self, request, pk):
        from core.models import Project
        try:
            project = Project.objects.get(pk=pk)
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)
        project.delete()
        return Response({'message': 'Project deleted'}, status=status.HTTP_204_NO_CONTENT)


# ---- Owner: Credential CRUD ----

@extend_schema(tags=['Owner'])
class OwnerCredentialCreateView(APIView):
    """Owner/Partner: Add a credential to a project"""
    permission_classes = [IsAuthenticated, IsOwnerOrPartner]

    def post(self, request):
        from core.models import Credential, Project
        data = request.data
        if not data.get('project_id') or not data.get('name'):
            return Response({'error': 'project_id and name are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            Project.objects.get(pk=data['project_id'])
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)

        cred = Credential.objects.create(
            project_id=data['project_id'],
            credential_type=data.get('credential_type', 'other'),
            name=data.get('name', ''),
            provider=data.get('provider', ''),
            url=data.get('url', ''),
            ip_address=data.get('ip_address') or None,
            username=data.get('username', ''),
            password=data.get('password', ''),
            ssh_key=data.get('ssh_key', ''),
            port=data.get('port') or None,
            purchase_date=data.get('purchase_date') or None,
            expiry_date=data.get('expiry_date') or None,
            auto_renew=data.get('auto_renew', False),
            renewal_cost=data.get('renewal_cost') or None,
            notes=data.get('notes', ''),
        )
        return Response({'id': str(cred.id), 'message': 'Credential created'}, status=status.HTTP_201_CREATED)


@extend_schema(tags=['Owner'])
class OwnerCredentialUpdateDeleteView(APIView):
    """Owner/Partner: Update or delete a credential"""
    permission_classes = [IsAuthenticated, IsOwnerOrPartner]

    def patch(self, request, pk):
        from core.models import Credential
        try:
            cred = Credential.objects.get(pk=pk)
        except Credential.DoesNotExist:
            return Response({'error': 'Credential not found'}, status=status.HTTP_404_NOT_FOUND)

        fields = ['credential_type', 'name', 'provider', 'url', 'ip_address', 'username',
                  'password', 'ssh_key', 'port', 'purchase_date', 'expiry_date', 'auto_renew',
                  'renewal_cost', 'notes', 'is_active']
        for field in fields:
            if field in request.data:
                val = request.data[field]
                if field in ('ip_address', 'port', 'purchase_date', 'expiry_date', 'renewal_cost') and val == '':
                    val = None
                setattr(cred, field, val)
        cred.save()
        return Response({'message': 'Credential updated'})

    def delete(self, request, pk):
        from core.models import Credential
        try:
            cred = Credential.objects.get(pk=pk)
        except Credential.DoesNotExist:
            return Response({'error': 'Credential not found'}, status=status.HTTP_404_NOT_FOUND)
        cred.delete()
        return Response({'message': 'Credential deleted'}, status=status.HTTP_204_NO_CONTENT)


# ---- Owner: Invoice CRUD ----

@extend_schema(tags=['Owner'])
class OwnerInvoiceCreateView(APIView):
    """Owner/Partner: Create an invoice"""
    permission_classes = [IsAuthenticated, IsOwnerOrPartner]

    def post(self, request):
        from core.models import Invoice, InvoiceItem
        data = request.data
        if not data.get('client_id') or not data.get('title'):
            return Response({'error': 'client_id and title are required'}, status=status.HTTP_400_BAD_REQUEST)

        inv = Invoice(
            client_id=data['client_id'],
            project_id=data.get('project_id') or None,
            title=data.get('title', ''),
            description=data.get('description', ''),
            status=data.get('status', 'draft'),
            discount=data.get('discount', 0),
            tax_rate=data.get('tax_rate', 0),
            issue_date=data.get('issue_date') or None,
            due_date=data.get('due_date') or None,
            terms=data.get('terms', ''),
            client_notes=data.get('client_notes', ''),
            notes=data.get('notes', ''),
        )
        inv.save()

        # Create line items
        items = data.get('items', [])
        for i, item in enumerate(items):
            InvoiceItem.objects.create(
                invoice=inv,
                description=item.get('description', ''),
                details=item.get('details', ''),
                quantity=item.get('quantity', 1),
                unit_price=item.get('unit_price', 0),
                amount=float(item.get('quantity', 1)) * float(item.get('unit_price', 0)),
                order=i,
            )

        inv.calculate_totals()
        return Response({'id': str(inv.id), 'invoice_number': inv.invoice_number, 'message': 'Invoice created'},
                        status=status.HTTP_201_CREATED)


@extend_schema(tags=['Owner'])
class OwnerInvoiceUpdateDeleteView(APIView):
    """Owner/Partner: Update or delete an invoice"""
    permission_classes = [IsAuthenticated, IsOwnerOrPartner]

    def patch(self, request, pk):
        from core.models import Invoice, InvoiceItem
        try:
            inv = Invoice.objects.get(pk=pk)
        except Invoice.DoesNotExist:
            return Response({'error': 'Invoice not found'}, status=status.HTTP_404_NOT_FOUND)

        fields = ['title', 'description', 'status', 'discount', 'tax_rate',
                  'issue_date', 'due_date', 'terms', 'client_notes', 'notes']
        for field in fields:
            if field in request.data:
                val = request.data[field]
                if field in ('due_date', 'issue_date') and val == '':
                    val = None
                setattr(inv, field, val)

        if 'client_id' in request.data:
            inv.client_id = request.data['client_id']
        if 'project_id' in request.data:
            inv.project_id = request.data['project_id'] or None

        # Replace items if provided
        if 'items' in request.data:
            inv.items.all().delete()
            for i, item in enumerate(request.data['items']):
                InvoiceItem.objects.create(
                    invoice=inv,
                    description=item.get('description', ''),
                    details=item.get('details', ''),
                    quantity=item.get('quantity', 1),
                    unit_price=item.get('unit_price', 0),
                    amount=float(item.get('quantity', 1)) * float(item.get('unit_price', 0)),
                    order=i,
                )
            inv.calculate_totals()
        else:
            inv.save()

        return Response({'message': 'Invoice updated'})

    def delete(self, request, pk):
        from core.models import Invoice
        try:
            inv = Invoice.objects.get(pk=pk)
        except Invoice.DoesNotExist:
            return Response({'error': 'Invoice not found'}, status=status.HTTP_404_NOT_FOUND)
        if inv.amount_paid > 0:
            return Response({'error': 'Cannot delete invoice with payments recorded'}, status=status.HTTP_400_BAD_REQUEST)
        inv.delete()
        return Response({'message': 'Invoice deleted'}, status=status.HTTP_204_NO_CONTENT)


# ---- Owner: Payment (Record payment against invoice) ----

@extend_schema(tags=['Owner'])
class OwnerPaymentCreateView(APIView):
    """Owner/Partner: Record a payment against an invoice"""
    permission_classes = [IsAuthenticated, IsOwnerOrPartner]

    def post(self, request):
        from core.models import Payment, Invoice
        data = request.data
        if not data.get('invoice_id') or not data.get('amount'):
            return Response({'error': 'invoice_id and amount are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            invoice = Invoice.objects.get(pk=data['invoice_id'])
        except Invoice.DoesNotExist:
            return Response({'error': 'Invoice not found'}, status=status.HTTP_404_NOT_FOUND)

        payment = Payment.objects.create(
            invoice=invoice,
            amount=data['amount'],
            payment_date=data.get('payment_date') or None,
            payment_method=data.get('payment_method', 'bank_transfer'),
            transaction_id=data.get('transaction_id', ''),
            notes=data.get('notes', ''),
        )
        return Response({
            'id': str(payment.id),
            'message': 'Payment recorded',
            'invoice_status': invoice.status,
            'amount_paid': str(invoice.amount_paid),
            'balance_due': str(invoice.balance_due),
        }, status=status.HTTP_201_CREATED)


# ---- Owner: Quote CRUD ----

@extend_schema(tags=['Owner'])
class OwnerQuoteCreateView(APIView):
    """Owner/Partner: Create a quote"""
    permission_classes = [IsAuthenticated, IsOwnerOrPartner]

    def post(self, request):
        from core.models import Quote, QuoteItem
        data = request.data
        if not data.get('client_id') or not data.get('title') or not data.get('valid_until'):
            return Response({'error': 'client_id, title, and valid_until are required'},
                            status=status.HTTP_400_BAD_REQUEST)

        quote = Quote(
            client_id=data['client_id'],
            project_id=data.get('project_id') or None,
            title=data.get('title', ''),
            description=data.get('description', ''),
            status=data.get('status', 'draft'),
            discount=data.get('discount', 0),
            tax_rate=data.get('tax_rate', 0),
            issue_date=data.get('issue_date') or None,
            valid_until=data['valid_until'],
            duration=data.get('duration', ''),
            start_date=data.get('start_date') or None,
            deliverables=data.get('deliverables', ''),
            payment_terms=data.get('payment_terms', '50-50'),
            terms=data.get('terms', ''),
            client_notes=data.get('client_notes', ''),
            notes=data.get('notes', ''),
        )
        quote.save()

        items = data.get('items', [])
        for i, item in enumerate(items):
            QuoteItem.objects.create(
                quote=quote,
                description=item.get('description', ''),
                details=item.get('details', ''),
                quantity=item.get('quantity', 1),
                unit_price=item.get('unit_price', 0),
                amount=float(item.get('quantity', 1)) * float(item.get('unit_price', 0)),
                order=i,
            )

        quote.calculate_totals()
        return Response({'id': str(quote.id), 'quote_number': quote.quote_number, 'message': 'Quote created'},
                        status=status.HTTP_201_CREATED)


@extend_schema(tags=['Owner'])
class OwnerQuoteUpdateDeleteView(APIView):
    """Owner/Partner: Update or delete a quote"""
    permission_classes = [IsAuthenticated, IsOwnerOrPartner]

    def patch(self, request, pk):
        from core.models import Quote, QuoteItem
        try:
            quote = Quote.objects.get(pk=pk)
        except Quote.DoesNotExist:
            return Response({'error': 'Quote not found'}, status=status.HTTP_404_NOT_FOUND)

        fields = ['title', 'description', 'status', 'discount', 'tax_rate',
                  'issue_date', 'valid_until', 'duration', 'start_date',
                  'deliverables', 'payment_terms', 'terms', 'client_notes', 'notes']
        for field in fields:
            if field in request.data:
                val = request.data[field]
                if field in ('issue_date', 'valid_until', 'start_date') and val == '':
                    val = None
                setattr(quote, field, val)

        if 'client_id' in request.data:
            quote.client_id = request.data['client_id']
        if 'project_id' in request.data:
            quote.project_id = request.data['project_id'] or None

        if 'items' in request.data:
            quote.items.all().delete()
            for i, item in enumerate(request.data['items']):
                QuoteItem.objects.create(
                    quote=quote,
                    description=item.get('description', ''),
                    details=item.get('details', ''),
                    quantity=item.get('quantity', 1),
                    unit_price=item.get('unit_price', 0),
                    amount=float(item.get('quantity', 1)) * float(item.get('unit_price', 0)),
                    order=i,
                )
            quote.calculate_totals()
        else:
            quote.save()

        return Response({'message': 'Quote updated'})

    def delete(self, request, pk):
        from core.models import Quote
        try:
            quote = Quote.objects.get(pk=pk)
        except Quote.DoesNotExist:
            return Response({'error': 'Quote not found'}, status=status.HTTP_404_NOT_FOUND)
        quote.delete()
        return Response({'message': 'Quote deleted'}, status=status.HTTP_204_NO_CONTENT)


# ---- Owner: Expense CRUD ----

@extend_schema(tags=['Owner'])
class OwnerExpenseCreateView(APIView):
    """Owner/Partner: Create an expense"""
    permission_classes = [IsAuthenticated, IsOwnerOrPartner]

    def post(self, request):
        from core.models import Expense
        data = request.data
        if not data.get('amount') or not data.get('vendor') or not data.get('category'):
            return Response({'error': 'amount, vendor, and category are required'},
                            status=status.HTTP_400_BAD_REQUEST)

        expense = Expense.objects.create(
            category=data['category'],
            amount=data['amount'],
            date=data.get('date') or None,
            vendor=data.get('vendor', ''),
            description=data.get('description', ''),
            receipt=request.FILES.get('receipt'),
            project_id=data.get('project_id') or None,
            is_billable=data.get('is_billable', False),
            payment_method=data.get('payment_method', 'bank_transfer'),
            notes=data.get('notes', ''),
        )
        return Response({'id': str(expense.id), 'message': 'Expense created'}, status=status.HTTP_201_CREATED)


@extend_schema(tags=['Owner'])
class OwnerExpenseUpdateDeleteView(APIView):
    """Owner/Partner: Update or delete an expense"""
    permission_classes = [IsAuthenticated, IsOwnerOrPartner]

    def patch(self, request, pk):
        from core.models import Expense
        try:
            expense = Expense.objects.get(pk=pk)
        except Expense.DoesNotExist:
            return Response({'error': 'Expense not found'}, status=status.HTTP_404_NOT_FOUND)

        fields = ['category', 'amount', 'date', 'vendor', 'description',
                  'is_billable', 'payment_method', 'notes']
        for field in fields:
            if field in request.data:
                setattr(expense, field, request.data[field])

        if 'project_id' in request.data:
            expense.project_id = request.data['project_id'] or None
        if 'receipt' in request.FILES:
            expense.receipt = request.FILES['receipt']

        expense.save()
        return Response({'message': 'Expense updated'})

    def delete(self, request, pk):
        from core.models import Expense
        try:
            expense = Expense.objects.get(pk=pk)
        except Expense.DoesNotExist:
            return Response({'error': 'Expense not found'}, status=status.HTTP_404_NOT_FOUND)
        expense.delete()
        return Response({'message': 'Expense deleted'}, status=status.HTTP_204_NO_CONTENT)


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


@extend_schema(tags=['Admin'])
class AdminScheduledClassListCreateView(APIView):
    """Admin: List all scheduled classes or create a new one"""
    permission_classes = [IsAdminUser]

    def get(self, request):
        qs = ScheduledClass.objects.all()
        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return Response(ScheduledClassSerializer(qs, many=True, context={'request': request}).data)

    def post(self, request):
        data = request.data
        scheduled_class = ScheduledClass.objects.create(
            title=data.get('title', ''),
            description=data.get('description', ''),
            date=data.get('date'),
            start_time=data.get('start_time'),
            end_time=data.get('end_time'),
            instructor=data.get('instructor', ''),
            location=data.get('location', ''),
            status=data.get('status', 'scheduled'),
            notes=data.get('notes', ''),
            attachment=request.FILES.get('attachment'),
            created_by=request.user,
        )

        scheduled_class.refresh_from_db()

        # Assign specific interns or notify all interns
        intern_ids = data.getlist('intern_ids') if hasattr(data, 'getlist') else data.get('intern_ids', [])
        if intern_ids:
            scheduled_class.interns.set(intern_ids)

        # Notify interns
        if intern_ids:
            interns = Employee.objects.filter(pk__in=intern_ids)
        else:
            interns = Employee.objects.filter(employment_type='intern', status='active')

        for intern in interns:
            Notification.objects.create(
                employee=intern,
                title='New Class Scheduled',
                body=f'{scheduled_class.title} on {scheduled_class.date} at {scheduled_class.start_time.strftime("%I:%M %p")}',
                notification_type='general',
                data={'class_id': str(scheduled_class.id)},
            )
            send_push_notification(
                intern,
                'New Class Scheduled',
                f'{scheduled_class.title} on {scheduled_class.date}',
            )

        return Response(ScheduledClassSerializer(scheduled_class, context={'request': request}).data,
                        status=status.HTTP_201_CREATED)


@extend_schema(tags=['Admin'])
class AdminScheduledClassDetailView(APIView):
    """Admin: View, update, or delete a scheduled class"""
    permission_classes = [IsAdminUser]

    def get(self, request, pk):
        try:
            scheduled_class = ScheduledClass.objects.get(pk=pk)
        except ScheduledClass.DoesNotExist:
            return Response({'error': 'Class not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(ScheduledClassSerializer(scheduled_class, context={'request': request}).data)

    def patch(self, request, pk):
        try:
            scheduled_class = ScheduledClass.objects.get(pk=pk)
        except ScheduledClass.DoesNotExist:
            return Response({'error': 'Class not found'}, status=status.HTTP_404_NOT_FOUND)

        data = request.data
        for field in ['title', 'description', 'date', 'start_time', 'end_time',
                       'instructor', 'location', 'status', 'notes']:
            if field in data:
                setattr(scheduled_class, field, data[field])

        if 'attachment' in request.FILES:
            scheduled_class.attachment = request.FILES['attachment']
        elif data.get('remove_attachment'):
            scheduled_class.attachment = None

        scheduled_class.save()

        intern_ids = data.getlist('intern_ids') if hasattr(data, 'getlist') else data.get('intern_ids')
        if intern_ids is not None:
            scheduled_class.interns.set(intern_ids)

        return Response(ScheduledClassSerializer(scheduled_class, context={'request': request}).data)

    def delete(self, request, pk):
        try:
            scheduled_class = ScheduledClass.objects.get(pk=pk)
        except ScheduledClass.DoesNotExist:
            return Response({'error': 'Class not found'}, status=status.HTTP_404_NOT_FOUND)
        scheduled_class.delete()
        return Response({'message': 'Class deleted'}, status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=['Admin'])
class AdminPayrollGenerateView(APIView):
    """Admin: Generate payroll for a month. Auto-calculates leave deductions."""
    permission_classes = [IsAdminUser]

    def post(self, request):
        month = int(request.data.get('month', timezone.now().month))
        year = int(request.data.get('year', timezone.now().year))
        working_days = int(request.data.get('working_days', 26))
        employee_id = request.data.get('employee_id')  # None = all active employees

        if employee_id:
            employees = Employee.objects.filter(pk=employee_id, status='active')
        else:
            employees = Employee.objects.filter(status='active')

        results = []
        for emp in employees:
            # Skip if already generated
            if Payroll.objects.filter(employee=emp, month=month, year=year).exists():
                continue

            base = emp.monthly_salary or 0

            # Calculate attendance
            attendance = Attendance.objects.filter(
                employee=emp, date__month=month, date__year=year
            )
            days_present = attendance.filter(status__in=['present', 'late', 'work_from_home']).count()
            half_days = attendance.filter(status='half_day').count()
            days_present += half_days * 0.5

            # Calculate leave
            approved_leaves = LeaveRequest.objects.filter(
                employee=emp, status='approved',
                start_date__month=month, start_date__year=year,
            )
            paid_leave_days = 0
            unpaid_leave_days = 0
            for lr in approved_leaves:
                if lr.leave_type and lr.leave_type.is_paid:
                    paid_leave_days += lr.total_days
                else:
                    unpaid_leave_days += lr.total_days

            # Also count absent days not covered by leave
            days_absent = max(0, working_days - int(days_present) - paid_leave_days - unpaid_leave_days)

            payroll = Payroll(
                employee=emp,
                month=month,
                year=year,
                base_salary=base,
                working_days=working_days,
                days_present=int(days_present),
                days_absent=days_absent,
                paid_leave_days=paid_leave_days,
                unpaid_leave_days=unpaid_leave_days,
                generated_by=request.user,
            )
            payroll.calculate()
            payroll.save()
            results.append(PayrollSerializer(payroll).data)

        return Response({
            'message': f'Payroll generated for {len(results)} employee(s)',
            'payrolls': results,
        }, status=status.HTTP_201_CREATED)


@extend_schema(tags=['Admin'])
class AdminPayrollListView(APIView):
    """Admin: List all payroll records for a month"""
    permission_classes = [IsAdminUser]

    def get(self, request):
        month = int(request.query_params.get('month', timezone.now().month))
        year = int(request.query_params.get('year', timezone.now().year))
        qs = Payroll.objects.filter(month=month, year=year).select_related('employee__user')
        return Response(PayrollSerializer(qs, many=True).data)


@extend_schema(tags=['Admin'])
class AdminPayrollDetailView(APIView):
    """Admin: View/update a payroll record"""
    permission_classes = [IsAdminUser]

    def get(self, request, pk):
        try:
            payroll = Payroll.objects.get(pk=pk)
        except Payroll.DoesNotExist:
            return Response({'error': 'Payroll not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(PayrollSerializer(payroll).data)

    def patch(self, request, pk):
        try:
            payroll = Payroll.objects.get(pk=pk)
        except Payroll.DoesNotExist:
            return Response({'error': 'Payroll not found'}, status=status.HTTP_404_NOT_FOUND)

        data = request.data
        for field in ['base_salary', 'working_days', 'days_present', 'days_absent',
                       'paid_leave_days', 'unpaid_leave_days', 'bonus', 'deductions',
                       'status', 'notes']:
            if field in data:
                setattr(payroll, field, data[field])

        payroll.calculate()
        payroll.save()

        # Notify employee when payslip is confirmed or paid
        if data.get('status') in ['confirmed', 'paid']:
            Notification.objects.create(
                employee=payroll.employee,
                title=f'Payslip {payroll.get_status_display()}',
                body=f'Your payslip for {payroll.month}/{payroll.year} is now {payroll.get_status_display().lower()}. Net pay: {payroll.net_pay}',
                notification_type='general',
                data={'payroll_id': str(payroll.id)},
            )
            send_push_notification(
                payroll.employee,
                f'Payslip {payroll.get_status_display()}',
                f'Your payslip for {payroll.month}/{payroll.year}: Net pay {payroll.net_pay}',
            )

        return Response(PayrollSerializer(payroll).data)

    def delete(self, request, pk):
        try:
            payroll = Payroll.objects.get(pk=pk)
        except Payroll.DoesNotExist:
            return Response({'error': 'Payroll not found'}, status=status.HTTP_404_NOT_FOUND)
        if payroll.status == 'paid':
            return Response({'error': 'Cannot delete a paid payroll record'}, status=status.HTTP_400_BAD_REQUEST)
        payroll.delete()
        return Response({'message': 'Payroll deleted'}, status=status.HTTP_204_NO_CONTENT)


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


# ============================================================
# Certificate APIs
# ============================================================

class CertificateListCreateView(generics.ListCreateAPIView):
    """List all certificates or create a new one"""
    permission_classes = [IsAuthenticated, IsAdminOrOwner]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CertificateCreateSerializer
        return CertificateSerializer

    def get_queryset(self):
        queryset = Certificate.objects.all()
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(student_name__icontains=search) |
                Q(certificate_number__icontains=search) |
                Q(course_name__icontains=search)
            )
        return queryset

    def perform_create(self, serializer):
        serializer.save(issued_by=self.request.user)

    @extend_schema(tags=['Certificates'])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(tags=['Certificates'])
    def post(self, request, *args, **kwargs):
        serializer = CertificateCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        certificate = serializer.save(issued_by=request.user)
        return Response(
            CertificateSerializer(certificate, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )


class CertificateDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update or delete a certificate"""
    queryset = Certificate.objects.all()
    serializer_class = CertificateSerializer
    permission_classes = [IsAuthenticated, IsAdminOrOwner]

    @extend_schema(tags=['Certificates'])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(tags=['Certificates'])
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @extend_schema(tags=['Certificates'])
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @extend_schema(tags=['Certificates'])
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


class CertificatePDFView(APIView):
    """Generate and download certificate PDF"""
    permission_classes = [IsAuthenticated, IsAdminOrOwner]

    @extend_schema(tags=['Certificates'])
    def get(self, request, pk):
        try:
            certificate = Certificate.objects.get(pk=pk)
        except Certificate.DoesNotExist:
            return Response({'error': 'Certificate not found'}, status=status.HTTP_404_NOT_FOUND)

        from django.template.loader import render_to_string
        from django.conf import settings
        import weasyprint
        import qrcode
        import qrcode.image.svg
        import base64
        from io import BytesIO

        # Generate QR code with verification URL
        verify_url = request.build_absolute_uri(
            f'/api/employees/certificates/verify/{certificate.verification_id}/'
        )
        qr = qrcode.QRCode(version=1, box_size=10, border=1)
        qr.add_data(verify_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        qr_img.save(buffer, format='PNG')
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()

        # Build asset paths as file URIs for weasyprint
        static_dir = settings.BASE_DIR / 'static' / 'certificates'
        header_logo = (static_dir / 'headerlogo.png').as_uri()
        signature = (static_dir / 'jobin_signature.png').as_uri()
        seal = (static_dir / 'seal.png').as_uri()
        footer_logo = (static_dir / 'footer_right_logo.png').as_uri()

        # Format dates
        def format_date(d):
            day = d.day
            if 4 <= day <= 20 or 24 <= day <= 30:
                suffix = "th"
            else:
                suffix = ["st", "nd", "rd"][day % 10 - 1]
            return f"{day}{suffix} {d.strftime('%B %Y')}"

        # Render body_text with placeholders
        from django.utils.html import escape
        skills_html = ''
        if certificate.skills:
            items = ''.join(f'<li>{escape(s)}</li>' for s in certificate.skills)
            skills_html = f'<ul class="skills-list">{items}</ul>'

        body_raw = certificate.body_text or ''
        try:
            body_rendered = body_raw.format(
                salutation=certificate.salutation,
                student_name=certificate.student_name,
                college_name=certificate.college_name or '',
                course_name=certificate.course_name or '',
                start_date=format_date(certificate.start_date) if certificate.start_date else '',
                end_date=format_date(certificate.end_date) if certificate.end_date else '',
                duration_days=certificate.duration_days or '',
                mode=certificate.get_mode_display() if certificate.mode else '',
                skills=skills_html,
                pronoun=certificate.pronoun,
                pronoun_cap=certificate.pronoun_cap,
                possessive=certificate.possessive,
                object_pronoun=certificate.object_pronoun,
            )
        except (KeyError, IndexError):
            body_rendered = body_raw

        # Convert paragraphs (double newlines) to HTML
        paragraphs = body_rendered.split('\n\n')
        rendered_body = ''
        for p in paragraphs:
            p = p.strip()
            if not p:
                continue
            if p.startswith('<ul'):
                rendered_body += p
            else:
                rendered_body += f'<p class="body-text">{p}</p>'

        # Process wish_text placeholders
        wish_text = certificate.wish_text.format(
            pronoun=certificate.object_pronoun,
            possessive=certificate.possessive,
        )

        context = {
            'cert': certificate,
            'qr_base64': qr_base64,
            'header_logo': header_logo,
            'signature': signature,
            'seal': seal,
            'footer_logo': footer_logo,
            'rendered_body': rendered_body,
            'date_of_issuance_fmt': certificate.date_of_issuance.strftime('%d/%m/%Y'),
            'wish_text': wish_text,
        }

        html_string = render_to_string('employees/certificate_pdf.html', context)
        from django.http import HttpResponse
        pdf = weasyprint.HTML(string=html_string).write_pdf()

        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"Certificate_{certificate.student_name.replace(' ', '_')}_{certificate.certificate_number.replace('/', '_')}.pdf"
        if request.query_params.get('download'):
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
        else:
            response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response


class CertificateDefaultsView(APIView):
    """Get default title, body_text, and wish_text for a certificate type"""
    permission_classes = [IsAuthenticated, IsAdminOrOwner]

    @extend_schema(tags=['Certificates'])
    def get(self, request):
        cert_type = request.query_params.get('type', 'inter')
        return Response({
            'certificate_type': cert_type,
            'title': Certificate.TYPE_TITLE_MAP.get(cert_type, 'CERTIFICATE'),
            'body_text': Certificate.TYPE_BODY_MAP.get(cert_type, ''),
            'wish_text': Certificate.TYPE_WISH_MAP.get(cert_type, ''),
        })


class CertificateVerifyView(APIView):
    """Public endpoint to verify a certificate via QR code"""
    permission_classes = []
    authentication_classes = []

    @extend_schema(tags=['Certificates'])
    def get(self, request, verification_id):
        try:
            certificate = Certificate.objects.get(verification_id=verification_id)
        except Certificate.DoesNotExist:
            return render(request, 'employees/certificate_verify.html', {
                'valid': False,
            })

        return render(request, 'employees/certificate_verify.html', {
            'valid': True,
            'cert': certificate,
        })


