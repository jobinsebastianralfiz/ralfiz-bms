from django.urls import path
from . import views

app_name = 'interiodesk'

urlpatterns = [
    # Public Config (No Auth Required)
    path('config/', views.get_app_config, name='app_config'),
]