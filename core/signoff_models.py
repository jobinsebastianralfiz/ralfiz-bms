"""Project sign-off documents: a handover the client ticks, signs and approves online.

Every project hands over something different, so a sign-off has no fixed
template. It is a list of sections, each a list of blocks (text, a checklist
the client ticks, a table, bullets, side-by-side cards, a note), written per
project - normally by Claude through the BMS connector - and frozen in
`snapshot_json` when it is created. The client opens a private link, ticks what
was delivered, and approves or reports a problem. A corrected sign-off is a new
document that supersedes the open one; nothing the client saw is rewritten.
"""
import hashlib
import json
import uuid
from datetime import timedelta
from urllib.parse import quote

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from employees.agreement_models import generate_token

DEFAULT_EXPIRY_DAYS = 30

BLOCK_TYPES = ('text', 'checklist', 'table', 'bullets', 'cards', 'note')
CARD_TONES = ('good', 'bad', 'plain')

MAX_SECTIONS = 30
MAX_BLOCKS = 20
MAX_ITEMS = 60
MAX_COLUMNS = 6
MAX_TEXT = 4000


class SignoffError(ValueError):
    """The sign-off content is malformed; the message says what to fix."""


def default_signoff_expiry():
    return timezone.now() + timedelta(days=DEFAULT_EXPIRY_DAYS)


def _text(value, where, required=True, limit=MAX_TEXT):
    if value is None:
        value = ''
    if not isinstance(value, (str, int, float)) or isinstance(value, bool):
        raise SignoffError(f'{where} must be text.')
    value = str(value).strip()
    if required and not value:
        raise SignoffError(f'{where} is empty.')
    if len(value) > limit:
        raise SignoffError(f'{where} is too long (over {limit} characters).')
    return value


def _strings(value, where, minimum=1):
    if not isinstance(value, list):
        raise SignoffError(f'{where} must be a list of text items.')
    if len(value) > MAX_ITEMS:
        raise SignoffError(f'{where} has more than {MAX_ITEMS} items.')
    items = [_text(item, f'{where} item {i}', limit=600) for i, item in enumerate(value, 1)]
    if len(items) < minimum:
        raise SignoffError(f'{where} needs at least {minimum} item{"s" if minimum != 1 else ""}.')
    return items


def _block(raw, where, next_check_id):
    if not isinstance(raw, dict):
        raise SignoffError(f'{where} must be an object with a "type".')
    kind = raw.get('type')
    if kind not in BLOCK_TYPES:
        raise SignoffError(f'{where}: type must be one of {", ".join(BLOCK_TYPES)}.')

    if kind in ('text', 'note'):
        return {'type': kind, 'text': _text(raw.get('text'), f'{where} text')}

    if kind == 'bullets':
        return {'type': kind, 'items': _strings(raw.get('items'), f'{where} items')}

    if kind == 'checklist':
        items = _strings(raw.get('items'), f'{where} items')
        return {
            'type': kind,
            'title': _text(raw.get('title'), f'{where} title', required=False, limit=200),
            'items': [{'id': next_check_id(), 'text': item} for item in items],
        }

    if kind == 'table':
        columns = _strings(raw.get('columns'), f'{where} columns')
        if len(columns) > MAX_COLUMNS:
            raise SignoffError(f'{where} has more than {MAX_COLUMNS} columns.')
        rows_raw = raw.get('rows')
        if not isinstance(rows_raw, list) or not rows_raw:
            raise SignoffError(f'{where} rows must be a list of rows, each a list of cells.')
        if len(rows_raw) > MAX_ITEMS:
            raise SignoffError(f'{where} has more than {MAX_ITEMS} rows.')
        rows = []
        for r, row in enumerate(rows_raw, 1):
            if not isinstance(row, list) or len(row) != len(columns):
                raise SignoffError(f'{where} row {r} must have {len(columns)} cells, one per column.')
            rows.append([_text(cell, f'{where} row {r} cell {c}', required=False, limit=600)
                         for c, cell in enumerate(row, 1)])
        return {'type': kind, 'columns': columns, 'rows': rows}

    # cards: two or three boxes side by side, e.g. "covers" / "does not cover"
    cards_raw = raw.get('cards')
    if not isinstance(cards_raw, list) or not 1 <= len(cards_raw) <= 3:
        raise SignoffError(f'{where} cards must be a list of one to three cards.')
    cards = []
    for c, card in enumerate(cards_raw, 1):
        if not isinstance(card, dict):
            raise SignoffError(f'{where} card {c} must be an object.')
        tone = card.get('tone') or 'plain'
        if tone not in CARD_TONES:
            raise SignoffError(f'{where} card {c}: tone must be one of {", ".join(CARD_TONES)}.')
        cards.append({
            'title': _text(card.get('title'), f'{where} card {c} title', limit=200),
            'note': _text(card.get('note'), f'{where} card {c} note', required=False, limit=200),
            'tone': tone,
            'items': _strings(card.get('items'), f'{where} card {c} items'),
        })
    return {'type': kind, 'cards': cards}


def build_signoff_snapshot(project, *, title, sections, acceptance, eyebrow='', document_date=None):
    """Check the content and freeze it. Raises SignoffError naming the first
    problem, so whoever wrote the content (usually Claude) can correct it."""
    from core.models import CompanySettings

    if not isinstance(sections, list) or not sections:
        raise SignoffError('sections must be a list with at least one section.')
    if len(sections) > MAX_SECTIONS:
        raise SignoffError(f'A sign-off can have at most {MAX_SECTIONS} sections.')

    counter = iter(range(1, 100000))

    def next_check_id():
        return f'c{next(counter)}'

    clean_sections = []
    for s, section in enumerate(sections, 1):
        where = f'Section {s}'
        if not isinstance(section, dict):
            raise SignoffError(f'{where} must be an object with "heading" and "blocks".')
        blocks = section.get('blocks')
        if not isinstance(blocks, list) or not blocks:
            raise SignoffError(f'{where} needs at least one block.')
        if len(blocks) > MAX_BLOCKS:
            raise SignoffError(f'{where} has more than {MAX_BLOCKS} blocks.')
        clean_sections.append({
            'heading': _text(section.get('heading'), f'{where} heading', limit=200),
            'blocks': [_block(b, f'{where} block {i}', next_check_id) for i, b in enumerate(blocks, 1)],
        })

    client = project.client
    company = CompanySettings.get_settings()
    check_ids = [item['id'] for sec in clean_sections for block in sec['blocks']
                 if block['type'] == 'checklist' for item in block['items']]
    return {
        'version': 'v1.0',
        'eyebrow': _text(eyebrow, 'eyebrow', required=False, limit=80) or 'PROJECT HANDOVER',
        'title': _text(title, 'title', limit=200),
        'date': (document_date or timezone.localdate()).strftime('%d %B %Y').lstrip('0'),
        'provider_name': company.company_name or 'Ralfiz Technologies',
        'client_party': client.company_name or client.name,
        'client_name': client.name,
        'project_name': project.name,
        'sections': clean_sections,
        'acceptance': _text(acceptance, 'acceptance'),
        'check_ids': check_ids,
    }


class ProjectSignoff(models.Model):
    """One signable sign-off link for one project."""

    STATUS_PENDING = 'pending'
    STATUS_VIEWED = 'viewed'
    STATUS_APPROVED = 'approved'
    STATUS_ISSUES = 'issues'
    STATUS_CANCELLED = 'cancelled'
    STATUS_SUPERSEDED = 'superseded'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Sent'),
        (STATUS_VIEWED, 'Opened'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_ISSUES, 'Problem reported'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_SUPERSEDED, 'Superseded'),
    ]

    OPEN_STATUSES = (STATUS_PENDING, STATUS_VIEWED)
    RESPONDED_STATUSES = (STATUS_APPROVED, STATUS_ISSUES)

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token = models.CharField(max_length=64, unique=True, db_index=True, default=generate_token)
    reference = models.CharField(max_length=40, blank=True, db_index=True,
                                 help_text='e.g. RT/SO/26/0003')
    revision = models.PositiveIntegerField(default=1)

    project = models.ForeignKey('core.Project', on_delete=models.CASCADE, related_name='signoffs')
    title = models.CharField(max_length=200)
    snapshot_json = models.JSONField(default=dict, blank=True,
                                     help_text='Everything the client is shown, frozen at send time')

    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_PENDING,
                              db_index=True)
    sent_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='signoffs_sent')
    sent_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=default_signoff_expiry)

    first_viewed_at = models.DateTimeField(null=True, blank=True)
    last_viewed_at = models.DateTimeField(null=True, blank=True)
    view_count = models.PositiveIntegerField(default=0)

    # ---- Response ----
    responded_at = models.DateTimeField(null=True, blank=True)
    signer_name = models.CharField(max_length=200, blank=True)
    signer_role = models.CharField(max_length=200, blank=True)
    signer_email = models.EmailField(blank=True)
    signed_name = models.CharField(max_length=200, blank=True,
                                   help_text='Typed signature - the binding one')
    signature_image = models.ImageField(upload_to='signoffs/signatures/', null=True, blank=True)
    checked_items = models.JSONField(default=list, blank=True,
                                     help_text='Ids of the checklist items the client ticked')
    issue_notes = models.TextField(blank=True, help_text='What the client said is wrong or missing')

    # ---- Evidence ----
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    body_hash = models.CharField(max_length=64, blank=True)

    superseded_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='supersedes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f'{self.reference} - {self.title} ({self.get_status_display()})'

    # ---- State ----
    @property
    def is_expired(self):
        return self.status in self.OPEN_STATUSES and timezone.now() > self.expires_at

    @property
    def is_open(self):
        return self.status in self.OPEN_STATUSES and not self.is_expired

    @property
    def has_responded(self):
        return self.status in self.RESPONDED_STATUSES

    @property
    def status_label(self):
        return 'Expired' if self.is_expired else self.get_status_display()

    @property
    def status_css(self):
        """Inline badge colours from theme vars (the app has no .bg-info etc.)."""
        muted = 'background: var(--bg-hover); color: var(--text-muted);'
        if self.is_expired:
            return muted
        return {
            self.STATUS_PENDING: 'background: var(--info-bg); color: var(--info);',
            self.STATUS_VIEWED: 'background: var(--warning-bg); color: var(--warning);',
            self.STATUS_APPROVED: 'background: var(--success-bg); color: var(--success);',
            self.STATUS_ISSUES: 'background: var(--danger-bg); color: var(--danger);',
        }.get(self.status, muted)

    @property
    def check_ids(self):
        return list(self.snapshot_json.get('check_ids', []))

    @property
    def unticked_items(self):
        """Text of the checklist items the client left unticked."""
        ticked = set(self.checked_items or [])
        return [item['text'] for section in self.snapshot_json.get('sections', [])
                for block in section['blocks'] if block['type'] == 'checklist'
                for item in block['items'] if item['id'] not in ticked]

    # ---- Links ----
    def public_path(self):
        return f'/signoff/{self.token}/'

    def public_url(self, request=None):
        return request.build_absolute_uri(self.public_path()) if request else self.public_path()

    def whatsapp_url(self, request=None):
        client = self.project.client
        digits = ''.join(ch for ch in (client.whatsapp or client.phone or '') if ch.isdigit())
        if not digits:
            return ''
        if len(digits) == 10:
            digits = '91' + digits
        message = (
            f'Hi {client.name},\n\n'
            f'"{self.title}" from Ralfiz Technologies is ready for your sign-off. Please check '
            f'what was delivered and approve it online:\n{self.public_url(request)}\n\n'
            'If something is missing or not working, you can tell us from the same link. Thank you.'
        )
        return f'https://wa.me/{digits}?text={quote(message)}'

    def mailto_url(self, request=None):
        client = self.project.client
        if not client.email:
            return ''
        subject = f'{self.title} ({self.reference})'
        body = (f'Hi {client.name},\n\n"{self.title}" is ready for your sign-off. Please check what '
                f'was delivered and approve it online:\n{self.public_url(request)}\n\n'
                'Thank you,\nRalfiz Technologies')
        return f'mailto:{client.email}?subject={quote(subject)}&body={quote(body)}'

    # ---- Transitions ----
    def mark_viewed(self):
        now = timezone.now()
        if self.first_viewed_at is None:
            self.first_viewed_at = now
        self.last_viewed_at = now
        self.view_count += 1
        fields = ['first_viewed_at', 'last_viewed_at', 'view_count', 'updated_at']
        if self.status == self.STATUS_PENDING:
            self.status = self.STATUS_VIEWED
            fields.append('status')
        self.save(update_fields=fields)

    def compute_body_hash(self):
        payload = json.dumps(self.snapshot_json, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(payload.encode('utf-8')).hexdigest()

    def save(self, *args, **kwargs):
        if not self.reference:
            prefix = f'RT/SO/{str(timezone.now().year)[-2:]}/'
            last = ProjectSignoff.objects.filter(
                reference__startswith=prefix).order_by('-reference').first()
            nxt = 1
            if last:
                try:
                    nxt = int(last.reference.split('/')[-1]) + 1
                except ValueError:
                    nxt = 1
            self.reference = f'{prefix}{str(nxt).zfill(4)}'
        super().save(*args, **kwargs)


def create_signoff(project, user, *, title, sections, acceptance, eyebrow='', document_date=None,
                   expiry_days=DEFAULT_EXPIRY_DAYS, replaces=None):
    """Freeze the content and open a link. `replaces` is an earlier sign-off of
    the same project that this one corrects; an unanswered one is superseded."""
    snapshot = build_signoff_snapshot(project, title=title, sections=sections, acceptance=acceptance,
                                      eyebrow=eyebrow, document_date=document_date)
    revision = (replaces.revision + 1) if replaces else 1
    snapshot['version'] = f'v{revision}.0'
    signoff = ProjectSignoff.objects.create(
        project=project, title=snapshot['title'], snapshot_json=snapshot, revision=revision,
        sent_by=user, expires_at=timezone.now() + timedelta(days=expiry_days),
    )
    if replaces and replaces.status != ProjectSignoff.STATUS_APPROVED:
        replaces.status = ProjectSignoff.STATUS_SUPERSEDED
        replaces.superseded_by = signoff
        replaces.save(update_fields=['status', 'superseded_by', 'updated_at'])
    return signoff
