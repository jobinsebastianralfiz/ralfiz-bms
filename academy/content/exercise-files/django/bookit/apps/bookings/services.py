"""Business logic lives here — not in views, serializers or signals.

Views (HTML) and API viewsets both call these functions, so the rules
are written once and tested once.
"""
from datetime import date, datetime, time, timedelta

from django.db import transaction
from django.utils import timezone

from apps.catalog.models import Service

from .models import Booking


class BookingError(Exception):
    """A business rule was violated. The message is safe to show users."""


@transaction.atomic
def create_booking(*, customer, service: Service, start_at: datetime, staff=None, notes: str = "") -> Booking:
    # Lock the service row: two people clicking "Book" for the same slot at the
    # same moment are now processed one after the other, never both accepted.
    service = Service.objects.select_for_update().get(pk=service.pk)

    if not service.is_active:
        raise BookingError("This service is not available right now.")
    if start_at <= timezone.now():
        raise BookingError("Please choose a time in the future.")

    end_at = start_at + timedelta(minutes=service.duration_minutes)
    clash = Booking.objects.filter(
        service=service,
        status__in=Booking.ACTIVE_STATUSES,
        start_at__lt=end_at,  # overlap test: A.start < B.end AND A.end > B.start
        end_at__gt=start_at,
    ).exists()
    if clash:
        raise BookingError("That slot was just taken. Please pick another time.")

    return Booking.objects.create(
        customer=customer,
        service=service,
        staff=staff,
        start_at=start_at,
        end_at=end_at,
        price=service.price,
        notes=notes,
    )


@transaction.atomic
def change_status(*, booking: Booking, new_status: str, by) -> Booking:
    booking = Booking.objects.select_for_update().get(pk=booking.pk)
    if not booking.can_transition_to(new_status):
        raise BookingError(f"A {booking.get_status_display().lower()} booking cannot become '{new_status}'.")
    if not by.is_staff_member and booking.customer_id != by.pk:
        raise BookingError("You can only change your own bookings.")
    booking.status = new_status
    booking.save(update_fields=["status", "updated_at"])
    return booking


def available_slots(service: Service, day: date, *, opens=time(9), closes=time(18), step_minutes=30) -> list[str]:
    tz = timezone.get_current_timezone()
    window_start = datetime.combine(day, opens, tzinfo=tz)
    window_end = datetime.combine(day, closes, tzinfo=tz)
    duration = timedelta(minutes=service.duration_minutes)

    taken = list(
        Booking.objects.filter(
            service=service,
            status__in=Booking.ACTIVE_STATUSES,
            start_at__lt=window_end,
            end_at__gt=window_start,
        ).values_list("start_at", "end_at")
    )

    now = timezone.now()
    slots, cursor = [], window_start
    while cursor + duration <= window_end:
        end = cursor + duration
        free = all(not (s < end and e > cursor) for s, e in taken)
        if cursor > now and free:
            slots.append(cursor.isoformat())
        cursor += timedelta(minutes=step_minutes)
    return slots
