from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.bookings.models import Booking
from apps.catalog.models import Service


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def customer(db):
    return User.objects.create_user("anu", password="Str0ng-Pass!", role=User.Role.CUSTOMER)


@pytest.fixture
def other_customer(db):
    return User.objects.create_user("rahul", password="Str0ng-Pass!", role=User.Role.CUSTOMER)


@pytest.fixture
def service(db):
    return Service.objects.create(name="Full Car Wash", slug="full-car-wash", duration_minutes=60, price="499.00")


def tomorrow_at(hour):
    return (timezone.now() + timedelta(days=1)).replace(hour=hour, minute=0, second=0, microsecond=0)


def test_register_then_login_returns_jwt(api, db):
    r = api.post("/api/v1/auth/register/", {"username": "diya", "password": "Kerala@2026!", "phone": "9895000001"}, format="json")
    assert r.status_code == 201, r.data
    r = api.post("/api/v1/auth/token/", {"username": "diya", "password": "Kerala@2026!"}, format="json")
    assert r.status_code == 200
    assert {"access", "refresh"} <= r.data.keys()


def test_booking_snapshots_price_and_blocks_double_booking(api, customer, other_customer, service):
    payload = {"service_id": service.id, "start_at": tomorrow_at(10).isoformat()}

    api.force_authenticate(customer)
    r = api.post("/api/v1/bookings/", payload, format="json")
    assert r.status_code == 201, r.data
    assert r.data["price"] == "499.00"
    assert r.data["status"] == "pending"

    api.force_authenticate(other_customer)
    r = api.post("/api/v1/bookings/", payload, format="json")
    assert r.status_code == 400
    assert r.data["success"] is False


def test_customer_cannot_see_someone_elses_booking(api, customer, other_customer, service):
    b = Booking.objects.create(
        customer=customer, service=service, start_at=tomorrow_at(11),
        end_at=tomorrow_at(12), price=service.price,
    )
    api.force_authenticate(other_customer)
    assert api.get(f"/api/v1/bookings/{b.id}/").status_code == 404


def test_cancel_and_slots(api, customer, service):
    api.force_authenticate(customer)
    start = tomorrow_at(14)
    booking_id = api.post("/api/v1/bookings/", {"service_id": service.id, "start_at": start.isoformat()}, format="json").data["id"]

    slots = api.get(f"/api/v1/services/{service.slug}/slots/?date={timezone.localtime(start).date()}").data["slots"]
    assert timezone.localtime(start).isoformat() not in slots

    r = api.post(f"/api/v1/bookings/{booking_id}/cancel/")
    assert r.status_code == 200 and r.data["status"] == "cancelled"
    r = api.post(f"/api/v1/bookings/{booking_id}/cancel/")
    assert r.status_code == 400  # cancelled -> cancelled is not allowed


def test_dashboard_blocks_customers(client, customer):
    client.force_login(customer)
    assert client.get("/dashboard/").status_code == 403
