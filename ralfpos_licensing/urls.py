from django.urls import path

from . import views

app_name = 'ralfpos_licensing'

urlpatterns = [
    path('activate/', views.activate_license, name='activate'),
    path('check/', views.check_license, name='check'),
]
