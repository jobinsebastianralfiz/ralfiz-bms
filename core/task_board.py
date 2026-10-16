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
