"""UAT tools for the Claude connector (/mcp).

UAT plans are the test plans given to staff and interns: sections of test cases,
each section tested by its assignees (or every tester on the plan), who mark each
case Pass / Fail / Blocked in the staff portal. These tools read the same
progress the BMS page shows (uat.services.plan_overview) and write the same way
the BMS page does: problems marked fixed notify the tester to retest, new
assignments notify the testers, and completing a plan thanks the testers and
queues the XP reward (wallet signals on UATPlan save).

No API view exists for UAT, so the tools use the ORM; the connector itself is
owner-only (connector.auth.can_use_connector).
"""
from datetime import date

from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from connector.dispatch import ToolError
from connector.tools import LIMIT, Tool, register, s_bool, s_date, s_int, s_str, s_uuid
from employees.models import Employee

from . import services
from .models import UATPlan, UATResult

FIX_STATES = {'open': '', 'fixed': 'fixed', 'wont_fix': 'wont_fix', 'not_bug': 'not_bug'}


def _plan(plan_id):
    plan = UATPlan.objects.filter(pk=plan_id).first()
    if plan is None:
        raise ToolError('No UAT plan with that id. Use list_uat_plans to find it.')
    return plan


def _person(emp):
    return f'{emp.user.get_full_name() or emp.user.username} ({emp.employee_id})'


def _staff_page(ctx, plan):
    return ctx.request.build_absolute_uri(reverse('uat_plan_detail', kwargs={'pk': plan.pk}))


def _testers(ids, what='tester_ids'):
    """Active employees (staff or interns) for the given ids; every id must match one."""
    ids = [str(i) for i in ids or []]
    people = list(Employee.objects.filter(pk__in=ids, status='active').select_related('user'))
    missing = set(ids) - {str(e.pk) for e in people}
    if missing:
        raise ToolError(f'{what}: no active employee or intern with id {", ".join(sorted(missing))}. '
                        'Use search with types ["employees"] to find them.')
    return people


def _plan_row(ctx, plan, stats):
    return {
        'id': str(plan.id), 'name': plan.name, 'product': plan.product,
        'status': plan.get_status_display(),
        'due_date': plan.due_date.isoformat() if plan.due_date else None,
        'testers': stats['testers'], 'progress': f"{stats['pct']}%",
        'failed': stats['fail'], 'blocked': stats['blocked'], 'open_problems': stats['open'],
        'staff_page': _staff_page(ctx, plan),
    }


# ---------------------------------------------------------------- read

def _list_uat_plans(ctx, args):
    qs = UATPlan.objects.prefetch_related('testers__user')
    status = args.get('status', 'active')
    if status != 'all':
        qs = qs.filter(status=status)
    if args.get('query'):
        q = args['query'].strip()
        qs = qs.filter(name__icontains=q) | qs.filter(product__icontains=q)
    limit = args.get('limit', 50)
    plans = list(qs.distinct()[:limit])
    stats = services.plan_stats(plans)
    return {'count': qs.distinct().count(), 'returned': len(plans),
            'items': [_plan_row(ctx, p, stats[p.pk]) for p in plans]}


register(Tool(
    'list_uat_plans', 'UAT test plans',
    'UAT test plans given to staff and interns to test a product or client project, newest first: '
    'progress (share of tests marked), failed and blocked counts, and problems nobody has handled yet. '
    'Use get_uat_plan for who tests what and the problems themselves.',
    _list_uat_plans,
    {
        'status': s_str('active = still in testing (default), closed = completed, all.', ['active', 'closed', 'all']),
        'query': s_str('Part of the plan name or product, e.g. "Shop Manager".'),
        'limit': LIMIT,
    },
))


def _problem(result):
    return {
        'result_id': str(result.id),
        'case': f'{result.case.code} {result.case.title}'.strip(),
        'section': result.case.section.name,
        'tester': _person(result.tester),
        'result': result.get_status_display(),
        'tester_note': result.note,
        'screenshot': bool(result.screenshot),
        'fix_status': result.get_fix_status_display(),
        'fix_note': result.fix_note,
        'reported_at': result.updated_at.isoformat(),
    }


def _get_uat_plan(ctx, args):
    plan = _plan(args['plan_id'])
    ov = services.plan_overview(plan)
    problems = services.open_problems(plan).order_by('fix_status', '-updated_at')
    which = args.get('problems', 'unresolved')
    if which == 'unresolved':
        problems = problems.filter(fix_status__in=['', 'fixed'])
    elif which == 'open':
        problems = problems.filter(fix_status='')
    out = {
        'id': str(plan.id), 'name': plan.name, 'product': plan.product, 'site_url': plan.site_url,
        'status': plan.get_status_display(),
        'due_date': plan.due_date.isoformat() if plan.due_date else None,
        'xp_reward_per_tester': plan.xp_reward,
        'instructions': plan.instructions,
        'tests': ov['case_count'],
        'overall': f"{ov['overall']['done']} of {ov['overall']['total']} marked ({ov['overall']['pct']}%)",
        'totals': ov['totals'],
        'testers': [{
            'employee_id': str(p['employee'].pk), 'name': _person(p['employee']),
            'sections': [s.name for s in p['sections']],
            'progress': f"{p['done']} of {p['total']} ({p['pct']}%)",
            'pass': p['pass'], 'fail': p['fail'], 'blocked': p['blocked'],
            'last_activity': p['last'].isoformat() if p['last'] else None,
        } for p in ov['people']],
        'sections': [{
            'section_id': str(r['section'].pk), 'name': r['section'].name, 'tests': r['cases'],
            'tested_by': [_person(e) for e in r['testers']],
            'assigned': 'specific testers' if r['section'].assignees.exists() else 'every tester on the plan',
            'progress': f"{r['done']} of {r['total']} ({r['pct']}%)",
            'pass': r['pass'], 'fail': r['fail'], 'blocked': r['blocked'],
            'locked_until_done': r['section'].starts_after.name if r['section'].starts_after else None,
        } for r in ov['sections']],
        'problems': [_problem(r) for r in problems[:100]],
        'files': [f.name for f in plan.files.all()],
        'staff_page': _staff_page(ctx, plan),
    }
    if args.get('include_cases'):
        out['cases'] = [{
            'section': c.section.name, 'code': c.code, 'title': c.title, 'steps': c.steps,
            'expected': c.expected,
            'results': [{'tester': _person(r.tester), 'result': r.get_status_display(), 'note': r.note}
                        for r in c.results.select_related('tester__user')],
        } for c in plan.cases().select_related('section').order_by('section__order', 'order')]
    return out


register(Tool(
    'get_uat_plan', 'UAT plan details',
    'One UAT test plan: its instructions, each tester (staff or intern) with their sections and '
    'progress, each section with who tests it and its pass/fail/blocked counts, and the problems '
    'testers reported (failed or blocked tests with their notes). Problems have a result_id for '
    'update_uat_problem. Set include_cases for every test case with each tester\'s result.',
    _get_uat_plan,
    {
        'plan_id': s_uuid('UAT plan (from list_uat_plans)'),
        'problems': s_str('unresolved = open + fixed awaiting retest (default), open = nobody handled yet, '
                          'all = also won\'t fix / not a bug.', ['unresolved', 'open', 'all']),
        'include_cases': s_bool('Also list every test case with its steps and each tester\'s result.'),
    },
    required=('plan_id',),
))


# ---------------------------------------------------------------- write

def _update_uat_problem(ctx, args):
    result = (UATResult.objects.select_related('case__section__plan', 'tester__user')
              .filter(pk=args['result_id'], status__in=['fail', 'blocked']).first())
    if result is None:
        raise ToolError('No failed or blocked test result with that id. Use get_uat_plan to see the problems.')
    fix = FIX_STATES[args['fix_status']]
    result.fix_status = fix
    result.fix_note = (args.get('note') or '').strip()
    result.fixed_by = ctx.user if fix else None
    result.fixed_at = timezone.now() if fix else None
    result.save(update_fields=['fix_status', 'fix_note', 'fixed_by', 'fixed_at', 'updated_at'])
    told = False
    if fix == 'fixed':
        services.notify(result.tester, f'Please retest {result.case.code}',
                        f'"{result.case.title}" was fixed. Open My Tasks and test it again.'
                        + (f' Note: {result.fix_note}' if result.fix_note else ''),
                        {'type': 'uat', 'plan_id': str(result.case.section.plan_id)})
        told = True
    out = _problem(result)
    out['plan'] = result.case.section.plan.name
    out['tester_notified'] = told
    return out


register(Tool(
    'update_uat_problem', 'Handle a UAT problem',
    'Mark a failed or blocked UAT test as fixed (the tester is notified to retest it), won\'t fix, '
    'not a bug, or back to open, with an optional note the tester sees. Same as the Problems box '
    'on the BMS UAT page.',
    _update_uat_problem,
    {
        'result_id': s_uuid('problem (result_id from get_uat_plan)'),
        'fix_status': s_str('fixed = ask the tester to retest; wont_fix; not_bug; open = undo.',
                            list(FIX_STATES)),
        'note': s_str('Short note for the tester, e.g. what was changed.'),
    },
    required=('result_id', 'fix_status'), write=True,
))


def _assign(plan, testers, section_map, notify):
    """Set the plan's testers and each named section's assignees; notify new (or all) testers."""
    before = set(plan.testers.values_list('pk', flat=True))
    plan.testers.set(testers)
    by_key = {}
    for s in plan.sections.all():
        by_key[str(s.pk)] = s
        if s.key:
            by_key.setdefault(s.key.lower(), s)
        by_key.setdefault(s.name.lower(), s)
    for ref, ids in (section_map or {}).items():
        section = by_key.get(str(ref).lower()) or by_key.get(str(ref))
        if section is None:
            raise ToolError(f'No section "{ref}" in this plan. Use the section_id, key or name from get_uat_plan.')
        people = _testers(ids, f'sections["{ref}"]')
        outside = [p for p in people if p.pk not in {t.pk for t in testers}]
        if outside:
            raise ToolError(f'{_person(outside[0])} is assigned to "{section.name}" but is not in tester_ids.')
        section.assignees.set(people)
    new = [t for t in testers if t.pk not in before]
    if notify != 'none':
        services.notify_assigned(plan, testers if notify == 'all' else new)
    return new


def _sections_arg(sections):
    """Validate the create_uat_plan sections into the shape uat.web_views.load_cases reads."""
    if not sections:
        raise ToolError('A plan needs at least one section with tests.')
    keys = set()
    data = []
    for i, s in enumerate(sections, 1):
        name = (s.get('name') or '').strip()
        tests = s.get('tests') or []
        if not name or not tests:
            raise ToolError(f'Section {i} needs a name and at least one test.')
        key = (s.get('key') or f'S{i}').strip()[:20]
        after = s.get('after')
        if after and after not in keys:
            raise ToolError(f'Section "{name}": after="{after}" must be the key of an earlier section.')
        keys.add(key)
        rows = []
        for j, t in enumerate(tests, 1):
            title = (t.get('title') or '').strip()
            if not title:
                raise ToolError(f'Section "{name}", test {j} needs a title.')
            rows.append({'code': t.get('code') or f'{key}-{j:02d}', 'title': title,
                         'steps': [str(x) for x in t.get('steps') or []],
                         'expected': t.get('expected', ''), 'tags': [str(x) for x in t.get('tags') or []]})
        data.append({'key': key, 'name': name, 'after': after, 'tests': rows})
    return {'sections': data}


def _create_uat_plan(ctx, args):
    from .web_views import load_cases

    name = (args.get('name') or '').strip()
    if not name:
        raise ToolError('Give the plan a name.')
    data = _sections_arg(args.get('sections'))
    testers = _testers(args.get('tester_ids'))
    section_map = {d['key']: raw['assignee_ids']
                   for d, raw in zip(data['sections'], args['sections']) if raw.get('assignee_ids')}
    due = date.fromisoformat(args['due_date']) if args.get('due_date') else None
    with transaction.atomic():
        plan = UATPlan.objects.create(
            name=name[:200], product=(args.get('product') or '').strip()[:120],
            site_url=(args.get('site_url') or '').strip(), instructions=(args.get('instructions') or '').strip(),
            due_date=due, xp_reward=args.get('xp_reward', 0), created_by=ctx.user)
        load_cases(plan, data)
        notify = args.get('notify', True)
        _assign(plan, testers, section_map, notify='all' if notify else 'none')
    out = _get_uat_plan(ctx, {'plan_id': plan.pk})
    out['testers_notified'] = bool(notify and testers)
    return out


TEST = {'type': 'object', 'properties': {
    'code': s_str('Short code shown to testers, e.g. "BIL-03" (default <section key>-<n>).'),
    'title': s_str('What is being tested, e.g. "Print a bill with GST".'),
    'steps': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Steps in order.'},
    'expected': s_str('What should happen.'),
    'tags': {'type': 'array', 'items': {'type': 'string'}},
}, 'required': ['title']}

register(Tool(
    'create_uat_plan', 'Create UAT test plan',
    'Create a UAT test plan for staff and interns: sections of test cases (each with steps and the '
    'expected result), who tests it, and optionally which testers take which section (a section '
    'with no assignees goes to every tester). A section can wait for an earlier one (`after`, e.g. '
    'shop setup before billing). Testers are notified in the staff portal unless notify is false. '
    'Write tests from what the user describes or the product; do not invent features. Show the '
    'user the sections, test titles and testers and get a yes before calling this.',
    _create_uat_plan,
    {
        'name': s_str('Plan name, e.g. "Shop Manager UAT – round 2".'),
        'product': s_str('Product or client project under test.'),
        'site_url': s_str('Where testers do the testing (URL).'),
        'instructions': s_str('Shown to testers at the top of the plan: logins, test data, how to report.'),
        'due_date': s_date('Testing deadline.'),
        'xp_reward': s_int('XP each tester earns once every test in their sections is marked (default 0).', 0, 10000),
        'tester_ids': {'type': 'array', 'items': s_uuid('employee or intern'),
                       'description': 'Everyone testing this plan (employee ids from search, type employees).'},
        'sections': {'type': 'array', 'description': 'Sections in order.', 'items': {
            'type': 'object',
            'properties': {
                'name': s_str('Section name, e.g. "Billing".'),
                'key': s_str('Short key, e.g. "BIL" (default S1, S2...). Used by `after` and test codes.'),
                'after': s_str('Key of an earlier section that must be fully tested first.'),
                'assignee_ids': {'type': 'array', 'items': s_uuid('employee or intern'),
                                 'description': 'Only these testers take this section (must be in tester_ids).'},
                'tests': {'type': 'array', 'items': TEST},
            },
            'required': ['name', 'tests'],
        }},
        'notify': s_bool('Notify the testers now (default true).'),
    },
    required=('name', 'tester_ids', 'sections'), write=True,
))


def _assign_uat_testers(ctx, args):
    plan = _plan(args['plan_id'])
    testers = _testers(args.get('tester_ids'))
    with transaction.atomic():
        new = _assign(plan, testers, args.get('sections'), notify='all' if args.get('notify_all') else 'new')
    out = _get_uat_plan(ctx, {'plan_id': plan.pk})
    out['newly_added_and_notified'] = [_person(e) for e in new]
    return out


register(Tool(
    'assign_uat_testers', 'Assign UAT testers',
    'Set who tests a UAT plan, and optionally which testers take which section. tester_ids is the '
    'full list (anyone left out is removed from the plan). sections maps a section (its section_id, '
    'key or name from get_uat_plan) to the testers for it; sections not mentioned keep their current '
    'assignees. New testers are notified; set notify_all to remind everyone. Confirm with the user first.',
    _assign_uat_testers,
    {
        'plan_id': s_uuid('UAT plan (from list_uat_plans)'),
        'tester_ids': {'type': 'array', 'items': s_uuid('employee or intern'),
                       'description': 'Everyone on the plan after this change.'},
        'sections': {'type': 'object', 'description': 'Section -> list of employee ids for that section. '
                     'An empty list means every tester on the plan.',
                     'additionalProperties': {'type': 'array', 'items': {'type': 'string'}}},
        'notify_all': s_bool('Notify every tester, not only the new ones.'),
    },
    required=('plan_id', 'tester_ids'), write=True,
))


def _complete_uat_plan(ctx, args):
    plan = _plan(args['plan_id'])
    done = args.get('completed', True)
    if done == plan.is_completed:
        raise ToolError(f'"{plan.name}" is already {"completed" if done else "in testing"}.')
    plan.set_completed(done, ctx.user)
    plan.save()  # wallet signals queue the XP reward on completion
    out = {'plan': plan.name, 'status': plan.get_status_display(), 'staff_page': _staff_page(ctx, plan)}
    if done:
        for emp in plan.testers.all():
            services.notify(emp, f'UAT completed: {plan.name}',
                            'Testing is finished. Thank you for testing! Open it in My Tasks to see your summary.',
                            {'type': 'uat', 'plan_id': str(plan.id)})
        out['testers_thanked'] = plan.testers.count()
        out['xp'] = (f'{plan.xp_reward} XP per tester who finished is waiting in XP Approvals.'
                     if plan.xp_reward else 'No XP reward is set on this plan.')
    else:
        out['next'] = 'Testers can mark tests again.'
    return out


register(Tool(
    'complete_uat_plan', 'Complete or reopen UAT plan',
    'Mark a UAT plan completed (testers stop seeing it, each gets a thank-you, and the XP reward goes '
    'to XP Approvals) or put it back into testing with completed=false. Confirm with the user first.',
    _complete_uat_plan,
    {
        'plan_id': s_uuid('UAT plan (from list_uat_plans)'),
        'completed': s_bool('true = completed (default), false = back into testing.'),
    },
    required=('plan_id',), write=True,
))
