"""UAT in the staff portal (/staff/uat/): testers see their sections and mark each case Pass / Fail / Blocked."""
from django.contrib import messages
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from employees.portal_views import _base_context, staff_required

from . import services
from .models import UATCase, UATFile, UATPlan, UATResult

MAX_SCREENSHOT = 8 * 1024 * 1024


def _my_plans(employee, open_only=False):
    """The tester's plans. Completed ones stay listed (as a thank-you card) but can't be marked any more."""
    plans = UATPlan.objects.filter(testers=employee).distinct()
    return plans.filter(status='active') if open_only else plans


def _summary(plan, employee):
    """One plan as this tester sees it: their sections, progress, what to do next."""
    sections = services.tester_sections(plan, employee)
    mine = {r.case_id: r for r in UATResult.objects.filter(tester=employee, case__section__plan=plan)}
    rows = []
    for s in sections:
        ids = list(s.cases.values_list('id', flat=True))
        done = [mine[i] for i in ids if i in mine]
        rows.append({'section': s, **services.progress(len(ids), len(done)), **services.counts(done),
                     'retest': sum(1 for r in done if r.needs_retest), 'waiting_on': s.waiting_on()})
    total = sum(r['total'] for r in rows)
    done = sum(r['done'] for r in rows)
    open_rows = [r for r in rows if not r['waiting_on']]
    locked = [r for r in rows if r['waiting_on']]
    todo = [r for r in open_rows if r['retest'] or r['done'] < r['total']]
    waiting = locked[0]['waiting_on'] if locked else None
    if plan.is_completed:  # nothing left to do: the card and the page say thanks instead
        todo, waiting = [], None
    if todo:
        todo[0]['is_next'] = True
    return {'plan': plan, 'open': open_rows, 'locked': locked, **services.progress(total, done),
            'retest': sum(r['retest'] for r in rows), 'next': todo[0] if todo else None,
            'waiting': waiting,
            'waiting_done': waiting.marked_count() if waiting else 0,
            'waiting_total': waiting.cases.count() if waiting else 0,
            'waiting_who': ', '.join(e.full_name.split()[0] for e in waiting.testers()) if waiting else '',
            'guide': services.instruction_blocks(plan.instructions),
            'todo': total - done, 'section_count': len(rows), 'completed': plan.is_completed,
            'found': sum(r['fail'] + r['blocked'] for r in rows), 'first_name': employee.full_name.split()[0] if employee.full_name else '',
            **_due(plan, total - done),
            **{k: sum(r[k] for r in rows) for k in ('pass', 'fail', 'blocked')}}


def _due(plan, todo):
    if not plan.due_date or not todo:
        return {'due_text': '', 'late': False}
    days = (plan.due_date - timezone.localdate()).days
    if days < 0:
        return {'due_text': f'{-days} day{"s" if days < -1 else ""} late', 'late': True}
    return {'due_text': {0: 'today', 1: 'tomorrow'}.get(days, f'{days} days left'), 'late': False}


@staff_required
def uat_home(request):
    """UAT plans now sit with the rest of your work under My Tasks; keep old links working."""
    return redirect('staff:work_list')


@staff_required
def uat_plan(request, plan_pk):
    plan = get_object_or_404(_my_plans(request.employee), pk=plan_pk)
    ctx = _base_context(request, 'work')
    ctx['p'] = _summary(plan, request.employee)
    ctx['files'] = plan.files.select_related('uploaded_by')
    ctx['file_max_mb'] = UATFile.MAX_MB
    return render(request, 'staff/uat/plan.html', ctx)


@staff_required
def uat_file_upload(request, plan_pk):
    """A tester sends files back on the plan (a zip of logs, recordings, exported data)."""
    plan = get_object_or_404(_my_plans(request.employee), pk=plan_pk)
    back = f"{reverse('staff:uat_plan', args=[plan.pk])}#files"
    if request.method != 'POST':
        return redirect(back)
    if plan.is_completed:
        messages.error(request, 'This UAT is completed, so files can no longer be added.')
        return redirect(back)
    n, error = services.add_files(plan, request.FILES.getlist('files'), request.user,
                                  request.POST.get('note', ''), from_tester=True)
    if error:
        messages.error(request, error)
    else:
        messages.success(request, f'{n} file{"s" if n != 1 else ""} uploaded.')
    return redirect(back)


@staff_required
def uat_file_download(request, plan_pk, file_id):
    plan = get_object_or_404(_my_plans(request.employee), pk=plan_pk)
    return services.file_response(get_object_or_404(UATFile, pk=file_id, plan=plan))


@staff_required
def uat_file_delete(request, plan_pk, file_id):
    """Testers can remove only what they uploaded themselves."""
    plan = get_object_or_404(_my_plans(request.employee), pk=plan_pk)
    f = get_object_or_404(UATFile, pk=file_id, plan=plan, uploaded_by=request.user, from_tester=True)
    if request.method == 'POST':
        services.delete_file(f)
        messages.success(request, f'"{f.name}" deleted.')
    return redirect(f"{reverse('staff:uat_plan', args=[plan.pk])}#files")


@staff_required
def uat_section(request, plan_pk, section_pk):
    employee = request.employee
    plan = get_object_or_404(_my_plans(employee), pk=plan_pk)
    if plan.is_completed:
        return redirect('staff:uat_plan', plan.pk)
    section = get_object_or_404(plan.sections.prefetch_related('assignees'), pk=section_pk)
    if not section.is_for(employee):
        raise Http404

    waiting_on = section.waiting_on()
    if request.method == 'POST':
        if waiting_on:
            error = f'Wait until "{waiting_on.name}" is finished.'
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'ok': False, 'error': error}, status=400)
            messages.error(request, error)
            return redirect('staff:uat_section', plan.pk, section.pk)
        return _save(request, employee, section)

    mine = {r.case_id: r for r in UATResult.objects.filter(tester=employee, case__section=section)}
    cases = [{'case': c, 'result': mine.get(c.id)} for c in section.cases.all()]
    tally = services.counts(mine.values())
    sections = services.tester_sections(plan, employee)
    idx = [s.pk for s in sections].index(section.pk)
    ctx = _base_context(request, 'work')
    ctx.update({'plan': plan, 'section': section, 'cases': cases,
                'done': len(mine), 'total': len(cases), 'waiting_on': waiting_on, 'tally': tally,
                'waiting_done': waiting_on.marked_count() if waiting_on else 0,
                'waiting_total': waiting_on.cases.count() if waiting_on else 0,
                'prev_section': sections[idx - 1] if idx > 0 else None,
                'next_section': sections[idx + 1] if idx + 1 < len(sections) else None})
    return render(request, 'staff/uat/section.html', ctx)


def _save(request, employee, section):
    ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
    case = get_object_or_404(UATCase, pk=request.POST.get('case'), section=section)
    status = request.POST.get('status', '')
    note = request.POST.get('note', '').strip()
    shot = request.FILES.get('screenshot')
    error = None
    if status not in dict(UATResult.STATUS_CHOICES):
        error = 'Choose Pass, Fail or Blocked.'
    elif status in ('fail', 'blocked') and not note:
        error = 'For Fail or Blocked, write what you did and what you saw.'
    elif shot and (shot.size > MAX_SCREENSHOT or not (shot.content_type or '').startswith('image/')):
        error = 'The screenshot must be an image under 8 MB.'
    if error:
        if ajax:
            return JsonResponse({'ok': False, 'error': error}, status=400)
        messages.error(request, f'{case.code}: {error}')
    else:
        result = UATResult.objects.filter(case=case, tester=employee).first() or UATResult(case=case, tester=employee)
        result.record(status, note, shot)
        if ajax:
            return JsonResponse({'ok': True, 'status': result.status, 'label': result.get_status_display(),
                                 'screenshot': result.screenshot.url if result.screenshot else '',
                                 'done': UATResult.objects.filter(tester=employee, case__section=section).count()})
        messages.success(request, f'{case.code} saved as {result.get_status_display()}.')
    url = reverse('staff:uat_section', args=[section.plan_id, section.pk])
    return redirect(f'{url}#case-{case.pk}')
