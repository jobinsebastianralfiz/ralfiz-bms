from django.urls import path
from . import views

app_name = 'licensing'

urlpatterns = [
    path('validate/', views.validate_license, name='validate'),
    path('check/', views.check_license, name='check'),
    path('refresh/', views.refresh_license, name='refresh'),
    path('renew/', views.renew_license, name='renew'),
    path('deactivate/', views.deactivate_license, name='deactivate'),
    path('public-key/', views.get_public_key, name='public_key'),
    path('by-email/', views.get_licenses_by_email, name='licenses_by_email'),
]
