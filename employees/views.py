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
    CertificateTemplate, Certificate, LateCheckInGrant
)
from crm.models import Lead, LeadNote, LeadReferenceLink, DailyActivity, Demo, FollowUp, LeadActivity
from core.models import (
    Client, Project, Credential, AMCContract, AMCPayment, CredentialRenewal,
    Partner, CapitalContribution, CompanyAsset, CompanyDocument,
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
    CertificateTemplateSerializer, CertificateSerializer, CertificateCreateSerializer,
    LeadSerializer, LeadCreateSerializer, LeadNoteSerializer,
    LeadReferenceLinkSerializer,
    DailyActivitySerializer, DailyActivityCreateSerializer,
    DemoSerializer, DemoCreateSerializer, CRMDashboardSerializer,
    FollowUpSerializer, FollowUpCreateSerializer, LeadActivitySerializer,
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

        # Include today's team attendance for owners/partners
        if employee.role in ('owner', 'partner'):
            try:
                all_employees = Employee.objects.filter(status='active').select_related('user').order_by('user__first_name')
                team_attendance = []
                for emp in all_employees:
                    emp_att = Attendance.objects.filter(employee=emp, date=today).first()
                    try:
                        photo_url = request.build_absolute_uri(emp.profile_photo.url) if emp.profile_photo and emp.profile_photo.name else None
                    except Exception:
                        photo_url = None
                    team_attendance.append({
                        'employee_id': emp.employee_id,
                        'name': emp.full_name,
                        'department': emp.department,
                        'profile_photo': photo_url,
                        'checked_in': emp_att is not None,
                        'check_in': emp_att.check_in.strftime('%I:%M %p') if emp_att and emp_att.check_in else None,
                        'check_out': emp_att.check_out.strftime('%I:%M %p') if emp_att and emp_att.check_out else None,
                        'working_hours': str(emp_att.working_hours) if emp_att and emp_att.working_hours else None,
                    })
                data['team_attendance'] = team_attendance
            except Exception:
                data['team_attendance'] = []

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

def verify_office_qr(qr_value, today=None):
    """Return True if qr_value matches OfficeConfig sticker or a live daily QRCode."""
    from .models import OfficeConfig
    if not qr_value:
        return False
    if OfficeConfig.objects.filter(qr_code=qr_value).exists():
        return True
    today = today or date.today()
    qr = QRCode.objects.filter(code=qr_value, is_active=True, date=today).first()
    return bool(qr and not qr.is_expired)


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
        is_remote_req = bool(data.get('is_remote')) or method == 'remote'

        # Enforce check-in deadline (default 10:15). Owner/partner can bypass.
        # Employees with an unconsumed LateCheckInGrant for today can also bypass.
        from .models import OfficeConfig
        from datetime import time as dtime
        cfg = OfficeConfig.objects.first()
        deadline_time = cfg.check_in_deadline if cfg else dtime(10, 15)
        required_hours = float(cfg.daily_required_hours) if cfg else 6.0
        now = timezone.localtime(timezone.now())
        is_owner_or_partner = employee.role in ('owner', 'partner')
        grant = LateCheckInGrant.objects.filter(
            employee=employee, date=today, consumed_at__isnull=True
        ).first()
        if now.time() > deadline_time and not is_owner_or_partner and not grant:
            return Response({
                'error': f'Check-in window closed at {deadline_time.strftime("%H:%M")}. Please contact admin to record your attendance.',
                'check_in_deadline': deadline_time.strftime('%H:%M'),
            }, status=status.HTTP_400_BAD_REQUEST)
        is_late_bypass = bool(grant) and now.time() > deadline_time

        # Remote check-in path (hybrid / remote employees only)
        if is_remote_req:
            if employee.work_mode not in ('hybrid', 'remote'):
                return Response({'error': 'Remote check-in is only allowed for hybrid/remote employees.'},
                                status=status.HTTP_403_FORBIDDEN)
            face_photo = data.get('face_photo')
            if not face_photo:
                return Response({'error': 'Face photo (selfie) is required for remote check-in.'},
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

            attendance = Attendance.objects.create(
                employee=employee,
                date=today,
                check_in=timezone.now(),
                status='work_from_home',
                verification_method='remote',
                check_in_latitude=data.get('latitude'),
                check_in_longitude=data.get('longitude'),
                face_verified=True,
                face_confidence=face_confidence,
                face_photo=face_photo,
                qr_verified=False,
                required_hours=required_hours,
                is_remote=True,
                notes=f'Late check-in granted: {grant.reason}' if is_late_bypass else '',
            )
            if is_late_bypass:
                grant.consumed_at = timezone.now()
                grant.save(update_fields=['consumed_at'])
            return Response({
                'message': 'Checked in remotely',
                'attendance': AttendanceSerializer(attendance).data,
            }, status=status.HTTP_201_CREATED)

        # Onsite check-in: location required
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
            qr_verified = verify_office_qr(data['qr_code'], today=today)
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
            status='late' if is_late_bypass else 'present',
            verification_method=method,
            check_in_latitude=data.get('latitude'),
            check_in_longitude=data.get('longitude'),
            face_verified=face_verified,
            face_confidence=face_confidence,
            face_photo=data.get('face_photo'),
            qr_verified=qr_verified,
            required_hours=required_hours,
            is_remote=False,
            notes=f'Late check-in granted: {grant.reason}' if is_late_bypass else '',
        )
        if is_late_bypass:
            grant.consumed_at = timezone.now()
            grant.save(update_fields=['consumed_at'])

        return Response({
            'message': 'Checked in successfully',
            'attendance': AttendanceSerializer(attendance).data,
        }, status=status.HTTP_201_CREATED)


@extend_schema(tags=['Attendance'], request=CheckOutSerializer)
class CheckOutView(APIView):
    """Mark attendance check-out. Requires QR scan (onsite) and enforces
    6-hour / 4 PM minimum, unless `force=true` is passed (shortfall tracked).
    """
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
        force = bool(data.get('force'))

        # Onsite attendance must rescan office QR. Remote rows skip QR.
        if not attendance.is_remote:
            qr_code = data.get('qr_code')
            if not qr_code:
                return Response({'error': 'Please scan the office QR to check out.'},
                                status=status.HTTP_400_BAD_REQUEST)
            if not verify_office_qr(qr_code, today=today):
                return Response({'error': 'Invalid QR code. Please scan the office QR sticker.'},
                                status=status.HTTP_400_BAD_REQUEST)

        now = timezone.now()
        min_checkout = attendance.minimum_checkout_time()
        if min_checkout and now < min_checkout and not force:
            remaining = int((min_checkout - now).total_seconds())
            return Response({
                'error': 'Minimum working hours not completed.',
                'minimum_checkout_time': min_checkout.isoformat(),
                'seconds_remaining': max(remaining, 0),
                'required_hours': float(attendance.required_hours),
                'can_force': True,
            }, status=status.HTTP_400_BAD_REQUEST)

        # Commit check-out + compute shortfall
        from decimal import Decimal
        worked_seconds = (now - attendance.check_in).total_seconds()
        worked_hours = Decimal(str(round(worked_seconds / 3600, 2)))
        pending = attendance.required_hours - worked_hours
        if pending < 0:
            pending = Decimal('0')

        attendance.check_out = now
        attendance.check_out_latitude = data.get('latitude')
        attendance.check_out_longitude = data.get('longitude')
        attendance.worked_hours = worked_hours
        attendance.pending_hours = pending
        attendance.is_force_checkout = force and pending > 0
        if pending > 0 and attendance.status == 'present':
            attendance.status = 'half_day'
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
    """Get today's attendance status with check-in/out window info."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        employee = get_employee(request.user)
        if not employee:
            return Response({'error': 'Employee profile not found'}, status=status.HTTP_404_NOT_FOUND)

        from .models import OfficeConfig
        from datetime import time as dtime
        cfg = OfficeConfig.objects.first()
        deadline_time = cfg.check_in_deadline if cfg else dtime(10, 15)
        min_checkout_floor = cfg.min_checkout_time_floor if cfg else dtime(16, 0)
        required_hours = float(cfg.daily_required_hours) if cfg else 6.0

        now_local = timezone.localtime(timezone.now())
        is_owner_or_partner = employee.role in ('owner', 'partner')
        today = date.today()
        has_late_grant = LateCheckInGrant.objects.filter(
            employee=employee, date=today, consumed_at__isnull=True
        ).exists()
        can_check_in_now = (now_local.time() <= deadline_time
                            or is_owner_or_partner
                            or has_late_grant)

        attendance = Attendance.objects.filter(employee=employee, date=today).first()
        return Response({
            'checked_in': attendance is not None,
            'checked_out': attendance.check_out is not None if attendance else False,
            'attendance': AttendanceSerializer(attendance).data if attendance else None,
            'work_mode': employee.work_mode,
            'can_check_in': can_check_in_now and attendance is None,
            'check_in_deadline': deadline_time.strftime('%H:%M'),
            'min_checkout_time_floor': min_checkout_floor.strftime('%H:%M'),
            'required_hours': required_hours,
            'has_late_checkin_grant': has_late_grant,
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
        from core.models import Client, Project, Invoice, Payment, Expense, OpeningBalance
        from django.db.models import Sum, Count, Q, F
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

        # Revenue: sum of every payment received (matches web dashboard).
        # Previously this used Invoice.status='paid' which missed partial
        # payments and any invoice whose status wasn't flipped to 'paid'.
        total_revenue = Payment.objects.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')

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
            'amount': f'{p.amount:.2f}',
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

        # Cash position — now uses per-account BankAccount helper. Legacy
        # cash_in_hand / cash_in_account keys still populated for back-compat
        # with existing Flutter clients.
        from core.cash_position import cash_position as _cp, pending_transfers
        opening = OpeningBalance.current()
        cp = _cp()
        cash_card = next((r for r in cp['accounts'] if r['account'].is_cash), None)
        bank_card = next((r for r in cp['accounts'] if r['account'].is_primary_bank), None)
        current_outstanding = Invoice.objects.exclude(
            status__in=['paid', 'cancelled']
        ).aggregate(total=Sum(F('total_amount') - F('amount_paid')))['total'] or Decimal('0')
        pending_qs = pending_transfers()
        accounts_payload = [{
            'id': str(r['account'].id),
            'name': r['account'].name,
            'account_type': r['account'].account_type,
            'is_primary_bank': r['account'].is_primary_bank,
            'is_cash': r['account'].is_cash,
            'bank_name': r['account'].bank_name,
            'account_number_last4': r['account'].account_number_last4,
            'balance': f"{r['balance']:.2f}",
        } for r in cp['accounts']]
        cash_position = {
            'cash_in_hand': f"{(cash_card['balance'] if cash_card else Decimal('0')):.2f}",
            'cash_in_account': f"{(bank_card['balance'] if bank_card else Decimal('0')):.2f}",
            'total_assets': f"{cp['total']:.2f}",
            'other_assets': f"{cp['other_assets']:.2f}",
            'total_with_assets': f"{cp['total_with_assets']:.2f}",
            'accounts': accounts_payload,
            'pending_transfer_count': pending_qs.count(),
            'receivables_carried_in': f"{(opening.accounts_receivable if opening else Decimal('0')):.2f}",
            'current_outstanding_receivables': f'{current_outstanding:.2f}',
            'opening_label': opening.label if opening else None,
            'opening_as_of': opening.as_of_date.isoformat() if opening else None,
            'opening_cash_in_hand': f"{(opening.cash_in_hand if opening else Decimal('0')):.2f}",
            'opening_cash_in_account': f"{(opening.cash_in_account if opening else Decimal('0')):.2f}",
        }

        # Capital summary (partners + total contributed)
        total_capital = CapitalContribution.objects.aggregate(t=Sum('amount'))['t'] or Decimal('0')
        capital_summary = {
            'total_invested': f'{total_capital:.2f}',
            'partner_count': Partner.objects.filter(is_active=True).count(),
        }

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
                'total': f'{total_revenue:.2f}',
                'this_month': f'{month_revenue:.2f}',
                'outstanding': f'{outstanding_amount:.2f}',
            },
            'expenses': {
                'total': f'{total_expenses:.2f}',
                'this_month': f'{month_expenses:.2f}',
            },
            'cash_position': cash_position,
            'capital': capital_summary,
            'recent_payments': recent_payments_data,
            'employees': employee_counts,
            'dues_summary': self._get_dues_summary(today),
        })

    def _get_dues_summary(self, today):
        from datetime import timedelta
        from decimal import Decimal

        overdue_amc_count = AMCContract.objects.filter(status='active', next_due_date__lt=today).count()
        upcoming_amc_count = AMCContract.objects.filter(
            status='active', next_due_date__range=[today, today + timedelta(days=30)]
        ).count()
        expired_creds_count = Credential.objects.filter(expiry_date__lt=today, is_active=True).count()
        expiring_creds_count = Credential.objects.filter(
            expiry_date__range=[today, today + timedelta(days=30)], is_active=True
        ).count()

        total_amc = AMCContract.objects.filter(
            status='active', next_due_date__lte=today + timedelta(days=30)
        ).aggregate(total=Sum('annual_amount'))['total'] or Decimal('0')
        total_cred = Credential.objects.filter(
            expiry_date__lte=today + timedelta(days=30), is_active=True
        ).aggregate(total=Sum('renewal_cost'))['total'] or Decimal('0')

        expired_docs_count = CompanyDocument.objects.filter(expiry_date__lt=today).count()
        expiring_docs_count = CompanyDocument.objects.filter(
            expiry_date__range=[today, today + timedelta(days=30)]
        ).count()

        return {
            'total_dues': str(total_amc + total_cred),
            'amc_overdue_count': overdue_amc_count,
            'amc_upcoming_count': upcoming_amc_count,
            'credentials_expired_count': expired_creds_count,
            'credentials_expiring_count': expiring_creds_count,
            'company_docs_expired_count': expired_docs_count,
            'company_docs_expiring_count': expiring_docs_count,
        }


@extend_schema(tags=['Owner'])
class OwnerClientListView(APIView):
    """Owner/Partner: List all clients with revenue data"""
    permission_classes = [IsAuthenticated, IsOwnerOrPartner]

    def get(self, request):
        from core.models import Client, Invoice, Payment, Project
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
            # Revenue = sum of every payment received against this client's
            # invoices (matches web logic; previously only counted invoices
            # with status='paid' which missed partials).
            total_revenue = Payment.objects.filter(
                invoice__client=client
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
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
                'total_revenue': f'{total_revenue:.2f}',
                'pending_amount': f'{pending:.2f}',
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
                'client_id': str(project.client_id) if project.client_id else '',
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
class OwnerForceCheckoutView(APIView):
    """Owner/Partner: Force check-out employees who forgot to check out."""
    permission_classes = [IsAuthenticated, IsOwnerOrPartner]

    def post(self, request):
        from decimal import Decimal

        employee_id = request.data.get('employee_id')
        target_date = request.data.get('date')  # optional, defaults to today

        if not employee_id:
            return Response({'error': 'employee_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            employee = Employee.objects.get(pk=employee_id)
        except Employee.DoesNotExist:
            return Response({'error': 'Employee not found'}, status=status.HTTP_404_NOT_FOUND)

        checkout_date = date.today()
        if target_date:
            from datetime import datetime
            checkout_date = datetime.strptime(target_date, '%Y-%m-%d').date()

        attendance = Attendance.objects.filter(employee=employee, date=checkout_date, check_out__isnull=True).first()
        if not attendance:
            return Response({'error': f'No open check-in found for {employee.full_name} on {checkout_date}'},
                            status=status.HTTP_404_NOT_FOUND)

        # Use the configured min checkout time or end of day
        from .models import OfficeConfig
        from datetime import time as dtime
        cfg = OfficeConfig.objects.first()
        min_checkout_floor = cfg.min_checkout_time_floor if cfg else dtime(16, 0)

        # Set check-out to min_checkout_floor on that date, or now if today
        if checkout_date == date.today():
            checkout_time = timezone.now()
        else:
            checkout_time = timezone.make_aware(
                timezone.datetime.combine(checkout_date, min_checkout_floor)
            )

        worked_seconds = (checkout_time - attendance.check_in).total_seconds()
        worked_hours = Decimal(str(round(worked_seconds / 3600, 2)))
        pending = attendance.required_hours - worked_hours
        if pending < 0:
            pending = Decimal('0')

        attendance.check_out = checkout_time
        attendance.worked_hours = worked_hours
        attendance.pending_hours = pending
        attendance.is_force_checkout = True
        if pending > 0 and attendance.status == 'present':
            attendance.status = 'half_day'
        attendance.save()

        return Response({
            'message': f'Force checked out {employee.full_name} for {checkout_date}',
            'attendance': AttendanceSerializer(attendance).data,
        })


@extend_schema(tags=['Owner'])
class OwnerManualCheckInView(APIView):
    """Owner/Partner: Manually add check-in for employees who missed the window."""
    permission_classes = [IsAuthenticated, IsOwnerOrPartner]

    def post(self, request):
        employee_id = request.data.get('employee_id')
        target_date = request.data.get('date')  # optional, defaults to today
        check_in_time = request.data.get('check_in_time')  # optional HH:MM, defaults to now

        if not employee_id:
            return Response({'error': 'employee_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            employee = Employee.objects.get(pk=employee_id)
        except Employee.DoesNotExist:
            return Response({'error': 'Employee not found'}, status=status.HTTP_404_NOT_FOUND)

        checkin_date = date.today()
        if target_date:
            from datetime import datetime
            checkin_date = datetime.strptime(target_date, '%Y-%m-%d').date()

        if Attendance.objects.filter(employee=employee, date=checkin_date).exists():
            return Response({'error': f'{employee.full_name} already has an attendance record for {checkin_date}'},
                            status=status.HTTP_400_BAD_REQUEST)

        from .models import OfficeConfig
        cfg = OfficeConfig.objects.first()
        required_hours = float(cfg.daily_required_hours) if cfg else 6.0

        if check_in_time:
            from datetime import datetime as dt
            parsed_time = dt.strptime(check_in_time, '%H:%M').time()
            checkin_dt = timezone.make_aware(timezone.datetime.combine(checkin_date, parsed_time))
        elif checkin_date == date.today():
            checkin_dt = timezone.now()
        else:
            from datetime import time as dtime
            checkin_dt = timezone.make_aware(timezone.datetime.combine(checkin_date, dtime(9, 0)))

        attendance = Attendance.objects.create(
            employee=employee,
            date=checkin_date,
            check_in=checkin_dt,
            status='present',
            verification_method='manual',
            required_hours=required_hours,
        )

        return Response({
            'message': f'Manually checked in {employee.full_name} for {checkin_date}',
            'attendance': AttendanceSerializer(attendance).data,
        }, status=status.HTTP_201_CREATED)


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

        gst_filing_filter = request.query_params.get('gst_filing_status')
        if gst_filing_filter:
            invoices = invoices.filter(gst_filing_status=gst_filing_filter)

        data = [{
            'id': str(inv.id),
            'invoice_number': inv.invoice_number,
            'title': inv.title,
            'client_name': inv.client.name if inv.client else '',
            'project_name': inv.project.name if inv.project else '',
            'status': inv.status,
            'total_amount': f'{inv.total_amount:.2f}',
            'amount_paid': f'{inv.amount_paid:.2f}',
            'balance_due': f'{inv.balance_due:.2f}',
            'issue_date': str(inv.issue_date),
            'due_date': str(inv.due_date) if inv.due_date else None,
            'is_overdue': inv.is_overdue,
            'gst_filing_status': inv.gst_filing_status,
            'gst_filing_status_display': inv.get_gst_filing_status_display(),
            'gst_filed_at': inv.gst_filed_at.isoformat() if inv.gst_filed_at else None,
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
            'unit_price': f'{item.unit_price:.2f}',
            'amount': f'{item.amount:.2f}',
        } for item in inv.items.all()]

        payments = [{
            'id': str(p.id),
            'amount': f'{p.amount:.2f}',
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
            'subtotal': f'{inv.subtotal:.2f}',
            'discount': f'{inv.discount:.2f}',
            'tax_rate': f'{inv.tax_rate:.2f}',
            'tax_amount': f'{inv.tax_amount:.2f}',
            'total_amount': f'{inv.total_amount:.2f}',
            'amount_paid': f'{inv.amount_paid:.2f}',
            'balance_due': f'{inv.balance_due:.2f}',
            'issue_date': str(inv.issue_date),
            'due_date': str(inv.due_date) if inv.due_date else None,
            'is_overdue': inv.is_overdue,
            'gst_filing_status': inv.gst_filing_status,
            'gst_filing_status_display': inv.get_gst_filing_status_display(),
            'gst_filed_at': inv.gst_filed_at.isoformat() if inv.gst_filed_at else None,
            'items': items,
            'payments': payments,
        })


@extend_schema(tags=['Owner'])
class OwnerQuoteListView(APIView):
    """Owner/Partner: List all quotes"""
    permission_classes = [IsAuthenticated, IsOwnerOrPartner]

    def get(self, request):
        from core.models import Quote

        quotes = Quote.objects.select_related('client', 'project', 'lead').all()

        status_filter = request.query_params.get('status')
        if status_filter:
            quotes = quotes.filter(status=status_filter)

        client_id = request.query_params.get('client_id')
        if client_id:
            quotes = quotes.filter(client_id=client_id)

        lead_id = request.query_params.get('lead_id')
        if lead_id:
            quotes = quotes.filter(lead_id=lead_id)

        data = [{
            'id': str(q.id),
            'quote_number': q.quote_number,
            'title': q.title,
            'client_name': q.client.name if q.client else '',
            'project_name': q.project.name if q.project else '',
            'lead_id': q.lead_id,
            'lead_name': q.lead.contact_person if q.lead else '',
            'is_lead_quote': q.is_lead_quote,
            'recipient_name': q.recipient_name,
            'status': q.status,
            'total_amount': str(q.total_amount),
            'issue_date': str(q.issue_date),
            'valid_until': str(q.valid_until),
            'is_expired': q.is_expired,
        } for q in quotes]

        return Response(data)


@extend_schema(tags=['Owner'])
class OwnerQuoteDetailView(APIView):
    """Owner/Partner: Retrieve a single quote with its line items."""
    permission_classes = [IsAuthenticated, IsOwnerOrPartner]

    def get(self, request, pk):
        from core.models import Quote
        try:
            q = Quote.objects.select_related('client', 'project', 'lead').get(pk=pk)
        except Quote.DoesNotExist:
            return Response({'error': 'Quote not found'}, status=status.HTTP_404_NOT_FOUND)

        items = [{
            'id': str(it.id),
            'description': it.description,
            'details': it.details,
            'quantity': str(it.quantity),
            'unit_price': str(it.unit_price),
            'amount': str(it.amount),
            'order': it.order,
        } for it in q.items.all()]

        return Response({
            'id': str(q.id),
            'quote_number': q.quote_number,
            'title': q.title,
            'description': q.description,
            'client_name': q.client.name if q.client else '',
            'client_id': str(q.client.id) if q.client else '',
            'project_name': q.project.name if q.project else '',
            'project_id': str(q.project.id) if q.project else '',
            'lead_id': q.lead_id,
            'lead_name': q.lead.contact_person if q.lead else '',
            'is_lead_quote': q.is_lead_quote,
            'recipient_name': q.recipient_name,
            'recipient_company': q.recipient_company,
            'recipient_email': q.recipient_email,
            'recipient_phone': q.recipient_phone,
            'status': q.status,
            'subtotal': str(q.subtotal),
            'discount': str(q.discount),
            'tax_rate': str(q.tax_rate),
            'tax_amount': str(q.tax_amount),
            'total_amount': str(q.total_amount),
            'issue_date': str(q.issue_date) if q.issue_date else None,
            'valid_until': str(q.valid_until) if q.valid_until else None,
            'is_expired': q.is_expired,
            'duration': q.duration,
            'start_date': str(q.start_date) if q.start_date else None,
            'deliverables': q.deliverables,
            'payment_terms': q.payment_terms,
            'terms': q.terms,
            'client_notes': q.client_notes,
            'items': items,
        })


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


@extend_schema(tags=['Owner'])
class OwnerPartnerListView(APIView):
    """Owner/Partner: List all partners with capital contributions."""
    permission_classes = [IsAuthenticated, IsOwnerOrPartner]

    def get(self, request):
        from decimal import Decimal

        partners = Partner.objects.all().order_by('-is_active', 'name')
        active_only = request.query_params.get('active_only') == 'true'
        if active_only:
            partners = partners.filter(is_active=True)

        data = []
        for p in partners:
            contributions = list(p.contributions.select_related('bank_account').all())
            data.append({
                'id': str(p.id),
                'name': p.name,
                'title': p.title,
                'email': p.email,
                'phone': p.phone,
                'join_date': str(p.join_date) if p.join_date else None,
                'is_active': p.is_active,
                'photo_url': p.photo.url if p.photo else None,
                'total_contribution': f'{p.total_contribution:.2f}',
                'contributions': [{
                    'id': str(c.id),
                    'date': str(c.date),
                    'amount': f'{c.amount:.2f}',
                    'contribution_type': c.contribution_type,
                    'contribution_type_display': c.get_contribution_type_display(),
                    'bank_account_name': c.bank_account.name if c.bank_account else None,
                    'description': c.description,
                } for c in contributions],
            })

        total = sum((Decimal(p['total_contribution']) for p in data), Decimal('0'))
        return Response({
            'total_invested': f'{total:.2f}',
            'count': len(data),
            'partners': data,
        })


@extend_schema(tags=['Owner'])
class OwnerCompanyAssetListView(APIView):
    """Owner/Partner: List all company assets (rent advance, deposits, equipment)."""
    permission_classes = [IsAuthenticated, IsOwnerOrPartner]

    def get(self, request):
        from decimal import Decimal

        assets = CompanyAsset.objects.all()
        active_only = request.query_params.get('active_only') == 'true'
        if active_only:
            assets = assets.filter(is_active=True)
        asset_type = request.query_params.get('asset_type')
        if asset_type:
            assets = assets.filter(asset_type=asset_type)

        active_qs = assets.filter(is_active=True)
        total_active = active_qs.aggregate(t=Sum('amount'))['t'] or Decimal('0')
        total_refundable = active_qs.filter(is_refundable=True).aggregate(t=Sum('amount'))['t'] or Decimal('0')

        data = [{
            'id': str(a.id),
            'name': a.name,
            'asset_type': a.asset_type,
            'asset_type_display': a.get_asset_type_display(),
            'amount': f'{a.amount:.2f}',
            'acquired_date': str(a.acquired_date),
            'counterparty': a.counterparty,
            'expected_return_date': str(a.expected_return_date) if a.expected_return_date else None,
            'is_refundable': a.is_refundable,
            'is_active': a.is_active,
            'notes': a.notes,
        } for a in assets]

        return Response({
            'total_active': f'{total_active:.2f}',
            'total_refundable': f'{total_refundable:.2f}',
            'count': len(data),
            'assets': data,
        })


@extend_schema(tags=['Owner'])
class OwnerCompanyDocumentListView(APIView):
    """Owner/Partner: List all company documents with expiry tracking."""
    permission_classes = [IsAuthenticated, IsOwnerOrPartner]

    def get(self, request):
        from datetime import timedelta
        today = date.today()
        documents = CompanyDocument.objects.all()
        doc_type = request.query_params.get('document_type')
        if doc_type:
            documents = documents.filter(document_type=doc_type)

        expiring_only = request.query_params.get('expiring_only') == 'true'
        if expiring_only:
            documents = documents.filter(expiry_date__lte=today + timedelta(days=30))

        data = [{
            'id': str(d.id),
            'title': d.title,
            'document_type': d.document_type,
            'document_type_display': d.get_document_type_display(),
            'file_url': request.build_absolute_uri(d.file.url) if d.file else None,
            'issuer': d.issuer,
            'reference_number': d.reference_number,
            'issue_date': str(d.issue_date) if d.issue_date else None,
            'expiry_date': str(d.expiry_date) if d.expiry_date else None,
            'is_expired': d.is_expired,
            'is_expiring_soon': d.is_expiring_soon,
            'days_until_expiry': d.days_until_expiry,
            'notes': d.notes,
        } for d in documents]

        return Response({
            'count': len(data),
            'expired_count': sum(1 for d in data if d['is_expired']),
            'expiring_count': sum(1 for d in data if d['is_expiring_soon']),
            'documents': data,
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


@extend_schema(tags=['Owner'])
class OwnerInvoiceGSTStatusView(APIView):
    """Owner/Partner: Set the GST filing status on a single invoice.

    PATCH body: {"gst_filing_status": "pending" | "filed" | "not_applicable"}
    Auto-sets gst_filed_at to now when status='filed', clears it otherwise.
    """
    permission_classes = [IsAuthenticated, IsOwnerOrPartner]

    def patch(self, request, pk):
        from core.models import Invoice
        from django.utils import timezone
        try:
            inv = Invoice.objects.get(pk=pk)
        except Invoice.DoesNotExist:
            return Response({'error': 'Invoice not found'}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get('gst_filing_status', '')
        valid = {key for key, _ in Invoice.GST_FILING_STATUS_CHOICES}
        if new_status not in valid:
            return Response(
                {'error': f'gst_filing_status must be one of {sorted(valid)}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        inv.gst_filing_status = new_status
        inv.gst_filed_at = timezone.now() if new_status == 'filed' else None
        inv.save(update_fields=['gst_filing_status', 'gst_filed_at'])

        return Response({
            'id': str(inv.id),
            'invoice_number': inv.invoice_number,
            'gst_filing_status': inv.gst_filing_status,
            'gst_filing_status_display': inv.get_gst_filing_status_display(),
            'gst_filed_at': inv.gst_filed_at.isoformat() if inv.gst_filed_at else None,
        })


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
        if not data.get('title') or not data.get('valid_until'):
            return Response({'error': 'title and valid_until are required'},
                            status=status.HTTP_400_BAD_REQUEST)
        if not data.get('client_id') and not data.get('lead_id'):
            return Response({'error': 'Either client_id or lead_id is required'},
                            status=status.HTTP_400_BAD_REQUEST)

        quote = Quote(
            client_id=data.get('client_id') or None,
            lead_id=data.get('lead_id') or None,
            project_id=data.get('project_id') or None,
            title=data.get('title', ''),
            description=data.get('description', ''),
            status=data.get('status', 'draft'),
            discount=data.get('discount', 0),
            tax_rate=data.get('tax_rate', 0),
            issue_date=data.get('issue_date') or timezone.now().date(),
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

        # Support multiple employees via employee_ids list or single employee_id
        employee_ids = data.get('employee_ids', [])
        if not employee_ids and data.get('employee_id'):
            employee_ids = [data.get('employee_id')]

        if not employee_ids:
            return Response({'error': 'employee_ids or employee_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        employees = Employee.objects.filter(pk__in=employee_ids)
        if not employees.exists():
            return Response({'error': 'No valid employees found'}, status=status.HTTP_404_NOT_FOUND)

        assignment = WorkAssignment.objects.create(
            title=data.get('title', ''),
            description=data.get('description', ''),
            assigned_by=request.user,
            project_id=data.get('project_id'),
            priority=data.get('priority', 'medium'),
            due_date=data.get('due_date'),
            attachment=request.FILES.get('attachment'),
            confidentiality_disclaimer=data.get('confidentiality_disclaimer', ''),
        )
        assignment.assigned_to.set(employees)

        # Notify all assigned employees
        for employee in employees:
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
        allowed_fields = ['title', 'description', 'priority', 'status', 'due_date', 'notes', 'confidentiality_disclaimer']
        for field in allowed_fields:
            if field in data:
                setattr(assignment, field, data[field])

        # Handle employee reassignment (supports employee_ids list or single employee_id)
        employee_ids = data.get('employee_ids', [])
        if not employee_ids and 'employee_id' in data:
            employee_ids = [data['employee_id']]
        if employee_ids:
            employees = Employee.objects.filter(pk__in=employee_ids)
            if not employees.exists():
                return Response({'error': 'No valid employees found'}, status=status.HTTP_404_NOT_FOUND)
            assignment.assigned_to.set(employees)

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
        award_badge = (static_dir / 'award_badge.png').as_uri()
        bottom_graphics = (static_dir / 'bottom_graphics.png').as_uri()

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

        # Convert **bold** to <strong> tags
        import re
        body_rendered = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', body_rendered)

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
            'award_badge': award_badge,
            'bottom_graphics': bottom_graphics,
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


class CertificateTemplateListView(generics.ListAPIView):
    """List all active certificate templates"""
    serializer_class = CertificateTemplateSerializer
    permission_classes = [IsAuthenticated, IsAdminOrOwner]

    def get_queryset(self):
        queryset = CertificateTemplate.objects.filter(is_active=True)
        cert_type = self.request.query_params.get('type')
        if cert_type:
            queryset = queryset.filter(certificate_type=cert_type)
        return queryset

    @extend_schema(tags=['Certificates'])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


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


# ============================================================
# CRM APIs (for intern mobile app + admin)
# ============================================================

def get_intern_employee(user):
    """Get employee profile, return (employee, is_intern) tuple"""
    employee = get_employee(user)
    if not employee:
        return None, False
    is_intern = employee.role == 'intern' or employee.employment_type == 'intern'
    return employee, is_intern


@extend_schema(tags=['CRM'])
class CRMDashboardView(APIView):
    """CRM dashboard — shows leads, demos, activities, and work assignments combined"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        employee, is_intern = get_intern_employee(request.user)
        if not employee:
            return Response({'error': 'Employee profile not found'}, status=status.HTTP_404_NOT_FOUND)

        today = date.today()

        if is_intern:
            leads = Lead.objects.filter(assigned_to=request.user)
            activities = DailyActivity.objects.filter(intern=request.user)
            demos = Demo.objects.filter(conducted_by=request.user)
            assignments = WorkAssignment.objects.filter(
                assigned_to=employee, status__in=['assigned', 'in_progress']
            )
        else:
            leads = Lead.objects.all()
            activities = DailyActivity.objects.all()
            demos = Demo.objects.all()
            assignments = WorkAssignment.objects.filter(
                assigned_to=employee, status__in=['assigned', 'in_progress']
            )

        data = {
            'total_leads': leads.count(),
            'new_leads': leads.filter(status='new').count(),
            'converted_leads': leads.filter(status='converted').count(),
            'upcoming_demos': demos.filter(scheduled_date__gte=timezone.now(), status='scheduled').count(),
            'pending_activities': activities.filter(approval_status='pending').count(),
            'recent_leads': LeadSerializer(
                leads[:10], many=True, context={'request': request}
            ).data,
            'upcoming_demos_list': DemoSerializer(
                demos.filter(scheduled_date__gte=timezone.now(), status='scheduled')[:5],
                many=True, context={'request': request}
            ).data,
            'active_assignments': WorkAssignmentSerializer(
                assignments[:5], many=True, context={'request': request}
            ).data,
        }
        return Response(data)


# ---- Lead APIs ----

@extend_schema(tags=['CRM - Leads'])
class CRMLeadListCreateView(APIView):
    """List leads (filtered for interns) or create a new lead"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        employee, is_intern = get_intern_employee(request.user)
        if not employee:
            return Response({'error': 'Employee profile not found'}, status=status.HTTP_404_NOT_FOUND)

        if is_intern:
            leads = Lead.objects.filter(assigned_to=request.user)
        else:
            leads = Lead.objects.all()

        # Filters
        lead_status = request.query_params.get('status')
        source = request.query_params.get('source')
        if lead_status:
            leads = leads.filter(status=lead_status)
        if source:
            leads = leads.filter(source=source)

        serializer = LeadSerializer(leads, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request):
        employee, is_intern = get_intern_employee(request.user)
        if not employee:
            return Response({'error': 'Employee profile not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = LeadCreateSerializer(data=request.data)
        if serializer.is_valid():
            lead = serializer.save(
                created_by=request.user,
                assigned_to=request.user if is_intern else request.data.get('assigned_to', request.user),
            )
            log_lead_activity(lead, 'created', f'Lead created for {lead.contact_person}', user=request.user)
            return Response(LeadSerializer(lead, context={'request': request}).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=['CRM - Leads'])
class CRMLeadDetailView(APIView):
    """View, update a lead"""
    permission_classes = [IsAuthenticated]

    def get_lead(self, pk, user):
        employee, is_intern = get_intern_employee(user)
        try:
            lead = Lead.objects.get(pk=pk)
        except Lead.DoesNotExist:
            return None, 'Lead not found'
        if is_intern and lead.assigned_to != user:
            return None, 'You can only view leads assigned to you'
        return lead, None

    def get(self, request, pk):
        lead, error = self.get_lead(pk, request.user)
        if error:
            return Response({'error': error}, status=status.HTTP_404_NOT_FOUND)
        return Response(LeadSerializer(lead, context={'request': request}).data)

    def patch(self, request, pk):
        lead, error = self.get_lead(pk, request.user)
        if error:
            return Response({'error': error}, status=status.HTTP_404_NOT_FOUND)

        if lead.status == 'converted':
            return Response({'error': 'Converted leads cannot be edited.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = LeadCreateSerializer(lead, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(LeadSerializer(lead, context={'request': request}).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        lead, error = self.get_lead(pk, request.user)
        if error:
            return Response({'error': error}, status=status.HTTP_404_NOT_FOUND)
        lead.delete()
        return Response({'message': 'Lead deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=['CRM - Leads'])
class CRMLeadStatusUpdateView(APIView):
    """Update lead status"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        employee, is_intern = get_intern_employee(request.user)
        if not employee:
            return Response({'error': 'Employee profile not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            lead = Lead.objects.get(pk=pk)
        except Lead.DoesNotExist:
            return Response({'error': 'Lead not found'}, status=status.HTTP_404_NOT_FOUND)

        if is_intern and lead.assigned_to != request.user:
            return Response({'error': 'You can only update leads assigned to you'}, status=status.HTTP_403_FORBIDDEN)

        if lead.status == 'converted':
            return Response({'error': 'Converted leads cannot be modified.'}, status=status.HTTP_400_BAD_REQUEST)

        new_status = request.data.get('status')
        valid_statuses = [c[0] for c in Lead.STATUS_CHOICES]
        if new_status not in valid_statuses:
            return Response({'error': f'Invalid status. Choose from: {valid_statuses}'}, status=status.HTTP_400_BAD_REQUEST)

        old_status = lead.status
        lead.status = new_status
        if request.data.get('next_follow_up_date'):
            lead.next_follow_up_date = request.data['next_follow_up_date']
        if request.data.get('closing_probability') is not None:
            lead.closing_probability = request.data['closing_probability']

        # Capture / clear the lost reason depending on the new status.
        if new_status in Lead.CLOSED_LOST_STATUSES:
            lost_reason = request.data.get('lost_reason')
            valid_reasons = [c[0] for c in Lead.LOST_REASON_CHOICES]
            if lost_reason and lost_reason not in valid_reasons:
                return Response(
                    {'error': f'Invalid lost_reason. Choose from: {valid_reasons}'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if lost_reason:
                lead.lost_reason = lost_reason
        else:
            # Re-activated / progressing lead no longer carries a lost reason.
            lead.lost_reason = ''
        lead.save()

        log_lead_activity(
            lead, 'status_change',
            f'Status changed from {old_status} to {new_status}',
            user=request.user,
            metadata={'old_status': old_status, 'new_status': new_status},
        )

        # Auto-create Client when lead is converted
        client_data = None
        if new_status == 'converted' and not lead.client:
            client = Client.objects.create(
                name=lead.contact_person,
                company_name=lead.company_name,
                email=lead.email or f'lead-{lead.pk}@placeholder.local',
                phone=lead.phone,
                notes=f'Auto-created from CRM lead #{lead.pk}. Source: {lead.get_source_display()}.',
            )
            lead.client = client
            lead.save(update_fields=['client'])
            # Back-link any quotes raised for this lead to the new client.
            lead.quotes.filter(client__isnull=True).update(client=client)
            log_lead_activity(
                lead, 'status_change',
                f'Client "{client.name}" auto-created from converted lead',
                user=request.user,
                metadata={'client_id': str(client.id), 'client_name': client.name},
            )
            client_data = {
                'id': str(client.id),
                'name': client.name,
                'company_name': client.company_name,
            }

        response_data = LeadSerializer(lead, context={'request': request}).data
        if client_data:
            response_data['converted_client'] = client_data

        return Response(response_data)


@extend_schema(tags=['CRM - Leads'])
class CRMLeadNoteCreateView(APIView):
    """Add a note to a lead"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        employee, is_intern = get_intern_employee(request.user)
        if not employee:
            return Response({'error': 'Employee profile not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            lead = Lead.objects.get(pk=pk)
        except Lead.DoesNotExist:
            return Response({'error': 'Lead not found'}, status=status.HTTP_404_NOT_FOUND)

        if is_intern and lead.assigned_to != request.user:
            return Response({'error': 'You can only add notes to leads assigned to you'}, status=status.HTTP_403_FORBIDDEN)

        note_text = request.data.get('note', '').strip()
        if not note_text:
            return Response({'error': 'Note text is required'}, status=status.HTTP_400_BAD_REQUEST)

        note = LeadNote.objects.create(lead=lead, note=note_text, created_by=request.user)
        log_lead_activity(lead, 'note_added', note_text[:100], user=request.user)
        return Response(LeadNoteSerializer(note).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=['CRM - Leads'])
class CRMLeadReferenceLinkListCreateView(APIView):
    """List or add reference links (client-provided) for a lead"""
    permission_classes = [IsAuthenticated]

    def get_lead(self, pk, user):
        employee, is_intern = get_intern_employee(user)
        try:
            lead = Lead.objects.get(pk=pk)
        except Lead.DoesNotExist:
            return None, 'Lead not found'
        if is_intern and lead.assigned_to != user:
            return None, 'You can only access leads assigned to you'
        return lead, None

    def get(self, request, pk):
        lead, error = self.get_lead(pk, request.user)
        if error:
            return Response({'error': error}, status=status.HTTP_404_NOT_FOUND)
        links = lead.reference_links.select_related('created_by').all()
        return Response(LeadReferenceLinkSerializer(links, many=True).data)

    def post(self, request, pk):
        lead, error = self.get_lead(pk, request.user)
        if error:
            return Response({'error': error}, status=status.HTTP_404_NOT_FOUND)

        url = request.data.get('url', '').strip()
        title = request.data.get('title', '').strip()
        if not url:
            return Response({'error': 'Link URL is required'}, status=status.HTTP_400_BAD_REQUEST)

        link = LeadReferenceLink.objects.create(
            lead=lead, url=url, title=title, created_by=request.user
        )
        return Response(LeadReferenceLinkSerializer(link).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=['CRM - Leads'])
class CRMLeadReferenceLinkDeleteView(APIView):
    """Delete a reference link from a lead"""
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk, link_id):
        employee, is_intern = get_intern_employee(request.user)
        try:
            lead = Lead.objects.get(pk=pk)
        except Lead.DoesNotExist:
            return Response({'error': 'Lead not found'}, status=status.HTTP_404_NOT_FOUND)
        if is_intern and lead.assigned_to != request.user:
            return Response({'error': 'You can only modify leads assigned to you'}, status=status.HTTP_403_FORBIDDEN)

        try:
            link = LeadReferenceLink.objects.get(pk=link_id, lead=lead)
        except LeadReferenceLink.DoesNotExist:
            return Response({'error': 'Reference link not found'}, status=status.HTTP_404_NOT_FOUND)

        link.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=['CRM - Leads'])
class CRMLeadCheckDuplicateView(APIView):
    """Check for duplicate leads by phone or email"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        phone = request.data.get('phone')
        email = request.data.get('email')
        duplicates = Lead.check_duplicate(phone=phone, email=email)
        return Response({
            'has_duplicates': len(duplicates) > 0,
            'duplicates': LeadSerializer(duplicates, many=True, context={'request': request}).data,
        })


# ---- Daily Activity APIs ----

@extend_schema(tags=['CRM - Activities'])
class CRMActivityListCreateView(APIView):
    """List or create daily activities"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        employee, is_intern = get_intern_employee(request.user)
        if not employee:
            return Response({'error': 'Employee profile not found'}, status=status.HTTP_404_NOT_FOUND)

        if is_intern:
            activities = DailyActivity.objects.filter(intern=request.user)
        else:
            activities = DailyActivity.objects.all()
            # Admin can filter by intern
            intern_id = request.query_params.get('intern_id')
            if intern_id:
                activities = activities.filter(intern_id=intern_id)

        # Date filters
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        if date_from:
            activities = activities.filter(date__gte=date_from)
        if date_to:
            activities = activities.filter(date__lte=date_to)

        approval = request.query_params.get('approval_status')
        if approval:
            activities = activities.filter(approval_status=approval)

        serializer = DailyActivitySerializer(activities, many=True)
        return Response(serializer.data)

    def post(self, request):
        employee, is_intern = get_intern_employee(request.user)
        if not employee:
            return Response({'error': 'Employee profile not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = DailyActivityCreateSerializer(data=request.data)
        if serializer.is_valid():
            activity_date = serializer.validated_data.get('date', date.today())

            # Check if already submitted for this date
            if DailyActivity.objects.filter(intern=request.user, date=activity_date).exists():
                return Response(
                    {'error': 'Activity already submitted for this date. Use edit instead.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Auto-detect intern_type from employee profile
            intern_type = employee.intern_type or 'digital'
            activity = serializer.save(intern=request.user, intern_type=intern_type)
            return Response(DailyActivitySerializer(activity).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=['CRM - Activities'])
class CRMActivityDetailView(APIView):
    """View or edit a daily activity (editable within 24hrs)"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        employee, is_intern = get_intern_employee(request.user)
        if not employee:
            return Response({'error': 'Employee profile not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            activity = DailyActivity.objects.get(pk=pk)
        except DailyActivity.DoesNotExist:
            return Response({'error': 'Activity not found'}, status=status.HTTP_404_NOT_FOUND)

        if is_intern and activity.intern != request.user:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        return Response(DailyActivitySerializer(activity).data)

    def patch(self, request, pk):
        employee, is_intern = get_intern_employee(request.user)
        if not employee:
            return Response({'error': 'Employee profile not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            activity = DailyActivity.objects.get(pk=pk)
        except DailyActivity.DoesNotExist:
            return Response({'error': 'Activity not found'}, status=status.HTTP_404_NOT_FOUND)

        if is_intern and activity.intern != request.user:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        if is_intern and not activity.is_editable:
            return Response({'error': 'Activity can only be edited within 24 hours'}, status=status.HTTP_403_FORBIDDEN)

        serializer = DailyActivityCreateSerializer(activity, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(DailyActivitySerializer(activity).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=['CRM - Activities'])
class CRMActivityApproveView(APIView):
    """Approve or reject a daily activity (admin only)"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        employee, is_intern = get_intern_employee(request.user)
        if not employee:
            return Response({'error': 'Employee profile not found'}, status=status.HTTP_404_NOT_FOUND)

        if is_intern:
            return Response({'error': 'Only admins can approve activities'}, status=status.HTTP_403_FORBIDDEN)

        try:
            activity = DailyActivity.objects.get(pk=pk)
        except DailyActivity.DoesNotExist:
            return Response({'error': 'Activity not found'}, status=status.HTTP_404_NOT_FOUND)

        action = request.data.get('action')  # 'approve' or 'reject'
        if action not in ('approve', 'reject'):
            return Response({'error': 'Action must be "approve" or "reject"'}, status=status.HTTP_400_BAD_REQUEST)

        activity.approval_status = 'approved' if action == 'approve' else 'rejected'
        activity.approved_by = request.user
        activity.save()

        return Response(DailyActivitySerializer(activity).data)


@extend_schema(tags=['CRM - Activities'])
class CRMActivityWeeklySummaryView(APIView):
    """Weekly summary of activities for an intern"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        employee, is_intern = get_intern_employee(request.user)
        if not employee:
            return Response({'error': 'Employee profile not found'}, status=status.HTTP_404_NOT_FOUND)

        from datetime import timedelta
        today = date.today()
        week_start = today - timedelta(days=today.weekday())

        if is_intern:
            activities = DailyActivity.objects.filter(intern=request.user, date__gte=week_start, date__lte=today)
        else:
            intern_id = request.query_params.get('intern_id')
            if intern_id:
                activities = DailyActivity.objects.filter(intern_id=intern_id, date__gte=week_start, date__lte=today)
            else:
                activities = DailyActivity.objects.filter(date__gte=week_start, date__lte=today)

        summary = activities.aggregate(
            total_posts=Sum('social_media_posts'),
            total_reels=Sum('reels_created'),
            total_dms=Sum('dms_sent'),
            total_digital_leads=Sum('digital_leads_generated'),
            total_calls=Sum('calls_made'),
            total_visits=Sum('visits_done'),
            total_demos=Sum('demos_conducted'),
            total_field_leads=Sum('field_leads_generated'),
        )

        # Replace None with 0
        summary = {k: v or 0 for k, v in summary.items()}
        summary['week_start'] = week_start.isoformat()
        summary['week_end'] = today.isoformat()
        summary['days_logged'] = activities.count()

        return Response(summary)


# ---- Demo APIs ----

@extend_schema(tags=['CRM - Demos'])
class CRMDemoListCreateView(APIView):
    """List demos or schedule a new demo"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        employee, is_intern = get_intern_employee(request.user)
        if not employee:
            return Response({'error': 'Employee profile not found'}, status=status.HTTP_404_NOT_FOUND)

        if is_intern:
            demos = Demo.objects.filter(conducted_by=request.user)
        else:
            demos = Demo.objects.all()

        demo_status = request.query_params.get('status')
        if demo_status:
            demos = demos.filter(status=demo_status)

        serializer = DemoSerializer(demos, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request):
        employee, is_intern = get_intern_employee(request.user)
        if not employee:
            return Response({'error': 'Employee profile not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = DemoCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            demo = serializer.save(conducted_by=request.user, created_by=request.user)

            # Auto-update lead status to demo_scheduled
            lead = demo.lead
            if lead.status in ('new', 'contacted', 'interested'):
                lead.status = 'demo_scheduled'
                lead.save()

            log_lead_activity(
                lead, 'demo_scheduled',
                f'Demo scheduled for {demo.scheduled_date.strftime("%b %d, %Y %I:%M %p")} at {demo.location or "TBD"}',
                user=request.user,
                metadata={'demo_id': demo.id},
            )

            return Response(DemoSerializer(demo, context={'request': request}).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=['CRM - Demos'])
class CRMDemoDetailView(APIView):
    """View or update a demo"""
    permission_classes = [IsAuthenticated]

    def get_demo(self, pk, user):
        employee, is_intern = get_intern_employee(user)
        try:
            demo = Demo.objects.get(pk=pk)
        except Demo.DoesNotExist:
            return None, 'Demo not found'
        if is_intern and demo.conducted_by != user:
            return None, 'Not found'
        return demo, None

    def get(self, request, pk):
        demo, error = self.get_demo(pk, request.user)
        if error:
            return Response({'error': error}, status=status.HTTP_404_NOT_FOUND)
        return Response(DemoSerializer(demo, context={'request': request}).data)

    def patch(self, request, pk):
        demo, error = self.get_demo(pk, request.user)
        if error:
            return Response({'error': error}, status=status.HTTP_404_NOT_FOUND)

        serializer = DemoCreateSerializer(demo, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(DemoSerializer(demo, context={'request': request}).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=['CRM - Demos'])
class CRMDemoStatusUpdateView(APIView):
    """Update demo status"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        employee, is_intern = get_intern_employee(request.user)
        if not employee:
            return Response({'error': 'Employee profile not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            demo = Demo.objects.get(pk=pk)
        except Demo.DoesNotExist:
            return Response({'error': 'Demo not found'}, status=status.HTTP_404_NOT_FOUND)

        if is_intern and demo.conducted_by != request.user:
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

        new_status = request.data.get('status')
        valid_statuses = [c[0] for c in Demo.STATUS_CHOICES]
        if new_status not in valid_statuses:
            return Response({'error': f'Invalid status. Choose from: {valid_statuses}'}, status=status.HTTP_400_BAD_REQUEST)

        demo.status = new_status
        if request.data.get('outcome_notes'):
            demo.outcome_notes = request.data['outcome_notes']
        if request.data.get('closing_probability') is not None:
            demo.closing_probability = request.data['closing_probability']
        demo.save()

        # Auto-update lead status based on demo outcome
        lead = demo.lead
        if new_status == 'converted':
            lead.status = 'converted'
            lead.save()
            log_lead_activity(lead, 'demo_converted', f'Demo converted! {demo.outcome_notes or ""}', user=request.user, metadata={'demo_id': demo.id})
            # Auto-create Client
            if not lead.client:
                client = Client.objects.create(
                    name=lead.contact_person,
                    company_name=lead.company_name,
                    email=lead.email or f'lead-{lead.pk}@placeholder.local',
                    phone=lead.phone,
                    notes=f'Auto-created from CRM lead #{lead.pk} via demo conversion.',
                )
                lead.client = client
                lead.save(update_fields=['client'])
                log_lead_activity(lead, 'status_change', f'Client "{client.name}" auto-created', user=request.user, metadata={'client_id': str(client.id)})
        elif new_status == 'completed' and lead.status == 'demo_scheduled':
            lead.status = 'demo_completed'
            lead.save()
            log_lead_activity(lead, 'demo_completed', f'Demo completed. {demo.outcome_notes or ""}', user=request.user, metadata={'demo_id': demo.id})

        return Response(DemoSerializer(demo, context={'request': request}).data)


# ---- Admin CRM APIs ----

@extend_schema(tags=['CRM - Admin'])
class CRMAdminReassignLeadsView(APIView):
    """Bulk reassign leads from one intern to another (e.g., when intern leaves)"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        employee, is_intern = get_intern_employee(request.user)
        if not employee or is_intern:
            return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)

        from_user_id = request.data.get('from_user_id')
        to_user_id = request.data.get('to_user_id')
        lead_ids = request.data.get('lead_ids')  # Optional — if empty, reassign all

        if not from_user_id or not to_user_id:
            return Response({'error': 'from_user_id and to_user_id are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            from_user = User.objects.get(pk=from_user_id)
            to_user = User.objects.get(pk=to_user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        leads = Lead.objects.filter(assigned_to=from_user)
        if lead_ids:
            leads = leads.filter(pk__in=lead_ids)

        count = leads.count()
        leads.update(assigned_to=to_user)

        return Response({
            'reassigned': count,
            'from': from_user.get_full_name() or from_user.username,
            'to': to_user.get_full_name() or to_user.username,
        })


@extend_schema(tags=['CRM - Admin'])
class CRMAdminInternStatsView(APIView):
    """Get CRM stats for all interns (for admin overview)"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        employee, is_intern = get_intern_employee(request.user)
        if not employee or is_intern:
            return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)

        interns = Employee.objects.filter(
            employment_type='intern', status='active'
        ).select_related('user')

        result = []
        for intern in interns:
            user = intern.user
            leads = Lead.objects.filter(assigned_to=user)
            result.append({
                'employee_id': str(intern.id),
                'emp_code': intern.employee_id,
                'name': intern.full_name,
                'intern_type': intern.intern_type,
                'total_leads': leads.count(),
                'new_leads': leads.filter(status='new').count(),
                'converted_leads': leads.filter(status='converted').count(),
                'pending_activities': DailyActivity.objects.filter(
                    intern=user, approval_status='pending'
                ).count(),
                'upcoming_demos': Demo.objects.filter(
                    conducted_by=user, status='scheduled',
                    scheduled_date__gte=timezone.now()
                ).count(),
            })

        return Response(result)


class CRMInternLeadReportView(APIView):
    """Get leads submitted by each intern, filterable by date range"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        employee, is_intern = get_intern_employee(request.user)
        if not employee:
            return Response({'error': 'Employee profile not found'}, status=status.HTTP_404_NOT_FOUND)

        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        intern_id = request.query_params.get('intern_id')

        leads = Lead.objects.select_related('assigned_to', 'created_by').all()

        if is_intern:
            leads = leads.filter(created_by=request.user)
        elif intern_id:
            leads = leads.filter(created_by_id=intern_id)

        if date_from:
            leads = leads.filter(created_at__date__gte=date_from)
        if date_to:
            leads = leads.filter(created_at__date__lte=date_to)

        # Group by intern
        from django.db.models import Count, Q
        from collections import defaultdict
        intern_data = defaultdict(lambda: {'leads': [], 'total': 0, 'new': 0, 'converted': 0, 'lost': 0})

        for lead in leads.order_by('-created_at'):
            creator_name = lead.created_by.get_full_name() if lead.created_by else 'Unknown'
            creator_id = lead.created_by_id or 0
            key = str(creator_id)
            entry = intern_data[key]
            entry['intern_id'] = creator_id
            entry['intern_name'] = creator_name
            entry['total'] += 1
            if lead.status == 'new':
                entry['new'] += 1
            elif lead.status == 'converted':
                entry['converted'] += 1
            elif lead.status == 'lost':
                entry['lost'] += 1
            entry['leads'].append({
                'id': lead.id,
                'contact_person': lead.contact_person,
                'company_name': lead.company_name,
                'phone': lead.phone,
                'status': lead.status,
                'source': lead.source,
                'created_at': lead.created_at.isoformat(),
            })

        result = list(intern_data.values())
        result.sort(key=lambda x: x['total'], reverse=True)
        return Response(result)


# ============== Helper: Create Lead Activity ==============

def log_lead_activity(lead, activity_type, description, user=None, metadata=None):
    """Create a LeadActivity entry for the unified timeline."""
    LeadActivity.objects.create(
        lead=lead,
        activity_type=activity_type,
        description=description,
        metadata=metadata or {},
        created_by=user,
    )


# ============== Follow-up Endpoints ==============

class CRMLeadFollowUpListCreateView(APIView):
    """List and create follow-ups for a lead"""
    permission_classes = [IsAuthenticated]

    def get(self, request, lead_id):
        lead = Lead.objects.filter(id=lead_id).first()
        if not lead:
            return Response({'error': 'Lead not found'}, status=status.HTTP_404_NOT_FOUND)
        follow_ups = lead.follow_ups.all()
        return Response(FollowUpSerializer(follow_ups, many=True).data)

    def post(self, request, lead_id):
        lead = Lead.objects.filter(id=lead_id).first()
        if not lead:
            return Response({'error': 'Lead not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = FollowUpCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        follow_up = serializer.save(lead=lead, created_by=request.user)

        # Update lead's next_follow_up_date
        lead.next_follow_up_date = follow_up.scheduled_date.date()
        lead.save(update_fields=['next_follow_up_date'])

        # Log activity
        log_lead_activity(
            lead, 'follow_up_scheduled',
            f'{follow_up.get_follow_up_type_display()} scheduled for {follow_up.scheduled_date.strftime("%b %d, %Y %I:%M %p")}',
            user=request.user,
            metadata={'follow_up_id': follow_up.id, 'type': follow_up.follow_up_type},
        )

        return Response(FollowUpSerializer(follow_up).data, status=status.HTTP_201_CREATED)


class CRMFollowUpDetailView(APIView):
    """Update a follow-up (complete, reschedule, etc.)"""
    permission_classes = [IsAuthenticated]

    def patch(self, request, follow_up_id):
        follow_up = FollowUp.objects.filter(id=follow_up_id).first()
        if not follow_up:
            return Response({'error': 'Follow-up not found'}, status=status.HTTP_404_NOT_FOUND)

        old_status = follow_up.status
        new_status = request.data.get('status', follow_up.status)

        serializer = FollowUpSerializer(follow_up, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # If completing the follow-up
        if new_status == 'completed' and old_status != 'completed':
            follow_up.completed_at = timezone.now()
            follow_up.save(update_fields=['completed_at'])
            log_lead_activity(
                follow_up.lead, 'follow_up_completed',
                f'{follow_up.get_follow_up_type_display()} completed. {follow_up.outcome or ""}',
                user=request.user,
                metadata={'follow_up_id': follow_up.id, 'outcome': follow_up.outcome},
            )
        elif new_status == 'missed' and old_status != 'missed':
            log_lead_activity(
                follow_up.lead, 'follow_up_missed',
                f'{follow_up.get_follow_up_type_display()} was missed.',
                user=request.user,
                metadata={'follow_up_id': follow_up.id},
            )

        return Response(FollowUpSerializer(follow_up).data)


class CRMUpcomingFollowUpsView(APIView):
    """Get all upcoming follow-ups for the authenticated user"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        employee, is_intern = get_intern_employee(request.user)
        if not employee:
            return Response({'error': 'Employee profile not found'}, status=status.HTTP_404_NOT_FOUND)

        follow_ups = FollowUp.objects.filter(status='scheduled').select_related('lead', 'created_by')

        if is_intern:
            follow_ups = follow_ups.filter(lead__assigned_to=request.user)

        # Include overdue ones too
        today_follow_ups = follow_ups.filter(
            scheduled_date__date=timezone.now().date()
        )
        overdue = follow_ups.filter(
            scheduled_date__lt=timezone.now()
        )
        upcoming = follow_ups.filter(
            scheduled_date__gt=timezone.now()
        )[:10]

        return Response({
            'today': FollowUpSerializer(today_follow_ups, many=True).data,
            'overdue': FollowUpSerializer(overdue, many=True).data,
            'upcoming': FollowUpSerializer(upcoming, many=True).data,
        })


# ============== Lead Timeline ==============

class CRMLeadTimelineView(APIView):
    """Unified timeline for a lead (activities + notes + follow-ups + demos merged)"""
    permission_classes = [IsAuthenticated]

    def get(self, request, lead_id):
        lead = Lead.objects.filter(id=lead_id).first()
        if not lead:
            return Response({'error': 'Lead not found'}, status=status.HTTP_404_NOT_FOUND)

        timeline = []

        # Activities
        for activity in lead.activities.select_related('created_by').all():
            timeline.append({
                'type': 'activity',
                'activity_type': activity.activity_type,
                'type_display': activity.get_activity_type_display(),
                'description': activity.description,
                'metadata': activity.metadata,
                'created_by': activity.created_by.get_full_name() if activity.created_by else '',
                'created_at': activity.created_at.isoformat(),
            })

        # Notes
        for note in lead.lead_notes.select_related('created_by').all():
            timeline.append({
                'type': 'note',
                'activity_type': 'note_added',
                'type_display': 'Note',
                'description': note.note,
                'metadata': {},
                'created_by': note.created_by.get_full_name() if note.created_by else '',
                'created_at': note.created_at.isoformat(),
            })

        # Follow-ups
        for fu in lead.follow_ups.select_related('created_by').all():
            timeline.append({
                'type': 'follow_up',
                'activity_type': f'follow_up_{fu.status}',
                'type_display': f'{fu.get_follow_up_type_display()} ({fu.get_status_display()})',
                'description': fu.notes or fu.outcome or f'{fu.get_follow_up_type_display()} {fu.get_status_display().lower()}',
                'metadata': {
                    'follow_up_id': fu.id,
                    'follow_up_type': fu.follow_up_type,
                    'status': fu.status,
                    'scheduled_date': fu.scheduled_date.isoformat(),
                    'is_overdue': fu.is_overdue,
                },
                'created_by': fu.created_by.get_full_name() if fu.created_by else '',
                'created_at': fu.created_at.isoformat(),
            })

        # Demos
        for demo in lead.demos.select_related('conducted_by', 'created_by').all():
            timeline.append({
                'type': 'demo',
                'activity_type': f'demo_{demo.status}',
                'type_display': f'Demo ({demo.get_status_display()})',
                'description': demo.outcome_notes or f'Demo {demo.get_status_display().lower()} at {demo.location or "TBD"}',
                'metadata': {
                    'demo_id': demo.id,
                    'status': demo.status,
                    'scheduled_date': demo.scheduled_date.isoformat(),
                    'location': demo.location,
                    'probability': demo.closing_probability,
                },
                'created_by': demo.conducted_by.get_full_name() if demo.conducted_by else (demo.created_by.get_full_name() if demo.created_by else ''),
                'created_at': demo.created_at.isoformat(),
            })

        # Sort by date descending
        timeline.sort(key=lambda x: x['created_at'], reverse=True)

        return Response(timeline)


# ============== Create Project from Lead ==============

class CRMLeadCreateProjectView(APIView):
    """Create a project for a converted lead's client"""
    permission_classes = [IsAuthenticated]

    def post(self, request, lead_id):
        lead = Lead.objects.filter(id=lead_id).select_related('client').first()
        if not lead:
            return Response({'error': 'Lead not found'}, status=status.HTTP_404_NOT_FOUND)

        if not lead.client:
            return Response({'error': 'Lead has no associated client. Convert the lead first.'}, status=status.HTTP_400_BAD_REQUEST)

        name = request.data.get('name', '').strip()
        if not name:
            return Response({'error': 'Project name is required'}, status=status.HTTP_400_BAD_REQUEST)

        project = Project.objects.create(
            client=lead.client,
            name=name,
            project_type=request.data.get('project_type', 'web_app'),
            description=request.data.get('description', ''),
            status='confirmed',
            estimated_budget=request.data.get('estimated_budget') or None,
            start_date=request.data.get('start_date') or None,
            deadline=request.data.get('deadline') or None,
            notes=request.data.get('notes', ''),
        )

        # Attach the lead's quotes (that have no project yet) to the new project.
        lead.quotes.filter(project__isnull=True).update(project=project)

        log_lead_activity(
            lead, 'status_change',
            f'Project "{project.name}" created for client "{lead.client.name}"',
            user=request.user,
            metadata={'project_id': str(project.id), 'project_name': project.name},
        )

        return Response({
            'id': str(project.id),
            'name': project.name,
            'project_type': project.project_type,
            'status': project.status,
            'client_id': str(lead.client.id),
            'client_name': lead.client.name,
        }, status=status.HTTP_201_CREATED)


# ============== Quotes for a Lead ==============

@extend_schema(tags=['CRM - Leads'])
class CRMLeadQuoteListCreateView(APIView):
    """List or create quotes for a CRM lead (quote first, convert later)."""
    permission_classes = [IsAuthenticated]

    def get(self, request, lead_id):
        lead = Lead.objects.filter(id=lead_id).first()
        if not lead:
            return Response({'error': 'Lead not found'}, status=status.HTTP_404_NOT_FOUND)
        data = [{
            'id': str(q.id),
            'quote_number': q.quote_number,
            'title': q.title,
            'status': q.status,
            'total_amount': str(q.total_amount),
            'issue_date': str(q.issue_date) if q.issue_date else None,
            'valid_until': str(q.valid_until) if q.valid_until else None,
            'is_expired': q.is_expired,
            'recipient_name': q.recipient_name,
        } for q in lead.quotes.order_by('-created_at')]
        return Response(data)

    def post(self, request, lead_id):
        from core.models import Quote, QuoteItem
        lead = Lead.objects.filter(id=lead_id).first()
        if not lead:
            return Response({'error': 'Lead not found'}, status=status.HTTP_404_NOT_FOUND)

        data = request.data
        if not data.get('title') or not data.get('valid_until'):
            return Response({'error': 'title and valid_until are required'},
                            status=status.HTTP_400_BAD_REQUEST)

        quote = Quote(
            lead=lead,
            client=lead.client,  # already linked if the lead was converted, else None
            title=data.get('title', ''),
            description=data.get('description', ''),
            status=data.get('status', 'draft'),
            discount=data.get('discount', 0),
            tax_rate=data.get('tax_rate', 0),
            issue_date=data.get('issue_date') or timezone.now().date(),
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

        for i, item in enumerate(data.get('items', [])):
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

        log_lead_activity(
            lead, 'note_added',
            f'Quote "{quote.quote_number}" created for lead',
            user=request.user,
            metadata={'quote_id': str(quote.id), 'quote_number': quote.quote_number},
        )
        return Response({
            'id': str(quote.id),
            'quote_number': quote.quote_number,
            'total_amount': str(quote.total_amount),
            'message': 'Quote created',
        }, status=status.HTTP_201_CREATED)


# ============== Owner: Dues Dashboard ==============

@extend_schema(tags=['Owner'])
class OwnerDuesDashboardView(APIView):
    """Combined dues dashboard: AMC + credential renewals"""
    permission_classes = [IsAuthenticated, IsOwnerOrPartner]

    def get(self, request):
        from datetime import timedelta
        from decimal import Decimal

        today = date.today()

        # AMC dues
        overdue_amc = AMCContract.objects.filter(
            status='active', next_due_date__lt=today
        ).select_related('project', 'project__client')
        upcoming_amc = AMCContract.objects.filter(
            status='active', next_due_date__range=[today, today + timedelta(days=30)]
        ).select_related('project', 'project__client')

        overdue_amc_data = [{
            'id': str(a.id), 'project_name': a.project.name,
            'client_name': a.project.client.name, 'amount': str(a.annual_amount),
            'due_date': str(a.next_due_date), 'days_overdue': abs(a.days_until_due),
            'billing_cycle': a.billing_cycle,
            'contract_type': a.contract_type,
            'contract_type_display': a.get_contract_type_display(),
        } for a in overdue_amc]

        upcoming_amc_data = [{
            'id': str(a.id), 'project_name': a.project.name,
            'client_name': a.project.client.name, 'amount': str(a.annual_amount),
            'due_date': str(a.next_due_date), 'days_until_due': a.days_until_due,
            'billing_cycle': a.billing_cycle,
            'contract_type': a.contract_type,
            'contract_type_display': a.get_contract_type_display(),
        } for a in upcoming_amc]

        total_amc_overdue = overdue_amc.aggregate(total=Sum('annual_amount'))['total'] or Decimal('0')
        total_amc_upcoming = upcoming_amc.aggregate(total=Sum('annual_amount'))['total'] or Decimal('0')

        # Credential dues
        expired_creds = Credential.objects.filter(
            expiry_date__lt=today, is_active=True
        ).select_related('project', 'project__client')
        expiring_creds = Credential.objects.filter(
            expiry_date__range=[today, today + timedelta(days=30)], is_active=True
        ).select_related('project', 'project__client')

        expired_creds_data = [{
            'id': str(c.id), 'name': c.name, 'credential_type': c.credential_type,
            'project_name': c.project.name, 'client_name': c.project.client.name,
            'renewal_cost': str(c.renewal_cost or 0), 'expired_since': str(c.expiry_date),
            'days_expired': abs(c.days_until_expiry),
        } for c in expired_creds]

        expiring_creds_data = [{
            'id': str(c.id), 'name': c.name, 'credential_type': c.credential_type,
            'project_name': c.project.name, 'client_name': c.project.client.name,
            'renewal_cost': str(c.renewal_cost or 0), 'expiry_date': str(c.expiry_date),
            'days_until_expiry': c.days_until_expiry,
        } for c in expiring_creds]

        total_cred_cost = (
            (expired_creds.aggregate(total=Sum('renewal_cost'))['total'] or Decimal('0')) +
            (expiring_creds.aggregate(total=Sum('renewal_cost'))['total'] or Decimal('0'))
        )

        total_dues = total_amc_overdue + total_amc_upcoming + total_cred_cost

        return Response({
            'total_dues': str(total_dues),
            'amc_dues': {
                'overdue': overdue_amc_data,
                'upcoming': upcoming_amc_data,
                'total_overdue': str(total_amc_overdue),
                'total_upcoming': str(total_amc_upcoming),
            },
            'credential_dues': {
                'expired': expired_creds_data,
                'expiring_soon': expiring_creds_data,
                'total_renewal_cost': str(total_cred_cost),
            },
        })


# ============== Owner: Credential APIs ==============

@extend_schema(tags=['Owner'])
class OwnerCredentialListView(APIView):
    """List all credentials with renewal status"""
    permission_classes = [IsAuthenticated, IsOwnerOrPartner]

    def get(self, request):
        creds = Credential.objects.select_related('project', 'project__client').filter(is_active=True)

        cred_type = request.query_params.get('type')
        if cred_type:
            creds = creds.filter(credential_type=cred_type)

        search = request.query_params.get('search')
        if search:
            creds = creds.filter(
                Q(name__icontains=search) | Q(project__name__icontains=search) |
                Q(project__client__name__icontains=search)
            )

        data = [{
            'id': str(c.id), 'name': c.name, 'credential_type': c.credential_type,
            'credential_type_display': c.get_credential_type_display(),
            'provider': c.provider, 'project_name': c.project.name,
            'project_id': str(c.project.id),
            'client_name': c.project.client.name,
            'expiry_date': str(c.expiry_date) if c.expiry_date else None,
            'days_until_expiry': c.days_until_expiry,
            'is_expired': c.is_expired, 'is_expiring_soon': c.is_expiring_soon,
            'auto_renew': c.auto_renew, 'renewal_cost': str(c.renewal_cost or 0),
            'last_renewed_date': str(c.last_renewed_date) if c.last_renewed_date else None,
        } for c in creds]

        return Response(data)


@extend_schema(tags=['Owner'])
class OwnerCredentialExpiringView(APIView):
    """Expired + expiring credentials in categories"""
    permission_classes = [IsAuthenticated, IsOwnerOrPartner]

    def get(self, request):
        from datetime import timedelta
        today = date.today()

        expired = Credential.objects.filter(
            expiry_date__lt=today, is_active=True
        ).select_related('project', 'project__client')

        this_week = Credential.objects.filter(
            expiry_date__gte=today, expiry_date__lte=today + timedelta(days=7), is_active=True
        ).select_related('project', 'project__client')

        this_month = Credential.objects.filter(
            expiry_date__gt=today + timedelta(days=7),
            expiry_date__lte=today + timedelta(days=30), is_active=True
        ).select_related('project', 'project__client')

        def serialize(qs):
            return [{
                'id': str(c.id), 'name': c.name, 'credential_type': c.credential_type,
                'credential_type_display': c.get_credential_type_display(),
                'project_name': c.project.name, 'client_name': c.project.client.name,
                'expiry_date': str(c.expiry_date), 'days_until_expiry': c.days_until_expiry,
                'renewal_cost': str(c.renewal_cost or 0), 'auto_renew': c.auto_renew,
            } for c in qs]

        return Response({
            'expired': serialize(expired),
            'this_week': serialize(this_week),
            'this_month': serialize(this_month),
            'counts': {
                'expired': expired.count(),
                'this_week': this_week.count(),
                'this_month': this_month.count(),
            },
        })


@extend_schema(tags=['Owner'])
class OwnerCredentialRenewView(APIView):
    """Renew a credential: update expiry and record history"""
    permission_classes = [IsAuthenticated, IsOwnerOrPartner]

    def post(self, request, pk):
        try:
            credential = Credential.objects.get(pk=pk, is_active=True)
        except Credential.DoesNotExist:
            return Response({'error': 'Credential not found'}, status=status.HTTP_404_NOT_FOUND)

        new_expiry = request.data.get('new_expiry_date')
        if not new_expiry:
            return Response({'error': 'new_expiry_date is required'}, status=status.HTTP_400_BAD_REQUEST)

        cost = request.data.get('cost')
        notes = request.data.get('notes', '')

        CredentialRenewal.objects.create(
            credential=credential,
            old_expiry=credential.expiry_date,
            new_expiry=new_expiry,
            cost=cost,
            notes=notes,
        )
        credential.expiry_date = new_expiry
        credential.last_renewed_date = date.today()
        credential.save()

        return Response({
            'message': f'Credential "{credential.name}" renewed successfully',
            'id': str(credential.id), 'name': credential.name,
            'new_expiry_date': str(credential.expiry_date),
            'last_renewed_date': str(credential.last_renewed_date),
        })


@extend_schema(tags=['Owner'])
class OwnerCredentialRenewalHistoryView(APIView):
    """Renewal history for a credential"""
    permission_classes = [IsAuthenticated, IsOwnerOrPartner]

    def get(self, request, pk):
        try:
            credential = Credential.objects.get(pk=pk)
        except Credential.DoesNotExist:
            return Response({'error': 'Credential not found'}, status=status.HTTP_404_NOT_FOUND)

        renewals = credential.renewal_history.all()
        data = [{
            'id': str(r.id), 'renewed_date': str(r.renewed_date),
            'old_expiry': str(r.old_expiry) if r.old_expiry else None,
            'new_expiry': str(r.new_expiry), 'cost': str(r.cost or 0),
            'notes': r.notes, 'created_at': str(r.created_at),
        } for r in renewals]

        return Response({
            'credential_name': credential.name,
            'credential_type': credential.credential_type,
            'renewals': data,
        })


# ============== Owner: AMC APIs ==============

@extend_schema(tags=['Owner'])
class OwnerAMCListView(APIView):
    """List all AMC contracts"""
    permission_classes = [IsAuthenticated, IsOwnerOrPartner]

    def get(self, request):
        contracts = AMCContract.objects.select_related('project', 'project__client').all()

        status_filter = request.query_params.get('status')
        if status_filter:
            contracts = contracts.filter(status=status_filter)

        type_filter = request.query_params.get('type')
        if type_filter:
            contracts = contracts.filter(contract_type=type_filter)

        data = [{
            'id': str(a.id), 'project_name': a.project.name,
            'project_id': str(a.project.id),
            'client_name': a.project.client.name,
            'contract_type': a.contract_type,
            'contract_type_display': a.get_contract_type_display(),
            'annual_amount': str(a.annual_amount),
            'billing_cycle': a.billing_cycle,
            'billing_cycle_display': a.get_billing_cycle_display(),
            'start_date': str(a.start_date), 'end_date': str(a.end_date),
            'next_due_date': str(a.next_due_date),
            'status': a.status, 'status_display': a.get_status_display(),
            'auto_renew': a.auto_renew,
            'is_overdue': a.is_overdue, 'is_due_soon': a.is_due_soon,
            'days_until_due': a.days_until_due,
            'total_paid': str(a.total_paid),
        } for a in contracts]

        return Response(data)


@extend_schema(tags=['Owner'])
class OwnerAMCDetailView(APIView):
    """AMC contract detail with payment history"""
    permission_classes = [IsAuthenticated, IsOwnerOrPartner]

    def get(self, request, pk):
        try:
            amc = AMCContract.objects.select_related('project', 'project__client').get(pk=pk)
        except AMCContract.DoesNotExist:
            return Response({'error': 'AMC contract not found'}, status=status.HTTP_404_NOT_FOUND)

        payments = amc.payments.all()
        payments_data = [{
            'id': str(p.id), 'payment_date': str(p.payment_date),
            'amount': str(p.amount), 'period_start': str(p.period_start),
            'period_end': str(p.period_end), 'payment_method': p.payment_method,
            'payment_method_display': p.get_payment_method_display(),
            'reference': p.reference, 'notes': p.notes,
        } for p in payments]

        return Response({
            'id': str(amc.id), 'project_name': amc.project.name,
            'project_id': str(amc.project.id),
            'client_name': amc.project.client.name,
            'contract_type': amc.contract_type,
            'contract_type_display': amc.get_contract_type_display(),
            'annual_amount': str(amc.annual_amount),
            'billing_cycle': amc.billing_cycle,
            'billing_cycle_display': amc.get_billing_cycle_display(),
            'start_date': str(amc.start_date), 'end_date': str(amc.end_date),
            'next_due_date': str(amc.next_due_date),
            'status': amc.status, 'auto_renew': amc.auto_renew,
            'is_overdue': amc.is_overdue, 'is_due_soon': amc.is_due_soon,
            'days_until_due': amc.days_until_due,
            'total_paid': str(amc.total_paid),
            'notes': amc.notes,
            'payments': payments_data,
        })


@extend_schema(tags=['Owner'])
class OwnerAMCCreateView(APIView):
    """Create an AMC contract for a project"""
    permission_classes = [IsAuthenticated, IsOwnerOrPartner]

    def post(self, request):
        from dateutil.relativedelta import relativedelta

        project_id = request.data.get('project_id')
        if not project_id:
            return Response({'error': 'project_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            project = Project.objects.get(pk=project_id)
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)

        contract_type = request.data.get('contract_type', 'amc')
        annual_amount = request.data.get('annual_amount')
        billing_cycle = request.data.get('billing_cycle', 'yearly')
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        notes = request.data.get('notes', '')
        auto_renew = request.data.get('auto_renew', False)

        if not all([annual_amount, start_date, end_date]):
            return Response({'error': 'annual_amount, start_date, end_date are required'}, status=status.HTTP_400_BAD_REQUEST)

        from datetime import datetime
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()

        cycle_map = {
            'monthly': relativedelta(months=1),
            'quarterly': relativedelta(months=3),
            'half_yearly': relativedelta(months=6),
            'yearly': relativedelta(years=1),
        }
        next_due = start + cycle_map.get(billing_cycle, relativedelta(years=1))

        amc = AMCContract.objects.create(
            project=project, contract_type=contract_type, annual_amount=annual_amount,
            billing_cycle=billing_cycle, start_date=start, end_date=end,
            next_due_date=next_due, auto_renew=auto_renew, notes=notes,
        )

        return Response({
            'id': str(amc.id), 'project_name': project.name,
            'contract_type': amc.contract_type,
            'contract_type_display': amc.get_contract_type_display(),
            'annual_amount': str(amc.annual_amount),
            'next_due_date': str(amc.next_due_date),
            'message': f'{amc.get_contract_type_display()} contract created successfully',
        }, status=status.HTTP_201_CREATED)


@extend_schema(tags=['Owner'])
class OwnerAMCRecordPaymentView(APIView):
    """Record an AMC payment"""
    permission_classes = [IsAuthenticated, IsOwnerOrPartner]

    def post(self, request, pk):
        try:
            amc = AMCContract.objects.get(pk=pk)
        except AMCContract.DoesNotExist:
            return Response({'error': 'AMC contract not found'}, status=status.HTTP_404_NOT_FOUND)

        amount = request.data.get('amount')
        period_start = request.data.get('period_start')
        period_end = request.data.get('period_end')

        if not all([amount, period_start, period_end]):
            return Response({'error': 'amount, period_start, period_end are required'}, status=status.HTTP_400_BAD_REQUEST)

        payment = AMCPayment.objects.create(
            amc=amc,
            payment_date=request.data.get('payment_date', date.today()),
            amount=amount,
            period_start=period_start,
            period_end=period_end,
            payment_method=request.data.get('payment_method', 'bank_transfer'),
            reference=request.data.get('reference', ''),
            notes=request.data.get('notes', ''),
        )
        amc.advance_due_date()

        return Response({
            'id': str(payment.id),
            'amount': str(payment.amount),
            'next_due_date': str(amc.next_due_date),
            'message': 'Payment recorded and due date advanced',
        }, status=status.HTTP_201_CREATED)


# ============== Owner: Completion Certificate API ==============

@extend_schema(tags=['Owner'])
class OwnerProjectCompletionCertificateView(APIView):
    """Project completion certificate as JSON or PDF"""
    permission_classes = [IsAuthenticated, IsOwnerOrPartner]

    def get(self, request, pk):
        from core.models import Invoice, Payment, CompanySettings
        from decimal import Decimal

        try:
            project = Project.objects.select_related('client').prefetch_related(
                'team_members', 'credentials'
            ).get(pk=pk)
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)

        # Financial summary
        total_invoiced = Invoice.objects.filter(project=project).aggregate(
            total=Sum('total_amount'))['total'] or Decimal('0')
        total_paid = Payment.objects.filter(invoice__project=project).aggregate(
            total=Sum('amount'))['total'] or Decimal('0')

        amc = project.amc_contracts.first()
        credentials = project.credentials.filter(is_active=True)
        deliverables_list = [d.strip() for d in project.deliverables.split('\n') if d.strip()] if project.deliverables else []

        # PDF format
        if request.query_params.get('format') == 'pdf':
            try:
                from weasyprint import HTML
                from django.template.loader import render_to_string
                from django.http import HttpResponse

                company = CompanySettings.get_settings()
                context = {
                    'project': project, 'company': company,
                    'total_invoiced': total_invoiced, 'total_paid': total_paid,
                    'balance_due': total_invoiced - total_paid,
                    'amc': amc, 'credentials': credentials,
                    'deliverables_list': deliverables_list,
                    'team_members': project.team_members.filter(is_active=True),
                }
                html_string = render_to_string('projects/completion_certificate.html', context)
                html = HTML(string=html_string)
                pdf = html.write_pdf()

                safe_name = project.name.replace(' ', '_')[:50]
                response = HttpResponse(pdf, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="completion_certificate_{safe_name}.pdf"'
                return response
            except ImportError:
                return Response({'error': 'WeasyPrint not installed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # JSON format
        team_data = [{
            'name': m.name, 'role': m.get_role_display(),
        } for m in project.team_members.filter(is_active=True)]

        cred_data = [{
            'name': c.name, 'type': c.get_credential_type_display(),
            'provider': c.provider, 'expiry_date': str(c.expiry_date) if c.expiry_date else None,
        } for c in credentials]

        amc_data = None
        if amc:
            amc_data = {
                'annual_amount': str(amc.annual_amount),
                'billing_cycle': amc.get_billing_cycle_display(),
                'start_date': str(amc.start_date), 'end_date': str(amc.end_date),
                'next_due_date': str(amc.next_due_date),
            }

        return Response({
            'project': {
                'id': str(project.id), 'name': project.name,
                'project_type': project.get_project_type_display(),
                'tech_stack': project.tech_stack,
                'start_date': str(project.start_date) if project.start_date else None,
                'completed_date': str(project.completed_date) if project.completed_date else None,
                'live_url': project.live_url,
                'warranty_period': project.warranty_period,
                'completion_notes': project.completion_notes,
            },
            'client': {
                'name': project.client.name,
                'company_name': project.client.company_name,
                'email': project.client.email, 'phone': project.client.phone,
            },
            'financial_summary': {
                'estimated_budget': str(project.estimated_budget or 0),
                'final_amount': str(project.final_amount or 0),
                'total_invoiced': str(total_invoiced),
                'total_paid': str(total_paid),
                'balance_due': str(total_invoiced - total_paid),
            },
            'deliverables': deliverables_list,
            'credentials': cred_data,
            'amc': amc_data,
            'team': team_data,
        })


# ============== Owner: Invoice / Quote PDF (JWT) ==============

@extend_schema(tags=['Owner'])
class OwnerInvoicePDFView(APIView):
    """JWT-authenticated invoice PDF for the mobile app"""
    permission_classes = [IsAuthenticated, IsOwnerOrPartner]

    def get(self, request, pk):
        from core.models import Invoice, CompanySettings
        from decimal import Decimal
        from django.template.loader import render_to_string
        from django.http import HttpResponse

        try:
            invoice = Invoice.objects.select_related('client', 'project').prefetch_related(
                'items', 'payments'
            ).get(pk=pk)
        except Invoice.DoesNotExist:
            return Response({'error': 'Invoice not found'}, status=status.HTTP_404_NOT_FOUND)

        company = CompanySettings.get_settings()
        with_gst = request.query_params.get('gst', '0') == '1'

        taxable_amount = invoice.subtotal - (invoice.discount or Decimal('0'))
        tax_rate = Decimal(str(invoice.tax_rate)) if invoice.tax_rate is not None else Decimal('0')

        cgst_amount = Decimal('0')
        sgst_amount = Decimal('0')
        tax_amount = Decimal('0')
        total = taxable_amount

        if with_gst:
            cgst_amount = taxable_amount * (tax_rate / 2 / 100)
            sgst_amount = taxable_amount * (tax_rate / 2 / 100)
            tax_amount = cgst_amount + sgst_amount
            total = taxable_amount + tax_amount

        balance_due = total - (invoice.amount_paid or Decimal('0'))

        context = {
            'invoice': invoice,
            'company': company,
            'with_gst': with_gst,
            'taxable_amount': taxable_amount,
            'tax_rate': tax_rate,
            'cgst_rate': tax_rate / 2 if with_gst else 0,
            'sgst_rate': tax_rate / 2 if with_gst else 0,
            'cgst_amount': cgst_amount,
            'sgst_amount': sgst_amount,
            'tax_amount': tax_amount,
            'total_with_gst': total,
            'balance_due': balance_due,
        }

        try:
            from weasyprint import HTML
            html_string = render_to_string('invoices/pdf.html', context)
            pdf = HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf()
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.invoice_number}.pdf"'
            return response
        except ImportError:
            return Response({'error': 'WeasyPrint not installed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(tags=['Owner'])
class OwnerQuotePDFView(APIView):
    """JWT-authenticated quote PDF for the mobile app"""
    permission_classes = [IsAuthenticated, IsOwnerOrPartner]

    def get(self, request, pk):
        from core.models import Quote, CompanySettings
        from decimal import Decimal
        from django.template.loader import render_to_string
        from django.http import HttpResponse

        try:
            quote = Quote.objects.select_related('client', 'project').prefetch_related(
                'items'
            ).get(pk=pk)
        except Quote.DoesNotExist:
            return Response({'error': 'Quote not found'}, status=status.HTTP_404_NOT_FOUND)

        company = CompanySettings.get_settings()
        with_gst = request.query_params.get('gst', '0') == '1'

        taxable_amount = quote.subtotal - (quote.discount or Decimal('0'))
        tax_rate = Decimal(str(quote.tax_rate)) if quote.tax_rate is not None else Decimal('0')

        cgst_amount = Decimal('0')
        sgst_amount = Decimal('0')
        tax_amount = Decimal('0')
        total = taxable_amount

        if with_gst:
            cgst_amount = taxable_amount * (tax_rate / 2 / 100)
            sgst_amount = taxable_amount * (tax_rate / 2 / 100)
            tax_amount = cgst_amount + sgst_amount
            total = taxable_amount + tax_amount

        context = {
            'quote': quote,
            'company': company,
            'with_gst': with_gst,
            'taxable_amount': taxable_amount,
            'tax_rate': tax_rate,
            'cgst_rate': tax_rate / 2 if with_gst else 0,
            'sgst_rate': tax_rate / 2 if with_gst else 0,
            'cgst_amount': cgst_amount,
            'sgst_amount': sgst_amount,
            'tax_amount': tax_amount,
            'total_with_gst': total,
        }

        try:
            from weasyprint import HTML
            html_string = render_to_string('quotes/pdf.html', context)
            pdf = HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf()
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="quote_{quote.quote_number}.pdf"'
            return response
        except ImportError:
            return Response({'error': 'WeasyPrint not installed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(tags=['Owner'])
class OwnerPaymentDeleteView(APIView):
    """Delete a single payment on an invoice"""
    permission_classes = [IsAuthenticated, IsOwnerOrPartner]

    def delete(self, request, pk, payment_id):
        from core.models import Payment
        try:
            payment = Payment.objects.get(pk=payment_id, invoice_id=pk)
        except Payment.DoesNotExist:
            return Response({'error': 'Payment not found'}, status=status.HTTP_404_NOT_FOUND)
        payment.delete()
        return Response({'message': 'Payment deleted'}, status=status.HTTP_204_NO_CONTENT)


# ============== Bank Accounts & Internal Transfers ==============

def _bank_account_to_dict(account, balance=None):
    return {
        'id': str(account.id),
        'name': account.name,
        'account_type': account.account_type,
        'bank_name': account.bank_name,
        'account_number': account.account_number,
        'account_number_last4': account.account_number_last4,
        'ifsc': account.ifsc,
        'branch': account.branch,
        'upi_id': account.upi_id,
        'opening_balance': f'{account.opening_balance:.2f}',
        'opening_date': account.opening_date.isoformat() if account.opening_date else None,
        'is_active': account.is_active,
        'is_primary_bank': account.is_primary_bank,
        'is_cash': account.is_cash,
        'display_order': account.display_order,
        'notes': account.notes,
        'balance': f'{balance:.2f}' if balance is not None else None,
    }


def _transfer_to_dict(t):
    return {
        'id': str(t.id),
        'from_account_id': str(t.from_account_id),
        'from_account_name': t.from_account.name,
        'to_account_id': str(t.to_account_id),
        'to_account_name': t.to_account.name,
        'amount': f'{t.amount:.2f}',
        'date': t.date.isoformat() if t.date else None,
        'reference': t.reference,
        'notes': t.notes,
        'created_at': t.created_at.isoformat() if t.created_at else None,
    }


@extend_schema(tags=['Owner'])
class OwnerBankAccountListView(APIView):
    """GET: list bank accounts with current balances.
    POST: create a new bank account."""
    permission_classes = [IsAuthenticated, IsOwnerOrPartner]

    def get(self, request):
        from core.models import BankAccount
        from core.cash_position import cash_position
        include_inactive = request.query_params.get('include_inactive') in ('1', 'true', 'yes')
        cp = cash_position(include_inactive=include_inactive)
        accounts = [_bank_account_to_dict(r['account'], r['balance']) for r in cp['accounts']]
        return Response({
            'accounts': accounts,
            'total_assets': f"{cp['total']:.2f}",
        })

    def post(self, request):
        from core.models import BankAccount
        from datetime import date as date_cls
        data = request.data
        try:
            account = BankAccount.objects.create(
                name=(data.get('name') or '').strip(),
                account_type=data.get('account_type') or 'bank',
                bank_name=data.get('bank_name') or '',
                account_number=data.get('account_number') or '',
                ifsc=data.get('ifsc') or '',
                branch=data.get('branch') or '',
                upi_id=data.get('upi_id') or '',
                opening_balance=data.get('opening_balance') or 0,
                opening_date=data.get('opening_date') or date_cls.today(),
                is_active=bool(data.get('is_active', True)),
                is_primary_bank=bool(data.get('is_primary_bank', False)),
                is_cash=bool(data.get('is_cash', False)),
                display_order=int(data.get('display_order') or 0),
                notes=data.get('notes') or '',
            )
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        from core.cash_position import compute_account_balance
        account.refresh_from_db()
        return Response(
            _bank_account_to_dict(account, compute_account_balance(account)),
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=['Owner'])
class OwnerBankAccountDetailView(APIView):
    """GET: account details + balance + recent ledger.
    PATCH: edit account.
    DELETE: only if no payments/expenses/transfers reference it."""
    permission_classes = [IsAuthenticated, IsOwnerOrPartner]

    def get(self, request, pk):
        from core.models import BankAccount, InternalTransfer, Payment, Expense
        from core.cash_position import compute_account_balance
        try:
            account = BankAccount.objects.get(pk=pk)
        except BankAccount.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        balance = compute_account_balance(account)
        entries = []
        for p in Payment.objects.filter(
            payment_date__gte=account.opening_date,
            payment_method__in=account.resolved_payment_methods(),
        ).select_related('invoice', 'invoice__client').order_by('-payment_date')[:50]:
            entries.append({
                'date': p.payment_date.isoformat(),
                'kind': 'payment_in',
                'description': f"Invoice #{p.invoice.invoice_number}" if p.invoice else '',
                'method': p.payment_method,
                'amount': f'{p.amount:.2f}',
                'direction': 'in',
            })
        for e in Expense.objects.filter(
            date__gte=account.opening_date,
            payment_method__in=account.resolved_expense_methods(),
        ).order_by('-date')[:50]:
            entries.append({
                'date': e.date.isoformat(),
                'kind': 'expense',
                'description': f"{e.vendor} - {e.get_category_display()}",
                'method': e.payment_method,
                'amount': f'{e.amount:.2f}',
                'direction': 'out',
            })
        for t in InternalTransfer.objects.filter(to_account=account).select_related('from_account')[:50]:
            entries.append({
                'date': t.date.isoformat(),
                'kind': 'transfer_in',
                'description': f"From {t.from_account.name}",
                'method': 'internal',
                'amount': f'{t.amount:.2f}',
                'direction': 'in',
                'reference': t.reference,
            })
        for t in InternalTransfer.objects.filter(from_account=account).select_related('to_account')[:50]:
            entries.append({
                'date': t.date.isoformat(),
                'kind': 'transfer_out',
                'description': f"To {t.to_account.name}",
                'method': 'internal',
                'amount': f'{t.amount:.2f}',
                'direction': 'out',
                'reference': t.reference,
            })
        entries.sort(key=lambda x: x['date'], reverse=True)
        return Response({
            **_bank_account_to_dict(account, balance),
            'ledger': entries[:100],
        })

    def patch(self, request, pk):
        from core.models import BankAccount
        from core.cash_position import compute_account_balance
        try:
            account = BankAccount.objects.get(pk=pk)
        except BankAccount.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        for f in ['name', 'account_type', 'bank_name', 'account_number', 'ifsc', 'branch', 'upi_id', 'notes']:
            if f in request.data:
                setattr(account, f, request.data[f] or '')
        if 'opening_balance' in request.data:
            account.opening_balance = request.data['opening_balance'] or 0
        if 'opening_date' in request.data and request.data['opening_date']:
            account.opening_date = request.data['opening_date']
        if 'is_active' in request.data:
            account.is_active = bool(request.data['is_active'])
        if 'is_primary_bank' in request.data:
            account.is_primary_bank = bool(request.data['is_primary_bank'])
        if 'is_cash' in request.data:
            account.is_cash = bool(request.data['is_cash'])
        if 'display_order' in request.data:
            account.display_order = int(request.data['display_order'] or 0)
        try:
            account.save()
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        account.refresh_from_db()
        return Response(_bank_account_to_dict(account, compute_account_balance(account)))


@extend_schema(tags=['Owner'])
class OwnerTransferListView(APIView):
    """GET: list internal transfers (filter by ?account=<id>, ?pending=1).
    POST: create a new transfer."""
    permission_classes = [IsAuthenticated, IsOwnerOrPartner]

    def get(self, request):
        from core.models import InternalTransfer
        qs = InternalTransfer.objects.select_related('from_account', 'to_account').all()
        account_id = request.query_params.get('account')
        if account_id:
            from django.db.models import Q
            qs = qs.filter(Q(from_account_id=account_id) | Q(to_account_id=account_id))
        if request.query_params.get('pending') in ('1', 'true', 'yes'):
            qs = qs.filter(date__gt=date.today())
        limit = int(request.query_params.get('limit') or 100)
        return Response({
            'transfers': [_transfer_to_dict(t) for t in qs[:limit]],
            'count': qs.count(),
        })

    def post(self, request):
        from core.models import InternalTransfer, BankAccount
        data = request.data
        try:
            transfer = InternalTransfer(
                from_account=BankAccount.objects.get(pk=data['from_account']),
                to_account=BankAccount.objects.get(pk=data['to_account']),
                amount=data['amount'],
                date=data.get('date') or date.today(),
                reference=data.get('reference') or '',
                notes=data.get('notes') or '',
                created_by=request.user if request.user.is_authenticated else None,
            )
            transfer.full_clean()
            transfer.save()
        except BankAccount.DoesNotExist:
            return Response({'error': 'Account not found'}, status=status.HTTP_404_NOT_FOUND)
        except KeyError as e:
            return Response({'error': f'Missing field: {e}'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(_transfer_to_dict(transfer), status=status.HTTP_201_CREATED)


@extend_schema(tags=['Owner'])
class OwnerTransferDetailView(APIView):
    """GET / PATCH / DELETE a single internal transfer."""
    permission_classes = [IsAuthenticated, IsOwnerOrPartner]

    def get(self, request, pk):
        from core.models import InternalTransfer
        try:
            t = InternalTransfer.objects.select_related('from_account', 'to_account').get(pk=pk)
        except InternalTransfer.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(_transfer_to_dict(t))

    def patch(self, request, pk):
        from core.models import InternalTransfer, BankAccount
        try:
            t = InternalTransfer.objects.get(pk=pk)
        except InternalTransfer.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        data = request.data
        try:
            if 'from_account' in data:
                t.from_account = BankAccount.objects.get(pk=data['from_account'])
            if 'to_account' in data:
                t.to_account = BankAccount.objects.get(pk=data['to_account'])
            if 'amount' in data:
                t.amount = data['amount']
            if 'date' in data and data['date']:
                t.date = data['date']
            if 'reference' in data:
                t.reference = data['reference'] or ''
            if 'notes' in data:
                t.notes = data['notes'] or ''
            t.full_clean()
            t.save()
        except BankAccount.DoesNotExist:
            return Response({'error': 'Account not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(_transfer_to_dict(t))

    def delete(self, request, pk):
        from core.models import InternalTransfer
        try:
            t = InternalTransfer.objects.get(pk=pk)
        except InternalTransfer.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        t.delete()
        return Response({'message': 'Transfer deleted'}, status=status.HTTP_204_NO_CONTENT)
