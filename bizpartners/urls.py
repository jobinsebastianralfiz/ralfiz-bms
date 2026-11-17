from django.urls import path

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
    path('projects/<uuid:project_pk>/<str:kind>/new/', views.item_form, name='item_create'),
    path('projects/<uuid:project_pk>/<str:kind>/<uuid:pk>/edit/', views.item_form, name='item_edit'),
    path('projects/<uuid:project_pk>/<str:kind>/<uuid:pk>/delete/', views.item_delete, name='item_delete'),
    path('projects/<uuid:project_pk>/<str:kind>/<uuid:pk>/file/', views.item_file, name='item_file'),
]
