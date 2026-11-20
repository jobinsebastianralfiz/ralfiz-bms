from django.urls import path

from . import issue_views as iv
from . import views

app_name = 'bizpartners'

urlpatterns = [
    path('', views.partner_list, name='list'),
    path('new/', views.partner_form, name='create'),
    path('<uuid:pk>/', views.partner_detail, name='detail'),
    path('<uuid:pk>/edit/', views.partner_form, name='edit'),
    path('<uuid:pk>/login/', views.partner_login, name='login'),
    path('<uuid:pk>/login/toggle/', views.partner_login_toggle, name='login_toggle'),
    path('<uuid:partner_pk>/projects/new/', views.project_form, name='project_create'),
    path('projects/<uuid:pk>/', views.project_detail, name='project'),
    path('projects/<uuid:pk>/edit/', views.project_form, name='project_edit'),
    path('projects/<uuid:pk>/delete/', views.project_delete, name='project_delete'),
    # Issue list. Before the <str:kind> routes, so "issues" is never read as a kind.
    path('projects/<uuid:pk>/issues/export/', iv.issue_export, name='issue_export'),
    path('projects/<uuid:pk>/issues/add/', iv.issue_save, name='issue_add'),
    path('projects/<uuid:pk>/issues/read/', iv.issue_draft, name='issue_draft'),
    path('projects/<uuid:pk>/issues/add-many/', iv.issue_add_many, name='issue_add_many'),
    path('projects/<uuid:pk>/issues/import/', iv.issue_import, name='issue_import'),
    path('projects/<uuid:pk>/issues/bulk/', iv.issue_bulk, name='issue_bulk'),
    path('projects/<uuid:pk>/issues/<uuid:issue_id>/toggle/', iv.issue_toggle, name='issue_toggle'),
    path('projects/<uuid:pk>/issues/<uuid:issue_id>/save/', iv.issue_save, name='issue_save'),
    path('projects/<uuid:pk>/issues/<uuid:issue_id>/delete/', iv.issue_delete, name='issue_delete'),
    path('projects/<uuid:project_pk>/<str:kind>/new/', views.item_form, name='item_create'),
    path('projects/<uuid:project_pk>/<str:kind>/<uuid:pk>/edit/', views.item_form, name='item_edit'),
    path('projects/<uuid:project_pk>/<str:kind>/<uuid:pk>/delete/', views.item_delete, name='item_delete'),
    path('projects/<uuid:project_pk>/<str:kind>/<uuid:pk>/file/', views.item_file, name='item_file'),
]
