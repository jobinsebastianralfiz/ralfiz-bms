from django.urls import path

from . import agreement_views

urlpatterns = [
    # More specific paths first: a bare <token> would otherwise swallow them.
    path('<str:token>/done/', agreement_views.agreement_done, name='agreement_done'),
    path('<str:token>/pay/', agreement_views.agreement_pay, name='agreement_pay'),
    path('<str:token>/copy/', agreement_views.agreement_copy, name='agreement_copy'),
    path('<str:token>/copy.pdf', agreement_views.agreement_copy_pdf, name='agreement_copy_pdf'),
    path('<str:token>/', agreement_views.agreement_sign, name='agreement_sign'),
]
