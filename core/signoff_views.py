"""Project sign-offs: the staff page that tracks one, and the public token link
the client opens to tick, sign and approve. Sign-offs are created through the
BMS connector (connector/tools.py: create_signoff)."""
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from employees.agreement_views import (
    _client_ip, _decode_signature, _file_data_uri, company_countersignature,
)

from .models import CompanySettings
from .signoff_models import ProjectSignoff

logger = logging.getLogger(__name__)


def _context(signoff, errors=None, posted=None):
    doc = signoff.snapshot_json or {}
    posted = posted or {}
    if signoff.has_responded:
        ticked = signoff.checked_items or []
    else:
        ticked = posted.get('_checks', [])
    return {
        'signoff': signoff, 'doc': doc, 'project': signoff.project,
        'client': signoff.project.client, 'sections': doc.get('sections', []),
        'ticked': ticked, 'check_total': len(doc.get('check_ids', [])),
        'today': timezone.localdate(), 'errors': errors or {}, 'posted': posted,
    }


def _notify_owners(signoff):
    """Tell the owners the client answered. Never blocks the client's response."""
    try:
        from employees.models import Employee, Notification
        from employees.utils import send_push_notification

        approved = signoff.status == ProjectSignoff.STATUS_APPROVED
        title = 'Sign-off approved' if approved else 'Sign-off: problem reported'
        body = (f'{signoff.signer_name} approved "{signoff.title}".' if approved else
                f'{signoff.signer_name} reported a problem on "{signoff.title}": '
                f'{signoff.issue_notes[:200]}')
        for owner in Employee.objects.filter(status='active', role__in=('owner', 'partner')):
            Notification.objects.create(
                employee=owner, title=title, body=body, notification_type='general',
                data={'kind': 'signoff', 'signoff_id': str(signoff.pk)})
            send_push_notification(owner, title, body)
    except Exception:  # noqa: BLE001 - a failed alert must not lose the signature
        logger.exception('Could not notify owners about sign-off %s', signoff.reference)


# ---------------------------------------------------------------------------
# Staff
# ---------------------------------------------------------------------------

@login_required
def signoff_detail(request, pk):
    signoff = get_object_or_404(ProjectSignoff.objects.select_related('project__client'), pk=pk)
    return render(request, 'signoffs/detail.html', {
        **_context(signoff),
        'url': signoff.public_url(request),
        'whatsapp_url': signoff.whatsapp_url(request),
        'mailto_url': signoff.mailto_url(request),
        'unticked': signoff.unticked_items if signoff.has_responded else [],
        'history': signoff.project.signoffs.exclude(pk=signoff.pk),
    })


@login_required
@require_POST
def signoff_cancel(request, pk):
    signoff = get_object_or_404(ProjectSignoff, pk=pk)
    if signoff.has_responded:
        messages.error(request, 'That sign-off has already been answered.')
    else:
        signoff.status = ProjectSignoff.STATUS_CANCELLED
        signoff.save(update_fields=['status', 'updated_at'])
        messages.success(request, 'Link cancelled. The client can no longer open it.')
    return redirect('signoff_detail', pk=pk)


@login_required
def signoff_staff_pdf(request, pk):
    signoff = get_object_or_404(ProjectSignoff.objects.select_related('project__client'), pk=pk)
    return _pdf_response(request, signoff)


# ---------------------------------------------------------------------------
# Public - no login, reached only by the secret token
# ---------------------------------------------------------------------------

def _get_or_404(token):
    return get_object_or_404(ProjectSignoff.objects.select_related('project__client'), token=token)


@require_http_methods(['GET', 'POST'])
def signoff_sign(request, token):
    signoff = _get_or_404(token)
    if signoff.status in (ProjectSignoff.STATUS_CANCELLED, ProjectSignoff.STATUS_SUPERSEDED):
        return render(request, 'signoffs/closed.html', _context(signoff))
    if signoff.has_responded:
        return redirect('signoff_done', token=token)
    if signoff.is_expired:
        return render(request, 'signoffs/closed.html', {**_context(signoff), 'expired': True})

    if request.method == 'GET':
        # Our own staff previewing the link is not the client opening it.
        if not (request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)):
            signoff.mark_viewed()
        return render(request, 'signoffs/sign.html', _context(signoff))

    posted = request.POST.dict()
    valid_ids = signoff.check_ids
    posted['_checks'] = [c for c in request.POST.getlist('check') if c in valid_ids]
    decision = posted.get('decision')
    errors = {}
    if not posted.get('signer_name', '').strip():
        errors['signer_name'] = 'Please enter your full name.'
    if decision == 'approve':
        missing = len(valid_ids) - len(set(posted['_checks']))
        if missing:
            errors['checks'] = (f'{missing} item{"s are" if missing != 1 else " is"} not ticked. Tick every '
                                'item you have checked, or choose "Report a problem" if something is '
                                'missing or not working.')
        if not posted.get('signed_name', '').strip():
            errors['signed_name'] = 'Please type your name to sign.'
        if posted.get('agreed') != 'on':
            errors['agreed'] = 'Please confirm that you accept the handover.'
    elif decision == 'issues':
        if not posted.get('issue_notes', '').strip():
            errors['issue_notes'] = 'Please tell us what is missing or not working.'
    else:
        errors['decision'] = 'Please choose to approve or report a problem.'
    if errors:
        return render(request, 'signoffs/sign.html', _context(signoff, errors, posted), status=400)

    signoff.signer_name = posted['signer_name'].strip()[:200]
    signoff.signer_role = posted.get('signer_role', '').strip()[:200]
    signoff.signer_email = posted.get('signer_email', '').strip()[:254]
    signoff.checked_items = [c for c in valid_ids if c in posted['_checks']]
    if decision == 'approve':
        signoff.status = ProjectSignoff.STATUS_APPROVED
        signoff.signed_name = posted['signed_name'].strip()[:200]
        signature = _decode_signature(posted.get('signature_data', ''))
        if signature:
            signoff.signature_image.save(f'sig-{signoff.id}.png', ContentFile(signature), save=False)
    else:
        signoff.status = ProjectSignoff.STATUS_ISSUES
        signoff.issue_notes = posted['issue_notes'].strip()
    signoff.responded_at = timezone.now()
    signoff.ip_address = _client_ip(request)
    signoff.user_agent = request.META.get('HTTP_USER_AGENT', '')[:1000]
    signoff.body_hash = signoff.compute_body_hash()
    signoff.save()
    _notify_owners(signoff)
    return redirect('signoff_done', token=token)


def signoff_done(request, token):
    signoff = _get_or_404(token)
    if not signoff.has_responded:
        return redirect('signoff_sign', token=token)
    return render(request, 'signoffs/done.html', _context(signoff))


def signoff_copy_pdf(request, token):
    signoff = _get_or_404(token)
    if signoff.status != ProjectSignoff.STATUS_APPROVED:
        return redirect('signoff_sign', token=token)
    return _pdf_response(request, signoff)


def pdf_context(signoff, for_pdf=True):
    ctx = _context(signoff)
    project = signoff.project
    sig = ''
    if signoff.signature_image:
        sig = _file_data_uri(signoff.signature_image) if for_pdf else signoff.signature_image.url
    client_logo = ''
    if project.logo:
        client_logo = _file_data_uri(project.logo) if for_pdf else project.logo.url
    ctx.update({
        'for_pdf': for_pdf, 'signature_src': sig, 'client_logo': client_logo,
        'company': company_countersignature(for_pdf=for_pdf),
        'letterhead': CompanySettings.get_settings(),
        'font_dir': (settings.BASE_DIR / 'static' / 'certificates' / 'fonts').as_uri(),
        'approved': signoff.status == ProjectSignoff.STATUS_APPROVED,
    })
    return ctx


def render_pdf(signoff, base_url):
    from weasyprint import HTML
    html = render_to_string('signoffs/pdf.html', pdf_context(signoff))
    return HTML(string=html, base_url=base_url).write_pdf()


def _pdf_response(request, signoff):
    """The signed PDF, or the same document as a printable page when
    WeasyPrint's native libraries are missing. Before approval, staff get it
    as a preview of what was sent."""
    try:
        pdf = render_pdf(signoff, request.build_absolute_uri('/'))
    except Exception as exc:  # noqa: BLE001
        logger.warning('Sign-off PDF unavailable: %s', exc)
        return render(request, 'signoffs/pdf.html', pdf_context(signoff, for_pdf=False))
    response = HttpResponse(pdf, content_type='application/pdf')
    filename = f"Ralfiz-Sign-off-{signoff.reference.replace('/', '-')}.pdf"
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response
