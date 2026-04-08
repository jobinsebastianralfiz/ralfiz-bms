from django.urls import path
from . import views

app_name = 'eduflow_licensing'

urlpatterns = [
    path('validate/', views.validate_license, name='validate'),
    path('check/', views.check_license, name='check'),
    path('status/', views.license_status, name='status'),
    path('renew/', views.renew_license, name='renew'),
    path('revoke/', views.revoke_license, name='revoke'),
    path('suspend/', views.suspend_license, name='suspend'),
    path('reactivate/', views.reactivate_license, name='reactivate'),
]
