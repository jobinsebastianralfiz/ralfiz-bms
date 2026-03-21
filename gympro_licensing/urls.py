from django.urls import path
from . import views

app_name = 'gympro_licensing'

urlpatterns = [
    # ─── Gym-facing API (called by GymPro backends) ────
    path('validate/', views.validate_license, name='validate'),
    path('check/', views.check_license, name='check'),
    path('status/', views.license_status, name='status'),

    # ─── Admin API (called by Ralfiz admin) ────────────
    path('renew/', views.renew_license, name='renew'),
    path('revoke/', views.revoke_license, name='revoke'),
    path('suspend/', views.suspend_license, name='suspend'),
    path('reactivate/', views.reactivate_license, name='reactivate'),
]
