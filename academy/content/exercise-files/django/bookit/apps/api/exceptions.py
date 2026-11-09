from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    """One error shape for every endpoint, so the Flutter/Next.js client
    can always read response['errors']."""
    response = exception_handler(exc, context)
    if response is not None:
        response.data = {
            "success": False,
            "status_code": response.status_code,
            "errors": response.data,
        }
    return response
