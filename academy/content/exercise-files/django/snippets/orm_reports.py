# python manage.py shell  — paste these one by one and watch the SQL
from datetime import timedelta
from decimal import Decimal

from django.db import connection, reset_queries
from django.db.models import Count, F, Q, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone

from apps.accounts.models import User
from apps.bookings.models import Booking
from apps.catalog.models import Service

today = timezone.localdate()
S = Booking.Status

# 1. Today's confirmed bookings — customer + service fetched in the SAME query (JOIN)
todays = Booking.objects.filter(start_at__date=today, status=S.CONFIRMED).select_related("customer", "service")

# 2. This month's revenue and count (one aggregate query)
month = Booking.objects.filter(
    status=S.COMPLETED, start_at__year=today.year, start_at__month=today.month
).aggregate(revenue=Sum("price"), jobs=Count("id"))

# 3. Most popular services, with a conditional count
popular = Service.objects.annotate(
    total=Count("bookings"),
    cancelled=Count("bookings", filter=Q(bookings__status=S.CANCELLED)),
).order_by("-total")

# 4. Daily revenue for a chart (GROUP BY date)
daily = (
    Booking.objects.filter(status=S.COMPLETED, start_at__date__gte=today - timedelta(days=30))
    .annotate(day=TruncDate("start_at"))
    .values("day")
    .annotate(revenue=Sum("price"))
    .order_by("day")
)

# 5. Top 5 customers by spend
top_customers = (
    User.objects.filter(role=User.Role.CUSTOMER)
    .annotate(spent=Sum("bookings__price", filter=Q(bookings__status=S.COMPLETED)))
    .filter(spent__isnull=False)
    .order_by("-spent")[:5]
)

# 6. Search across relations with OR
q = "anu"
found = Booking.objects.filter(
    Q(customer__first_name__icontains=q) | Q(customer__phone__icontains=q) | Q(service__name__icontains=q)
)

# 7. Bulk update in the database — no Python loop, no race condition
#    (in real life: round prices afterwards, and log who changed them)
Service.objects.filter(slug="bike-wash").update(price=F("price") + Decimal("20"))

# 8. Staff who are free tomorrow
tomorrow = today + timedelta(days=1)
free_staff = User.objects.filter(role=User.Role.STAFF).exclude(assigned_bookings__start_at__date=tomorrow)

# ---- The N+1 problem, measured ----
from django.conf import settings
settings.DEBUG = True  # query log is only kept when DEBUG is on

reset_queries()
for b in Booking.objects.all()[:50]:
    _ = (b.customer.first_name, b.service.name)   # each access = a new query
print("without select_related:", len(connection.queries))  # 101

reset_queries()
for b in Booking.objects.select_related("customer", "service")[:50]:
    _ = (b.customer.first_name, b.service.name)
print("with select_related:", len(connection.queries))     # 1

print(todays.count(), month, list(popular.values("name", "total"))[:2], len(daily), list(top_customers.values("username", "spent"))[:2], found.count(), free_staff.count())
print(todays.query)  # see the generated SQL
