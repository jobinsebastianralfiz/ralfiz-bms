from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user from day one — changing AUTH_USER_MODEL later is painful."""

    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        STAFF = "staff", "Staff"
        CUSTOMER = "customer", "Customer"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CUSTOMER)
    phone = models.CharField(max_length=15, unique=True, null=True, blank=True)

    @property
    def is_staff_member(self) -> bool:
        return self.role in {self.Role.ADMIN, self.Role.STAFF}

    def __str__(self) -> str:
        return self.get_full_name() or self.username
