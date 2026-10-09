"""Internship enrolment: HR sends a student a personal link, the student fills
in their own details and documents, and HR approves the application into an
intern Employee with a staff-portal login -- no re-typing from paper forms.

Uploaded documents (ID proof, college letter...) are personal data, so they go
to a private folder that the public /media/ route refuses to serve; HR reads
them through a login-protected view.
"""

import secrets
import uuid
from datetime import timedelta
from pathlib import Path
from urllib.parse import quote

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.utils import timezone

PRIVATE_DIR = 'private'


def private_storage():
    """Files under MEDIA_ROOT/private/, which config/urls.py never serves."""
    return FileSystemStorage(location=str(Path(settings.MEDIA_ROOT) / PRIVATE_DIR), base_url=None)


def default_enrolment_expiry():
    return timezone.now() + timedelta(days=14)


def generate_enrolment_token():
    return secrets.token_urlsafe(32)


def _document_path(instance, filename, kind):
    return f'enrolments/{instance.pk}/{kind}{Path(filename).suffix.lower()[:6]}'


def enrolment_photo_path(instance, filename):
    return _document_path(instance, filename, 'photo')


def enrolment_id_proof_path(instance, filename):
    return _document_path(instance, filename, 'id_proof')


def enrolment_resume_path(instance, filename):
    return _document_path(instance, filename, 'resume')


def enrolment_college_letter_path(instance, filename):
    return _document_path(instance, filename, 'college_letter')


def duration_label(months):
    if not months:
        return ''
    return f'{months} month' if str(months) == '1' else f'{months} months'


WORK_MODE_CHOICES = [
    ('onsite', 'Onsite (at our office)'),
    ('hybrid', 'Hybrid'),
    ('remote', 'Remote'),
]


def default_tracks():
    return [
        {'label': 'Software Development', 'department': 'engineering'},
        {'label': 'UI/UX & Graphic Design', 'department': 'design'},
        {'label': 'Digital Marketing', 'department': 'marketing'},
        {'label': 'Data Analytics', 'department': 'engineering'},
    ]


def default_work_modes():
    return ['onsite']


def default_durations():
    return [1, 2, 3, 6]


class EnrolmentSettings(models.Model):
    """What the enrolment form offers, set by HR at /hr/enrolments/settings/."""

    work_modes = models.JSONField(default=default_work_modes,
                                  help_text='Keys from WORK_MODE_CHOICES to offer')
    tracks = models.JSONField(default=default_tracks,
                              help_text='[{"label": ..., "department": Employee department}]')
    allow_other_track = models.BooleanField(default=True,
                                            help_text='Offer "Other" with a free-text area')
    durations = models.JSONField(default=default_durations, help_text='Month counts to offer')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Enrolment settings'
        verbose_name_plural = 'Enrolment settings'

    def __str__(self):
        return 'Enrolment settings'

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def work_mode_choices(self):
        return [(k, label) for k, label in WORK_MODE_CHOICES if k in self.work_modes]

    def track_choices(self):
        choices = [(t['label'], t['label']) for t in self.tracks]
        if self.allow_other_track:
            choices.append((OTHER_TRACK, 'Other'))
        return choices

    def duration_choices(self):
        return [(str(n), duration_label(n)) for n in sorted(self.durations)]

    def department_for(self, track):
        for t in self.tracks:
            if t['label'].casefold() == (track or '').casefold():
                return t['department']
        return 'other'


#: Form value of the "Other" area; the student's own text goes in track_other.
OTHER_TRACK = '__other__'


class InternEnrolment(models.Model):
    STATUS_SENT = 'sent'
    STATUS_OPENED = 'opened'
    STATUS_SUBMITTED = 'submitted'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (STATUS_SENT, 'Link sent'),
        (STATUS_OPENED, 'Opened'),
        (STATUS_SUBMITTED, 'To review'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]
    OPEN_STATUSES = (STATUS_SENT, STATUS_OPENED)

    YEAR_CHOICES = [
        ('1', '1st year'),
        ('2', '2nd year'),
        ('3', '3rd year'),
        ('4', '4th year'),
        ('5', '5th year'),
        ('graduated', 'Graduated'),
    ]
    WORK_MODE_CHOICES = WORK_MODE_CHOICES

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token = models.CharField(max_length=64, unique=True, db_index=True, default=generate_enrolment_token)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_SENT, db_index=True)

    # ---- Invite (filled by HR) ----
    invite_name = models.CharField(max_length=200)
    invite_phone = models.CharField(max_length=20, blank=True)
    invite_email = models.EmailField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='enrolments_sent')
    sent_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=default_enrolment_expiry)
    first_opened_at = models.DateTimeField(null=True, blank=True)

    # ---- Personal & contact (filled by the student) ----
    full_name = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    whatsapp = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    guardian_name = models.CharField(max_length=200, blank=True)
    guardian_phone = models.CharField(max_length=20, blank=True)

    # ---- Education ----
    college_name = models.CharField(max_length=300, blank=True)
    course = models.CharField(max_length=200, blank=True, help_text='Course and branch, e.g. B.Tech CSE')
    year_of_study = models.CharField(max_length=10, choices=YEAR_CHOICES, blank=True)
    register_number = models.CharField(max_length=50, blank=True)

    # ---- Internship ----
    #: The area's name as offered when the student applied (areas are set by HR
    #: in EnrolmentSettings, so a later rename never rewrites old applications).
    track = models.CharField(max_length=200, blank=True)
    track_other = models.CharField(max_length=200, blank=True)
    preferred_start_date = models.DateField(null=True, blank=True)
    duration_months = models.CharField(max_length=2, blank=True)
    work_mode = models.CharField(max_length=10, choices=WORK_MODE_CHOICES, blank=True)
    skills = models.TextField(blank=True, help_text='What the student already knows')

    # ---- Documents (private) ----
    photo = models.ImageField(upload_to=enrolment_photo_path, storage=private_storage, blank=True)
    id_proof = models.FileField(upload_to=enrolment_id_proof_path, storage=private_storage, blank=True)
    resume = models.FileField(upload_to=enrolment_resume_path, storage=private_storage, blank=True)
    college_letter = models.FileField(upload_to=enrolment_college_letter_path, storage=private_storage,
                                      blank=True)

    # ---- Submission / review ----
    submitted_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='enrolments_reviewed')
    rejection_reason = models.TextField(blank=True)
    employee = models.OneToOneField('employees.Employee', on_delete=models.SET_NULL, null=True,
                                    blank=True, related_name='enrolment')
    hr_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f'{self.display_name} ({self.get_status_display()})'

    # ---- State ----
    @property
    def display_name(self):
        return self.full_name or self.invite_name

    @property
    def is_expired(self):
        return self.status in self.OPEN_STATUSES and timezone.now() > self.expires_at

    @property
    def is_open(self):
        return self.status in self.OPEN_STATUSES and not self.is_expired

    @property
    def status_label(self):
        return 'Expired' if self.is_expired else self.get_status_display()

    @property
    def status_css(self):
        if self.is_expired:
            return 'background: var(--warning-bg); color: var(--warning);'
        return {
            self.STATUS_SENT: 'background: var(--info-bg); color: var(--info);',
            self.STATUS_OPENED: 'background: var(--info-bg); color: var(--info);',
            self.STATUS_SUBMITTED: 'background: var(--warning-bg); color: var(--warning);',
            self.STATUS_APPROVED: 'background: var(--success-bg); color: var(--success);',
            self.STATUS_REJECTED: 'background: var(--danger-bg); color: var(--danger);',
        }.get(self.status, 'background: var(--gray-100); color: var(--gray-600);')

    @property
    def track_label(self):
        return self.track_other or self.track

    @property
    def duration_label(self):
        return duration_label(self.duration_months)

    def mark_opened(self):
        if self.first_opened_at is None:
            self.first_opened_at = timezone.now()
            if self.status == self.STATUS_SENT:
                self.status = self.STATUS_OPENED
            self.save(update_fields=['first_opened_at', 'status', 'updated_at'])

    def documents(self):
        """(field name, label, file) for every uploaded document."""
        labels = (('photo', 'Photo'), ('id_proof', 'ID proof'), ('resume', 'Resume'),
                  ('college_letter', 'College letter / NOC'))
        return [(name, label, getattr(self, name)) for name, label in labels if getattr(self, name)]

    # ---- Links ----
    def public_path(self):
        return f'/enrol/{self.token}/'

    def public_url(self, request=None):
        return request.build_absolute_uri(self.public_path()) if request else self.public_path()

    def whatsapp_url(self, request=None):
        """wa.me link with the invite prefilled. Empty when HR gave no phone."""
        digits = ''.join(ch for ch in (self.invite_phone or '') if ch.isdigit())
        if not digits:
            return ''
        if len(digits) == 10:
            digits = '91' + digits
        message = (
            f'Hi {self.invite_name},\n\n'
            'Welcome to Ralfiz Technologies! Please fill in your internship enrolment '
            f'form here:\n{self.public_url(request)}\n\n'
            'Keep your photo and ID proof ready. The link is personal to you.'
        )
        return f'https://wa.me/{digits}?text={quote(message)}'

    # ---- Review ----
    def suggested_username(self):
        base = (self.email.split('@')[0] if self.email else self.display_name.split(' ')[0]).lower()
        base = ''.join(ch for ch in base if ch.isalnum() or ch in '._') or 'intern'
        username, n = base, 1
        while User.objects.filter(username__iexact=username).exists():
            n += 1
            username = f'{base}{n}'
        return username

    def approve(self, by, *, username, password, joining_date, department, designation):
        """Create the intern's login and Employee record from the submitted form.

        Raises ValueError with a message HR can act on.
        """
        from django.core.files.base import ContentFile
        from django.db import transaction

        from .models import Employee

        if self.status != self.STATUS_SUBMITTED:
            raise ValueError('Only a submitted enrolment can be approved.')
        if User.objects.filter(username__iexact=username).exists():
            raise ValueError(f'The username "{username}" is already taken.')

        first, _, last = self.full_name.partition(' ')
        notes = '\n'.join(line for line in (
            'From enrolment form:',
            f'College: {self.college_name}',
            f'Course: {self.course} ({self.get_year_of_study_display()})',
            f'Register no: {self.register_number}' if self.register_number else '',
            f'Track: {self.track_label}, {self.duration_label}',
            f'Guardian: {self.guardian_name} {self.guardian_phone}',
            f'WhatsApp: {self.whatsapp}' if self.whatsapp else '',
            f'Skills: {self.skills}' if self.skills else '',
        ) if line)

        with transaction.atomic():
            user = User.objects.create_user(username=username, password=password, email=self.email,
                                            first_name=first[:150], last_name=last[:150])
            employee = Employee.objects.create(
                user=user,
                employee_id=Employee.next_employee_id(),
                employment_type='intern',
                role='intern',
                department=department,
                designation=designation,
                phone=self.phone,
                emergency_contact=self.guardian_phone,
                address=self.address,
                date_of_birth=self.date_of_birth,
                joining_date=joining_date,
                work_mode=self.work_mode or 'onsite',
                status='active',
                notes=notes,
            )
            if self.photo:
                with self.photo.open('rb') as fh:
                    employee.profile_photo.save(f'{employee.employee_id}{Path(self.photo.name).suffix}',
                                                ContentFile(fh.read()), save=True)
            self.employee = employee
            self.status = self.STATUS_APPROVED
            self.reviewed_by = by
            self.reviewed_at = timezone.now()
            self.save()
        return employee

    def reject(self, by, reason=''):
        if self.status != self.STATUS_SUBMITTED:
            raise ValueError('Only a submitted enrolment can be rejected.')
        self.status = self.STATUS_REJECTED
        self.rejection_reason = reason
        self.reviewed_by = by
        self.reviewed_at = timezone.now()
        self.save()
