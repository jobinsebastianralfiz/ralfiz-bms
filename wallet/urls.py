from django.urls import path

from . import web_views as v

app_name = 'wallet'

urlpatterns = [
    path('', v.approvals, name='approvals'),
    path('decide/', v.decide, name='decide'),
    path('wallets/', v.wallet_list, name='list'),
    path('wallets/<uuid:pk>/', v.wallet_detail, name='detail'),
    path('settings/', v.settings_view, name='settings'),
]
