from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .auth import ClientTokenObtainView
from . import views, admin_views

urlpatterns = [
    # Auth
    path('auth/login/', ClientTokenObtainView.as_view(), name='api-login'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='api-token-refresh'),
    path('auth/change-password/', views.ClientChangePasswordView.as_view(), name='api-change-password'),

    # Dashboard
    path('dashboard/', views.ClientDashboardView.as_view(), name='api-dashboard'),

    # Profile
    path('profile/', views.ClientProfileView.as_view(), name='api-profile'),

    # Projects
    path('projects/', views.ClientProjectListView.as_view(), name='api-project-list'),
    path('projects/<uuid:project_id>/', views.ClientProjectDetailView.as_view(), name='api-project-detail'),
    path('projects/<uuid:project_id>/board/', views.ClientTaskBoardView.as_view(), name='api-task-board'),
    path('projects/<uuid:project_id>/updates/', views.ClientProjectUpdatesView.as_view(), name='api-project-updates'),
    path('projects/<uuid:project_id>/comments/', views.ClientCommentListView.as_view(), name='api-project-comments'),
    path('projects/<uuid:project_id>/documents/', views.ClientDocumentListView.as_view(), name='api-project-documents'),

    # Tasks
    path('tasks/', views.ClientAllTasksView.as_view(), name='api-all-tasks'),

    # Invoices
    path('invoices/', views.ClientInvoiceListView.as_view(), name='api-invoice-list'),
    path('invoices/<uuid:invoice_id>/', views.ClientInvoiceDetailView.as_view(), name='api-invoice-detail'),

    # Quotes
    path('quotes/', views.ClientQuoteListView.as_view(), name='api-quote-list'),
    path('quotes/<uuid:quote_id>/', views.ClientQuoteDetailView.as_view(), name='api-quote-detail'),
    path('quotes/<uuid:quote_id>/respond/', views.ClientQuoteRespondView.as_view(), name='api-quote-respond'),

    # Comments
    path('comments/', views.ClientCommentCreateView.as_view(), name='api-comment-create'),

    # Notifications
    path('notifications/', views.ClientNotificationListView.as_view(), name='api-notification-list'),
    path('notifications/read/', views.ClientNotificationMarkReadView.as_view(), name='api-notifications-read-all'),
    path('notifications/<uuid:notification_id>/read/', views.ClientNotificationMarkSingleReadView.as_view(), name='api-notification-read'),

    # Admin
    path('admin/accounts/', admin_views.AdminListClientAccountsView.as_view(), name='admin-accounts-list'),
    path('admin/accounts/create/', admin_views.AdminCreateClientAccountView.as_view(), name='admin-account-create'),
    path('admin/accounts/reset-password/', admin_views.AdminResetClientPasswordView.as_view(), name='admin-reset-password'),
    path('admin/accounts/<uuid:client_id>/toggle/', admin_views.AdminDeactivateClientAccountView.as_view(), name='admin-account-toggle'),
    path('admin/updates/post/', admin_views.AdminPostProjectUpdateView.as_view(), name='admin-post-update'),
    path('admin/notifications/send/', admin_views.AdminSendClientNotificationView.as_view(), name='admin-send-notification'),
]
