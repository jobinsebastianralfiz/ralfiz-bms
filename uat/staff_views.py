"""UAT in the staff portal (/staff/uat/): testers see their sections and mark each case Pass / Fail / Blocked."""
from django.contrib import messages
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from employees.portal_views import _base_context, staff_required

from . import services
from .models import UATCase, UATPlan, UATResult

MAX_SCREENSHOT = 8 * 1024 * 1024


def _my_plans(employee):
    return UATPlan.objects.filter(testers=employee, status='active').distinct()


@staff_required
def uat_home(request):
    employee = request.employee
    plans = []
    for plan in _my_plans(employee):
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
        plans.append({'plan': plan, 'open': open_rows, 'locked': locked, **services.progress(total, done),
                      'retest': sum(r['retest'] for r in rows), 'next': todo[0] if todo else None,
                      'waiting': waiting,
                      'waiting_done': waiting.marked_count() if waiting else 0,
                      'waiting_total': waiting.cases.count() if waiting else 0,
                      'waiting_who': ', '.join(e.full_name.split()[0] for e in waiting.testers()) if waiting else '',
                      'guide': services.instruction_blocks(plan.instructions),
                      'todo': total - done, 'section_count': len(rows),
                      **{k: sum(r[k] for r in rows) for k in ('pass', 'fail', 'blocked')}})
    ctx = _base_context(request, 'uat')
    ctx['plans'] = plans
    return render(request, 'staff/uat/home.html', ctx)


@staff_required
def uat_section(request, plan_pk, section_pk):
    employee = request.employee
    plan = get_object_or_404(_my_plans(employee), pk=plan_pk)
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
    ctx = _base_context(request, 'uat')
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
