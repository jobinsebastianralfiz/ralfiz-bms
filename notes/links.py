"""Linking a note to one BMS record: a project, a client or a CRM lead.

A user may only link records they can open in the BMS: projects and clients are business-side
pages (interns and employees are kept out of them by employees.middleware), and leads follow
the CRM's own rule (admins see all, interns only the leads assigned to them)."""
from django.core.exceptions import ValidationError
from django.urls import reverse

LINK_KINDS = ("project", "client", "lead")


def _business_user(user):
    from client_portal.middleware import client_only
    from core.views import _staff_portal_user

    return not _staff_portal_user(user) and not client_only(user)


def linkable(kind, user):
    """The records of `kind` this user may link a note to."""
    if kind == "project":
        from core.models import Project

        return Project.objects.all() if _business_user(user) else Project.objects.none()
    if kind == "client":
        from core.models import Client

        return Client.objects.all() if _business_user(user) else Client.objects.none()
    if kind == "lead":
        from crm.models import Lead
        from crm.views import can_access_crm, is_intern

        if not can_access_crm(user):
            return Lead.objects.none()
        return Lead.objects.filter(assigned_to=user) if is_intern(user) else Lead.objects.all()
    raise ValueError(kind)


def find_record(kind, pk, user):
    """The record a note should link to, or None if it doesn't exist or isn't the user's to link."""
    try:
        return linkable(kind, user).filter(pk=pk).first()
    except (ValueError, TypeError, ValidationError):  # unknown kind, or a malformed id
        return None


def set_link(note, kind, record):
    """Link `note` to `record` (or unlink it when `kind` is None), clearing any other link."""
    for field in LINK_KINDS:
        setattr(note, field, record if field == kind else None)


def link_payload(note):
    """What the editor shows as the linked-record chip, or None."""
    if note.project_id:
        record, kind, url = note.project, "project", reverse("project_detail", args=[note.project_id])
        label = record.name
    elif note.client_id:
        record, kind, url = note.client, "client", reverse("client_detail", args=[note.client_id])
        label = record.company_name or record.name
    elif note.lead_id:
        record, kind, url = note.lead, "lead", reverse("crm:lead_detail", args=[note.lead_id])
        label = record.company_name or record.contact_person
    else:
        return None
    return {"kind": kind, "id": str(record.pk), "label": label, "url": url}
