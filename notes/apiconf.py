"""Settings shared by every Notes API view (/notes/api/).

The Notes frontend expects its own conventions, which differ from the rest of the BMS API:
session auth only, limit/offset pages, and errors shaped `{detail, code, fields}`. They are set
per view here, so the global REST_FRAMEWORK settings used by the mobile apps stay untouched."""
from rest_framework.authentication import SessionAuthentication
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import BasePermission
from rest_framework.renderers import JSONRenderer
from rest_framework.views import exception_handler


def notes_exception_handler(exc, context):
    """Every error body carries a machine-readable `code` alongside `detail`; validation
    errors put the per-field messages under `fields` (the frontend's ApiError relies on it)."""
    response = exception_handler(exc, context)
    if response is None:
        return None
    if isinstance(response.data, dict) and "detail" in response.data:
        codes = exc.get_codes() if hasattr(exc, "get_codes") else None
        response.data["code"] = codes if isinstance(codes, str) else getattr(exc, "default_code", "error")
    elif isinstance(response.data, list):
        response.data = {"detail": " ".join(str(m) for m in response.data), "code": "invalid"}
    elif isinstance(response.data, dict):
        general = response.data.pop("non_field_errors", None)
        detail = " ".join(str(m) for m in general) if general else "Please check the highlighted fields."
        response.data = {"detail": detail, "code": "invalid", "fields": response.data}
    return response


class IsNotesUser(BasePermission):
    """Any signed-in BMS user except client portal logins (who are confined to /portal/)."""

    def has_permission(self, request, view):
        from client_portal.middleware import client_only

        user = request.user
        return bool(user and user.is_authenticated and not client_only(user))


class NotesPagination(LimitOffsetPagination):
    default_limit = 50
    max_limit = 200


class NotesAPIMixin:
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsNotesUser]
    renderer_classes = [JSONRenderer]
    pagination_class = NotesPagination
    # Kept out of the mobile API docs at /api/docs/.
    schema = None

    def get_exception_handler(self):
        return notes_exception_handler
