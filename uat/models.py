"""
UAT (user acceptance testing) for any Ralfiz product or client project.

A plan (e.g. "Shop Manager UAT") has sections of test cases. Each section is given to one or more
testers (employees / interns). Testers mark every case Pass / Fail / Blocked in the staff portal,
with a note and a screenshot. Ralfiz staff follow progress and handle problems in the BMS dashboard.
"""

import os
import uuid

from django.db import models
from django.utils import timezone

from core.models import _private_storage


class UATPlan(models.Model):
    STATUS_CHOICES = [('active', 'In testing'), ('closed', 'Completed')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    product = models.CharField(max_length=120, blank=True, help_text='Product or project under test')
    site_url = models.URLField(blank=True, help_text='Where testers do the testing')
    instructions = models.TextField(blank=True, help_text='Shown to testers at the top of the plan')
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    xp_reward = models.PositiveIntegerField(
        default=0, help_text='XP each tester earns once every test in their sections is marked. 0 = no reward.')
    testers = models.ManyToManyField('employees.Employee', blank=True, related_name='uat_plans',
                                     help_text='Everyone testing this plan (sections with no tester go to all of them)')
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    completed_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'UAT plan'

    @property
    def is_completed(self):
        return self.status == 'closed'

    def set_completed(self, done, user=None):
        """Mark the whole UAT completed (testers no longer see it) or put it back into testing."""
        self.status = 'closed' if done else 'active'
        self.completed_at = timezone.now() if done else None
        self.completed_by = user if done else None

    def __str__(self):
        return self.name

    def cases(self):
        return UATCase.objects.filter(section__plan=self)


class UATSection(models.Model):
    plan = models.ForeignKey(UATPlan, on_delete=models.CASCADE, related_name='sections')
    key = models.CharField(max_length=20, blank=True)
    name = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=0)
    assignees = models.ManyToManyField('employees.Employee', blank=True, related_name='uat_sections',
                                       help_text='Empty = every tester on the plan')
    starts_after = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='+',
                                     help_text='Locked for testers until every test in that section is marked '
                                               '(e.g. shop setup before billing)')

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f'{self.plan.name} · {self.name}'

    def marked_count(self):
        """How many of this section's tests have a result from anyone."""
        return self.cases.filter(results__isnull=False).distinct().count()

    def waiting_on(self):
        """The section that must be finished first, or None when this one is open."""
        before = self.starts_after
        if before and before.marked_count() < before.cases.count():
            return before
        return None

    def testers(self):
        people = list(self.assignees.all())
        return people or list(self.plan.testers.all())

    def is_for(self, employee):
        return any(e.pk == employee.pk for e in self.testers())


class UATCase(models.Model):
    section = models.ForeignKey(UATSection, on_delete=models.CASCADE, related_name='cases')
    code = models.CharField(max_length=20)
    title = models.CharField(max_length=255)
    tags = models.JSONField(default=list, blank=True)
    steps = models.JSONField(default=list, blank=True, help_text='List of steps, in order')
    expected = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f'{self.code} {self.title}'


class UATResult(models.Model):
    STATUS_CHOICES = [('pass', 'Pass'), ('fail', 'Fail'), ('blocked', 'Blocked')]
    FIX_CHOICES = [('', 'Open'), ('fixed', 'Fixed – retest'), ('wont_fix', "Won't fix"), ('not_bug', 'Not a bug')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(UATCase, on_delete=models.CASCADE, related_name='results')
    tester = models.ForeignKey('employees.Employee', on_delete=models.CASCADE, related_name='uat_results')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    note = models.TextField(blank=True)
    screenshot = models.ImageField(upload_to='uat/screens/%Y/%m/', blank=True, null=True)
    # Ralfiz side, for Fail / Blocked
    fix_status = models.CharField(max_length=10, choices=FIX_CHOICES, blank=True, default='')
    fix_note = models.TextField(blank=True)
    fixed_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    fixed_at = models.DateTimeField(null=True, blank=True)
    history = models.JSONField(default=list, blank=True, help_text='Earlier results for this case')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        constraints = [models.UniqueConstraint(fields=['case', 'tester'], name='uat_one_result_per_tester')]

    def __str__(self):
        return f'{self.case.code} · {self.tester} · {self.status}'

    @property
    def needs_retest(self):
        return self.fix_status == 'fixed' and self.status != 'pass'

    def record(self, status, note, screenshot=None):
        """A tester (re)marks this case. Keeps the earlier result in history."""
        if self.pk and self.status:
            self.history = (self.history or [])[-9:] + [{
                'status': self.status, 'note': self.note, 'fix_status': self.fix_status,
                'at': (self.updated_at or timezone.now()).isoformat()}]
        self.status, self.note = status, note
        if screenshot:
            self.screenshot = screenshot
        if self.fix_status == 'fixed':  # retested after a fix: the new result stands on its own
            self.fix_status = ''
        self.save()


def uat_file_path(instance, filename):
    return f'uat_files/{instance.plan_id}/{uuid.uuid4().hex[:8]}_{os.path.basename(filename)}'


class UATFile(models.Model):
    """A file kept with a plan: the build or test data Ralfiz gives the testers, or a zip of logs /
    recordings a tester sends back. Stored under media/private/, downloaded only through a login view."""
    MAX_MB = 200

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plan = models.ForeignKey(UATPlan, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to=uat_file_path, storage=_private_storage, max_length=300)
    name = models.CharField(max_length=255)
    note = models.CharField(max_length=255, blank=True)
    size = models.BigIntegerField(default=0)
    uploaded_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    from_tester = models.BooleanField(default=False, help_text='Uploaded by a tester in the staff portal')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'UAT file'

    def __str__(self):
        return self.name

    @property
    def uploader_name(self):
        u = self.uploaded_by
        return (u.get_full_name() or u.username) if u else 'Ralfiz'
