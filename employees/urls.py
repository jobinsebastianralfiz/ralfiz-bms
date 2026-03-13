from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views
from .auth_views import EmployeeTokenObtainView

app_name = 'employees'

urlpatterns = [
    # ---- Auth ----
    path('auth/login/', EmployeeTokenObtainView.as_view(), name='login'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    path('auth/delete-account/', views.DeleteAccountView.as_view(), name='delete_account'),

    # ---- Public Pages ----
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('data-retention-policy/', views.data_retention_policy, name='data_retention_policy'),

    # ---- Employee App APIs ----
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/face/', views.FacePhotoUploadView.as_view(), name='face_photo'),
    path('device-token/', views.RegisterDeviceTokenView.as_view(), name='register_device'),

    # Attendance
    path('attendance/check-in/', views.CheckInView.as_view(), name='check_in'),
    path('attendance/check-out/', views.CheckOutView.as_view(), name='check_out'),
    path('attendance/today/', views.TodayAttendanceView.as_view(), name='today_attendance'),
    path('attendance/history/', views.AttendanceHistoryView.as_view(), name='attendance_history'),

    # Leave
    path('leave/types/', views.LeaveTypeListView.as_view(), name='leave_types'),
    path('leave/requests/', views.LeaveRequestListCreateView.as_view(), name='leave_requests'),
    path('leave/requests/<uuid:pk>/cancel/', views.LeaveRequestCancelView.as_view(), name='leave_cancel'),
    path('leave/balance/', views.LeaveBalanceView.as_view(), name='leave_balance'),

    # Work Assignments
    path('work/', views.WorkAssignmentListView.as_view(), name='work_list'),
    path('work/<uuid:pk>/', views.WorkAssignmentDetailView.as_view(), name='work_detail'),
    path('work/<uuid:pk>/status/', views.WorkStatusUpdateView.as_view(), name='work_status'),
    path('work/<uuid:pk>/update/', views.WorkUpdateCreateView.as_view(), name='work_update'),

    # Scheduled Classes (for interns)
    path('classes/', views.ScheduledClassListView.as_view(), name='class_list'),
    path('classes/<uuid:pk>/', views.ScheduledClassDetailView.as_view(), name='class_detail'),

    # Notifications
    path('notifications/', views.NotificationListView.as_view(), name='notifications'),
    path('notifications/read/', views.NotificationMarkReadView.as_view(), name='notifications_read_all'),
    path('notifications/<uuid:pk>/read/', views.NotificationMarkReadView.as_view(), name='notification_read'),

    # ---- Admin APIs ----
    path('admin/employees/', views.AdminEmployeeListView.as_view(), name='admin_employees'),
    path('admin/employees/<uuid:pk>/', views.AdminEmployeeDetailView.as_view(), name='admin_employee_detail'),
    path('admin/leaves/', views.AdminLeaveReviewView.as_view(), name='admin_leaves'),
    path('admin/leaves/<uuid:pk>/review/', views.AdminLeaveReviewView.as_view(), name='admin_leave_review'),
    path('admin/work/assign/', views.AdminWorkAssignView.as_view(), name='admin_work_assign'),
    path('admin/work/<uuid:pk>/', views.AdminWorkAssignDetailView.as_view(), name='admin_work_detail'),
    path('admin/attendance/report/', views.AdminAttendanceReportView.as_view(), name='admin_attendance_report'),
    path('admin/attendance/qr/', views.AdminGenerateQRView.as_view(), name='admin_generate_qr'),
    path('admin/notifications/send/', views.AdminSendNotificationView.as_view(), name='admin_send_notification'),

    # Admin: Scheduled Classes
    path('admin/classes/', views.AdminScheduledClassListCreateView.as_view(), name='admin_class_list'),
    path('admin/classes/<uuid:pk>/', views.AdminScheduledClassDetailView.as_view(), name='admin_class_detail'),
]
