"""HR screens for agreement e-signing: select people, generate links, track responses."""
import uuid
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from employees.models import AgreementRequest, AgreementTemplate, Employee


@login_required
def agreement_list(request):
    """Dashboard of every agreement sent, with status counters."""
    qs = AgreementRequest.objects.select_related('employee__user', 'template')

    status_filter = request.GET.get('status', '')
    search = request.GET.get('q', '').strip()

    now = timezone.now()
    if status_filter == 'expired':
        qs = qs.filter(status__in=AgreementRequest.OPEN_STATUSES, expires_at__lt=now)
    elif status_filter == 'open':
        qs = qs.filter(status__in=AgreementRequest.OPEN_STATUSES, expires_at__gte=now)
    elif status_filter:
        qs = qs.filter(status=status_filter)

    if search:
        qs = qs.filter(
            Q(employee__user__first_name__icontains=search)
            | Q(employee__user__last_name__icontains=search)
            | Q(employee__employee_id__icontains=search)
            | Q(reference__icontains=search)
        )

    all_requests = AgreementRequest.objects.all()
    open_qs = all_requests.filter(status__in=AgreementRequest.OPEN_STATUSES)
    counters = {
        'awaiting': open_qs.filter(expires_at__gte=now).count(),
        'accepted': all_requests.filter(status=AgreementRequest.STATUS_ACCEPTED).count(),
        'declined': all_requests.filter(status=AgreementRequest.STATUS_DECLINED).count(),
        'expired': open_qs.filter(expires_at__lt=now).count(),
    }

    return render(request, 'hr/agreement_list.html', {
        'agreements': qs[:300],
        'counters': counters,
        'status_filter': status_filter,
        'search': search,
        'statuses': AgreementRequest.STATUS_CHOICES,
        'has_template': AgreementTemplate.objects.filter(is_active=True).exists(),
    })


@login_required
def agreement_send(request):
    """Pick people, generate one signing link each."""
    templates = AgreementTemplate.objects.filter(is_active=True)

    if request.method == 'POST':
        employee_ids = request.POST.getlist('employees')
        template_id = request.POST.get('template')
        try:
            expiry_days = int(request.POST.get('expiry_days', 14))
        except (TypeError, ValueError):
            expiry_days = 14
        expiry_days = max(1, min(expiry_days, 180))

        if not employee_ids:
            messages.error(request, 'Select at least one person to send the agreement to.')
            return redirect('agreement_send')

        template = get_object_or_404(AgreementTemplate, pk=template_id)
        employees = Employee.objects.select_related('user').filter(id__in=employee_ids)

        batch = uuid.uuid4()
        snapshot = template.build_snapshot()
        expires_at = timezone.now() + timedelta(days=expiry_days)

        created = 0
        for employee in employees:
            # An older open link for the same person would let them answer twice.
            AgreementRequest.objects.filter(
                employee=employee, status__in=AgreementRequest.OPEN_STATUSES,
            ).update(status=AgreementRequest.STATUS_SUPERSEDED)

            AgreementRequest.objects.create(
                employee=employee,
                template=template,
                snapshot_json=snapshot,
                snapshot_version=template.version,
                snapshot_fee=template.monthly_fee,
                sent_by=request.user,
                expires_at=expires_at,
                batch=batch,
            )
            created += 1

        messages.success(request, f'Generated {created} agreement link{"s" if created != 1 else ""}.')
        return redirect('agreement_batch', batch=batch)

    employees = Employee.objects.select_related('user').filter(status='active')

    type_filter = request.GET.get('type', 'intern')
    if type_filter == 'intern':
        employees = employees.filter(Q(employment_type='intern') | Q(role='intern'))
    elif type_filter == 'staff':
        employees = employees.exclude(Q(employment_type='intern') | Q(role='intern'))

    # Show what each person's latest agreement did, so HR doesn't re-send blindly.
    latest = {}
    for req in AgreementRequest.objects.filter(
        employee__in=employees
    ).select_related('employee').order_by('employee_id', '-sent_at'):
        latest.setdefault(req.employee_id, req)

    rows = [{'employee': e, 'latest': latest.get(e.id)} for e in employees]

    return render(request, 'hr/agreement_send.html', {
        'rows': rows,
        'templates': templates,
        'type_filter': type_filter,
    })


@login_required
def agreement_batch(request, batch):
    """Result page: copy / WhatsApp each generated link."""
    agreements = AgreementRequest.objects.select_related('employee__user').filter(batch=batch)
    if not agreements:
        messages.error(request, 'That batch of links no longer exists.')
        return redirect('agreement_list')

    rows = [{
        'agreement': a,
        'url': a.public_url(request),
        'whatsapp': a.whatsapp_url(request),
    } for a in agreements]

    return render(request, 'hr/agreement_batch.html', {
        'rows': rows,
        'batch': batch,
        'no_phone_count': sum(1 for r in rows if not r['whatsapp']),
    })


@login_required
def agreement_detail(request, pk):
    agreement = get_object_or_404(
        AgreementRequest.objects.select_related('employee__user', 'template', 'sent_by'), pk=pk
    )
    return render(request, 'hr/agreement_detail.html', {
        'agreement': agreement,
        'doc': agreement.snapshot_json or {},
        'url': agreement.public_url(request),
        'whatsapp': agreement.whatsapp_url(request),
        'history': AgreementRequest.objects.filter(
            employee=agreement.employee
        ).exclude(pk=agreement.pk).order_by('-sent_at')[:10],
    })


@login_required
def agreement_cancel(request, pk):
    agreement = get_object_or_404(AgreementRequest, pk=pk)
    if request.method != 'POST':
        return redirect('agreement_detail', pk=pk)

    if agreement.has_responded:
        messages.error(request, 'This agreement has already been answered and cannot be cancelled.')
    else:
        agreement.status = AgreementRequest.STATUS_CANCELLED
        agreement.save(update_fields=['status', 'updated_at'])
        messages.success(request, 'Agreement link cancelled. It no longer opens.')
    return redirect('agreement_detail', pk=pk)


@login_required
def agreement_resend(request, pk):
    """Issue a fresh link. The old record is kept intact for the audit trail."""
    old = get_object_or_404(AgreementRequest.objects.select_related('employee'), pk=pk)
    if request.method != 'POST':
        return redirect('agreement_detail', pk=pk)

    template = old.template or AgreementTemplate.objects.filter(is_active=True).first()
    if template is None:
        messages.error(request, 'No active agreement template to send.')
        return redirect('agreement_detail', pk=pk)

    new = AgreementRequest.objects.create(
        employee=old.employee,
        template=template,
        snapshot_json=template.build_snapshot(),
        snapshot_version=template.version,
        snapshot_fee=template.monthly_fee,
        sent_by=request.user,
        batch=uuid.uuid4(),
    )

    if not old.has_responded:
        old.status = AgreementRequest.STATUS_SUPERSEDED
        old.superseded_by = new
        old.save(update_fields=['status', 'superseded_by', 'updated_at'])

    messages.success(request, f'New link generated for {old.employee.full_name}.')
    return redirect('agreement_batch', batch=new.batch)


@login_required
def agreement_pdf(request, pk):
    """HR download of a signed copy. Falls back to the printable page when
    WeasyPrint's native libraries aren't available."""
    from employees.agreement_views import (
        _pdf_filename, render_agreement_pdf,
    )

    agreement = get_object_or_404(
        AgreementRequest.objects.select_related('employee__user'), pk=pk
    )
    if not agreement.has_responded:
        messages.error(request, 'That agreement has not been signed yet.')
        return redirect('agreement_detail', pk=pk)

    pdf = render_agreement_pdf(agreement, base_url=request.build_absolute_uri('/'))
    if pdf is None:
        return redirect('agreement_copy', token=agreement.token)

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{_pdf_filename(agreement)}"'
    return response
