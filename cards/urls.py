from django.urls import path

from . import views

app_name = 'cards'

urlpatterns = [
    # Public: what clients and leads open
    path('card/<slug:slug>/', views.public_card, name='public'),
    path('card/<slug:slug>/contact.vcf', views.card_vcf, name='vcf'),
    path('card/<slug:slug>/qr.png', views.card_qr, name='qr'),
    path('card/<slug:slug>/connect/', views.card_enquiry, name='enquiry'),

    # Owner
    path('cards/', views.card_list, name='list'),
    path('cards/new/', views.card_create, name='create'),
    path('cards/<uuid:pk>/', views.card_share, name='share'),
    path('cards/<uuid:pk>/edit/', views.card_edit, name='edit'),
    path('cards/<uuid:pk>/delete/', views.card_delete, name='delete'),
]
