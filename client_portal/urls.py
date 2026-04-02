from django.urls import path
from . import web_views

app_name = 'client_portal'

urlpatterns = [
    # Auth
    path('login/', web_views.portal_login, name='portal_login'),
    path('logout/', web_views.portal_logout, name='portal_logout'),

    # Dashboard
    path('', web_views.portal_dashboard, name='portal_dashboard'),

    # Projects
    path('projects/', web_views.portal_projects, name='portal_projects'),
    path('projects/<uuid:project_id>/', web_views.portal_project_detail, name='portal_project_detail'),
    path('projects/<uuid:project_id>/comment/', web_views.portal_add_comment, name='portal_add_comment'),

    # Invoices
    path('invoices/', web_views.portal_invoices, name='portal_invoices'),
    path('invoices/<uuid:invoice_id>/', web_views.portal_invoice_detail, name='portal_invoice_detail'),

    # Quotes
    path('quotes/', web_views.portal_quotes, name='portal_quotes'),
    path('quotes/<uuid:quote_id>/', web_views.portal_quote_detail, name='portal_quote_detail'),
    path('quotes/<uuid:quote_id>/respond/', web_views.portal_quote_respond, name='portal_quote_respond'),

    # Notifications
    path('notifications/', web_views.portal_notifications, name='portal_notifications'),
    path('notifications/mark-all-read/', web_views.portal_mark_all_read, name='portal_mark_all_read'),
    path('notifications/<uuid:notification_id>/read/', web_views.portal_mark_read, name='portal_mark_read'),

    # Profile
    path('profile/', web_views.portal_profile, name='portal_profile'),
    path('change-password/', web_views.portal_change_password, name='portal_change_password'),
]
