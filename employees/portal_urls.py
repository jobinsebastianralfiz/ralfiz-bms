"""URLs for the staff portal (interns & employees) at /staff/."""
from django.urls import path

from uat import staff_views as uat_v

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

    # Daily report
    path('daily-report/', v.daily_report, name='daily_report'),

    # Work assignments
    path('work/', v.work_list, name='work_list'),
    path('work/<uuid:pk>/', v.work_detail, name='work_detail'),
    path('tasks/<uuid:pk>/', v.board_task_detail, name='board_task_detail'),
    path('tasks/<uuid:pk>/update/', v.board_task_update, name='board_task_update'),

    # UAT testing
    path('uat/', uat_v.uat_home, name='uat_home'),
    path('uat/<uuid:plan_pk>/', uat_v.uat_plan, name='uat_plan'),
    path('uat/<uuid:plan_pk>/<int:section_pk>/', uat_v.uat_section, name='uat_section'),

    # Classes & assessments
    path('classes/', v.class_list, name='class_list'),
    path('classes/<uuid:pk>/', v.class_detail, name='class_detail'),
    path('assessments/', v.assessment_list, name='assessment_list'),
    path('bootcamp/', v.bootcamp_open, name='bootcamp'),

    # Payslips
    path('payslips/', v.payslip_list, name='payslip_list'),
    path('payslips/<uuid:pk>/', v.payslip_detail, name='payslip_detail'),

    # Resignation
    path('resignation/', v.resignation, name='resignation'),

    # Notifications
    path('notifications/', v.notification_list, name='notification_list'),

    # Profile
    path('profile/', v.profile, name='profile'),
    path('search/', v.staff_search, name='search'),

    # CRM leads (marketing interns)
    path('leads/', v.lead_list, name='lead_list'),
    path('leads/<int:pk>/', v.lead_detail, name='lead_detail'),

    # PWA
    path('manifest.webmanifest', v.manifest, name='manifest'),
    path('sw.js', v.service_worker, name='service_worker'),
    path('offline/', v.offline, name='offline'),
]
