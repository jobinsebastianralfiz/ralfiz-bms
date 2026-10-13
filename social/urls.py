from django.urls import path

from . import views

app_name = 'social'

urlpatterns = [
    path('', views.home, name='home'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('post/new/', views.compose, name='post_new'),
    path('post/<uuid:pk>/', views.compose, name='post_edit'),
    path('post/<uuid:pk>/action/', views.post_action, name='post_action'),
    path('post/<uuid:pk>/move/', views.post_move, name='post_move'),
    path('posts/', views.posts_library, name='posts'),
    path('approvals/', views.approvals, name='approvals'),
    path('inbox/', views.inbox, name='inbox'),
    path('inbox/<uuid:pk>/action/', views.inbox_action, name='inbox_action'),
    path('analytics/', views.analytics, name='analytics'),
    path('website/', views.website, name='website'),
    path('reports/', views.reports, name='reports'),
    path('reports/<uuid:ws>/<str:month>.pdf', views.report_pdf, name='report_pdf'),
    path('media/', views.media_library, name='media'),
    path('media/<uuid:pk>/delete/', views.media_delete, name='media_delete'),
    path('m/<str:token>/', views.media_file, name='media_file'),
    path('accounts/', views.accounts, name='accounts'),
    path('accounts/<uuid:pk>/action/', views.account_action, name='account_action'),
    path('connect/pick/', views.connect_pick, name='connect_pick'),
    path('connect/whatsapp/signup/', views.connect_whatsapp, name='connect_whatsapp'),
    path('connect/<str:platform>/', views.connect_start, name='connect'),
    path('connect/<str:platform>/manual/', views.connect_manual, name='connect_manual'),
    path('oauth/callback/<str:platform>/', views.oauth_callback, name='oauth_callback'),
    path('activity/', views.activity, name='activity'),
    path('clients/', views.workspaces, name='workspaces'),
    path('review/<str:token>/', views.review, name='review'),
    path('webhooks/meta/', views.meta_webhook, name='meta_webhook'),
]
