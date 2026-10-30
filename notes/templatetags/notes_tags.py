from django import template

from notes.links import LINK_KINDS
from notes.models import Note

register = template.Library()

SHOWN = 8


@register.inclusion_tag("notes/_record_notes.html", takes_context=True)
def record_notes(context, record, kind, style="panel"):
    """The "Notes" card on a project, client or lead page: the signed-in user's own notes
    linked to this record, and a button that starts a new linked note.

        {% record_notes project "project" %}          stage-panel look (project, client)
        {% record_notes lead "lead" style="card" %}   Bootstrap card look (CRM lead)
    """
    if kind not in LINK_KINDS:
        raise template.TemplateSyntaxError(f"record_notes: unknown kind {kind!r}")
    request = context["request"]
    notes = (
        Note.objects.filter(owner=request.user, deleted_at__isnull=True, **{kind: record})
        .only("id", "kind", "title", "updated_at")
        .order_by("-updated_at")
    )
    total = notes.count()
    return {
        "request": request,
        "csrf_token": context.get("csrf_token"),
        "record": record,
        "kind": kind,
        "style": style,
        "notes": notes[:SHOWN],
        "total": total,
        "more": total - SHOWN if total > SHOWN else 0,
    }
