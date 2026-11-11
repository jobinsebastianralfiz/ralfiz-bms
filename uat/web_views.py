"""UAT in the Ralfiz BMS dashboard (Ralfiz staff): plans, who tests what, progress and problems."""
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from employees.models import Employee

from . import services
from .models import UATCase, UATPlan, UATResult, UATSection


def _xp(post):
    raw = (post.get('xp_reward') or '').strip()
    return int(raw) if raw.isdigit() else 0


def _staff_choices():
    return Employee.objects.filter(status='active').select_related('user').order_by('employee_id')


@login_required
def uat_plan_list(request):
    plans = list(UATPlan.objects.prefetch_related('testers__user'))
    stats = services.plan_stats(plans)
    for p in plans:
        p.stats = stats[p.pk]
    return render(request, 'uat/plan_list.html', {'plans': plans})


@login_required
def uat_plan_create(request):
    if request.method == 'POST':
        p = request.POST
        name = p.get('name', '').strip()
        if not name:
            messages.error(request, 'Give the plan a name.')
        else:
            plan = UATPlan.objects.create(name=name, product=p.get('product', '').strip(),
                                          site_url=p.get('site_url', '').strip(),
                                          instructions=p.get('instructions', '').strip(),
                                          due_date=p.get('due_date') or None, created_by=request.user,
                                          xp_reward=_xp(p))
            plan.testers.set(Employee.objects.filter(pk__in=p.getlist('testers')))
            upload = request.FILES.get('cases_json')
            if upload:
                try:
                    load_cases(plan, json.load(upload))
                except (ValueError, KeyError, TypeError) as e:
                    messages.warning(request, f'Plan created, but the test file could not be read: {e}')
            messages.success(request, f'Plan "{plan.name}" created.')
            return redirect('uat_plan_detail', pk=plan.pk)
    return render(request, 'uat/plan_form.html', {'staff': _staff_choices()})


def load_cases(plan, data, owner_map=None):
    """data = {"sections": [{"key", "name", "owner"?, "after"? (key of an earlier section), "tests": [{"code","title","tags","steps","expected"}]}]}.
    owner_map maps a section's owner label (e.g. "Intern 1") to employees; other owners mean everyone."""
    owner_map = owner_map or {}
    by_key = {}
    for i, s in enumerate(data['sections']):
        section = UATSection.objects.create(plan=plan, key=s.get('key', '')[:20], name=s['name'][:200], order=i,
                                            starts_after=by_key.get(s.get('after')))
        by_key[section.key] = section
        if owner_map.get(s.get('owner')):
            section.assignees.set(owner_map[s['owner']])
        UATCase.objects.bulk_create([
            UATCase(section=section, code=str(t.get('code', ''))[:20], title=str(t['title'])[:255],
                    tags=list(t.get('tags') or []), steps=list(t.get('steps') or []),
                    expected=str(t.get('expected', '')), order=j)
            for j, t in enumerate(s.get('tests', []))])


@login_required
def uat_plan_detail(request, pk):
    plan = UATPlan.objects.filter(pk=pk).first()
    if not plan:
        messages.info(request, 'That test plan was replaced. Open it again from this list.')
        return redirect('uat_plan_list')
    tab = request.GET.get('tab', 'open')
    problems = services.open_problems(plan)
    problem_counts = {'open': problems.filter(fix_status='').count(),
                      'fixed': problems.filter(fix_status='fixed').count(),
                      'closed': problems.filter(fix_status__in=['wont_fix', 'not_bug']).count()}
    problems = {'open': problems.filter(fix_status=''), 'fixed': problems.filter(fix_status='fixed'),
                'closed': problems.filter(fix_status__in=['wont_fix', 'not_bug'])}.get(tab, problems.filter(fix_status=''))
    return render(request, 'uat/plan_detail.html', {
        'plan': plan, 'ov': services.plan_overview(plan), 'problems': problems, 'tab': tab,
        'problem_counts': problem_counts, 'staff': _staff_choices(),
        'tester_ids': {str(e.pk) for e in plan.testers.all()},
    })


@login_required
def uat_plan_cases(request, pk):
    """Every case with each tester's result: the full grid."""
    plan = UATPlan.objects.filter(pk=pk).first()
    if not plan:
        messages.info(request, 'That test plan was replaced. Open it again from this list.')
        return redirect('uat_plan_list')
    testers = list(plan.testers.select_related('user'))
    results = {(r.case_id, r.tester_id): r for r in UATResult.objects.filter(case__section__plan=plan)}
    sections = []
    for s in plan.sections.prefetch_related('cases', 'assignees'):
        who = {e.pk for e in s.testers()}
        rows = [{'case': c, 'cells': [results.get((c.id, t.pk)) if t.pk in who else 'na' for t in testers]}
                for c in s.cases.all()]
        sections.append({'section': s, 'rows': rows})
    return render(request, 'uat/plan_cases.html', {'plan': plan, 'testers': testers, 'sections': sections})


@login_required
@require_POST
def uat_plan_update(request, pk):
    plan = get_object_or_404(UATPlan, pk=pk)
    p = request.POST
    action = p.get('action')

    if action == 'details':
        plan.name = p.get('name', plan.name).strip() or plan.name
        plan.product = p.get('product', '').strip()
        plan.site_url = p.get('site_url', '').strip()
        plan.instructions = p.get('instructions', '').strip()
        plan.due_date = p.get('due_date') or None
        plan.xp_reward = _xp(p)
        plan.status = p.get('status') if p.get('status') in dict(UATPlan.STATUS_CHOICES) else plan.status
        plan.save()
        messages.success(request, 'Plan updated.')

    elif action == 'assign':
        before = set(plan.testers.values_list('pk', flat=True))
        plan.testers.set(Employee.objects.filter(pk__in=p.getlist('testers')))
        for section in plan.sections.all():
            ids = p.getlist(f'section_{section.pk}')
            section.assignees.set(plan.testers.filter(pk__in=ids))
        new = plan.testers.exclude(pk__in=before)
        if p.get('notify'):
            services.notify_assigned(plan, plan.testers.all())
            messages.success(request, 'Assignments saved and every tester was notified.')
        else:
            services.notify_assigned(plan, new)
            messages.success(request, 'Assignments saved.' + (f' {new.count()} new tester(s) notified.' if new else ''))

    return redirect('uat_plan_detail', pk=pk)


@login_required
@require_POST
def uat_problem_update(request, pk):
    result = get_object_or_404(UATResult.objects.select_related('case__section__plan', 'tester'), pk=pk)
    fix = request.POST.get('fix_status', '')
    if fix in dict(UATResult.FIX_CHOICES):
        result.fix_status = fix
        result.fix_note = request.POST.get('fix_note', '').strip()
        result.fixed_by = request.user if fix else None
        result.fixed_at = timezone.now() if fix else None
        result.save(update_fields=['fix_status', 'fix_note', 'fixed_by', 'fixed_at', 'updated_at'])
        if fix == 'fixed':
            services.notify(result.tester, f'Please retest {result.case.code}',
                            f'"{result.case.title}" was fixed. Open UAT Testing and test it again.'
                            + (f' Note: {result.fix_note}' if result.fix_note else ''),
                            {'type': 'uat', 'plan_id': str(result.case.section.plan_id)})
        messages.success(request, f'{result.case.code}: {result.get_fix_status_display()}.')
    plan_id = result.case.section.plan_id
    return redirect(f"{redirect('uat_plan_detail', pk=plan_id).url}?tab={request.POST.get('tab', 'open')}#problems")
