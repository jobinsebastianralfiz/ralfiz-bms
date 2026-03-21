"""
GymPro Licensing — Online API-based license management.

Ralfiz centrally manages all gym client licenses. Each GymPro deployment
validates against this API on startup + periodically.

No RSA crypto needed — pure online validation with domain binding.
"""

import uuid
import hashlib
import secrets
from datetime import timedelta

from django.db import models
from django.utils import timezone


class GymLicense(models.Model):
    """A license issued to a gym client for their GymPro deployment."""

    LICENSE_TYPE_CHOICES = [
        ('trial', 'Trial (30 days)'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('half_yearly', 'Half Yearly'),
        ('yearly', 'Yearly'),
        ('lifetime', 'Lifetime'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended'),
        ('revoked', 'Revoked'),
    ]

    BILLING_CYCLE_CHOICES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('half_yearly', 'Half Yearly'),
        ('yearly', 'Yearly'),
        ('lifetime', 'Lifetime'),
    ]

    MODULE_CHOICES = [
        ('members', 'Member Management'),
        ('trainers', 'Trainer Management'),
        ('schedules', 'Session Scheduling'),
        ('attendance', 'Attendance (QR + GPS)'),
        ('fees', 'Fee Engine'),
        ('store', 'Store / POS'),
        ('salary', 'Salary Payroll'),
        ('expenses', 'Expense Tracking'),
        ('notifications', 'Push + WhatsApp'),
        ('reports', 'Reports & Analytics'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # ─── Client Link ──────────────────────────────────
    client = models.ForeignKey(
        'core.Client', on_delete=models.CASCADE,
        related_name='gympro_licenses', null=True, blank=True,
        help_text='Link to Ralfiz client record'
    )

    # ─── Gym Identity ─────────────────────────────────
    gym_name = models.CharField(max_length=255, help_text='Name of the gym')
    gym_owner_name = models.CharField(max_length=255, blank=True)
    gym_email = models.EmailField(help_text='Primary contact email')
    gym_phone = models.CharField(max_length=20, blank=True)
    gym_address = models.TextField(blank=True)

    # ─── License Key & Domain ─────────────────────────
    license_key = models.CharField(
        max_length=64, unique=True, db_index=True,
        help_text='Unique license key sent to the gym (GYM-XXXX-XXXX-XXXX)'
    )
    api_domain = models.CharField(
        max_length=255, unique=True,
        help_text='The gym\'s API domain (e.g., api.fitzone.com). License is bound to this domain.'
    )
    landing_domain = models.CharField(max_length=255, blank=True, help_text='Landing page domain')

    # ─── License Config ───────────────────────────────
    license_type = models.CharField(max_length=20, choices=LICENSE_TYPE_CHOICES, default='yearly')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', db_index=True)
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLE_CHOICES, default='yearly')
    auto_renew = models.BooleanField(default=False)
    grace_period_days = models.PositiveIntegerField(default=7)

    # ─── Validity ─────────────────────────────────────
    issued_at = models.DateTimeField(auto_now_add=True)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField()
    last_renewed_at = models.DateTimeField(null=True, blank=True)
    renewal_count = models.PositiveIntegerField(default=0)

    # ─── Module Control ───────────────────────────────
    enabled_modules = models.JSONField(
        default=list,
        help_text='List of enabled module keys. Empty = all modules enabled.',
        blank=True,
    )
    max_members = models.PositiveIntegerField(
        default=0, help_text='Max members allowed. 0 = unlimited.'
    )
    max_trainers = models.PositiveIntegerField(
        default=0, help_text='Max trainers allowed. 0 = unlimited.'
    )

    # ─── Deployment Info ──────────────────────────────
    server_ip = models.GenericIPAddressField(null=True, blank=True)
    deployment_notes = models.TextField(blank=True)

    # ─── Tracking ─────────────────────────────────────
    last_check_at = models.DateTimeField(null=True, blank=True, help_text='Last time gym validated license')
    last_check_ip = models.GenericIPAddressField(null=True, blank=True)
    total_checks = models.PositiveIntegerField(default=0)

    # ─── Meta ─────────────────────────────────────────
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'GymPro License'
        verbose_name_plural = 'GymPro Licenses'

    def __str__(self):
        return f"{self.gym_name} — {self.license_key} ({self.status})"

    def save(self, *args, **kwargs):
        if not self.license_key:
            self.license_key = self.generate_license_key()
        if not self.valid_until:
            self.valid_until = self._calculate_expiry()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_license_key():
        """Generate a unique license key: GYM-XXXX-XXXX-XXXX"""
        parts = [secrets.token_hex(2).upper() for _ in range(3)]
        return f"GYM-{parts[0]}-{parts[1]}-{parts[2]}"

    def _calculate_expiry(self):
        """Calculate expiry based on license type."""
        base = self.valid_from or timezone.now()
        durations = {
            'trial': timedelta(days=30),
            'monthly': timedelta(days=30),
            'quarterly': timedelta(days=90),
            'half_yearly': timedelta(days=180),
            'yearly': timedelta(days=365),
            'lifetime': timedelta(days=36500),  # 100 years
        }
        return base + durations.get(self.license_type, timedelta(days=365))

    def is_valid(self):
        """Check if license is currently valid."""
        if self.status not in ('active',):
            return False
        now = timezone.now()
        return self.valid_from <= now <= self.valid_until

    def is_in_grace_period(self):
        """Check if license is expired but within grace period."""
        if self.status != 'active':
            return False
        now = timezone.now()
        if now <= self.valid_until:
            return False  # Not expired yet
        grace_end = self.valid_until + timedelta(days=self.grace_period_days)
        return now <= grace_end

    def days_remaining(self):
        """Days until expiry. Negative = days overdue."""
        delta = self.valid_until - timezone.now()
        return delta.days

    def renew(self, extend_days=None):
        """Extend license validity."""
        if extend_days:
            self.valid_until += timedelta(days=extend_days)
        else:
            # Use billing cycle duration
            durations = {
                'monthly': 30, 'quarterly': 90, 'half_yearly': 180,
                'yearly': 365, 'lifetime': 36500,
            }
            days = durations.get(self.billing_cycle, 365)
            # Extend from now or from valid_until (whichever is later)
            base = max(self.valid_until, timezone.now())
            self.valid_until = base + timedelta(days=days)

        self.status = 'active'
        self.renewal_count += 1
        self.last_renewed_at = timezone.now()
        self.save()

    def validate_domain(self, domain):
        """Check if the requesting domain matches the licensed domain."""
        # Strip protocol and trailing slashes
        clean = domain.lower().strip().rstrip('/')
        for prefix in ['https://', 'http://']:
            if clean.startswith(prefix):
                clean = clean[len(prefix):]
        licensed = self.api_domain.lower().strip().rstrip('/')
        for prefix in ['https://', 'http://']:
            if licensed.startswith(prefix):
                licensed = licensed[len(prefix):]
        return clean == licensed

    def get_enabled_modules(self):
        """Return list of enabled module keys. Empty list = all enabled."""
        if not self.enabled_modules:
            return [m[0] for m in self.MODULE_CHOICES]  # All modules
        return self.enabled_modules

    def record_check(self, ip_address=None):
        """Record a license validation check."""
        self.last_check_at = timezone.now()
        self.last_check_ip = ip_address
        self.total_checks += 1
        self.save(update_fields=['last_check_at', 'last_check_ip', 'total_checks'])


class GymLicenseLog(models.Model):
    """Audit log for all license events."""

    EVENT_CHOICES = [
        ('validate', 'Validate'),
        ('check', 'Check'),
        ('renew', 'Renew'),
        ('expire', 'Expire'),
        ('revoke', 'Revoke'),
        ('suspend', 'Suspend'),
        ('reactivate', 'Reactivate'),
        ('create', 'Create'),
        ('update', 'Update'),
        ('domain_mismatch', 'Domain Mismatch'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    license = models.ForeignKey(
        GymLicense, on_delete=models.CASCADE, related_name='logs'
    )
    event = models.CharField(max_length=30, choices=EVENT_CHOICES)
    status = models.CharField(max_length=20)  # Result status
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    domain = models.CharField(max_length=255, blank=True)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.license.gym_name} — {self.event} ({self.status})"
