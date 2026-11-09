import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from apps.accounts.models import User
from apps.bookings.models import Booking
from apps.catalog.models import Service

SERVICES = [
    ("Basic Car Wash", 30, "299"),
    ("Full Car Wash", 60, "499"),
    ("Interior Detailing", 90, "1499"),
    ("Ceramic Coating", 240, "8999"),
    ("Bike Wash", 30, "149"),
]
NAMES = ["Anu", "Rahul", "Fathima", "Arjun", "Sneha", "Nihal", "Diya", "Joel", "Ameena", "Vishnu"]


class Command(BaseCommand):
    help = "Create demo services, staff, customers and bookings"

    def add_arguments(self, parser):
        parser.add_argument("--bookings", type=int, default=200)

    @transaction.atomic
    def handle(self, *args, **options):
        services = [
            Service.objects.get_or_create(
                slug=slugify(name),
                defaults={"name": name, "duration_minutes": mins, "price": Decimal(price)},
            )[0]
            for name, mins, price in SERVICES
        ]
        staff = [
            User.objects.get_or_create(username=f"staff{i}", defaults={"role": User.Role.STAFF, "first_name": f"Staff {i}"})[0]
            for i in range(1, 4)
        ]
        customers = []
        for i, name in enumerate(NAMES, start=1):
            user, created = User.objects.get_or_create(
                username=name.lower(),
                defaults={"first_name": name, "phone": f"98950{i:05d}", "role": User.Role.CUSTOMER},
            )
            if created:
                user.set_password("demo12345")
                user.save(update_fields=["password"])
            customers.append(user)

        now = timezone.now().replace(minute=0, second=0, microsecond=0)
        bookings = []
        for _ in range(options["bookings"]):
            service = random.choice(services)
            start = now + timedelta(days=random.randint(-60, 14), hours=random.randint(-4, 6))
            status = Booking.Status.COMPLETED if start < now else random.choice(Booking.ACTIVE_STATUSES)
            if random.random() < 0.1:
                status = Booking.Status.CANCELLED
            bookings.append(
                Booking(
                    customer=random.choice(customers),
                    staff=random.choice(staff),
                    service=service,
                    start_at=start,
                    end_at=start + timedelta(minutes=service.duration_minutes),
                    status=status,
                    price=service.price,
                )
            )
        # bulk_create = one INSERT instead of hundreds (seed data only; skips overlap rules)
        Booking.objects.bulk_create(bookings, batch_size=500)
        self.stdout.write(self.style.SUCCESS(f"Seeded {len(bookings)} bookings, {len(customers)} customers."))
