from django.urls import path

from . import enrolment_views

urlpatterns = [
    path('<str:token>/done/', enrolment_views.enrolment_done, name='enrolment_done'),
    path('<str:token>/', enrolment_views.enrolment_form, name='enrolment_form'),
]
