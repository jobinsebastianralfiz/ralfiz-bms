"""Daily report APIs -- the end-of-day write-up every employee and intern files.

One report per person per day: what they worked on, what they learned, and
anything blocking them. HR reads the feed and can reply; the reply comes back
to the author in their portal and app.
"""
from datetime import timedelta

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import DailyReport, DailyReportComment, Employee, Notification
from .serializers import DailyReportSerializer, DailyReportCommentSerializer
from .utils import send_push_notification


def get_employee(user):
    return Employee.objects.filter(user=user, status='active').first()


def is_hr(user):
    return bool(user.is_staff or user.is_superuser)


def parse_date(value):
    """Parse YYYY-MM-DD, returning None when absent or malformed."""
    if not value:
        return None
    try:
        return timezone.datetime.strptime(value, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


@extend_schema(tags=['Daily Reports'])
class MyDailyReportListCreateView(generics.ListCreateAPIView):
    """GET my recent reports; POST today's (or a recent day's) report.

    Posting twice for the same date updates the existing report rather than
    erroring -- the app's save button should be idempotent.
    """
    serializer_class = DailyReportSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        employee = get_employee(self.request.user)
        if not employee:
            return DailyReport.objects.none()
        qs = DailyReport.objects.filter(employee=employee).prefetch_related('comments__author')
        start = parse_date(self.request.query_params.get('start'))
        end = parse_date(self.request.query_params.get('end'))
        if start:
            qs = qs.filter(date__gte=start)
        if end:
            qs = qs.filter(date__lte=end)
        return qs

    def create(self, request, *args, **kwargs):
        employee = get_employee(request.user)
        if not employee:
            return Response({'error': 'Employee profile not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        report_date = serializer.validated_data.get('date') or timezone.localdate()

        existing = DailyReport.objects.filter(employee=employee, date=report_date).first()
        if existing:
            if not existing.is_editable:
                return Response(
                    {'error': 'This report is too old to change.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            update = self.get_serializer(existing, data=request.data, partial=True)
            update.is_valid(raise_exception=True)
            update.save()
            return Response(update.data, status=status.HTTP_200_OK)

        report = serializer.save(employee=employee, date=report_date)
        return Response(self.get_serializer(report).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=['Daily Reports'])
class MyDailyReportDetailView(generics.RetrieveUpdateAPIView):
    """Read or edit one of my reports (today's and yesterday's only)."""
    serializer_class = DailyReportSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        employee = get_employee(self.request.user)
        qs = DailyReport.objects.prefetch_related('comments__author')
        if is_hr(self.request.user):
            return get_object_or_404(qs, pk=self.kwargs['pk'])
        if not employee:
            return get_object_or_404(qs, pk=None)
        return get_object_or_404(qs, pk=self.kwargs['pk'], employee=employee)

    def update(self, request, *args, **kwargs):
        report = self.get_object()
        if not report.is_editable:
            return Response(
                {'error': 'This report is too old to change.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().update(request, *args, **kwargs)


@extend_schema(tags=['Daily Reports'])
class DailyReportCommentCreateView(APIView):
    """Reply on a report. The author and HR may both post here."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        report = get_object_or_404(
            DailyReport.objects.select_related('employee__user'), pk=pk)
        employee = get_employee(request.user)
        is_author = employee is not None and report.employee_id == employee.id
        if not (is_author or is_hr(request.user)):
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        message = (request.data.get('message') or '').strip()
        if not message:
            return Response({'error': 'message is required'}, status=status.HTTP_400_BAD_REQUEST)

        comment = DailyReportComment.objects.create(
            report=report, author=request.user, message=message)

        if not is_author:
            notify_author(report, request.user, message)

        return Response(DailyReportCommentSerializer(comment).data,
                        status=status.HTTP_201_CREATED)


def notify_author(report, actor, message):
    """Tell the report's author that HR replied."""
    who = actor.get_full_name() or actor.username
    title = f'{who} replied to your daily update'
    body = message[:140]
    Notification.objects.create(
        employee=report.employee,
        title=title,
        body=body,
        notification_type='general',
        data={'type': 'daily_report', 'report_id': str(report.id), 'date': str(report.date)},
    )
    try:
        send_push_notification(report.employee, title, body,
                               data={'type': 'daily_report', 'report_id': str(report.id)})
    except Exception:
        # A dead FCM token must never fail the reply itself.
        pass


@extend_schema(tags=['Daily Reports'], parameters=[
    OpenApiParameter(name='start', type=str, required=False, description='YYYY-MM-DD'),
    OpenApiParameter(name='end', type=str, required=False, description='YYYY-MM-DD'),
    OpenApiParameter(name='employee', type=str, required=False, description='Employee UUID'),
    OpenApiParameter(name='blockers', type=bool, required=False,
                     description='Only reports that flag a blocker'),
])
class AdminDailyReportListView(generics.ListAPIView):
    """HR feed: everyone's reports, newest first."""
    serializer_class = DailyReportSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if not is_hr(self.request.user):
            return DailyReport.objects.none()
        qs = (DailyReport.objects
              .select_related('employee__user')
              .prefetch_related('comments__author'))
        params = self.request.query_params
        start = parse_date(params.get('start'))
        end = parse_date(params.get('end'))
        if start:
            qs = qs.filter(date__gte=start)
        if end:
            qs = qs.filter(date__lte=end)
        if params.get('employee'):
            qs = qs.filter(employee_id=params['employee'])
        if params.get('blockers') in ('1', 'true', 'True'):
            qs = qs.exclude(blockers='')
        return qs


@extend_schema(tags=['Daily Reports'], parameters=[
    OpenApiParameter(name='date', type=str, required=False, description='YYYY-MM-DD'),
])
class AdminDailyReportMissingView(APIView):
    """Who has not filed a report for a given day."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not is_hr(request.user):
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        day = parse_date(request.query_params.get('date')) or timezone.localdate()
        filed = DailyReport.objects.filter(date=day).values_list('employee_id', flat=True)
        missing = (Employee.objects
                   .filter(status='active')
                   .exclude(id__in=list(filed))
                   .select_related('user'))
        return Response({
            'date': str(day),
            'missing': [
                {'id': str(e.id), 'employee_id': e.employee_id, 'name': e.full_name}
                for e in missing
            ],
        })
