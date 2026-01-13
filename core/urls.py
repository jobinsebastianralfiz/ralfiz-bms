from django.urls import path
from . import views

urlpatterns = [
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

    # Projects
    path('projects/', views.project_list, name='project_list'),
    path('projects/create/', views.project_create, name='project_create'),
    path('projects/import/', views.project_import, name='project_import'),
    path('projects/<uuid:pk>/', views.project_detail, name='project_detail'),
    path('projects/<uuid:pk>/edit/', views.project_update, name='project_update'),
    path('projects/<uuid:pk>/delete/', views.project_delete, name='project_delete'),

    # Credentials
    path('credentials/', views.credential_list, name='credential_list'),
    path('credentials/create/', views.credential_create, name='credential_create'),
    path('credentials/<uuid:pk>/', views.credential_detail, name='credential_detail'),
    path('credentials/<uuid:pk>/edit/', views.credential_update, name='credential_update'),
    path('credentials/<uuid:pk>/delete/', views.credential_delete, name='credential_delete'),
    path('credentials/expiring/', views.credential_expiry, name='credential_expiry'),

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
    path('invoices/<uuid:pk>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/<uuid:pk>/edit/', views.invoice_update, name='invoice_update'),
    path('invoices/<uuid:pk>/pdf/', views.invoice_pdf, name='invoice_pdf'),
    path('invoices/<uuid:pk>/delete/', views.invoice_delete, name='invoice_delete'),
    path('invoices/<uuid:pk>/clone/', views.invoice_clone, name='invoice_clone'),

    # Payments
    path('payments/', views.payment_list, name='payment_list'),
    path('payments/create/', views.payment_create, name='payment_create'),
    path('payments/<uuid:pk>/receipt/', views.payment_receipt, name='payment_receipt'),

    # Settings & Reports
    path('settings/', views.settings_view, name='settings'),
    path('reports/', views.reports_view, name='reports'),

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

    # Tasks
    path('tasks/', views.task_list, name='task_list'),
    path('tasks/board/', views.task_board, name='task_board'),
    path('tasks/create/', views.task_create, name='task_create'),
    path('tasks/<uuid:pk>/', views.task_detail, name='task_detail'),
    path('tasks/<uuid:pk>/edit/', views.task_update, name='task_update'),
    path('tasks/<uuid:pk>/delete/', views.task_delete, name='task_delete'),
    path('tasks/<uuid:pk>/status/', views.task_status_update, name='task_status_update'),

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
]
