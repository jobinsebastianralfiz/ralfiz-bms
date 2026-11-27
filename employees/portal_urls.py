"""URLs for the staff portal (interns & employees) at /staff/."""
from django.urls import path

from uat import staff_views as uat_v
from wallet import staff_views as wallet_v

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
    # Project boards (kept apart from My Tasks)
    path('projects/', v.project_list, name='project_list'),
    path('projects/<uuid:pk>/', v.project_board, name='project_board'),
    path('projects/<uuid:pk>/tasks/new/', v.board_task_create, name='board_task_create'),
    path('projects/<uuid:pk>/weeks/add/', v.sprint_create, name='sprint_create'),
    path('projects/<uuid:pk>/weeks/<uuid:sprint_id>/<str:action>/', v.sprint_action, name='sprint_action'),
    path('tasks/<uuid:pk>/edit/', v.board_task_edit, name='board_task_edit'),
    path('projects/<uuid:pk>/bugs/new/', v.bug_report, name='bug_report'),
    path('projects/<uuid:pk>/epics/add/', v.epic_create, name='epic_create'),
    path('projects/<uuid:pk>/epics/<uuid:epic_id>/toggle/', v.epic_toggle, name='epic_toggle'),
    path('tasks/<uuid:pk>/links/add/', v.link_add, name='link_add'),
    path('tasks/<uuid:pk>/links/<uuid:link_id>/remove/', v.link_remove, name='link_remove'),
    path('tasks/<uuid:pk>/checklist/<uuid:item_id>/', v.checklist_toggle, name='checklist_toggle'),
    path('tasks/<uuid:pk>/', v.board_task_detail, name='board_task_detail'),
    path('tasks/<uuid:pk>/update/', v.board_task_update, name='board_task_update'),

    # UAT testing
    path('uat/', uat_v.uat_home, name='uat_home'),
    path('uat/<uuid:plan_pk>/', uat_v.uat_plan, name='uat_plan'),
    path('uat/<uuid:plan_pk>/files/upload/', uat_v.uat_file_upload, name='uat_file_upload'),
    path('uat/<uuid:plan_pk>/files/<uuid:file_id>/download/', uat_v.uat_file_download, name='uat_file_download'),
    path('uat/<uuid:plan_pk>/files/<uuid:file_id>/delete/', uat_v.uat_file_delete, name='uat_file_delete'),
    path('uat/<uuid:plan_pk>/<int:section_pk>/', uat_v.uat_section, name='uat_section'),

    # Classes & assessments
    path('classes/', v.class_list, name='class_list'),
    path('classes/<uuid:pk>/', v.class_detail, name='class_detail'),
    path('assessments/', v.assessment_list, name='assessment_list'),
    path('assessments/<uuid:pk>/take/', v.assessment_take, name='assessment_take'),
    path('assessments/<uuid:pk>/result/', v.assessment_result, name='assessment_result'),
    path('assessments/<uuid:pk>/begin/', v.assessment_begin, name='assessment_begin'),
    path('assessments/<uuid:pk>/autosave/', v.assessment_autosave, name='assessment_autosave'),
    path('assessments/<uuid:pk>/proctor/', v.assessment_proctor, name='assessment_proctor'),
    path('bootcamp/', v.bootcamp_open, name='bootcamp'),

    # XP wallet
    path('wallet/', wallet_v.wallet, name='wallet'),

    # Payslips
    path('payslips/', v.payslip_list, name='payslip_list'),
    path('payslips/<uuid:pk>/', v.payslip_detail, name='payslip_detail'),

    # Resignation
    path('resignation/', v.resignation, name='resignation'),

    # Notifications
    path('notifications/', v.notification_list, name='notification_list'),

    # Profile
    path('profile/', v.profile, name='profile'),
    path('profile/github/', v.github_save, name='github_save'),
    path('search/', v.staff_search, name='search'),

    # CRM leads (marketing interns)
    path('leads/', v.lead_list, name='lead_list'),
    path('leads/<int:pk>/', v.lead_detail, name='lead_detail'),

    # PWA
    path('manifest.webmanifest', v.manifest, name='manifest'),
    path('sw.js', v.service_worker, name='service_worker'),
    path('offline/', v.offline, name='offline'),
]
