"""Shared pieces of the Velora-style task board (staff board and client portal)."""
from .models import Task

# Soft tag / avatar colours, picked by a stable hash of the text.
BOARD_TONES = ['violet', 'green', 'orange', 'blue', 'pink', 'teal']


def tone_for(text):
    return BOARD_TONES[sum(map(ord, text)) % len(BOARD_TONES)] if text else ''


def board_columns(tasks):
    """Decorate tasks for the card template and split them into status columns.

    Expects comment_total, attachment_total and open_issue_total annotations.
    """
    tasks = list(tasks)
    for t in tasks:
        t.tag = t.category or (t.assigned_to.get_role_display() if t.assigned_to else '')
        t.tag_tone = tone_for(t.tag)
        t.progress_left = 100 - t.progress_percent
        if t.assigned_to:
            t.avatar_tone = tone_for(t.assigned_to.name)
    return tasks, [
        {'key': key, 'label': label, 'tasks': [t for t in tasks if t.status == key]}
        for key, label in Task.STATUS_CHOICES
    ]


def decorate_team(members):
    members = list(members)
    for m in members:
        m.avatar_tone = tone_for(m.name)
    return members


def project_progress(project):
    """Percent complete shown to the client.

    A client-visible progress update wins. Otherwise it is the average of the
    tasks' own progress, and it only reaches 100% once the project itself is
    marked completed (a board with one finished task is not a finished project).
    """
    latest = project.updates.filter(progress_percentage__isnull=False, is_visible_to_client=True).first()
    if latest:
        return latest.progress_percentage
    if project.status == 'completed':
        return 100
    tasks = list(project.tasks.all())
    if not tasks:
        return 0
    pct = round(sum(t.progress_percent for t in tasks) / len(tasks))
    return min(pct, 99)
