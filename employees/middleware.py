from django.shortcuts import redirect

# What an intern/employee login may reach. Everything else is the business
# side (invoices, clients, dashboards...), most of which only checks
# @login_required, so without this an intern could open it by URL.
OPEN_PREFIXES = (
    '/staff/', '/crm/', '/api/', '/static/', '/media/', '/login/', '/logout/',
    '/agreement/', '/enrol/', '/academy/', '/portal/', '/v/', '/social/report-link/',
    '/oauth/', '/.well-known/', '/mcp', '/favicon', '/robots.txt',
)


class StaffConfinementMiddleware:
    """Keep intern/employee logins inside the staff portal and intern CRM.

    Owners, partners, team members and Django staff are not affected (see
    core.views._staff_portal_user), and the lookup is skipped for open paths.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if (user is not None and user.is_authenticated
                and not request.path.startswith(OPEN_PREFIXES)):
            from core.views import _staff_portal_user
            if _staff_portal_user(user):
                return redirect('staff:dashboard')
        return self.get_response(request)
