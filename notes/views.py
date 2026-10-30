from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from .links import LINK_KINDS, find_record, set_link
from .models import Note


@login_required
@ensure_csrf_cookie
def spa(request, *args, **kwargs):
    """Serve the built Notes app (noetsa_frontend, `npm run build`) for every /notes/ page;
    React Router takes it from there. The API lives under /notes/api/."""
    index = settings.NOTES_FRONTEND_DIST / "index.html"
    if not index.exists():
        return HttpResponse(
            "The Notes app has not been built. Run `npm ci && npm run build` in noetsa_frontend/.",
            status=503,
            content_type="text/plain",
        )
    response = HttpResponse(index.read_text(), content_type="text/html")
    # The shell names hashed bundles, so it must never be cached past a deploy.
    response["Cache-Control"] = "no-cache"
    return response


@login_required
@require_POST
def new_linked_note(request):
    """POST /notes/new/ from a project, client or lead page: `kind` + `id` of the record.
    Creates an empty doc note linked to it and opens it in the Notes app.
    With no `kind` (the dashboard) the note is unlinked, and `note_kind=board` starts a board."""
    kind = request.POST.get("kind")
    if not kind:
        if request.POST.get("note_kind") == Note.KIND_BOARD:
            note = Note.objects.create(owner=request.user, kind=Note.KIND_BOARD)
        else:
            note = Note.objects.create(owner=request.user, kind=Note.KIND_DOC,
                                       content={"type": "doc", "content": [{"type": "paragraph"}]})
        return redirect(f"/notes/n/{note.id}")
    record = find_record(kind, request.POST.get("id"), request.user) if kind in LINK_KINDS else None
    if record is None:
        messages.error(request, "That record can't be linked to a note.")
        return redirect(request.META.get("HTTP_REFERER") or "/notes/")
    note = Note(owner=request.user, kind=Note.KIND_DOC, content={"type": "doc", "content": [{"type": "paragraph"}]})
    set_link(note, kind, record)
    note.save()
    return redirect(f"/notes/n/{note.id}")
