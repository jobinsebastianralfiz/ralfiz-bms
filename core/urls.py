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
    path('clients/<uuid:pk>/', views.client_detail, name='client_detail'),
    path('clients/<uuid:pk>/edit/', views.client_update, name='client_update'),

    # Projects
    path('projects/', views.project_list, name='project_list'),
    path('projects/create/', views.project_create, name='project_create'),
    path('projects/<uuid:pk>/', views.project_detail, name='project_detail'),
    path('projects/<uuid:pk>/edit/', views.project_update, name='project_update'),

    # Credentials
    path('credentials/', views.credential_list, name='credential_list'),
    path('credentials/create/', views.credential_create, name='credential_create'),
    path('credentials/<uuid:pk>/', views.credential_detail, name='credential_detail'),
    path('credentials/<uuid:pk>/edit/', views.credential_update, name='credential_update'),
    path('credentials/expiring/', views.credential_expiry, name='credential_expiry'),

    # Quotes
    path('quotes/', views.quote_list, name='quote_list'),
    path('quotes/create/', views.quote_create, name='quote_create'),
    path('quotes/<uuid:pk>/', views.quote_detail, name='quote_detail'),
    path('quotes/<uuid:pk>/edit/', views.quote_update, name='quote_update'),
    path('quotes/<uuid:pk>/pdf/', views.quote_pdf, name='quote_pdf'),

    # Invoices
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/create/', views.invoice_create, name='invoice_create'),
    path('invoices/<uuid:pk>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/<uuid:pk>/edit/', views.invoice_update, name='invoice_update'),
    path('invoices/<uuid:pk>/pdf/', views.invoice_pdf, name='invoice_pdf'),

    # Payments
    path('payments/', views.payment_list, name='payment_list'),
    path('payments/create/', views.payment_create, name='payment_create'),

    # Settings & Reports
    path('settings/', views.settings_view, name='settings'),
    path('reports/', views.reports_view, name='reports'),
]
