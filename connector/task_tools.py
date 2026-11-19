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

from core.models import Project, Task, TaskActivity, TaskComment, TeamMember

from .dispatch import ToolError
from .tools import Tool, register, s_bool, s_date, s_int, s_str, s_uuid

STATUSES = [s for s, _ in Task.STATUS_CHOICES]
PRIORITIES = [p for p, _ in Task.PRIORITY_CHOICES]
OPEN = ('todo', 'in_progress', 'review')


def _log(task, user, verb, from_value='', to_value='', message='', visible=False, comment=None):
    TaskActivity.objects.create(
        task=task, actor=user, verb=verb, from_value=str(from_value)[:255],
        to_value=str(to_value)[:255], message=message[:500], is_visible_to_client=visible,
        related_comment=comment,
    )


def _task(task_id):
    task = Task.objects.select_related('project__client', 'assigned_to').filter(pk=task_id).first()
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
    }


def _detail(ctx, task):
    out = _summary(task)
    out.update(
        description=task.description,
        notes=task.notes,
        client=task.project.client.name if task.project.client_id else '',
        completed_date=str(task.completed_date) if task.completed_date else None,
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
    qs = Task.objects.select_related('project', 'assigned_to')
    if args.get('project_id'):
        if not Project.objects.filter(pk=args['project_id']).exists():
            raise ToolError('No project with that id. Use search to find it.')
        qs = qs.filter(project_id=args['project_id'])
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
    'Tasks on the project task board (/tasks/board/), grouped into To Do, In Progress, In Review '
    'and Completed columns. By default only open tasks (not completed). Filter by project, '
    'team member, status or text. Call for "what is pending on <project>", "what is <person> '
    'working on" or overdue tasks. These are board tasks, not daily tasks or work assignments.',
    _list_project_tasks,
    {
        'project_id': s_uuid('project'),
        'assigned_to': s_uuid('team member (from list_team_members or search)'),
        'status': s_str('Only this column.', STATUSES),
        'include_completed': s_bool('Also list completed tasks (ignored when status is given).'),
        'overdue_only': s_bool('Only open tasks past their due date.'),
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

def _create_task(ctx, args):
    project = Project.objects.filter(pk=args['project_id']).first()
    if project is None:
        raise ToolError('No project with that id. Use search to find it.')
    title = args['title'][:255]
    if not title:
        raise ToolError('title cannot be empty')
    task = Task(
        project=project, title=title,
        description=args.get('description', ''),
        status=args.get('status', 'todo'),
        priority=args.get('priority', 'medium'),
        category=args.get('label', '')[:60],
        due_date=date.fromisoformat(args['due_date']) if args.get('due_date') else None,
        assigned_to=_member(args['assigned_to']) if args.get('assigned_to') else None,
    )
    if task.status == 'completed':
        task.completed_date = timezone.now().date()
    task.save()
    _log(task, ctx.user, 'created', message='Created from Claude')
    return {'created': True, 'task': _detail(ctx, task)}


register(Tool(
    'create_task', 'Create board task',
    'Add a task card to a project\'s task board. It starts in To Do unless a status is given.',
    _create_task,
    {
        'project_id': s_uuid('project'),
        'title': s_str('Task title.'),
        'description': s_str('What needs doing.'),
        'assigned_to': s_uuid('team member (from list_team_members or search)'),
        'priority': s_str('Priority (default medium).', PRIORITIES),
        'status': s_str('Column to start in (default todo).', STATUSES),
        'due_date': s_date('Due date.'),
        'label': s_str('Board label, e.g. "Website Design" or "Mobile App".'),
    },
    required=('project_id', 'title'), write=True,
))


def _update_task(ctx, args):
    task = _task(args['task_id'])
    changed = []

    if 'status' in args and args['status'] != task.status:
        old = task.status
        task.status = args['status']
        task.completed_date = timezone.now().date() if task.status == 'completed' else None
        _log(task, ctx.user, 'status_changed', from_value=old, to_value=task.status, visible=True)
        changed.append('status')
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

    if not changed:
        raise ToolError('Nothing to change: give at least one field to update.')
    task.save()
    return {'updated': changed, 'task': _detail(ctx, task)}


register(Tool(
    'update_task', 'Update board task',
    'Move a board task to another column, or change its priority, assignee, due date, title, '
    'description, label or progress. Status changes show in the client portal\'s activity, '
    'like moving the card on the board.',
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
