"""Client project agreements: staff screens to prepare and send, and the public
token link the client opens to accept or ask for changes."""
import logging
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from employees.agreement_views import (
    _agreement_css, _client_ip, _decode_signature, _file_data_uri, company_countersignature,
)

from .client_agreement_models import (
    ClientAgreement, build_snapshot, default_milestone_text, milestones_total_percent,
    parse_milestones,
)
from .models import Project

logger = logging.getLogger(__name__)


def _lines(text):
    return [line.strip(' -•\t') for line in (text or '').splitlines() if line.strip(' -•\t')]


def _parse_date(raw):
    try:
        return date.fromisoformat(raw) if raw else None
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Staff
# ---------------------------------------------------------------------------

@login_required
def client_agreement_new(request, pk):
    """Prepare the agreement from the project's own data, then send."""
    project = get_object_or_404(Project.objects.select_related('client'), pk=pk)
    previous = project.client_agreements.exclude(
        status__in=[ClientAgreement.STATUS_CANCELLED, ClientAgreement.STATUS_SUPERSEDED]).first()

    initial = {
        'scope': project.description,
        'deliverables': project.deliverables,
        'start_date': project.start_date.isoformat() if project.start_date else '',
        'end_date': project.deadline.isoformat() if project.deadline else '',
        'total': project.final_amount or project.estimated_budget or '',
        'milestones': default_milestone_text(),
        'warranty_months': project.warranty_period if project.warranty_period is not None else 3,
        'support_note': '',
        'extra_terms': '',
        'expiry_days': 14,
    }
    if previous:  # a revision starts from what was last sent, not from scratch
        snap = previous.snapshot_json
        initial.update(previous.snapshot_json.get('_form', {}))
        initial['milestones'] = '\n'.join(
            f"{m['label']} | {m['percent']}" for m in snap.get('milestones', [])) or initial['milestones']

    errors = {}
    if request.method == 'POST':
        form = request.POST
        try:
            total = Decimal(form.get('total') or '0')
        except InvalidOperation:
            total = Decimal('0')
            errors['total'] = 'Enter the project fee as a number.'
        if total <= 0 and 'total' not in errors:
            errors['total'] = 'Enter the project fee.'
        milestones = parse_milestones(form.get('milestones'), total)
        if not milestones:
            errors['milestones'] = 'Add at least one payment milestone.'
        elif milestones_total_percent(milestones) != 100:
            errors['milestones'] = (f'Milestones add up to {milestones_total_percent(milestones):f}%, '
                                    'they must add up to 100%.')
        if not (form.get('scope') or '').strip():
            errors['scope'] = 'Describe the scope of work.'
        try:
            warranty = max(int(form.get('warranty_months') or 0), 0)
        except ValueError:
            warranty = 0
        try:
            expiry_days = min(max(int(form.get('expiry_days') or 14), 1), 90)
        except ValueError:
            expiry_days = 14

        if not errors:
            snapshot = build_snapshot(
                project,
                scope=form.get('scope', '').strip(),
                deliverables=_lines(form.get('deliverables')),
                start_date=_parse_date(form.get('start_date')),
                end_date=_parse_date(form.get('end_date')),
                total=total,
                milestones=milestones,
                warranty_months=warranty,
                support_note=form.get('support_note', '').strip(),
                extra_terms=_lines(form.get('extra_terms')),
            )
            # Kept so a revision can prefill the form; not shown to the client.
            snapshot['_form'] = {k: form.get(k, '') for k in (
                'scope', 'deliverables', 'start_date', 'end_date', 'total',
                'warranty_months', 'support_note', 'extra_terms', 'expiry_days')}
            revision = (previous.revision + 1) if previous else 1
            snapshot['version'] = f'v{revision}.0'
            agreement = ClientAgreement.objects.create(
                project=project, snapshot_json=snapshot, total_amount=total,
                revision=revision, sent_by=request.user,
                expires_at=timezone.now() + timedelta(days=expiry_days),
            )
            if previous and previous.status != ClientAgreement.STATUS_ACCEPTED:
                previous.status = ClientAgreement.STATUS_SUPERSEDED
                previous.superseded_by = agreement
                previous.save(update_fields=['status', 'superseded_by', 'updated_at'])
            messages.success(request, f'Agreement {agreement.reference} is ready. Send the link to the client.')
            return redirect('client_agreement_detail', pk=agreement.pk)
        initial.update(request.POST.dict())

    return render(request, 'client_agreements/form.html', {
        'project': project, 'form': initial, 'errors': errors, 'previous': previous,
    })


@login_required
def client_agreement_detail(request, pk):
    agreement = get_object_or_404(ClientAgreement.objects.select_related('project__client'), pk=pk)
    return render(request, 'client_agreements/detail.html', {
        'agreement': agreement,
        'doc': agreement.snapshot_json,
        'project': agreement.project,
        'url': agreement.public_url(request),
        'whatsapp_url': agreement.whatsapp_url(request),
        'mailto_url': agreement.mailto_url(request),
        'history': agreement.project.client_agreements.exclude(pk=agreement.pk),
    })


@login_required
@require_POST
def client_agreement_cancel(request, pk):
    agreement = get_object_or_404(ClientAgreement, pk=pk)
    if agreement.has_responded:
        messages.error(request, 'That agreement has already been answered.')
    else:
        agreement.status = ClientAgreement.STATUS_CANCELLED
        agreement.save(update_fields=['status', 'updated_at'])
        messages.success(request, 'Link cancelled. The client can no longer open it.')
    return redirect('client_agreement_detail', pk=pk)


@login_required
def client_agreement_staff_pdf(request, pk):
    agreement = get_object_or_404(ClientAgreement.objects.select_related('project__client'), pk=pk)
    return _pdf_or_copy(request, agreement)


# ---------------------------------------------------------------------------
# Public - no login, reached only by the secret token
# ---------------------------------------------------------------------------

def _get_or_404(token):
    return get_object_or_404(ClientAgreement.objects.select_related('project__client'), token=token)


def _sign_context(agreement, errors=None, posted=None):
    doc = agreement.snapshot_json or {}
    return {
        'agreement': agreement, 'doc': doc, 'client': agreement.project.client,
        'sections': doc.get('sections', []), 'today': timezone.localdate(),
        'errors': errors or {}, 'posted': posted or {},
    }


@require_http_methods(['GET', 'POST'])
def client_agreement_sign(request, token):
    agreement = _get_or_404(token)
    if agreement.status in (ClientAgreement.STATUS_CANCELLED, ClientAgreement.STATUS_SUPERSEDED):
        return render(request, 'client_agreements/closed.html', _sign_context(agreement))
    if agreement.has_responded:
        return redirect('client_agreement_done', token=token)
    if agreement.is_expired:
        return render(request, 'client_agreements/closed.html',
                      {**_sign_context(agreement), 'expired': True})

    if request.method == 'GET':
        agreement.mark_viewed()
        return render(request, 'client_agreements/sign.html', _sign_context(agreement))

    posted = request.POST.dict()
    decision = posted.get('decision')
    errors = {}
    if decision == 'accept':
        for field, msg in (('signer_name', 'Please enter your full name.'),
                           ('signed_name', 'Please type your name to sign.')):
            if not posted.get(field, '').strip():
                errors[field] = msg
        if posted.get('agreed_to_terms') != 'on':
            errors['agreed_to_terms'] = 'Please confirm that you accept the terms.'
    elif decision == 'changes':
        if not posted.get('change_notes', '').strip():
            errors['change_notes'] = 'Please tell us what you would like changed.'
        if not posted.get('signer_name', '').strip():
            errors['signer_name'] = 'Please enter your name.'
    else:
        errors['decision'] = 'Please choose to accept or request changes.'
    if errors:
        return render(request, 'client_agreements/sign.html',
                      _sign_context(agreement, errors, posted), status=400)

    agreement.signer_name = posted.get('signer_name', '').strip()
    agreement.signer_designation = posted.get('signer_designation', '').strip()
    agreement.signer_company = posted.get('signer_company', '').strip()
    agreement.signer_email = posted.get('signer_email', '').strip()[:254]
    if decision == 'accept':
        agreement.status = ClientAgreement.STATUS_ACCEPTED
        agreement.signed_name = posted['signed_name'].strip()
        agreement.agreed_to_terms = True
        signature = _decode_signature(posted.get('signature_data', ''))
        if signature:
            agreement.signature_image.save(f'sig-{agreement.id}.png', ContentFile(signature), save=False)
    else:
        agreement.status = ClientAgreement.STATUS_CHANGES
        agreement.change_notes = posted['change_notes'].strip()
    agreement.responded_at = timezone.now()
    agreement.ip_address = _client_ip(request)
    agreement.user_agent = request.META.get('HTTP_USER_AGENT', '')[:1000]
    agreement.body_hash = agreement.compute_body_hash()
    agreement.save()
    return redirect('client_agreement_done', token=token)


def client_agreement_done(request, token):
    agreement = _get_or_404(token)
    if not agreement.has_responded:
        return redirect('client_agreement_sign', token=token)
    return render(request, 'client_agreements/done.html', _sign_context(agreement))


def _copy_context(agreement, for_pdf=False):
    ctx = _sign_context(agreement)
    sig = ''
    if agreement.signature_image:
        sig = _file_data_uri(agreement.signature_image) if for_pdf else agreement.signature_image.url
    ctx.update({
        'for_pdf': for_pdf, 'signature_src': sig,
        'company': company_countersignature(for_pdf=for_pdf),
        'inline_css': _agreement_css() if for_pdf else '',
        'pdf_url': f'{agreement.public_path()}copy.pdf',
    })
    return ctx


def client_agreement_copy(request, token):
    agreement = _get_or_404(token)
    if agreement.status != ClientAgreement.STATUS_ACCEPTED:
        return redirect('client_agreement_sign', token=token)
    return render(request, 'client_agreements/copy.html', _copy_context(agreement))


def client_agreement_copy_pdf(request, token):
    agreement = _get_or_404(token)
    if agreement.status != ClientAgreement.STATUS_ACCEPTED:
        return redirect('client_agreement_sign', token=token)
    return _pdf_or_copy(request, agreement)


def _pdf_or_copy(request, agreement):
    """Signed PDF, or the printable page when WeasyPrint's native libs are missing.
    Before signing, staff get the same document as a preview of what was sent."""
    try:
        from weasyprint import HTML
        html = render_to_string('client_agreements/copy.html', _copy_context(agreement, for_pdf=True))
        pdf = HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf()
    except Exception as exc:
        logger.warning('Client agreement PDF unavailable: %s', exc)
        return render(request, 'client_agreements/copy.html', _copy_context(agreement))
    response = HttpResponse(pdf, content_type='application/pdf')
    filename = f"Ralfiz-Agreement-{agreement.reference.replace('/', '-')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
