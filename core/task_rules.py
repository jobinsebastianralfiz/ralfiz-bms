"""Task board rules: backlog visibility, who may move a card, task codes and weeks.

One place for the rules from the Backlog & Weekly Planning spec, used by the
admin board, the staff portal, the client portal and the Claude connector:

* Backlog cards are seen only by admins and the project's team lead. They never
  count as open, overdue or "mine" for anyone else, and clients never see them.
* A member moves only their own card, between To Do, In Progress and In Review
  (and to Completed if the project allows it). The lead and admins move anything.
* Projects with a code repository need a pull request link before In Review.
* Cards get codes like ALW-017 from the project's prefix, never reused.
"""
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

OPEN = ('todo', 'in_progress', 'review')
MEMBER_MOVES = ('todo', 'in_progress', 'review')


class TaskRuleError(Exception):
    """A move or edit the person is not allowed to make; the message is shown as is."""


# ---------------------------------------------------------------- visibility

def live(qs):
    """Cards that are on the board for everyone: everything except backlog."""
    return qs.exclude(status='backlog')


def visible_to(qs, member=None, is_admin=False):
    """Cards this person may see: admins see all, a lead also sees their projects' backlog."""
    if is_admin:
        return qs
    if member is None:
        return live(qs)
    return qs.filter(~Q(status='backlog') | Q(project__team_lead=member))


def is_lead(project, member):
    return member is not None and project.team_lead_id == member.pk


def can_plan(project, member=None, is_admin=False):
    """Create, edit and assign cards, see the backlog, start and close weeks."""
    return is_admin or is_lead(project, member)


def lead_name(project):
    return f'{project.team_lead.name} (team lead)' if project.team_lead_id else 'an admin'


# ---------------------------------------------------------------- codes

def next_code(project):
    """The next free code for a project with a prefix (ALW-017), or '' without one."""
    from .models import Project, Task
    if not project.task_prefix:
        return ''
    with transaction.atomic():
        locked = Project.objects.select_for_update().get(pk=project.pk)
        n = max(locked.next_task_number, 1)
        while True:
            code = f'{locked.task_prefix}-{n:03d}'
            if not Task.objects.filter(project=locked, code=code).exists():
                break
            n += 1
        locked.next_task_number = n + 1
        locked.save(update_fields=['next_task_number'])
    project.next_task_number = n + 1
    return code


def backfill_codes(project):
    """Give codes to cards whose title starts with the project's prefix ("ALW-004 Pages"),
    taking the code out of the title, and move next_task_number past the highest one.
    Returns how many cards were changed."""
    import re
    from .models import Task
    if not project.task_prefix:
        return 0
    pattern = re.compile(r'^\s*%s-(\d{1,5})\b[\s:.\-–—]*' % re.escape(project.task_prefix), re.I)
    changed, highest = 0, 0
    for task in Task.objects.filter(project=project):
        if task.code:
            m = re.match(r'.*-(\d+)$', task.code)
            highest = max(highest, int(m.group(1)) if m else 0)
            continue
        m = pattern.match(task.title)
        if not m:
            continue
        n = int(m.group(1))
        code = f'{project.task_prefix}-{n:03d}'
        if Task.objects.filter(project=project, code=code).exists():
            continue
        task.code = code
        task.title = task.title[m.end():].strip() or task.title
        task.save(update_fields=['code', 'title', 'updated_at'])
        highest = max(highest, n)
        changed += 1
    if highest >= project.next_task_number:
        project.next_task_number = highest + 1
        project.save(update_fields=['next_task_number'])
    return changed


# ---------------------------------------------------------------- logging

def log(task, actor, verb, from_value='', to_value='', message='', visible=False):
    from .models import TaskActivity
    TaskActivity.objects.create(task=task, actor=actor, verb=verb, from_value=str(from_value)[:255],
                                to_value=str(to_value)[:255], message=message[:500],
                                is_visible_to_client=visible)


# ---------------------------------------------------------------- create / move

def create_task(project, actor, *, title, checklist=(), **fields):
    """Create a card with the next code, its checklist and a 'created' log row."""
    from .models import Task, TaskChecklistItem
    title = (title or '').strip()[:255]
    if not title:
        raise TaskRuleError('A task needs a title.')
    sprint = fields.get('sprint')
    if sprint is not None and sprint.project_id != project.pk:
        raise TaskRuleError('That week belongs to another project.')
    task = Task(project=project, title=title, **fields)
    task.code = task.code or next_code(project)
    task.status_changed_at = timezone.now()
    if task.status == 'completed':
        task.completed_date = timezone.localdate()
    task.save()
    for i, text in enumerate(t.strip() for t in checklist if t and t.strip()):
        TaskChecklistItem.objects.create(task=task, text=text[:255], order=i)
    log(task, actor, 'created')
    return task


def change_status(task, new_status, actor, *, member=None, is_admin=False, pr_url=None):
    """Move a card, enforcing who may make the move. Raises TaskRuleError."""
    from .models import Task
    project = task.project
    if new_status not in dict(Task.STATUS_CHOICES):
        raise TaskRuleError('Unknown status.')
    planner = can_plan(project, member, is_admin)
    if not planner:
        if member is None or task.assigned_to_id != member.pk:
            raise TaskRuleError(f'Only {lead_name(project)} can move this card.')
        if new_status == task.status:
            pass   # not a move (e.g. adding a PR link or progress)
        elif new_status not in MEMBER_MOVES and not (new_status == 'completed' and project.members_can_complete):
            raise TaskRuleError(f'Only {lead_name(project)} can move this card to '
                                f'{dict(Task.STATUS_CHOICES)[new_status]}.')
        if task.status == 'backlog':
            raise TaskRuleError(f'Only {lead_name(project)} can move this card.')
    if pr_url is not None:
        pr_url = pr_url.strip()
        if pr_url and not pr_url.startswith(('http://', 'https://')):
            raise TaskRuleError('The pull request link must start with https://')
        if pr_url and pr_url != task.pr_url:
            task.pr_url = pr_url
            log(task, actor, 'pr_linked', to_value=pr_url)
    if (new_status == 'review' and task.status != 'review' and project.github_repo
            and not task.pr_url and not is_admin):
        raise TaskRuleError('Paste the pull request link before moving this card to In Review.')
    old = task.status
    if old != new_status:
        task.status = new_status
        task.status_changed_at = timezone.now()
        task.completed_date = timezone.localdate() if new_status == 'completed' else None
        log(task, actor, 'status_changed', from_value=old, to_value=new_status,
            visible='backlog' not in (old, new_status))
    task.save()
    return task


def set_checklist_item(item, done, actor, *, member=None, is_admin=False):
    task = item.task
    if not (can_plan(task.project, member, is_admin) or (member and task.assigned_to_id == member.pk)):
        raise TaskRuleError('Only the card owner or the team lead can tick this list.')
    if item.is_done != done:
        item.is_done = done
        item.done_by = actor if done else None
        item.done_at = timezone.now() if done else None
        item.save()
        log(task, actor, 'checklist', to_value='done' if done else 'not done', message=item.text)
    return item


# ---------------------------------------------------------------- weeks

def start_sprint(sprint, actor):
    """Start a week: its backlog cards go to To Do and each owner gets one notification.
    Returns {'moved': n, 'unassigned': [card labels]}."""
    from .models import ProjectSprint
    project = sprint.project
    if sprint.status != 'planned':
        raise TaskRuleError(f'{sprint.name} has already been {"started" if sprint.status == "active" else "closed"}.')
    active = project.sprints.filter(status='active').exclude(pk=sprint.pk).first()
    if active:
        raise TaskRuleError(f'{active.name} is still running. Close it first.')
    now = timezone.now()
    with transaction.atomic():
        ProjectSprint.objects.select_for_update().filter(project=project)
        cards = list(sprint.tasks.filter(status='backlog').select_related('assigned_to'))
        per_owner = {}
        for t in cards:
            t.status = 'todo'
            t.status_changed_at = now
            t.save(update_fields=['status', 'status_changed_at', 'updated_at'])
            log(t, actor, 'sprint_started', from_value='backlog', to_value='todo', message=sprint.name)
            if t.assigned_to_id:
                per_owner.setdefault(t.assigned_to, []).append(t)
        sprint.status = 'active'
        sprint.started_at = now
        sprint.started_by = actor
        sprint.save(update_fields=['status', 'started_at', 'started_by'])
    _notify_week(project, sprint, per_owner)
    return {'moved': len(cards),
            'unassigned': [f'{t.code} {t.title}'.strip() for t in cards if not t.assigned_to_id]}


def _notify_week(project, sprint, per_owner):
    from django.urls import reverse
    from employees.models import Notification
    from employees.utils import send_push_notification
    for member, cards in per_owner.items():
        emp = member.staff_employee()
        if emp is None:
            continue
        title = f'{sprint.name} has started'
        body = f'You have {len(cards)} task{"s" if len(cards) != 1 else ""} on {project.name}.'
        Notification.objects.create(employee=emp, title=title, body=body, notification_type='work',
                                    data={'url': reverse('staff:project_board', args=[project.pk])})
        try:
            send_push_notification(emp, title, body)
        except Exception:  # a push failure must not undo the week
            pass


def close_sprint(sprint, actor, carry_over='next'):
    """Close the active week. Open cards move to the next week ('next', keeping their
    column) or back to the backlog ('backlog'). Returns a summary dict."""
    if sprint.status != 'active':
        raise TaskRuleError(f'{sprint.name} is not running.')
    if carry_over not in ('next', 'backlog'):
        raise TaskRuleError('carry_over must be "next" or "backlog".')
    nxt = sprint.project.sprints.filter(order__gt=sprint.order).exclude(status='done').order_by('order').first()
    open_cards = list(sprint.tasks.filter(status__in=OPEN))
    if carry_over == 'next' and open_cards and nxt is None:
        raise TaskRuleError('There is no next week to move the open cards to. Add one, or send them to the backlog.')
    done = sprint.tasks.filter(status='completed').count()
    with transaction.atomic():
        for t in open_cards:
            if carry_over == 'next':
                t.sprint = nxt
                t.save(update_fields=['sprint', 'updated_at'])
                log(t, actor, 'sprint_changed', from_value=sprint.name, to_value=nxt.name)
            else:
                old = t.status
                t.status = 'backlog'
                t.status_changed_at = timezone.now()
                t.save(update_fields=['status', 'status_changed_at', 'updated_at'])
                log(t, actor, 'status_changed', from_value=old, to_value='backlog')
        sprint.status = 'done'
        sprint.closed_at = timezone.now()
        sprint.save(update_fields=['status', 'closed_at'])
    return {'completed': done, 'carried_over': len(open_cards),
            'to': (nxt.name if carry_over == 'next' and nxt else 'backlog') if open_cards else None}


def create_sprint(project, *, name, start_date, end_date, goal=''):
    from .models import ProjectSprint
    if end_date < start_date:
        raise TaskRuleError('A week cannot end before it starts.')
    last = project.sprints.order_by('-order').first()
    return ProjectSprint.objects.create(project=project, name=name.strip()[:60] or 'Week',
                                        goal=goal.strip()[:255], start_date=start_date,
                                        end_date=end_date, order=(last.order + 1) if last else 1)
