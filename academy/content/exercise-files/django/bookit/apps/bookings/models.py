from django.conf import settings
from django.db import models
from django.db.models import F, Q

from apps.catalog.models import Service
from apps.core.models import TimeStampedModel


class Booking(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    # A tiny state machine: which status can move to which
    ALLOWED_TRANSITIONS = {
        Status.PENDING: {Status.CONFIRMED, Status.CANCELLED},
        Status.CONFIRMED: {Status.COMPLETED, Status.CANCELLED},
        Status.COMPLETED: set(),
        Status.CANCELLED: set(),
    }
    ACTIVE_STATUSES = (Status.PENDING, Status.CONFIRMED)

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="bookings"
    )
    staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_bookings",
        limit_choices_to={"role": "staff"},
    )
    service = models.ForeignKey(Service, on_delete=models.PROTECT, related_name="bookings")
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    # Snapshot of the price at booking time — later price changes must not rewrite history
    price = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-start_at"]
        indexes = [
            models.Index(fields=["status", "start_at"]),
            models.Index(fields=["service", "start_at"]),
        ]
        constraints = [
            models.CheckConstraint(condition=Q(end_at__gt=F("start_at")), name="booking_end_after_start"),
        ]

    def can_transition_to(self, new_status: str) -> bool:
        return new_status in self.ALLOWED_TRANSITIONS[self.status]

    def __str__(self) -> str:
        return f"#{self.pk} {self.service} for {self.customer} @ {self.start_at:%d %b %H:%M}"
