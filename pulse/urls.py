from django.urls import path

from .views import (
    AskView,
    CommandCenterView,
    DocumentsView,
    GraphDashboardView,
    WeatherView,
)

app_name = 'pulse'

urlpatterns = [
    path('ask/', AskView.as_view(), name='ask'),
    path('documents/', DocumentsView.as_view(), name='documents'),
    path('weather/', WeatherView.as_view(), name='weather'),
    path('command-center/', CommandCenterView.as_view(), name='command-center'),
    path('portfolio/', GraphDashboardView.as_view(), name='portfolio'),
]
