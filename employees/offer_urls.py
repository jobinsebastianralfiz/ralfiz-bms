from django.urls import path

from . import offer_views

urlpatterns = [
    # More specific paths first: a bare <token> would otherwise swallow them.
    path('<str:token>/done/', offer_views.offer_done, name='offer_done'),
    path('<str:token>/copy/', offer_views.offer_copy, name='offer_copy'),
    path('<str:token>/copy.pdf', offer_views.offer_copy_pdf, name='offer_copy_pdf'),
    path('<str:token>/', offer_views.offer_view, name='offer_view'),
]
