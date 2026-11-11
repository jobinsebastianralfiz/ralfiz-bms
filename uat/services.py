import logging

from .models import UATCase, UATResult

log = logging.getLogger(__name__)


def tester_sections(plan, employee):
    return [s for s in plan.sections.prefetch_related('assignees').all() if s.is_for(employee)]


def counts(results):
    c = {'pass': 0, 'fail': 0, 'blocked': 0}
    for r in results:
        c[r.status] = c.get(r.status, 0) + 1
    return c


def progress(total, done):
    return {'total': total, 'done': done, 'pct': round(done * 100 / total) if total else 0}


def plan_overview(plan):
    """Per-tester and per-section progress for the BMS dashboard."""
    sections = list(plan.sections.prefetch_related('assignees', 'cases'))
    testers = list(plan.testers.select_related('user'))
    results = list(UATResult.objects.filter(case__section__plan=plan).select_related('case'))
    by_tester = {}
    for r in results:
        by_tester.setdefault(r.tester_id, []).append(r)

    people = []
    for emp in testers:
        mine = [s for s in sections if s.is_for(emp)]
        case_ids = {c.id for s in mine for c in s.cases.all()}
        theirs = [r for r in by_tester.get(emp.pk, []) if r.case_id in case_ids]
        people.append({'employee': emp, 'sections': mine, **progress(len(case_ids), len(theirs)), **counts(theirs),
                       'last': max((r.updated_at for r in theirs), default=None)})

    rows = []
    for s in sections:
        ids = {c.id for c in s.cases.all()}
        who = s.testers()
        expected = len(ids) * len(who)
        got = [r for r in results if r.case_id in ids and any(w.pk == r.tester_id for w in who)]
        rows.append({'section': s, 'testers': who, 'cases': len(ids), **progress(expected, len(got)), **counts(got)})

    total_expected = sum(p['total'] for p in people)
    total_done = sum(p['done'] for p in people)
    return {'people': people, 'sections': rows, 'overall': progress(total_expected, total_done),
            'totals': counts(results), 'case_count': UATCase.objects.filter(section__plan=plan).count()}


def notify(employee, title, body, data=None):
    """Staff-portal notification + push. A push failure must never break the page."""
    from employees.models import Notification

    Notification.objects.create(employee=employee, title=title, body=body, notification_type='work', data=data or {})
    try:
        from employees.utils import send_push_notification

        send_push_notification(employee, title, body, data=data or {})
    except Exception as e:  # noqa: BLE001
        log.warning('UAT push failed for %s: %s', employee, e)


def notify_assigned(plan, employees):
    for emp in employees:
        names = ', '.join(s.name for s in tester_sections(plan, emp))
        notify(emp, f'UAT: {plan.name}',
               f'You are testing: {names}. Open "My Tasks" in the staff portal.',
               {'type': 'uat', 'plan_id': str(plan.id)})


def open_problems(plan):
    return (UATResult.objects.filter(case__section__plan=plan, status__in=['fail', 'blocked'])
            .select_related('case__section', 'tester__user', 'fixed_by'))


def plan_stats(plans):
    """Small progress figures for the plan list."""
    out = {}
    for p in plans:
        ov = plan_overview(p)
        out[p.pk] = {'pct': ov['overall']['pct'], 'fail': ov['totals']['fail'], 'blocked': ov['totals']['blocked'],
                     'open': open_problems(p).filter(fix_status='').count(), 'testers': len(ov['people'])}
    return out



def instruction_blocks(text):
    """Split plan instructions into [{title, items, numbered}] for a readable layout.
    Paragraphs are separated by a blank line; the first line is the title, the rest are list items."""
    import re
    blocks = []
    for para in re.split(r'\n\s*\n', (text or '').strip()):
        lines = [l.strip() for l in para.splitlines() if l.strip()]
        if not lines:
            continue
        title, rest = (lines[0], lines[1:]) if len(lines) > 1 else ('', lines)
        numbered = bool(rest) and bool(re.match(r'\d+[.)]\s', rest[0]))
        items = [re.sub(r'^(\d+[.)]|[•\-*])\s*', '', l) for l in rest]
        blocks.append({'title': title, 'items': items, 'numbered': numbered})
    return blocks
