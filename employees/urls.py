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

    # Payslips (employee view)
    path('payslips/', views.PayslipListView.as_view(), name='payslip_list'),
    path('payslips/<uuid:pk>/', views.PayslipDetailView.as_view(), name='payslip_detail'),

    # Notifications
    path('notifications/', views.NotificationListView.as_view(), name='notifications'),
    path('notifications/read/', views.NotificationMarkReadView.as_view(), name='notifications_read_all'),
    path('notifications/<uuid:pk>/read/', views.NotificationMarkReadView.as_view(), name='notification_read'),

    # ---- Owner/Partner APIs ----
    path('owner/dashboard/', views.OwnerDashboardView.as_view(), name='owner_dashboard'),
    path('owner/clients/', views.OwnerClientListView.as_view(), name='owner_clients'),
    path('owner/clients/<uuid:pk>/', views.OwnerClientDetailView.as_view(), name='owner_client_detail'),
    path('owner/projects/', views.OwnerProjectListView.as_view(), name='owner_projects'),
    path('owner/projects/<uuid:pk>/', views.OwnerProjectDetailView.as_view(), name='owner_project_detail'),
    path('owner/invoices/', views.OwnerInvoiceListView.as_view(), name='owner_invoices'),
    path('owner/invoices/<uuid:pk>/', views.OwnerInvoiceDetailView.as_view(), name='owner_invoice_detail'),
    path('owner/quotes/', views.OwnerQuoteListView.as_view(), name='owner_quotes'),
    path('owner/expenses/', views.OwnerExpenseListView.as_view(), name='owner_expenses'),
    path('owner/financial-report/', views.OwnerFinancialReportView.as_view(), name='owner_financial_report'),
    path('owner/attendance/', views.OwnerAttendanceView.as_view(), name='owner_attendance'),
    path('owner/employees/', views.OwnerEmployeeListView.as_view(), name='owner_employees'),
    path('owner/employees/<uuid:pk>/', views.OwnerEmployeeDetailView.as_view(), name='owner_employee_detail'),

    # Owner/Partner CRUD
    path('owner/clients/create/', views.OwnerClientCreateView.as_view(), name='owner_client_create'),
    path('owner/clients/<uuid:pk>/edit/', views.OwnerClientUpdateDeleteView.as_view(), name='owner_client_edit'),
    path('owner/projects/create/', views.OwnerProjectCreateView.as_view(), name='owner_project_create'),
    path('owner/projects/<uuid:pk>/edit/', views.OwnerProjectUpdateDeleteView.as_view(), name='owner_project_edit'),
    path('owner/credentials/create/', views.OwnerCredentialCreateView.as_view(), name='owner_credential_create'),
    path('owner/credentials/<uuid:pk>/edit/', views.OwnerCredentialUpdateDeleteView.as_view(), name='owner_credential_edit'),
    path('owner/invoices/create/', views.OwnerInvoiceCreateView.as_view(), name='owner_invoice_create'),
    path('owner/invoices/<uuid:pk>/edit/', views.OwnerInvoiceUpdateDeleteView.as_view(), name='owner_invoice_edit'),
    path('owner/invoices/<uuid:pk>/payments/', views.OwnerPaymentCreateView.as_view(), name='owner_payment_create'),
    path('owner/quotes/create/', views.OwnerQuoteCreateView.as_view(), name='owner_quote_create'),
    path('owner/quotes/<uuid:pk>/edit/', views.OwnerQuoteUpdateDeleteView.as_view(), name='owner_quote_edit'),
    path('owner/expenses/create/', views.OwnerExpenseCreateView.as_view(), name='owner_expense_create'),
    path('owner/expenses/<uuid:pk>/edit/', views.OwnerExpenseUpdateDeleteView.as_view(), name='owner_expense_edit'),

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

    # Admin: Payroll
    path('admin/payroll/generate/', views.AdminPayrollGenerateView.as_view(), name='admin_payroll_generate'),
    path('admin/payroll/', views.AdminPayrollListView.as_view(), name='admin_payroll_list'),
    path('admin/payroll/<uuid:pk>/', views.AdminPayrollDetailView.as_view(), name='admin_payroll_detail'),

    # ---- Certificates ----
    path('certificates/', views.CertificateListCreateView.as_view(), name='certificate_list_create'),
    path('certificates/templates/', views.CertificateTemplateListView.as_view(), name='certificate_templates'),
    path('certificates/<uuid:pk>/', views.CertificateDetailView.as_view(), name='certificate_detail'),
    path('certificates/<uuid:pk>/pdf/', views.CertificatePDFView.as_view(), name='certificate_pdf'),
    path('certificates/verify/<uuid:verification_id>/', views.CertificateVerifyView.as_view(), name='certificate_verify'),

    # ---- CRM APIs (Leads, Activities, Demos) ----
    path('crm/dashboard/', views.CRMDashboardView.as_view(), name='crm_dashboard'),

    # Leads
    path('crm/leads/', views.CRMLeadListCreateView.as_view(), name='crm_leads'),
    path('crm/leads/check-duplicate/', views.CRMLeadCheckDuplicateView.as_view(), name='crm_lead_check_duplicate'),
    path('crm/leads/<int:pk>/', views.CRMLeadDetailView.as_view(), name='crm_lead_detail'),
    path('crm/leads/<int:pk>/status/', views.CRMLeadStatusUpdateView.as_view(), name='crm_lead_status'),
    path('crm/leads/<int:pk>/notes/', views.CRMLeadNoteCreateView.as_view(), name='crm_lead_notes'),

    # Daily Activities
    path('crm/activities/', views.CRMActivityListCreateView.as_view(), name='crm_activities'),
    path('crm/activities/weekly-summary/', views.CRMActivityWeeklySummaryView.as_view(), name='crm_activity_weekly'),
    path('crm/activities/<int:pk>/', views.CRMActivityDetailView.as_view(), name='crm_activity_detail'),
    path('crm/activities/<int:pk>/approve/', views.CRMActivityApproveView.as_view(), name='crm_activity_approve'),

    # Demos
    path('crm/demos/', views.CRMDemoListCreateView.as_view(), name='crm_demos'),
    path('crm/demos/<int:pk>/', views.CRMDemoDetailView.as_view(), name='crm_demo_detail'),
    path('crm/demos/<int:pk>/status/', views.CRMDemoStatusUpdateView.as_view(), name='crm_demo_status'),
]
