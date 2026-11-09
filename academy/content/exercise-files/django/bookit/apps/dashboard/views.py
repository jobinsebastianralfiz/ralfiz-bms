from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DetailView, ListView, TemplateView, UpdateView

from apps.bookings.models import Booking
from apps.bookings.services import BookingError, change_status
from apps.catalog.forms import ServiceForm
from apps.catalog.models import Service

from .mixins import StaffRequiredMixin


class DashboardHomeView(StaffRequiredMixin, TemplateView):
    template_name = "dashboard/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = timezone.localdate()
        bookings = Booking.objects.all()
        completed_this_month = bookings.filter(
            status=Booking.Status.COMPLETED, start_at__year=today.year, start_at__month=today.month
        )
        ctx["kpis"] = {
            "today": bookings.filter(start_at__date=today).count(),
            "pending": bookings.filter(status=Booking.Status.PENDING).count(),
            "month_revenue": completed_this_month.aggregate(total=Sum("price"))["total"] or 0,
            "month_completed": completed_this_month.count(),
        }
        ctx["upcoming"] = (
            bookings.filter(start_at__gte=timezone.now(), status__in=Booking.ACTIVE_STATUSES)
            .select_related("customer", "service", "staff")
            .order_by("start_at")[:8]
        )
        ctx["daily_revenue"] = (
            bookings.filter(status=Booking.Status.COMPLETED, start_at__date__gte=today - timedelta(days=14))
            .annotate(day=TruncDate("start_at"))
            .values("day")
            .annotate(revenue=Sum("price"), count=Count("id"))
            .order_by("day")
        )
        return ctx


class BookingListView(StaffRequiredMixin, ListView):
    template_name = "dashboard/bookings/list.html"
    context_object_name = "bookings"
    paginate_by = 20

    def get_queryset(self):
        qs = Booking.objects.select_related("customer", "service", "staff")
        q = self.request.GET.get("q", "").strip()
        status = self.request.GET.get("status", "")
        if q:
            qs = qs.filter(
                Q(customer__first_name__icontains=q)
                | Q(customer__phone__icontains=q)
                | Q(service__name__icontains=q)
            )
        if status in Booking.Status.values:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["statuses"] = Booking.Status.choices
        return ctx


class BookingDetailView(StaffRequiredMixin, DetailView):
    template_name = "dashboard/bookings/detail.html"
    queryset = Booking.objects.select_related("customer", "service", "staff")
    context_object_name = "booking"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        allowed = self.object.ALLOWED_TRANSITIONS[self.object.status]
        ctx["next_statuses"] = [(v, label) for v, label in Booking.Status.choices if v in allowed]
        return ctx


@require_POST
@login_required
def booking_change_status(request, pk):
    if not request.user.is_staff_member:
        raise PermissionDenied
    booking = get_object_or_404(Booking, pk=pk)
    try:
        change_status(booking=booking, new_status=request.POST.get("status", ""), by=request.user)
        messages.success(request, "Booking status updated.")
    except BookingError as exc:
        messages.error(request, str(exc))
    return redirect("dashboard:booking-detail", pk=pk)


class ServiceListView(StaffRequiredMixin, ListView):
    template_name = "dashboard/services/list.html"
    context_object_name = "services"
    queryset = Service.objects.annotate(total_bookings=Count("bookings"))


class ServiceFormMixin(StaffRequiredMixin, SuccessMessageMixin):
    model = Service
    form_class = ServiceForm
    template_name = "dashboard/services/form.html"
    success_url = reverse_lazy("dashboard:service-list")


class ServiceCreateView(ServiceFormMixin, CreateView):
    success_message = "Service “%(name)s” created."


class ServiceUpdateView(ServiceFormMixin, UpdateView):
    success_message = "Service “%(name)s” updated."
