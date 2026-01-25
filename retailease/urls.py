from django.urls import path
from . import views

app_name = 'retailease'

urlpatterns = [
    # Public Config (No Auth Required)
    path('config/', views.get_app_config, name='app_config'),

    # Authentication
    path('auth/', views.authenticate, name='authenticate'),
    path('auth/logout/', views.logout, name='logout'),

    # Status
    path('status/', views.status, name='status'),

    # Business
    path('business/', views.get_business, name='get_business'),
    path('business/register/', views.register_business, name='register_business'),

    # Counters
    path('counters/', views.list_counters, name='list_counters'),
    path('counters/<uuid:counter_id>/', views.update_counter, name='update_counter'),

    # Backups
    path('backups/', views.list_backups, name='list_backups'),
    path('backups/upload/', views.upload_backup, name='upload_backup'),
    path('backups/<uuid:backup_id>/', views.download_backup, name='download_backup'),
    path('backups/<uuid:backup_id>/delete/', views.delete_backup, name='delete_backup'),
    path('backups/cleanup/', views.cleanup_old_backups, name='cleanup_old_backups'),

    # Sync
    path('sync/start/', views.start_sync, name='start_sync'),
    path('sync/<uuid:sync_id>/complete/', views.complete_sync, name='complete_sync'),
    path('sync/history/', views.sync_history, name='sync_history'),
]