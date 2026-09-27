from django.shortcuts import redirect

from .access import student_only

# What a student-only login may reach outside /academy/.
OPEN_PREFIXES = ('/academy/', '/static/', '/media/', '/logout/', '/favicon')


class StudentConfinementMiddleware:
    """Keep student-only logins inside the Academy portal.

    Most BMS pages only check @login_required, so without this a student
    could open the business dashboard. Users with any other role are not
    affected, and the lookup is skipped for Academy and static requests.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if (user is not None and user.is_authenticated
                and not request.path.startswith(OPEN_PREFIXES)
                and student_only(user)):
            if request.path.startswith('/api/'):
                from django.http import JsonResponse
                return JsonResponse({'detail': 'Not available to Academy students.'}, status=403)
            return redirect('academy:home')
        return self.get_response(request)
