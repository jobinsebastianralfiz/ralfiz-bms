from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.accounts.models import User
from apps.bookings.models import Booking
from apps.bookings.services import BookingError, create_booking
from apps.catalog.models import Service


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "email", "phone", "password"]

    def validate_password(self, value):
        validate_password(value)  # reuse Django's password validators
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data, role=User.Role.CUSTOMER)


class MeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email", "phone", "role"]
        read_only_fields = ["username", "role"]


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ["id", "name", "slug", "description", "duration_minutes", "price", "gst_rate"]


class BookingSerializer(serializers.ModelSerializer):
    service = ServiceSerializer(read_only=True)  # nested on read
    service_id = serializers.PrimaryKeyRelatedField(  # plain id on write
        queryset=Service.objects.filter(is_active=True), source="service", write_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id", "service", "service_id", "start_at", "end_at",
            "status", "status_display", "price", "notes", "created_at",
        ]
        read_only_fields = ["end_at", "status", "price", "created_at"]

    def create(self, validated_data):
        try:
            return create_booking(customer=self.context["request"].user, **validated_data)
        except BookingError as exc:
            raise serializers.ValidationError({"start_at": [str(exc)]}) from exc
