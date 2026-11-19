"""Project task board tools for the Claude connector (/mcp).

The task board (/tasks/board/) holds core.Task cards per project, assigned to
TeamMembers. The mobile task API only shows a user their own tasks, so these
tools read and write the ORM directly, the way the web board does: status
changes stamp completed_date and go in the task's activity log (visible to the
client, like the board), and so do priority and assignee changes.

The connector itself is owner-only (connector.auth.can_use_connector).
"""
from datetime import date

from django.db.models import Count, Q
from django.urls import reverse
from django.utils import timezone

from core import task_rules
from core.models import Project, ProjectSprint, Task, TaskActivity, TaskComment, TeamMember

from .dispatch import ToolError
from .tools import Tool, register, s_bool, s_date, s_int, s_str, s_uuid

STATUSES = [s for s, _ in Task.STATUS_CHOICES]
PRIORITIES = [p for p, _ in Task.PRIORITY_CHOICES]
OPEN = task_rules.OPEN


def _log(task, user, verb, from_value='', to_value='', message='', visible=False, comment=None):
    TaskActivity.objects.create(
        task=task, actor=user, verb=verb, from_value=str(from_value)[:255],
        to_value=str(to_value)[:255], message=message[:500], is_visible_to_client=visible,
        related_comment=comment,
    )


def _task(task_id):
    task = Task.objects.select_related('project__client', 'assigned_to', 'sprint').filter(pk=task_id).first()
    if task is None:
        raise ToolError('No task with that id. Use list_project_tasks to find it.')
    return task


def _member(member_id):
    member = TeamMember.objects.filter(pk=member_id).first()
    if member is None:
        raise ToolError('No team member with that id. Use list_team_members or search '
                        '(tasks are assigned to team members, not employee ids).')
    return member


def _url(ctx, task):
    return ctx.request.build_absolute_uri(reverse('task_detail', args=[task.pk]))


def _summary(task):
    return {
        'id': str(task.id),
        'code': task.code or None,
        'title': task.title,
        'project': task.project.name,
        'project_id': str(task.project_id),
        'status': task.status,
        'priority': task.priority,
        'assigned_to': task.assigned_to.name if task.assigned_to_id else None,
        'assigned_to_id': str(task.assigned_to_id) if task.assigned_to_id else None,
        'due_date': str(task.due_date) if task.due_date else None,
        'is_overdue': task.is_overdue,
        'label': task.category,
        'progress_percent': task.progress_percent,
        'sprint': task.sprint.name if task.sprint_id else None,
        'sprint_id': str(task.sprint_id) if task.sprint_id else None,
        'pr_url': task.pr_url or None,
        'checklist': '{}/{}'.format(*task.checklist_progress) if task.checklist_progress[1] else None,
        'in_column_since': task.status_changed_at.isoformat() if task.status_changed_at else None,
    }


def _detail(ctx, task):
    out = _summary(task)
    out.update(
        description=task.description,
        notes=task.notes,
        client=task.project.client.name if task.project.client_id else '',
        completed_date=str(task.completed_date) if task.completed_date else None,
        branch_name=task.branch_name,
        done_when=[{'id': str(c.id), 'text': c.text, 'done': c.is_done} for c in task.checklist.all()],
        created_at=task.created_at.isoformat(),
        url=_url(ctx, task),
        comments=[
            {'id': str(c.id), 'author': (c.author.get_full_name() or c.author.username) if c.author_id else '',
             'body': c.body, 'visible_to_client': c.is_visible_to_client,
             'at': c.created_at.isoformat()}
            for c in task.comments.filter(is_deleted=False).select_related('author').order_by('-created_at')[:20]
        ],
        open_issues=[
            {'id': str(i.id), 'title': i.title, 'severity': i.severity, 'status': i.status}
            for i in task.issues.filter(status__in=('open', 'in_progress'))
        ],
        recent_activity=[
            {'verb': a.verb, 'from': a.from_value, 'to': a.to_value, 'message': a.message,
             'by': (a.actor.get_full_name() or a.actor.username) if a.actor_id else '',
             'at': a.created_at.isoformat()}
            for a in task.activities.select_related('actor')[:15]
        ],
    )
    return out


# ---------------------------------------------------------------- read

def _list_project_tasks(ctx, args):
    qs = Task.objects.select_related('project', 'assigned_to', 'sprint').prefetch_related('checklist')
    if args.get('project_id'):
        if not Project.objects.filter(pk=args['project_id']).exists():
            raise ToolError('No project with that id. Use search to find it.')
        qs = qs.filter(project_id=args['project_id'])
    if args.get('sprint_id'):
        qs = qs.filter(sprint_id=args['sprint_id'])
    elif args.get('current_week'):
        qs = qs.filter(sprint__status='active')
    if args.get('stuck_days'):
        cutoff = timezone.now() - timezone.timedelta(days=args['stuck_days'])
        qs = qs.filter(status__in=('in_progress', 'review'), status_changed_at__lt=cutoff)
    if args.get('assigned_to'):
        qs = qs.filter(assigned_to_id=args['assigned_to'])
    if args.get('search'):
        term = args['search']
        qs = qs.filter(Q(title__icontains=term) | Q(description__icontains=term)
                       | Q(category__icontains=term))
    if args.get('status'):
        qs = qs.filter(status=args['status'])
    elif not args.get('include_completed'):
        qs = qs.filter(status__in=OPEN)
    if args.get('overdue_only'):
        qs = qs.filter(due_date__lt=date.today(), status__in=OPEN)

    counts = {row['status']: row['n'] for row in qs.values('status').annotate(n=Count('id')).order_by()}
    limit = args.get('limit', 100)
    items = [_summary(t) for t in qs.order_by('status', '-priority', 'due_date')[:limit]]
    columns = {s: [t for t in items if t['status'] == s] for s in STATUSES if counts.get(s)}
    return {
        'count': sum(counts.values()),
        'per_status': {s: counts.get(s, 0) for s in STATUSES},
        'returned': len(items),
        'columns': columns,
    }


register(Tool(
    'list_project_tasks', 'Project task board',
    'Tasks on the project task board (/tasks/board/), grouped into Backlog, To Do, In Progress, '
    'In Review and Completed columns. By default only open tasks (To Do, In Progress, In Review); '
    'ask for status "backlog" to see planned cards the team cannot see yet. Filter by project, '
    'week (sprint_id or current_week), team member, status, text, overdue, or stuck (in a column '
    'longer than stuck_days). Each card has its code (ALW-017), week, PR link and Done-when '
    'progress. Call for "what is pending on <project>", "what is <person> working on", "what is '
    'stuck" or "plan for week 3". These are board tasks, not daily tasks or work assignments.',
    _list_project_tasks,
    {
        'project_id': s_uuid('project'),
        'assigned_to': s_uuid('team member (from list_team_members or search)'),
        'status': s_str('Only this column.', STATUSES),
        'include_completed': s_bool('Also list completed tasks (ignored when status is given).'),
        'overdue_only': s_bool('Only open tasks past their due date.'),
        'sprint_id': s_uuid('week (from list_sprints)'),
        'current_week': s_bool('Only cards in each project\'s running week.'),
        'stuck_days': s_int('Only In Progress / In Review cards that have not moved for this many days.', 1, 365),
        'search': s_str('Filter by task title, description or label.'),
        'limit': s_int('Maximum tasks to return (default 100).', 1, 500),
    },
))


def _get_task(ctx, args):
    return _detail(ctx, _task(args['task_id']))


register(Tool(
    'get_task', 'Task details',
    'One board task in full: description, assignee, due date, recent comments, open issues '
    'and its activity log.',
    _get_task,
    {'task_id': s_uuid('task (from list_project_tasks)')},
    required=('task_id',),
))


# ---------------------------------------------------------------- write

def _sprint(project, sprint_id):
    if not sprint_id:
        return None
    sprint = ProjectSprint.objects.filter(pk=sprint_id, project=project).first()
    if sprint is None:
        raise ToolError('No week with that id on this project. Use list_sprints.')
    return sprint


def _clean_pr(url):
    url = (url or '').strip()[:500]
    if url and not url.startswith(('http://', 'https://')):
        raise ToolError('pr_url must start with https://')
    return url


def _card_fields(project, args):
    """Card fields from tool arguments, checked; shared by create_task and create_tasks_bulk."""
    status = args.get('status') or 'todo'
    if status not in STATUSES:
        raise ToolError(f'status must be one of {", ".join(STATUSES)}')
    priority = args.get('priority') or 'medium'
    if priority not in PRIORITIES:
        raise ToolError(f'priority must be one of {", ".join(PRIORITIES)}')
    try:
        due = date.fromisoformat(args['due_date']) if args.get('due_date') else None
    except (TypeError, ValueError):
        raise ToolError('due_date must be YYYY-MM-DD')
    member = _member(args['assigned_to']) if args.get('assigned_to') else None
    checklist = args.get('checklist') or []
    if not isinstance(checklist, list) or not all(isinstance(c, str) for c in checklist):
        raise ToolError('checklist must be a list of strings')
    return dict(
        description=str(args.get('description') or ''),
        status=status, priority=priority,
        category=str(args.get('label') or '')[:60],
        due_date=due, assigned_to=member,
        sprint=_sprint(project, args.get('sprint_id')),
        branch_name=str(args.get('branch_name') or '')[:120],
        pr_url=_clean_pr(args.get('pr_url')),
    ), checklist


def _project(project_id):
    project = Project.objects.filter(pk=project_id).first()
    if project is None:
        raise ToolError('No project with that id. Use search to find it.')
    return project


def _create_task(ctx, args):
    project = _project(args['project_id'])
    fields, checklist = _card_fields(project, args)
    try:
        task = task_rules.create_task(project, ctx.user, title=args['title'], checklist=checklist, **fields)
    except task_rules.TaskRuleError as e:
        raise ToolError(str(e))
    return {'created': True, 'code': task.code or None, 'task': _detail(ctx, task)}


CARD_PARAMS = {
    'title': s_str('Task title, without the code (the code is given automatically).'),
    'description': s_str('What needs doing.'),
    'assigned_to': s_uuid('team member (from list_team_members or search)'),
    'priority': s_str('Priority (default medium).', PRIORITIES),
    'status': s_str('Column to start in (default todo). Use "backlog" for a later week: hidden from '
                    'the team and the client until the week is started.', STATUSES),
    'due_date': s_date('Due date.'),
    'label': s_str('Board label, e.g. "Backend" or "Mobile App".'),
    'sprint_id': s_uuid('week (from list_sprints or create_sprint)'),
    'branch_name': s_str('Git branch, e.g. feature/alw-017-page-model.'),
    'pr_url': s_str('Pull request link.'),
    'checklist': {'type': 'array', 'items': {'type': 'string'}, 'maxItems': 30,
                  'description': '"Done when" checklist, one line per item.'},
}


register(Tool(
    'create_task', 'Create board task',
    'Add one task card to a project\'s task board. It starts in To Do unless a status is given; '
    'put cards for a later week in "backlog" with that week\'s sprint_id. The card gets the '
    'project\'s next code (ALW-017) when the project has a prefix. For many cards at once use '
    'create_tasks_bulk.',
    _create_task,
    {'project_id': s_uuid('project'), **CARD_PARAMS},
    required=('project_id', 'title'), write=True,
))


def _update_task(ctx, args):
    task = _task(args['task_id'])
    changed = []

    if 'status' in args and args['status'] != task.status:
        old = task.status
        task.status = args['status']
        task.status_changed_at = timezone.now()
        task.completed_date = timezone.now().date() if task.status == 'completed' else None
        _log(task, ctx.user, 'status_changed', from_value=old, to_value=task.status,
             visible='backlog' not in (old, task.status))
        changed.append('status')
    if args.get('clear_sprint'):
        if task.sprint_id:
            _log(task, ctx.user, 'sprint_changed', from_value=task.sprint.name, to_value='')
            task.sprint = None
            changed.append('sprint')
    elif args.get('sprint_id') and args['sprint_id'] != str(task.sprint_id):
        sprint = _sprint(task.project, args['sprint_id'])
        _log(task, ctx.user, 'sprint_changed', from_value=task.sprint.name if task.sprint_id else '',
             to_value=sprint.name)
        task.sprint = sprint
        changed.append('sprint')
    if 'branch_name' in args:
        task.branch_name = args['branch_name'][:120]
        changed.append('branch_name')
    if 'pr_url' in args:
        url = _clean_pr(args['pr_url'])
        if url != task.pr_url:
            task.pr_url = url
            if url:
                _log(task, ctx.user, 'pr_linked', to_value=url)
            changed.append('pr_url')
    if 'priority' in args and args['priority'] != task.priority:
        _log(task, ctx.user, 'priority_changed', from_value=task.priority, to_value=args['priority'])
        task.priority = args['priority']
        changed.append('priority')
    if args.get('unassign'):
        if task.assigned_to_id:
            _log(task, ctx.user, 'assigned', from_value=task.assigned_to.name, to_value='')
            task.assigned_to = None
            changed.append('assigned_to')
    elif args.get('assigned_to') and args['assigned_to'] != str(task.assigned_to_id):
        member = _member(args['assigned_to'])
        _log(task, ctx.user, 'assigned',
             from_value=task.assigned_to.name if task.assigned_to_id else '', to_value=member.name)
        task.assigned_to = member
        changed.append('assigned_to')
    if args.get('clear_due_date'):
        if task.due_date:
            task.due_date = None
            changed.append('due_date')
    elif args.get('due_date'):
        task.due_date = date.fromisoformat(args['due_date'])
        changed.append('due_date')
    if args.get('title'):
        task.title = args['title'][:255]
        changed.append('title')
    if 'description' in args:
        task.description = args['description']
        changed.append('description')
    if 'label' in args:
        task.category = args['label'][:60]
        changed.append('label')
    if 'progress_percent' in args:
        task.progress = args['progress_percent']
        changed.append('progress_percent')

    if 'checklist' in args:
        from core.views import _save_checklist
        changed.append('checklist')

    if not changed:
        raise ToolError('Nothing to change: give at least one field to update.')
    task.save()
    if 'checklist' in args:
        _save_checklist(task, '\n'.join(str(c) for c in args['checklist']))
    return {'updated': changed, 'task': _detail(ctx, task)}


register(Tool(
    'update_task', 'Update board task',
    'Move a board task to another column, or change its priority, assignee, due date, week, '
    'branch, PR link, Done-when checklist, title, description, label or progress. Moves between '
    'live columns show in the client portal\'s activity, like moving the card on the board; '
    'backlog moves stay internal.',
    _update_task,
    {
        'task_id': s_uuid('task (from list_project_tasks)'),
        'status': s_str('New column.', STATUSES),
        'priority': s_str('New priority.', PRIORITIES),
        'assigned_to': s_uuid('team member to assign to'),
        'unassign': s_bool('Remove the assignee.'),
        'due_date': s_date('New due date.'),
        'clear_due_date': s_bool('Remove the due date.'),
        'title': s_str('New title.'),
        'description': s_str('New description (replaces the old one).'),
        'label': s_str('New board label.'),
        'progress_percent': s_int('Percent done.', 0, 100),
        'sprint_id': s_uuid('week to move the card into (from list_sprints)'),
        'clear_sprint': s_bool('Take the card out of its week.'),
        'branch_name': s_str('Git branch name.'),
        'pr_url': s_str('Pull request link ("" removes it).'),
        'checklist': {'type': 'array', 'items': {'type': 'string'}, 'maxItems': 30,
                      'description': 'Replace the Done-when checklist (ticks kept on unchanged lines).'},
    },
    required=('task_id',), write=True,
))


def _add_task_comment(ctx, args):
    task = _task(args['task_id'])
    body = args['body']
    if not body:
        raise ToolError('body cannot be empty')
    visible = bool(args.get('visible_to_client'))
    comment = TaskComment.objects.create(task=task, author=ctx.user, body=body,
                                         is_visible_to_client=visible)
    _log(task, ctx.user, 'commented', message=body[:140], visible=visible, comment=comment)
    return {'comment_id': str(comment.id), 'visible_to_client': visible, 'task': _summary(task)}


register(Tool(
    'add_task_comment', 'Comment on board task',
    'Add a comment to a board task. Staff-only unless visible_to_client is true, in which '
    'case the client sees it in their portal.',
    _add_task_comment,
    {
        'task_id': s_uuid('task (from list_project_tasks)'),
        'body': s_str('Comment text.'),
        'visible_to_client': s_bool('Show this comment to the client (default false).'),
    },
    required=('task_id', 'body'), write=True,
))


# ---------------------------------------------------------------- bulk + weeks

def _create_tasks_bulk(ctx, args):
    from django.db import transaction
    project = _project(args['project_id'])
    cards = args.get('tasks') or []
    if not isinstance(cards, list) or not cards:
        raise ToolError('tasks must be a non-empty list of cards.')
    if len(cards) > 200:
        raise ToolError('At most 200 cards per call.')
    allowed = set(CARD_PARAMS)
    prepared = []
    for n, card in enumerate(cards, 1):
        if not isinstance(card, dict):
            raise ToolError(f'Card {n} must be an object with at least a title.')
        unknown = set(card) - allowed
        if unknown:
            raise ToolError(f'Card {n}: unknown field(s) {", ".join(sorted(unknown))}')
        if not str(card.get('title') or '').strip():
            raise ToolError(f'Card {n} needs a title.')
        try:
            fields, checklist = _card_fields(project, card)
        except ToolError as e:
            raise ToolError(f'Card {n} ({card.get("title")}): {e}')
        prepared.append((card['title'], fields, checklist))
    # All or nothing: every card is checked above before any is saved.
    with transaction.atomic():
        made = [task_rules.create_task(project, ctx.user, title=t, checklist=c, **f) for t, f, c in prepared]
    return {
        'created': len(made),
        'project': project.name,
        'codes': [t.code for t in made if t.code],
        'per_status': {s: sum(1 for t in made if t.status == s) for s in STATUSES if any(t.status == s for t in made)},
        'cards': [{'id': str(t.id), 'code': t.code or None, 'title': t.title,
                   'sprint': t.sprint.name if t.sprint_id else None} for t in made],
    }


register(Tool(
    'create_tasks_bulk', 'Create many board tasks',
    'Load up to 200 cards onto one project\'s board in a single call, e.g. a whole plan for '
    'Weeks 2-5 into the backlog. Every card is checked first and nothing is saved if any card is '
    'wrong (all or nothing). Each card takes the same fields as create_task; give status '
    '"backlog" and a sprint_id for cards in later weeks. Codes are given in order. Read back the '
    'count and weeks and get a yes before calling.',
    _create_tasks_bulk,
    {
        'project_id': s_uuid('project'),
        'tasks': {'type': 'array', 'maxItems': 200, 'description': 'The cards to create, in order.',
                  'items': {'type': 'object', 'properties': CARD_PARAMS, 'required': ['title'],
                            'additionalProperties': False}},
    },
    required=('project_id', 'tasks'), write=True,
))


def _sprint_out(sp):
    counts = {r['status']: r['n'] for r in sp.tasks.values('status').annotate(n=Count('id')).order_by()}
    return {'id': str(sp.id), 'name': sp.name, 'goal': sp.goal, 'order': sp.order,
            'start_date': str(sp.start_date), 'end_date': str(sp.end_date), 'status': sp.status,
            'cards': sum(counts.values()), 'per_status': counts}


def _list_sprints(ctx, args):
    project = _project(args['project_id'])
    return {'project': project.name,
            'team_lead': project.team_lead.name if project.team_lead_id else None,
            'task_prefix': project.task_prefix or None,
            'next_code': f'{project.task_prefix}-{project.next_task_number:03d}' if project.task_prefix else None,
            'weeks': [_sprint_out(sp) for sp in project.sprints.all()]}


register(Tool(
    'list_sprints', 'Project weeks',
    'The weeks (sprints) planned for a project, with dates, status (planned, active, done) and '
    'how many cards each holds per column, plus the project\'s team lead and next task code.',
    _list_sprints,
    {'project_id': s_uuid('project')},
    required=('project_id',),
))


def _create_sprint(ctx, args):
    project = _project(args['project_id'])
    try:
        sp = task_rules.create_sprint(project, name=args['name'], goal=args.get('goal', ''),
                                      start_date=date.fromisoformat(args['start_date']),
                                      end_date=date.fromisoformat(args['end_date']))
    except task_rules.TaskRuleError as e:
        raise ToolError(str(e))
    return {'created': True, 'week': _sprint_out(sp)}


register(Tool(
    'create_sprint', 'Add a week',
    'Add a week (sprint) to a project\'s plan, e.g. "Week 3", 2026-11-30 to 2026-12-05. It starts '
    'as planned; start it with start_sprint.',
    _create_sprint,
    {'project_id': s_uuid('project'), 'name': s_str('Week name, e.g. "Week 3".'),
     'start_date': s_date('First day.'), 'end_date': s_date('Last day.'),
     'goal': s_str('What the week should deliver.')},
    required=('project_id', 'name', 'start_date', 'end_date'), write=True,
))


def _sprint_by_id(sprint_id):
    sp = ProjectSprint.objects.select_related('project').filter(pk=sprint_id).first()
    if sp is None:
        raise ToolError('No week with that id. Use list_sprints.')
    return sp


def _start_sprint(ctx, args):
    sp = _sprint_by_id(args['sprint_id'])
    try:
        result = task_rules.start_sprint(sp, ctx.user)
    except task_rules.TaskRuleError as e:
        raise ToolError(str(e))
    return {'started': sp.name, 'project': sp.project.name, 'moved_to_todo': result['moved'],
            'cards_without_owner': result['unassigned']}


register(Tool(
    'start_sprint', 'Start a week',
    'Start a planned week: its backlog cards move to To Do (the team and client see them) and '
    'each card owner gets one notification. Only one week per project can run at a time. '
    'Confirm with the user first.',
    _start_sprint,
    {'sprint_id': s_uuid('week (from list_sprints)')},
    required=('sprint_id',), write=True,
))


def _close_sprint(ctx, args):
    sp = _sprint_by_id(args['sprint_id'])
    try:
        result = task_rules.close_sprint(sp, ctx.user, args.get('carry_over', 'next'))
    except task_rules.TaskRuleError as e:
        raise ToolError(str(e))
    return {'closed': sp.name, 'project': sp.project.name, **result}


register(Tool(
    'close_sprint', 'Close a week',
    'Close the running week. Open cards move to the next week (carry_over "next", keeping their '
    'column) or back to the backlog ("backlog"). Returns how many were completed and carried. '
    'Confirm with the user first.',
    _close_sprint,
    {'sprint_id': s_uuid('week (from list_sprints)'),
     'carry_over': s_str('Where open cards go (default next).', ['next', 'backlog'])},
    required=('sprint_id',), write=True,
))


def _configure_project_board(ctx, args):
    import re
    project = _project(args['project_id'])
    changed = []
    if args.get('clear_team_lead'):
        project.team_lead = None
        changed.append('team_lead')
    elif args.get('team_lead'):
        member = project.team_members.filter(pk=args['team_lead']).first()
        if member is None:
            raise ToolError('The team lead must be on the project team. Add them to the team first '
                            '(project form) or pick someone from get_project\'s team.')
        project.team_lead = member
        changed.append('team_lead')
    if 'task_prefix' in args:
        prefix = re.sub(r'[^A-Za-z0-9]', '', args['task_prefix']).upper()[:6]
        project.task_prefix = prefix
        changed.append('task_prefix')
    if 'next_task_number' in args:
        project.next_task_number = args['next_task_number']
        changed.append('next_task_number')
    if 'members_can_complete' in args:
        project.members_can_complete = args['members_can_complete']
        changed.append('members_can_complete')
    if not changed:
        raise ToolError('Nothing to change.')
    project.save()
    backfilled = task_rules.backfill_codes(project) if 'task_prefix' in changed else 0
    project.refresh_from_db()
    return {'updated': changed, 'project': project.name,
            'team_lead': project.team_lead.name if project.team_lead_id else None,
            'task_prefix': project.task_prefix or None,
            'next_code': f'{project.task_prefix}-{project.next_task_number:03d}' if project.task_prefix else None,
            'members_can_complete': project.members_can_complete,
            'existing_cards_coded_from_title': backfilled}


register(Tool(
    'configure_project_board', 'Board settings',
    'Set a project\'s board settings: team lead (must be on the team; they see the backlog, plan '
    'and start weeks and move any card), task code prefix (ALW gives ALW-017) and next number, '
    'and whether members may move their own cards to Completed. Setting a prefix also gives codes '
    'to cards whose titles already start with it ("ALW-004 Pages" becomes code ALW-004, title "Pages").',
    _configure_project_board,
    {'project_id': s_uuid('project'),
     'team_lead': s_uuid('team member to lead the project'),
     'clear_team_lead': s_bool('Remove the team lead.'),
     'task_prefix': s_str('Code prefix, letters/digits up to 6, e.g. ALW ("" removes it).'),
     'next_task_number': s_int('Number the next card gets.', 1, 99999),
     'members_can_complete': s_bool('Members may move their own cards to Completed.')},
    required=('project_id',), write=True,
))
