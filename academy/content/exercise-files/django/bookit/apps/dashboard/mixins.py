from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Logged-in AND role is admin/staff. Customers get 403, guests go to login."""

    def test_func(self):
        return self.request.user.is_staff_member
