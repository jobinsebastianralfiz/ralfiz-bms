"""Permission scoping for PULSE.

Every query the AI can run goes through a PulseScope. Tools never receive a raw
User -- they receive a scope that has already been resolved and checked, so a
tool cannot accidentally run unscoped.

Phase 1 restricts PULSE to owner/partner users. The reason is structural: the
business models this app reads from (Project, Invoice, Quote, Client) have no
owner column of any kind, so there is nothing to filter a non-owner's view down
to. Rather than invent a scoping rule the schema cannot enforce, we gate at the
role level and widen later once the narrower views are designed.

Two independent gates are honoured, because in this codebase they do not imply
each other:

  * Employee.role in ('owner', 'partner')  -- the app's own role system
  * user.is_staff                          -- Django admin

A superuser is auto-promoted to role='owner' on JWT login (see
employees/auth_views.py), but an owner created by hand is not necessarily
is_staff. Checking only one gate locks out real users.
"""

from dataclasses import dataclass
from typing import Optional

from rest_framework.exceptions import PermissionDenied

from employees.models import Employee

#: Employee.role values that may query business-wide data.
OWNER_ROLES = ('owner', 'partner')


@dataclass(frozen=True)
class PulseScope:
    """A resolved, already-authorised view of who is asking."""

    user: object
    employee: Optional[Employee]
    can_query_business: bool

    @property
    def display_name(self) -> str:
        if self.employee is not None:
            return self.employee.full_name
        return self.user.get_full_name() or self.user.get_username()

    def require_business(self) -> None:
        """Raise unless this scope may read business-wide data.

        Every tool calls this before touching the ORM. It is deliberately a
        raise rather than a silent empty queryset: a caller who is not allowed
        to see revenue should get an error, not a confident report of zero.
        """
        if not self.can_query_business:
            raise PermissionDenied(
                'PULSE is available to owner and partner accounts only.'
            )


def resolve_scope(user) -> PulseScope:
    """Build the scope for an authenticated user.

    Never raises for an ordinary authenticated user -- it returns a scope with
    can_query_business=False. The raise happens at tool-call time via
    require_business(), so the view can still answer "who am I" style requests
    later without a permission wall at the door.
    """
    if user is None or not user.is_authenticated:
        raise PermissionDenied('Authentication required.')

    # Mirrors employees.views.get_employee: inactive employees resolve to None.
    employee = Employee.objects.filter(user=user, status='active').first()

    is_owner_role = employee is not None and employee.role in OWNER_ROLES
    can_query_business = bool(is_owner_role or user.is_staff)

    return PulseScope(
        user=user,
        employee=employee,
        can_query_business=can_query_business,
    )
