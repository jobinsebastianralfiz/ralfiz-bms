from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from core.models import Client
import re


class InternProfile(models.Model):
    """DEPRECATED: Use Employee model with employment_type='intern' instead.
    Kept for backwards compatibility during migration period."""
    INTERN_TYPE_CHOICES = [
        ('digital', 'Digital Marketing'),
        ('field', 'Field Marketing'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('completed', 'Completed'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='intern_profile'
    )
    intern_type = models.CharField(max_length=10, choices=INTERN_TYPE_CHOICES)
    supervisor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='supervised_interns'
    )
    default_commission_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=5.00
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    joining_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Intern Profile'
        verbose_name_plural = 'Intern Profiles'

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.get_intern_type_display()}"


class Lead(models.Model):
    STATUS_CHOICES = [
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('interested', 'Interested'),
        ('demo_scheduled', 'Demo Scheduled'),
        ('follow_up', 'Follow-up'),
        ('converted', 'Converted'),
        ('lost', 'Lost'),
    ]

    SOURCE_CHOICES = [
        ('instagram', 'Instagram'),
        ('facebook', 'Facebook'),
        ('linkedin', 'LinkedIn'),
        ('whatsapp', 'WhatsApp'),
        ('website', 'Website'),
        ('referral', 'Referral'),
        ('cold_call', 'Cold Call'),
        ('field_visit', 'Field Visit'),
        ('other', 'Other'),
    ]

    contact_person = models.CharField(max_length=200)
    company_name = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='other')
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='crm_leads'
    )
    next_follow_up_date = models.DateField(null=True, blank=True)
    closing_probability = models.IntegerField(
        default=0,
        help_text='Probability of closing (0-100%)'
    )
    notes = models.TextField(blank=True)
    client = models.ForeignKey(
        Client,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='crm_leads',
        help_text='Client created when lead is converted',
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='crm_leads_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Lead'
        verbose_name_plural = 'Leads'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['assigned_to']),
            models.Index(fields=['phone']),
        ]

    def __str__(self):
        return f"{self.contact_person} - {self.company_name or 'No Company'}"

    @property
    def normalized_phone(self):
        return re.sub(r'\D', '', self.phone)

    @classmethod
    def check_duplicate(cls, phone=None, email=None, exclude_pk=None):
        duplicates = []
        if phone:
            normalized = re.sub(r'\D', '', phone)
            if normalized:
                qs = cls.objects.all()
                if exclude_pk:
                    qs = qs.exclude(pk=exclude_pk)
                for lead in qs:
                    if re.sub(r'\D', '', lead.phone) == normalized:
                        duplicates.append(lead)
                        break
        if email and email.strip():
            qs = cls.objects.filter(email__iexact=email.strip())
            if exclude_pk:
                qs = qs.exclude(pk=exclude_pk)
            if qs.exists():
                for lead in qs[:1]:
                    if lead not in duplicates:
                        duplicates.append(lead)
        return duplicates


class LeadNote(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='lead_notes')
    note = models.TextField()
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='crm_lead_notes'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Lead Note'
        verbose_name_plural = 'Lead Notes'

    def __str__(self):
        return f"Note on {self.lead} by {self.created_by}"


class FollowUp(models.Model):
    TYPE_CHOICES = [
        ('call', 'Phone Call'),
        ('email', 'Email'),
        ('meeting', 'Meeting'),
        ('whatsapp', 'WhatsApp'),
        ('visit', 'Field Visit'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('missed', 'Missed'),
        ('rescheduled', 'Rescheduled'),
    ]

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='follow_ups')
    follow_up_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='call')
    scheduled_date = models.DateTimeField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='scheduled')
    notes = models.TextField(blank=True)
    outcome = models.TextField(blank=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='crm_follow_ups_created'
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['scheduled_date']
        verbose_name = 'Follow-up'
        verbose_name_plural = 'Follow-ups'

    def __str__(self):
        return f"{self.get_follow_up_type_display()} - {self.lead.contact_person} ({self.scheduled_date.strftime('%Y-%m-%d %H:%M')})"

    @property
    def is_overdue(self):
        return self.status == 'scheduled' and self.scheduled_date < timezone.now()


class LeadActivity(models.Model):
    ACTIVITY_TYPES = [
        ('created', 'Lead Created'),
        ('status_change', 'Status Changed'),
        ('note_added', 'Note Added'),
        ('follow_up_scheduled', 'Follow-up Scheduled'),
        ('follow_up_completed', 'Follow-up Completed'),
        ('follow_up_missed', 'Follow-up Missed'),
        ('demo_scheduled', 'Demo Scheduled'),
        ('demo_completed', 'Demo Completed'),
        ('demo_converted', 'Demo Converted'),
        ('call', 'Call Made'),
        ('email', 'Email Sent'),
        ('meeting', 'Meeting'),
        ('edited', 'Lead Edited'),
    ]

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=25, choices=ACTIVITY_TYPES)
    description = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='crm_activities_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Lead Activity'
        verbose_name_plural = 'Lead Activities'

    def __str__(self):
        return f"{self.get_activity_type_display()} - {self.lead.contact_person}"


class DailyActivity(models.Model):
    INTERN_TYPE_CHOICES = [
        ('digital', 'Digital Marketing'),
        ('field', 'Field Marketing'),
    ]

    APPROVAL_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    intern = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='crm_daily_activities'
    )
    date = models.DateField(default=timezone.now)
    intern_type = models.CharField(max_length=10, choices=INTERN_TYPE_CHOICES)

    # Digital marketing fields
    social_media_posts = models.IntegerField(default=0)
    reels_created = models.IntegerField(default=0)
    dms_sent = models.IntegerField(default=0)
    digital_leads_generated = models.IntegerField(default=0)

    # Field marketing fields
    calls_made = models.IntegerField(default=0)
    visits_done = models.IntegerField(default=0)
    demos_conducted = models.IntegerField(default=0)
    field_leads_generated = models.IntegerField(default=0)

    remarks = models.TextField(blank=True)
    approval_status = models.CharField(
        max_length=10, choices=APPROVAL_STATUS_CHOICES, default='pending'
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='crm_approved_activities'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        verbose_name = 'Daily Activity'
        verbose_name_plural = 'Daily Activities'
        unique_together = ['intern', 'date']

    def __str__(self):
        return f"{self.intern.get_full_name() or self.intern.username} - {self.date}"

    @property
    def is_editable(self):
        return (timezone.now() - self.created_at).total_seconds() < 86400


class Demo(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('rescheduled', 'Rescheduled'),
        ('cancelled', 'Cancelled'),
        ('converted', 'Converted'),
    ]

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='demos')
    scheduled_date = models.DateTimeField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='scheduled')
    conducted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='crm_demos_conducted'
    )
    closing_probability = models.IntegerField(
        default=0,
        help_text='Probability of closing after demo (0-100%)'
    )
    outcome_notes = models.TextField(blank=True)
    location = models.CharField(max_length=300, blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='crm_demos_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-scheduled_date']
        verbose_name = 'Demo'
        verbose_name_plural = 'Demos'

    def __str__(self):
        return f"Demo: {self.lead} - {self.scheduled_date.strftime('%Y-%m-%d %H:%M')}"
