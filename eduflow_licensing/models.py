"""
EduFlow Licensing — Online API-based license management.

Mirrors the GymPro licensing system but tailored for EduFlow institute
deployments. Each EduFlow FastAPI backend validates against this server
on activation and periodically thereafter.
"""

import uuid
import secrets
from datetime import timedelta

from django.db import models
from django.utils import timezone


class EduFlowLicense(models.Model):
    """A license issued to an institute for their EduFlow deployment."""

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
        ('users', 'User Management'),
        ('courses', 'Course Builder'),
        ('batches', 'Batch Management'),
        ('library', 'Content Library'),
        ('live_sessions', 'Live Sessions'),
        ('assignments', 'Assignments & Grading'),
        ('attendance', 'Attendance'),
        ('fees', 'Fee Management'),
        ('expenses', 'Expense Tracking'),
        ('coupons', 'Coupons & Discounts'),
        ('analytics', 'Analytics & Reports'),
        ('notifications', 'Notifications'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # ─── Client Link ──────────────────────────────────
    client = models.ForeignKey(
        'core.Client', on_delete=models.CASCADE,
        related_name='eduflow_licenses', null=True, blank=True,
        help_text='Link to Ralfiz client record',
    )

    # ─── Institute Identity ───────────────────────────
    institute_name = models.CharField(max_length=255, help_text='Name of the institute')
    institute_owner_name = models.CharField(max_length=255, blank=True)
    institute_email = models.EmailField(help_text='Primary contact email')
    institute_phone = models.CharField(max_length=20, blank=True)
    institute_address = models.TextField(blank=True)

    # ─── License Key & Domain ─────────────────────────
    license_key = models.CharField(
        max_length=64, unique=True, db_index=True,
        help_text="Unique license key (EDU-XXXX-XXXX-XXXX)",
    )
    api_domain = models.CharField(
        max_length=255, blank=True, default='',
        help_text="Bound API domain. Empty until first activation.",
    )
    landing_domain = models.CharField(max_length=255, blank=True)

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
        default=list, blank=True,
        help_text='List of enabled module keys. Empty = all modules enabled.',
    )
    max_users = models.PositiveIntegerField(default=0, help_text='0 = unlimited')
    max_batches = models.PositiveIntegerField(default=0, help_text='0 = unlimited')

    # ─── Deployment Info ──────────────────────────────
    server_ip = models.GenericIPAddressField(null=True, blank=True)
    deployment_notes = models.TextField(blank=True)

    # ─── Tracking ─────────────────────────────────────
    last_check_at = models.DateTimeField(null=True, blank=True)
    last_check_ip = models.GenericIPAddressField(null=True, blank=True)
    total_checks = models.PositiveIntegerField(default=0)

    # ─── Meta ─────────────────────────────────────────
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'EduFlow License'
        verbose_name_plural = 'EduFlow Licenses'

    def __str__(self):
        return f"{self.institute_name} — {self.license_key} ({self.status})"

    def save(self, *args, **kwargs):
        if not self.license_key:
            self.license_key = self.generate_license_key()
        if not self.valid_until:
            self.valid_until = self._calculate_expiry()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_license_key():
        parts = [secrets.token_hex(2).upper() for _ in range(3)]
        return f"EDU-{parts[0]}-{parts[1]}-{parts[2]}"

    def _calculate_expiry(self):
        base = self.valid_from or timezone.now()
        durations = {
            'trial': timedelta(days=30),
            'monthly': timedelta(days=30),
            'quarterly': timedelta(days=90),
            'half_yearly': timedelta(days=180),
            'yearly': timedelta(days=365),
            'lifetime': timedelta(days=36500),
        }
        return base + durations.get(self.license_type, timedelta(days=365))

    def is_valid(self):
        if self.status != 'active':
            return False
        now = timezone.now()
        return self.valid_from <= now <= self.valid_until

    def is_in_grace_period(self):
        if self.status != 'active':
            return False
        now = timezone.now()
        if now <= self.valid_until:
            return False
        grace_end = self.valid_until + timedelta(days=self.grace_period_days)
        return now <= grace_end

    def days_remaining(self):
        return (self.valid_until - timezone.now()).days

    def renew(self, extend_days=None):
        if extend_days:
            self.valid_until += timedelta(days=extend_days)
        else:
            durations = {
                'monthly': 30, 'quarterly': 90, 'half_yearly': 180,
                'yearly': 365, 'lifetime': 36500,
            }
            days = durations.get(self.billing_cycle, 365)
            base = max(self.valid_until, timezone.now())
            self.valid_until = base + timedelta(days=days)

        self.status = 'active'
        self.renewal_count += 1
        self.last_renewed_at = timezone.now()
        self.save()

    def validate_domain(self, domain):
        def normalize(d):
            d = (d or '').lower().strip().rstrip('/')
            for prefix in ('https://', 'http://'):
                if d.startswith(prefix):
                    d = d[len(prefix):]
            d_no_port = d.split(':')[0] if ':' in d else d
            return d, d_no_port

        clean, clean_no_port = normalize(domain)
        licensed, licensed_no_port = normalize(self.api_domain)
        return clean == licensed or clean_no_port == licensed_no_port

    def get_enabled_modules(self):
        if not self.enabled_modules:
            return [m[0] for m in self.MODULE_CHOICES]
        return self.enabled_modules

    def record_check(self, ip_address=None):
        self.last_check_at = timezone.now()
        self.last_check_ip = ip_address
        self.total_checks += 1
        self.save(update_fields=['last_check_at', 'last_check_ip', 'total_checks'])


class EduFlowLicenseLog(models.Model):
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
    license = models.ForeignKey(EduFlowLicense, on_delete=models.CASCADE, related_name='logs')
    event = models.CharField(max_length=30, choices=EVENT_CHOICES)
    status = models.CharField(max_length=20)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    domain = models.CharField(max_length=255, blank=True)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.license.institute_name} — {self.event} ({self.status})"
