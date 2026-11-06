"""HR screens for resignations: send a person their resignation link, approve
what they signed, and hand over the relieving letter."""
from datetime import date

from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from employees.models import Employee
from employees.resignation_models import ResignationRequest, default_resignation_expiry
from employees.resignation_views import KINDS, letter_context, pdf_response

from .enrolment_web_views import enrolment_admin


@enrolment_admin
def resignation_list(request):
    qs = ResignationRequest.objects.select_related('employee__user')
    status_filter = request.GET.get('status', '')
    search = request.GET.get('q', '').strip()
    if status_filter:
        qs = qs.filter(status=status_filter)
    if search:
        qs = qs.filter(Q(employee__user__first_name__icontains=search)
                       | Q(employee__user__last_name__icontains=search)
                       | Q(employee__employee_id__icontains=search) | Q(reference__icontains=search))
    rows = ResignationRequest.objects.all()
    counters = {
        'to_approve': rows.filter(status=ResignationRequest.STATUS_SUBMITTED).count(),
        'waiting': rows.filter(status__in=ResignationRequest.OPEN_STATUSES).count(),
        'approved': rows.filter(status=ResignationRequest.STATUS_APPROVED).count(),
    }
    return render(request, 'hr/resignation_list.html', {
        'items': qs[:300], 'counters': counters, 'status_filter': status_filter,
        'search': search, 'statuses': ResignationRequest.STATUS_CHOICES,
    })


@enrolment_admin
def resignation_send(request):
    people = (Employee.objects.select_related('user').filter(status='active')
              .exclude(role__in=('owner', 'partner')).order_by('user__first_name'))
    if request.method == 'POST':
        employee = get_object_or_404(people, pk=request.POST.get('employee'))
        existing = employee.resignations.filter(status__in=ResignationRequest.ACTIVE_STATUSES).first()
        if existing:
            messages.info(request, f'{employee.full_name} already has an open resignation.')
            return redirect('resignation_detail', pk=existing.pk)
        res = ResignationRequest.objects.create(employee=employee, created_by=request.user, source='hr')
        messages.success(request, 'Resignation link created. Send it on WhatsApp or copy it below.')
        return redirect('resignation_detail', pk=res.pk)
    return render(request, 'hr/resignation_send.html', {
        'people': people, 'selected': request.GET.get('employee', ''),
    })


@enrolment_admin
def resignation_detail(request, pk):
    res = get_object_or_404(ResignationRequest.objects.select_related('employee__user', 'approved_by'), pk=pk)
    return render(request, 'hr/resignation_detail.html', {
        'res': res, 'employee': res.employee,
        'url': res.public_url(request),
        'whatsapp': res.whatsapp_url(request),
        'approved_whatsapp': res.approved_whatsapp_url(request),
        'thanks_url': request.build_absolute_uri(res.thanks_path()),
    })


@enrolment_admin
def resignation_preview(request, pk, kind):
    res = get_object_or_404(ResignationRequest, pk=pk)
    if kind not in KINDS or not res.submitted_at:
        return redirect('resignation_detail', pk=pk)
    return render(request, 'resignations/letterhead.html',
                  letter_context(res, kind, pdf_url=f'/hr/resignations/{res.pk}/{kind}.pdf'))


@enrolment_admin
def resignation_pdf(request, pk, kind):
    res = get_object_or_404(ResignationRequest, pk=pk)
    if kind not in KINDS or not res.submitted_at:
        return redirect('resignation_detail', pk=pk)
    return (pdf_response(res, kind, request, disposition='inline')
            or redirect('resignation_preview', pk=pk, kind=kind))


@enrolment_admin
@require_POST
def resignation_approve(request, pk):
    res = get_object_or_404(ResignationRequest, pk=pk)
    try:
        relieving = date.fromisoformat(request.POST.get('relieving_date') or '')
    except ValueError:
        messages.error(request, 'Choose the relieving date.')
        return redirect('resignation_detail', pk=pk)
    if relieving < res.employee.joining_date:
        messages.error(request, 'The relieving date is before the joining date.')
        return redirect('resignation_detail', pk=pk)
    try:
        res.approve(request.user, relieving_date=relieving, note=request.POST.get('relieving_note', ''),
                    deactivate=bool(request.POST.get('deactivate')))
    except ValueError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, 'Resignation approved. The relieving letter is ready to download.')
    return redirect('resignation_detail', pk=pk)


@enrolment_admin
@require_POST
def resignation_reject(request, pk):
    res = get_object_or_404(ResignationRequest, pk=pk)
    try:
        res.reject(request.user, request.POST.get('reason', ''))
    except ValueError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, 'Resignation marked as not accepted.')
    return redirect('resignation_detail', pk=pk)


@enrolment_admin
@require_POST
def resignation_cancel(request, pk):
    res = get_object_or_404(ResignationRequest, pk=pk)
    if res.status in ResignationRequest.ACTIVE_STATUSES:
        res.status = ResignationRequest.STATUS_CANCELLED
        res.save(update_fields=['status', 'updated_at'])
        messages.success(request, 'Resignation cancelled. The link no longer opens.')
    return redirect('resignation_detail', pk=pk)


@enrolment_admin
@require_POST
def resignation_extend(request, pk):
    res = get_object_or_404(ResignationRequest, pk=pk)
    if res.status in ResignationRequest.OPEN_STATUSES:
        res.expires_at = default_resignation_expiry()
        res.save(update_fields=['expires_at', 'updated_at'])
        messages.success(request, 'Link extended by 14 days.')
    return redirect('resignation_detail', pk=pk)



@enrolment_admin
@require_POST
def resignation_send_thanks(request, pk):
    """Save the personal note; 'send' also stamps it sent and opens WhatsApp."""
    res = get_object_or_404(ResignationRequest.objects.select_related('employee'), pk=pk)
    if not res.can_download:
        messages.error(request, 'Approve the resignation before sending the thank-you card.')
        return redirect('resignation_detail', pk=pk)
    note = (request.POST.get('thanks_note') or '').strip()
    if len(note) > 700:
        messages.error(request, 'Keep the message under 700 characters so it fits on the card.')
        return redirect('resignation_detail', pk=pk)
    res.thanks_note = '' if note == res.default_thanks_note else note
    fields = ['thanks_note', 'updated_at']
    if request.POST.get('action') == 'send':
        res.thanks_sent_at = timezone.now()
        fields.append('thanks_sent_at')
    res.save(update_fields=fields)
    if request.POST.get('action') == 'send':
        return redirect(res.thanks_whatsapp_url(request) or res.thanks_path())
    messages.success(request, 'Thank-you card saved.')
    return redirect('resignation_detail', pk=pk)
