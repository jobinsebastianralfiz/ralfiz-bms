from django.urls import path

from . import views

app_name = 'shopmanager_licensing'

urlpatterns = [
    path('activate/', views.activate_license, name='activate'),
    path('check/', views.check_license, name='check'),
    path('chat/poll/', views.chat_poll, name='chat_poll'),
    path('chat/send/', views.chat_send, name='chat_send'),
]
