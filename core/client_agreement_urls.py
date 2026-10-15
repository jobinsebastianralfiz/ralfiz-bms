from django.urls import path

from . import client_agreement_views as views

urlpatterns = [
    # More specific paths first: a bare <token> would otherwise swallow them.
    path('<str:token>/done/', views.client_agreement_done, name='client_agreement_done'),
    path('<str:token>/copy/', views.client_agreement_copy, name='client_agreement_copy'),
    path('<str:token>/copy.pdf', views.client_agreement_copy_pdf, name='client_agreement_copy_pdf'),
    path('<str:token>/', views.client_agreement_sign, name='client_agreement_sign'),
]
