from django.urls import path

from . import signoff_views as views

urlpatterns = [
    # More specific paths first: a bare <token> would otherwise swallow them.
    path('<str:token>/done/', views.signoff_done, name='signoff_done'),
    path('<str:token>/copy.pdf', views.signoff_copy_pdf, name='signoff_copy_pdf'),
    path('<str:token>/', views.signoff_sign, name='signoff_sign'),
]
