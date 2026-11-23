from django.urls import path
from . import chat_views

app_name = 'support_chat'

urlpatterns = [
    path('', chat_views.inbox, name='inbox'),
    path('alerts/', chat_views.alerts, name='alerts'),
    path('<uuid:client_id>/', chat_views.inbox, name='thread'),
    path('<uuid:client_id>/poll/', chat_views.staff_poll, name='poll'),
    path('<uuid:client_id>/send/', chat_views.staff_send, name='send'),
]
