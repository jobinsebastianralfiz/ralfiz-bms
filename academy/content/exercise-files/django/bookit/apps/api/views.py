from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import generics, mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.bookings.models import Booking
from apps.bookings.services import BookingError, available_slots, change_status
from apps.catalog.models import Service

from .serializers import BookingSerializer, MeSerializer, RegisterSerializer, ServiceSerializer


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = MeSerializer

    def get_object(self):
        return self.request.user


class ServiceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Service.objects.filter(is_active=True)
    serializer_class = ServiceSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"
    search_fields = ["name", "description"]
    ordering_fields = ["price", "name", "duration_minutes"]

    @action(detail=True, methods=["get"])
    def slots(self, request, slug=None):
        """GET /api/v1/services/<slug>/slots/?date=2026-11-12"""
        service = self.get_object()
        day = parse_date(request.query_params.get("date", "")) or timezone.localdate()
        return Response({"date": day, "slots": available_slots(service, day)})


class BookingViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = BookingSerializer
    filterset_fields = ["status"]
    ordering_fields = ["start_at", "created_at"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):  # drf-spectacular schema generation
            return Booking.objects.none()
        qs = Booking.objects.select_related("service")
        user = self.request.user
        # Customers only ever see their own rows -> no IDOR (guessing /bookings/42/)
        return qs if user.is_staff_member else qs.filter(customer=user)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        booking = self.get_object()
        try:
            booking = change_status(booking=booking, new_status=Booking.Status.CANCELLED, by=request.user)
        except BookingError as exc:
            return Response({"success": False, "errors": {"detail": str(exc)}}, status=status.HTTP_400_BAD_REQUEST)
        return Response(self.get_serializer(booking).data)
