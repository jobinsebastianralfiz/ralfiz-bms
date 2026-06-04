from django.urls import path
from . import views
from gympro_licensing import web_views as gympro_web_views
from eduflow_licensing import web_views as eduflow_web_views

urlpatterns = [
    # Public Pages
    path('interiodesk/guide/', views.interiodesk_guide, name='interiodesk_guide'),
    path('share/feature-request/<uuid:token>/', views.public_feature_request, name='public_feature_request'),

    # Feature Requests (admin)
    path('feature-requests/', views.feature_request_list, name='feature_request_list'),
    path('feature-requests/create/', views.feature_request_create, name='feature_request_create'),
    path('feature-requests/<uuid:pk>/', views.feature_request_detail, name='feature_request_detail'),
    path('feature-requests/<uuid:pk>/regenerate/', views.feature_request_regenerate, name='feature_request_regenerate'),
    path('feature-requests/<uuid:pk>/delete/', views.feature_request_delete, name='feature_request_delete'),

    # Project Types & Features (admin)
    path('feature-requests/types/', views.project_type_list, name='project_type_list'),
    path('feature-requests/types/save/', views.project_type_save, name='project_type_save'),
    path('feature-requests/types/<uuid:pk>/delete/', views.project_type_delete, name='project_type_delete'),
    path('feature-requests/features/save/', views.project_feature_save, name='project_feature_save'),
    path('feature-requests/features/<uuid:pk>/delete/', views.project_feature_delete, name='project_feature_delete'),

    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Clients
    path('clients/', views.client_list, name='client_list'),
    path('clients/create/', views.client_create, name='client_create'),
    path('clients/import/', views.client_import, name='client_import'),
    path('clients/<uuid:pk>/', views.client_detail, name='client_detail'),
    path('clients/<uuid:pk>/edit/', views.client_update, name='client_update'),
    path('clients/<uuid:pk>/delete/', views.client_delete, name='client_delete'),
    path('clients/<uuid:pk>/retailease/', views.client_update_retailease, name='client_update_retailease'),
    path('clients/<uuid:pk>/portal/create/', views.client_portal_create_account, name='client_portal_create_account'),
    path('clients/<uuid:pk>/portal/reset-password/', views.client_portal_reset_password, name='client_portal_reset_password'),
    path('clients/<uuid:pk>/portal/toggle/', views.client_portal_toggle, name='client_portal_toggle'),

    # Projects
    path('projects/', views.project_list, name='project_list'),
    path('projects/create/', views.project_create, name='project_create'),
    path('projects/import/', views.project_import, name='project_import'),
    path('projects/<uuid:pk>/', views.project_detail, name='project_detail'),
    path('projects/<uuid:pk>/edit/', views.project_update, name='project_update'),
    path('projects/<uuid:pk>/delete/', views.project_delete, name='project_delete'),
    path('projects/<uuid:pk>/post-update/', views.project_post_update, name='project_post_update'),
    path('projects/<uuid:pk>/delete-update/<uuid:update_pk>/', views.project_delete_update, name='project_delete_update'),
    path('projects/<uuid:pk>/reply-comment/', views.project_reply_comment, name='project_reply_comment'),
    path('projects/<uuid:pk>/completion-certificate/', views.project_completion_certificate, name='project_completion_certificate'),

    # Credentials
    path('credentials/', views.credential_list, name='credential_list'),
    path('credentials/create/', views.credential_create, name='credential_create'),
    path('credentials/<uuid:pk>/', views.credential_detail, name='credential_detail'),
    path('credentials/<uuid:pk>/edit/', views.credential_update, name='credential_update'),
    path('credentials/<uuid:pk>/delete/', views.credential_delete, name='credential_delete'),
    path('credentials/<uuid:pk>/renew/', views.credential_renew, name='credential_renew'),
    path('credentials/expiring/', views.credential_expiry, name='credential_expiry'),

    # AMC Contracts
    path('amc/', views.amc_list, name='amc_list'),
    path('amc/create/', views.amc_create, name='amc_create'),
    path('amc/<uuid:pk>/', views.amc_detail, name='amc_detail'),
    path('amc/<uuid:pk>/edit/', views.amc_update, name='amc_update'),
    path('amc/<uuid:pk>/delete/', views.amc_delete, name='amc_delete'),
    path('amc/<uuid:pk>/record-payment/', views.amc_record_payment, name='amc_record_payment'),

    # Quotes
    path('quotes/', views.quote_list, name='quote_list'),
    path('quotes/create/', views.quote_create, name='quote_create'),
    path('quotes/<uuid:pk>/', views.quote_detail, name='quote_detail'),
    path('quotes/<uuid:pk>/edit/', views.quote_update, name='quote_update'),
    path('quotes/<uuid:pk>/pdf/', views.quote_pdf, name='quote_pdf'),
    path('quotes/<uuid:pk>/delete/', views.quote_delete, name='quote_delete'),
    path('quotes/<uuid:pk>/clone/', views.quote_clone, name='quote_clone'),
    path('quotes/<uuid:pk>/convert/', views.quote_convert, name='quote_convert'),

    # Invoices
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/create/', views.invoice_create, name='invoice_create'),
    path('invoices/backup-pdf/', views.invoices_backup_pdf, name='invoices_backup_pdf'),
    path('expenses/backup-pdf/', views.expenses_backup_pdf, name='expenses_backup_pdf'),
    path('clients/backup-pdf/', views.clients_credentials_backup_pdf, name='clients_credentials_backup_pdf'),
    path('clients/backup-xlsx/', views.clients_credentials_backup_xlsx, name='clients_credentials_backup_xlsx'),
    path('invoices/<uuid:pk>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/<uuid:pk>/edit/', views.invoice_update, name='invoice_update'),
    path('invoices/<uuid:pk>/pdf/', views.invoice_pdf, name='invoice_pdf'),
    path('invoices/<uuid:pk>/delete/', views.invoice_delete, name='invoice_delete'),
    path('invoices/<uuid:pk>/clone/', views.invoice_clone, name='invoice_clone'),
    path('invoices/<uuid:pk>/split-milestones/', views.invoice_split_to_milestones, name='invoice_split_to_milestones'),
    path('invoices/<uuid:pk>/update-number/', views.invoice_update_number, name='invoice_update_number'),

    # Payments
    path('payments/', views.payment_list, name='payment_list'),
    path('invoices/mark-gst-filed/', views.invoices_mark_gst_filed, name='invoices_mark_gst_filed'),
    path('invoices/mark-gst-pending/', views.invoices_mark_gst_pending, name='invoices_mark_gst_pending'),
    path('invoices/<uuid:pk>/set-gst-status/', views.invoice_set_gst_status, name='invoice_set_gst_status'),
    path('payments/create/', views.payment_create, name='payment_create'),
    path('payments/<uuid:pk>/edit/', views.payment_edit, name='payment_edit'),
    path('payments/<uuid:pk>/delete/', views.payment_delete, name='payment_delete'),
    path('payments/<uuid:pk>/receipt/', views.payment_receipt, name='payment_receipt'),

    # Settings & Reports
    path('settings/', views.settings_view, name='settings'),
    path('settings/start-new-fy/', views.start_new_fy, name='start_new_fy'),
    path('settings/start-new-fy-quotes/', views.start_new_fy_quotes, name='start_new_fy_quotes'),
    path('settings/fy-wizard/', views.fy_wizard, name='fy_wizard'),
    path('settings/opening-balance/save/', views.opening_balance_save, name='opening_balance_save'),
    path('settings/opening-balance/<uuid:pk>/edit/', views.opening_balance_edit, name='opening_balance_edit'),
    path('settings/opening-balance/<uuid:pk>/delete/', views.opening_balance_delete, name='opening_balance_delete'),
    path('settings/reset-financial-data/', views.fy_reset, name='fy_reset'),
    path('reports/', views.reports_view, name='reports'),
    path('reports/monthly/', views.monthly_report_view, name='monthly_report'),

    # Global Search
    path('search/', views.global_search, name='global_search'),

    # User Profile
    path('profile/', views.profile_view, name='profile'),
    path('profile/change-password/', views.change_password, name='change_password'),

    # Export to Excel
    path('export/clients/', views.export_clients, name='export_clients'),
    path('export/projects/', views.export_projects, name='export_projects'),
    path('export/invoices/', views.export_invoices, name='export_invoices'),
    path('export/quotes/', views.export_quotes, name='export_quotes'),

    # Backup & Restore
    path('backup/', views.backup_view, name='backup'),
    path('backup/download/', views.backup_download, name='backup_download'),
    path('backup/restore/', views.backup_restore, name='backup_restore'),

    # Expenses
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/create/', views.expense_create, name='expense_create'),
    path('expenses/<uuid:pk>/edit/', views.expense_update, name='expense_update'),
    path('expenses/<uuid:pk>/delete/', views.expense_delete, name='expense_delete'),

    # Bank Accounts & Internal Transfers
    path('accounts/', views.bank_account_list, name='bank_account_list'),
    path('accounts/new/', views.bank_account_create, name='bank_account_create'),
    path('accounts/<uuid:pk>/', views.bank_account_detail, name='bank_account_detail'),
    path('accounts/<uuid:pk>/edit/', views.bank_account_update, name='bank_account_update'),
    path('transfers/', views.transfer_list, name='transfer_list'),
    path('transfers/new/', views.transfer_create, name='transfer_create'),
    path('transfers/<uuid:pk>/edit/', views.transfer_update, name='transfer_update'),
    path('transfers/<uuid:pk>/delete/', views.transfer_delete, name='transfer_delete'),

    # Company Documents (statutory / business paperwork)
    path('documents/company/', views.company_document_list, name='company_document_list'),
    path('documents/company/new/', views.company_document_create, name='company_document_create'),
    path('documents/company/<uuid:pk>/edit/', views.company_document_update, name='company_document_update'),
    path('documents/company/<uuid:pk>/delete/', views.company_document_delete, name='company_document_delete'),
    path('documents/company/<uuid:pk>/download/', views.company_document_download, name='company_document_download'),

    # Partners & Capital Contributions
    path('partners/', views.partner_list, name='partner_list'),
    path('partners/new/', views.partner_create, name='partner_create'),
    path('partners/<uuid:pk>/', views.partner_detail, name='partner_detail'),
    path('partners/<uuid:pk>/edit/', views.partner_update, name='partner_update'),
    path('partners/<uuid:pk>/delete/', views.partner_delete, name='partner_delete'),
    path('partners/<uuid:partner_pk>/contributions/new/', views.contribution_create, name='contribution_create'),
    path('contributions/<uuid:pk>/edit/', views.contribution_update, name='contribution_update'),
    path('contributions/<uuid:pk>/delete/', views.contribution_delete, name='contribution_delete'),

    # Company Assets (deposits / advances / equipment)
    path('assets/', views.asset_list, name='asset_list'),
    path('assets/new/', views.asset_create, name='asset_create'),
    path('assets/<uuid:pk>/edit/', views.asset_update, name='asset_update'),
    path('assets/<uuid:pk>/delete/', views.asset_delete, name='asset_delete'),

    # Tasks
    path('tasks/', views.task_list, name='task_list'),
    path('tasks/board/', views.task_board, name='task_board'),
    path('tasks/create/', views.task_create, name='task_create'),
    path('tasks/<uuid:pk>/', views.task_detail, name='task_detail'),
    path('tasks/<uuid:pk>/edit/', views.task_update, name='task_update'),
    path('tasks/<uuid:pk>/delete/', views.task_delete, name='task_delete'),
    path('tasks/<uuid:pk>/status/', views.task_status_update, name='task_status_update'),
    path('tasks/<uuid:pk>/comments/add/', views.task_comment_add, name='task_comment_add'),
    path('tasks/<uuid:pk>/comments/<uuid:comment_id>/delete/', views.task_comment_delete, name='task_comment_delete'),
    path('tasks/<uuid:pk>/issues/create/', views.task_issue_create, name='task_issue_create'),
    path('tasks/<uuid:pk>/issues/<uuid:issue_id>/update/', views.task_issue_update, name='task_issue_update'),

    # Time Tracking
    path('time/', views.timeentry_list, name='timeentry_list'),
    path('time/create/', views.timeentry_create, name='timeentry_create'),
    path('time/<uuid:pk>/edit/', views.timeentry_update, name='timeentry_update'),
    path('time/<uuid:pk>/delete/', views.timeentry_delete, name='timeentry_delete'),

    # Activity Log
    path('activity-log/', views.activity_log, name='activity_log'),

    # Documents
    path('documents/upload/', views.document_upload, name='document_upload'),
    path('documents/<uuid:pk>/download/', views.document_download, name='document_download'),
    path('documents/<uuid:pk>/delete/', views.document_delete, name='document_delete'),

    # Email
    path('invoices/<uuid:pk>/send-email/', views.send_invoice_email, name='send_invoice_email'),
    path('quotes/<uuid:pk>/send-email/', views.send_quote_email, name='send_quote_email'),

    # Team Members
    path('team/', views.team_list, name='team_list'),
    path('team/create/', views.team_create, name='team_create'),
    path('team/<uuid:pk>/', views.team_detail, name='team_detail'),
    path('team/<uuid:pk>/edit/', views.team_update, name='team_update'),
    path('team/<uuid:pk>/delete/', views.team_delete, name='team_delete'),

    # Team Member Dashboard & Personal Views
    path('my-dashboard/', views.team_dashboard, name='team_dashboard'),
    path('my-tasks/', views.my_tasks, name='my_tasks'),
    path('my-time/', views.my_time, name='my_time'),

    # License Management
    path('licenses/', views.license_list, name='license_list'),
    path('licenses/create/', views.license_create, name='license_create'),
    path('licenses/<uuid:pk>/', views.license_detail, name='license_detail'),
    path('licenses/<uuid:pk>/update/', views.license_update, name='license_update'),
    path('licenses/<uuid:pk>/revoke/', views.license_revoke, name='license_revoke'),
    path('licenses/sync/', views.sync_licenses, name='sync_licenses'),
    path('licenses/<uuid:pk>/deactivate/<uuid:activation_id>/', views.license_deactivate_device, name='license_deactivate_device'),
    path('licenses/<uuid:pk>/delete-activation/<uuid:activation_id>/', views.license_delete_activation, name='license_delete_activation'),
    path('licenses/keys/', views.license_keys, name='license_keys'),
    path('licenses/keys/generate/', views.license_generate_keys, name='license_generate_keys'),

    # GymPro License Management (Web Views)
    path('gympro/licenses/', gympro_web_views.gym_license_list, name='gym_license_list'),
    path('gympro/licenses/create/', gympro_web_views.gym_license_create, name='gym_license_create'),
    path('gympro/licenses/<uuid:pk>/', gympro_web_views.gym_license_detail, name='gym_license_detail'),
    path('gympro/licenses/<uuid:pk>/update/', gympro_web_views.gym_license_update, name='gym_license_update'),

    # EduFlow License Management (Web Views)
    path('eduflow/licenses/', eduflow_web_views.eduflow_license_list, name='eduflow_license_list'),
    path('eduflow/licenses/create/', eduflow_web_views.eduflow_license_create, name='eduflow_license_create'),
    path('eduflow/licenses/<uuid:pk>/', eduflow_web_views.eduflow_license_detail, name='eduflow_license_detail'),
    path('eduflow/licenses/<uuid:pk>/update/', eduflow_web_views.eduflow_license_update, name='eduflow_license_update'),

    # HR & Admin
    path('hr/employees/', views.emp_employee_list, name='emp_employee_list'),
    path('hr/employees/create/', views.emp_employee_create, name='emp_employee_create'),
    path('hr/employees/import/', views.emp_employee_import, name='emp_employee_import'),
    path('hr/employees/<uuid:pk>/', views.emp_employee_detail, name='emp_employee_detail'),
    path('hr/employees/<uuid:pk>/delete/', views.emp_employee_delete, name='emp_employee_delete'),
    path('hr/attendance/', views.emp_attendance_list, name='emp_attendance_list'),
    path('hr/attendance/report/', views.emp_attendance_report, name='emp_attendance_report'),
    path('hr/attendance/late-grant/', views.emp_late_checkin_grant, name='emp_late_checkin_grant'),
    path('hr/attendance/late-grant/<uuid:pk>/revoke/', views.emp_late_checkin_revoke, name='emp_late_checkin_revoke'),
    path('hr/leave/', views.emp_leave_list, name='emp_leave_list'),
    path('hr/leave/<uuid:pk>/action/', views.emp_leave_action, name='emp_leave_action'),
    path('hr/leave/types/', views.emp_leave_types, name='emp_leave_types'),
    path('hr/office-qr/', views.emp_office_qr, name='emp_office_qr'),
    path('hr/work/', views.emp_work_list, name='emp_work_list'),
    path('hr/work/create/', views.emp_work_create, name='emp_work_create'),
    path('hr/work/<uuid:pk>/', views.emp_work_detail, name='emp_work_detail'),
    path('hr/work/<uuid:pk>/delete/', views.emp_work_delete, name='emp_work_delete'),

    # Scheduled Classes
    path('hr/classes/', views.emp_class_list, name='emp_class_list'),
    path('hr/classes/create/', views.emp_class_create, name='emp_class_create'),
    path('hr/classes/<uuid:pk>/', views.emp_class_detail, name='emp_class_detail'),
    path('hr/classes/<uuid:pk>/delete/', views.emp_class_delete, name='emp_class_delete'),

    # Payroll
    path('hr/payroll/', views.emp_payroll_list, name='emp_payroll_list'),

    # Certificate Templates
    path('hr/certificate-templates/', views.certificate_template_list, name='certificate_template_list'),
    path('hr/certificate-templates/create/', views.certificate_template_create, name='certificate_template_create'),
    path('hr/certificate-templates/<uuid:pk>/', views.certificate_template_detail, name='certificate_template_detail'),
    path('hr/certificate-templates/<uuid:pk>/delete/', views.certificate_template_delete, name='certificate_template_delete'),

    # Certificates
    path('hr/certificates/', views.certificate_list, name='certificate_list'),
    path('hr/certificates/create/', views.certificate_create, name='certificate_create'),
    path('hr/certificates/<uuid:pk>/', views.certificate_detail, name='certificate_detail'),
    path('hr/certificates/<uuid:pk>/delete/', views.certificate_delete, name='certificate_delete'),
    path('hr/certificates/<uuid:pk>/pdf/', views.certificate_pdf, name='certificate_pdf'),
]
