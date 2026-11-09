from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.DashboardHomeView.as_view(), name="home"),
    path("bookings/", views.BookingListView.as_view(), name="booking-list"),
    path("bookings/<int:pk>/", views.BookingDetailView.as_view(), name="booking-detail"),
    path("bookings/<int:pk>/status/", views.booking_change_status, name="booking-status"),
    path("services/", views.ServiceListView.as_view(), name="service-list"),
    path("services/new/", views.ServiceCreateView.as_view(), name="service-create"),
    path("services/<int:pk>/edit/", views.ServiceUpdateView.as_view(), name="service-edit"),
]
