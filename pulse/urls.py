from django.urls import path

from .views import AskView, CommandCenterView

app_name = 'pulse'

urlpatterns = [
    path('ask/', AskView.as_view(), name='ask'),
    path('command-center/', CommandCenterView.as_view(), name='command-center'),
]
