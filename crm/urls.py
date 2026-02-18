from django.urls import path
from . import views

app_name = 'crm'

urlpatterns = [
    # Dashboard
    path('', views.crm_dashboard, name='dashboard'),

    # Leads
    path('leads/', views.lead_list, name='lead_list'),
    path('leads/create/', views.lead_create, name='lead_create'),
    path('leads/check-duplicate/', views.lead_check_duplicate, name='lead_check_duplicate'),
    path('leads/<int:pk>/', views.lead_detail, name='lead_detail'),
    path('leads/<int:pk>/edit/', views.lead_edit, name='lead_edit'),
    path('leads/<int:pk>/change-status/', views.lead_change_status, name='lead_change_status'),
    path('leads/<int:lead_pk>/note/create/', views.lead_note_create, name='lead_note_create'),

    # Activities
    path('activities/', views.activity_list, name='activity_list'),
    path('activities/create/', views.activity_create, name='activity_create'),
    path('activities/weekly-summary/', views.activity_weekly_summary, name='activity_weekly_summary'),
    path('activities/<int:pk>/edit/', views.activity_edit, name='activity_edit'),
    path('activities/<int:pk>/approve/', views.activity_approve, name='activity_approve'),

    # Demos
    path('demos/', views.demo_list, name='demo_list'),
    path('demos/create/', views.demo_create, name='demo_create'),
    path('demos/<int:pk>/', views.demo_detail, name='demo_detail'),
    path('demos/<int:pk>/edit/', views.demo_edit, name='demo_edit'),
    path('demos/<int:pk>/update-status/', views.demo_update_status, name='demo_update_status'),

    # Interns
    path('interns/', views.intern_list, name='intern_list'),
    path('interns/create/', views.intern_create, name='intern_create'),
    path('interns/<int:pk>/', views.intern_profile_detail, name='intern_profile_detail'),
    path('interns/<int:pk>/edit/', views.intern_profile_edit, name='intern_profile_edit'),
]
