"""A quote sent to the client on WhatsApp (or email) as a private link.

The client opens /quote/<token>/, reads the quote, downloads it as a PDF, and
either accepts it (typed name + optional drawn signature) or asks for changes.
An accepted quote is kept as the agreement: who signed, when, from where, a
hash of exactly what they accepted, and a frozen signed PDF.
"""
import hashlib
import json
import uuid
from decimal import Decimal
from urllib.parse import quote as urlquote

from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils import timezone

from employees.agreement_models import generate_token


class QuoteLink(models.Model):
    STATUS_SENT = 'sent'
    STATUS_VIEWED = 'viewed'
    STATUS_ACCEPTED = 'accepted'
    STATUS_CHANGES = 'changes'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (STATUS_SENT, 'Sent'),
        (STATUS_VIEWED, 'Viewed'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_CHANGES, 'Changes requested'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]
    OPEN_STATUSES = (STATUS_SENT, STATUS_VIEWED)
    RESPONDED_STATUSES = (STATUS_ACCEPTED, STATUS_CHANGES)

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token = models.CharField(max_length=64, unique=True, db_index=True, default=generate_token)
    quote = models.ForeignKey('core.Quote', on_delete=models.CASCADE, related_name='links')
    with_gst = models.BooleanField(default=False, help_text='Show the quote with GST added')
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_SENT, db_index=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)

    first_viewed_at = models.DateTimeField(null=True, blank=True)
    last_viewed_at = models.DateTimeField(null=True, blank=True)
    view_count = models.PositiveIntegerField(default=0)

    # The client's answer
    responded_at = models.DateTimeField(null=True, blank=True)
    signer_name = models.CharField(max_length=150, blank=True)
    signer_designation = models.CharField(max_length=150, blank=True)
    signer_company = models.CharField(max_length=200, blank=True)
    signer_email = models.EmailField(blank=True)
    signed_name = models.CharField(max_length=150, blank=True)
    signature_image = models.ImageField(upload_to='quote_links/signatures/', null=True, blank=True)
    change_notes = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    # What was accepted, frozen: totals/items at that moment, its hash, and the signed PDF.
    snapshot = models.JSONField(default=dict, blank=True)
    body_hash = models.CharField(max_length=64, blank=True)
    signed_pdf = models.FileField(upload_to='quote_links/signed/', null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.quote.quote_number} link ({self.get_status_display()})'

    # ---- State ----
    @property
    def is_open(self):
        return self.status in self.OPEN_STATUSES

    @property
    def is_expired(self):
        return self.is_open and self.quote.valid_until and self.quote.valid_until < timezone.localdate()

    @property
    def status_label(self):
        return 'Expired' if self.is_expired else self.get_status_display()

    def mark_viewed(self):
        now = timezone.now()
        self.first_viewed_at = self.first_viewed_at or now
        self.last_viewed_at = now
        self.view_count += 1
        fields = ['first_viewed_at', 'last_viewed_at', 'view_count']
        if self.status == self.STATUS_SENT:
            self.status = self.STATUS_VIEWED
            fields.append('status')
        self.save(update_fields=fields)
        if self.quote.status in ('draft', 'sent'):
            self.quote.status = 'viewed'
            self.quote.save(update_fields=['status', 'updated_at'])

    # ---- Links ----
    def public_path(self):
        return reverse('quote_public', args=[self.token])

    def public_url(self, request=None):
        return request.build_absolute_uri(self.public_path()) if request else self.public_path()

    def whatsapp_url(self, request=None):
        q = self.quote
        phone = ''
        if q.client_id:
            phone = q.client.whatsapp or q.client.phone or ''
        elif q.lead_id:
            phone = q.lead.phone or ''
        digits = ''.join(ch for ch in phone if ch.isdigit())
        if len(digits) == 10:
            digits = '91' + digits
        message = (
            f'Hi {q.recipient_name},\n\n'
            f'Here is our quotation {q.quote_number} for "{q.title}" from Ralfiz Technologies.\n\n'
            f'You can view it, download the PDF and accept it here:\n{self.public_url(request)}\n\n'
            'If anything needs to change, you can tell us from the same link. Thank you.'
        )
        return f'https://wa.me/{digits}?text={urlquote(message)}' if digits else \
            f'https://wa.me/?text={urlquote(message)}'

    def mailto_url(self, request=None):
        q = self.quote
        if not q.recipient_email:
            return ''
        subject = f'Quotation {q.quote_number} - {q.title}'
        body = (f'Hi {q.recipient_name},\n\nPlease find our quotation {q.quote_number} for "{q.title}". '
                f'You can view it, download the PDF and accept it online:\n{self.public_url(request)}\n\n'
                'Thank you,\nRalfiz Technologies')
        return f'mailto:{q.recipient_email}?subject={urlquote(subject)}&body={urlquote(body)}'

    # ---- What the client accepts ----
    def build_snapshot(self, totals, chosen_addons=()):
        q = self.quote
        return {
            'quote_number': q.quote_number, 'title': q.title, 'description': q.description,
            'issue_date': q.issue_date.isoformat() if q.issue_date else '',
            'valid_until': q.valid_until.isoformat() if q.valid_until else '',
            'items': [{'id': str(i.pk), 'description': i.description, 'details': i.details,
                       'quantity': str(i.quantity), 'unit_price': str(i.unit_price), 'amount': str(i.amount),
                       'optional': i.is_optional}
                      for i in q.items.all()],
            'chosen_addons': list(chosen_addons),
            'subtotal': str(q.subtotal), 'discount': str(q.discount or 0),
            'with_gst': self.with_gst, 'total': str(Decimal(totals['grand_total']).quantize(Decimal('0.01'))),
            'payment_terms': q.payment_terms_display or '', 'terms': q.terms, 'notes': q.client_notes,
            'accepted_total': str(self._accepted_total(totals, chosen_addons)),
        }

    def _accepted_total(self, totals, chosen_addons):
        """Core total plus the add-ons the client ticked (with GST when shown)."""
        chosen = set(chosen_addons)
        extra = sum((a['total'] for a in totals.get('addons', []) if str(a['item'].pk) in chosen), Decimal('0'))
        return (Decimal(totals['grand_total']) + extra).quantize(Decimal('0.01'))

    @staticmethod
    def hash_snapshot(snapshot):
        return hashlib.sha256(json.dumps(snapshot, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
