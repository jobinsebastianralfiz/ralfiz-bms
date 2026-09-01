"""URLs for the staff portal (interns & employees) at /staff/."""
from django.urls import path

from . import portal_views as v

app_name = 'staff'

urlpatterns = [
    # Auth
    path('login/', v.staff_login, name='login'),
    path('logout/', v.staff_logout, name='logout'),

    # Dashboard
    path('', v.dashboard, name='dashboard'),

    # Attendance
    path('attendance/', v.attendance, name='attendance'),
    path('attendance/history/', v.attendance_history, name='attendance_history'),

    # Leave
    path('leave/', v.leave, name='leave'),

    # Work assignments
    path('work/', v.work_list, name='work_list'),
    path('work/<uuid:pk>/', v.work_detail, name='work_detail'),

    # Classes & assessments
    path('classes/', v.class_list, name='class_list'),
    path('classes/<uuid:pk>/', v.class_detail, name='class_detail'),
    path('assessments/', v.assessment_list, name='assessment_list'),

    # Payslips
    path('payslips/', v.payslip_list, name='payslip_list'),
    path('payslips/<uuid:pk>/', v.payslip_detail, name='payslip_detail'),

    # Notifications
    path('notifications/', v.notification_list, name='notification_list'),

    # Profile
    path('profile/', v.profile, name='profile'),

    # CRM leads (marketing interns)
    path('leads/', v.lead_list, name='lead_list'),
    path('leads/<int:pk>/', v.lead_detail, name='lead_detail'),

    # PWA
    path('manifest.webmanifest', v.manifest, name='manifest'),
    path('sw.js', v.service_worker, name='service_worker'),
    path('offline/', v.offline, name='offline'),
]
