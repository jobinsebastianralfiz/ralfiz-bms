"""Social Hub: publish, schedule, reply and report across client social accounts.

Every client-owned row carries ``workspace`` (directly or through its account)
so the hub can later serve outside customers without a schema change. One post
fans out to one PostTarget per account, so each platform succeeds or fails on
its own.
"""
import secrets
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from .crypto import decrypt, encrypt

PLATFORM_CHOICES = [
    ('facebook', 'Facebook'),
    ('instagram', 'Instagram'),
    ('linkedin', 'LinkedIn'),
    ('youtube', 'YouTube'),
    ('x', 'X'),
    ('whatsapp', 'WhatsApp'),
    ('google_business', 'Google Business'),
    ('email', 'Email'),
]
PLATFORM_LABELS = dict(PLATFORM_CHOICES)


def _review_token():
    return secrets.token_urlsafe(24)


class Workspace(models.Model):
    """One per client, plus one for Ralfiz itself (client left empty)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.OneToOneField('core.Client', on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='social_workspace')
    name = models.CharField(max_length=200)
    color = models.CharField(max_length=7, default='#6D4AFF')
    brand_kit = models.JSONField(default=dict, blank=True,
                                 help_text='hashtags, tone notes, colours')
    requires_approval = models.BooleanField(
        default=True, help_text='Posts must be approved before they go out.')
    reviewer_name = models.CharField(max_length=120, blank=True,
                                     help_text='Client contact who approves through the review link.')
    review_token = models.CharField(max_length=64, unique=True, default=_review_token)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def initial(self):
        return (self.name[:1] or '?').upper()


class Membership(models.Model):
    """Staff access to one workspace. Owners and partners see every workspace without a row."""
    ROLE_CHOICES = [('manager', 'Manager'), ('editor', 'Editor')]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='social_memberships')
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='editor')

    class Meta:
        unique_together = [('user', 'workspace')]


class SocialAccount(models.Model):
    STATUS_CHOICES = [
        ('active', 'Connected'),
        ('expiring', 'Expiring soon'),
        ('reconnect', 'Reconnect needed'),
        ('disconnected', 'Disconnected'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='accounts')
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    external_id = models.CharField(max_length=200, help_text='Page, account, channel or location id')
    name = models.CharField(max_length=200)
    handle = models.CharField(max_length=200, blank=True)
    avatar_url = models.URLField(max_length=1000, blank=True)
    token_encrypted = models.TextField(blank=True)
    refresh_token_encrypted = models.TextField(blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    extra = models.JSONField(default=dict, blank=True,
                             help_text='Platform ids the adapter needs (e.g. WABA id, account path)')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')
    last_error = models.TextField(blank=True)
    connected_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                     null=True, blank=True, related_name='+')
    last_synced_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['workspace__name', 'platform', 'name']
        unique_together = [('workspace', 'platform', 'external_id')]

    def __str__(self):
        return f'{self.name} ({self.get_platform_display()})'

    # Tokens are only ever handled decrypted in memory.
    @property
    def token(self):
        return decrypt(self.token_encrypted)

    @token.setter
    def token(self, value):
        self.token_encrypted = encrypt(value)

    @property
    def refresh_token(self):
        return decrypt(self.refresh_token_encrypted)

    @refresh_token.setter
    def refresh_token(self, value):
        self.refresh_token_encrypted = encrypt(value)

    @property
    def healthy(self):
        return self.status in ('active', 'expiring')


class MediaAsset(models.Model):
    KIND_CHOICES = [('image', 'Image'), ('video', 'Video')]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='media')
    file = models.FileField(upload_to='social/media/%Y/%m/')
    name = models.CharField(max_length=255, blank=True)
    kind = models.CharField(max_length=10, choices=KIND_CHOICES, default='image')
    content_type = models.CharField(max_length=100, blank=True)
    size = models.PositiveBigIntegerField(default=0)
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    tags = models.CharField(max_length=255, blank=True)
    source = models.CharField(max_length=20, default='upload')  # upload, url, canva
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
    def __str__(self):
        return self.name or self.file.name


class Post(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('review', 'In review'),
        ('changes', 'Changes requested'),
        ('scheduled', 'Scheduled'),
        ('publishing', 'Publishing'),
        ('published', 'Published'),
        ('partial', 'Partly published'),
        ('failed', 'Failed'),
    ]
    SOURCE_CHOICES = [('web', 'Dashboard'), ('mcp', 'Claude'), ('import', 'Imported')]
    #: Statuses a person can still edit, reschedule or delete.
    EDITABLE = ('draft', 'review', 'changes', 'scheduled', 'failed')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='posts')
    base_text = models.TextField(blank=True)
    first_comment = models.TextField(blank=True, help_text='Posted as the first comment (Instagram, Facebook, LinkedIn)')
    title = models.CharField(max_length=100, blank=True, help_text='YouTube video title')
    link = models.URLField(max_length=1000, blank=True)
    media = models.ManyToManyField(MediaAsset, through='PostMedia', blank=True, related_name='posts')
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='draft')
    scheduled_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='+')
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default='web',
                              help_text='Imported = already on the account, pulled in by sync')
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by_name = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['scheduled_at', 'created_at']
        indexes = [models.Index(fields=['status', 'scheduled_at'])]

    def __str__(self):
        return (self.base_text or self.title or 'Post')[:60]

    @property
    def is_editable(self):
        return self.status in self.EDITABLE

    def ordered_media(self):
        return [pm.asset for pm in self.post_media.select_related('asset').order_by('position')]


class PostMedia(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_media')
    asset = models.ForeignKey(MediaAsset, on_delete=models.CASCADE, related_name='+')
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['position']


class PostTarget(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('publishing', 'Publishing'),
        ('published', 'Published'),
        ('failed', 'Failed'),
    ]
    MAX_ATTEMPTS = 3

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='targets')
    account = models.ForeignKey(SocialAccount, on_delete=models.CASCADE, related_name='targets')
    text = models.TextField(blank=True, help_text='Per-platform caption; empty uses the post text')
    options = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='pending')
    attempts = models.PositiveSmallIntegerField(default=0)
    next_attempt_at = models.DateTimeField(null=True, blank=True)
    locked_at = models.DateTimeField(null=True, blank=True)
    external_id = models.CharField(max_length=300, blank=True)
    external_url = models.URLField(max_length=1000, blank=True)
    error = models.TextField(blank=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [('post', 'account')]
        indexes = [models.Index(fields=['account', 'external_id'])]

    @property
    def effective_text(self):
        return self.text or self.post.base_text

    @property
    def kind(self):
        return self.options.get('kind', 'post')

    @property
    def thumbnail_url(self):
        return self.options.get('thumb', '')


class Approval(models.Model):
    DECISION_CHOICES = [('submitted', 'Submitted'), ('approved', 'Approved'),
                        ('changes', 'Changes requested')]
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='approvals')
    decision = models.CharField(max_length=10, choices=DECISION_CHOICES)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                             null=True, blank=True, related_name='+')
    reviewer_name = models.CharField(max_length=120, blank=True)
    via = models.CharField(max_length=10, default='web')  # web, link, mcp
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

class InboxItem(models.Model):
    KIND_CHOICES = [('comment', 'Comment'), ('dm', 'Message'), ('review', 'Review'),
                    ('mention', 'Mention'), ('email', 'Email')]
    STATUS_CHOICES = [('open', 'Open'), ('done', 'Done')]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey(SocialAccount, on_delete=models.CASCADE, related_name='inbox')
    kind = models.CharField(max_length=10, choices=KIND_CHOICES)
    external_id = models.CharField(max_length=300)
    thread_id = models.CharField(max_length=300, blank=True,
                                 help_text='Conversation, post or review the item belongs to')
    author_name = models.CharField(max_length=200, blank=True)
    author_id = models.CharField(max_length=200, blank=True)
    text = models.TextField(blank=True)
    rating = models.PositiveSmallIntegerField(null=True, blank=True)
    permalink = models.URLField(max_length=1000, blank=True)
    received_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=5, choices=STATUS_CHOICES, default='open')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='+')
    raw = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-received_at']
        unique_together = [('account', 'external_id')]

    @property
    def reply_window_ends(self):
        """WhatsApp only allows free-form replies for 24 hours after the customer's message."""
        if self.account.platform != 'whatsapp':
            return None
        return self.received_at + timezone.timedelta(hours=24)

    @property
    def reply_window_open(self):
        end = self.reply_window_ends
        return end is None or end > timezone.now()


class InboxReply(models.Model):
    STATUS_CHOICES = [('draft', 'Draft'), ('sent', 'Sent'), ('failed', 'Failed')]
    item = models.ForeignKey(InboxItem, on_delete=models.CASCADE, related_name='replies')
    text = models.TextField()
    status = models.CharField(max_length=6, choices=STATUS_CHOICES, default='draft')
    source = models.CharField(max_length=5, default='web')  # web, mcp, phone (sent from the WhatsApp app)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='+')
    sent_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='+')
    external_id = models.CharField(max_length=300, blank=True)
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['created_at']


class MetricDaily(models.Model):
    """Account-level metrics, one row per metric per day."""
    account = models.ForeignKey(SocialAccount, on_delete=models.CASCADE, related_name='metrics')
    date = models.DateField()
    metric = models.CharField(max_length=40)  # reach, impressions, engagement, followers, views, clicks
    value = models.BigIntegerField(default=0)

    class Meta:
        unique_together = [('account', 'date', 'metric')]
        indexes = [models.Index(fields=['account', 'metric', 'date'])]


class PostMetric(models.Model):
    target = models.ForeignKey(PostTarget, on_delete=models.CASCADE, related_name='metrics')
    metric = models.CharField(max_length=40)
    value = models.BigIntegerField(default=0)
    captured_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = [('target', 'metric')]


class Automation(models.Model):
    """Comment-to-DM: a keyword under a post or reel gets a public reply and a private DM.

    Meta allows one private reply per comment, sent to the comment rather than a
    person, and only for about a week after the comment.
    """
    MATCH_CHOICES = [('contains', 'Comment contains the keyword'), ('exact', 'Comment is just the keyword')]
    DELIVERY_CHOICES = [('direct', 'Link in the first DM'),
                        ('opener', 'Button first, link after they tap')]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='automations')
    account = models.ForeignKey(SocialAccount, on_delete=models.CASCADE, related_name='automations')
    name = models.CharField(max_length=120)
    post_id = models.CharField(max_length=300, blank=True,
                               help_text='Post or reel id the comment is on; empty means every post')
    keywords = models.JSONField(default=list)
    match_type = models.CharField(max_length=10, choices=MATCH_CHOICES, default='contains')
    public_replies = models.JSONField(default=list, blank=True,
                                      help_text='Replies under the comment, one picked at random')
    dm_text = models.TextField()
    button_label = models.CharField(max_length=20, blank=True)
    button_url = models.URLField(max_length=1000, blank=True)
    # A tap on the opener button opens the 24-hour messaging window: it lets us check
    # the Instagram follow, send the link and one follow-up.
    delivery = models.CharField(max_length=6, choices=DELIVERY_CHOICES, default='direct')
    opener_label = models.CharField(max_length=20, blank=True)
    link_text = models.TextField(blank=True, help_text='Sent with the link after the tap')
    follow_gate = models.BooleanField(default=False, help_text='Instagram: only followers get the link')
    gate_text = models.TextField(blank=True, help_text='Sent to people who do not follow yet')
    followup_text = models.TextField(blank=True)
    followup_hours = models.PositiveSmallIntegerField(default=6)
    lead_keyword = models.CharField(max_length=30, blank=True,
                                    help_text='A DM with this word starts the lead form')
    is_active = models.BooleanField(default=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def is_live(self):
        return self.is_active and (self.ends_at is None or self.ends_at > timezone.now())


class Contact(models.Model):
    """A person an automation sent a DM to. ``platform_user_id`` is the commenter's id;
    ``messaging_id`` is the id their DMs and button taps come from (on Facebook the two differ)."""
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='contacts')
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    platform_user_id = models.CharField(max_length=200)
    messaging_id = models.CharField(max_length=200, blank=True, db_index=True)
    name = models.CharField(max_length=200, blank=True)
    username = models.CharField(max_length=200, blank=True)
    is_follower = models.BooleanField(null=True)
    tags = models.JSONField(default=list, blank=True)
    first_seen_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-last_seen_at']
        unique_together = [('workspace', 'platform', 'platform_user_id')]

    def __str__(self):
        return self.name or self.username or self.platform_user_id


class AutomationRun(models.Model):
    """One matched comment and what the worker did about it. The comment is unique,
    so a webhook delivered twice cannot send two DMs."""
    STATUS_CHOICES = [('queued', 'Queued'), ('sending', 'Sending'), ('sent', 'Sent'),
                      ('skipped', 'Skipped'), ('failed', 'Failed')]
    MAX_ATTEMPTS = 3
    automation = models.ForeignKey(Automation, on_delete=models.CASCADE, related_name='runs')
    item = models.OneToOneField(InboxItem, on_delete=models.CASCADE, related_name='automation_run')
    commenter_id = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default='queued')
    attempts = models.PositiveSmallIntegerField(default=0)
    next_attempt_at = models.DateTimeField(default=timezone.now)
    locked_at = models.DateTimeField(null=True, blank=True)
    dm_id = models.CharField(max_length=300, blank=True)
    reply_id = models.CharField(max_length=300, blank=True)
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    contact = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='runs')
    tapped_at = models.DateTimeField(null=True, blank=True)
    last_postback = models.CharField(max_length=300, blank=True, help_text='Dedupes redelivered taps')
    was_follower = models.BooleanField(null=True, help_text='Follow status at the first check')
    link_sent_at = models.DateTimeField(null=True, blank=True)
    followup_due_at = models.DateTimeField(null=True, blank=True)
    followup_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['status', 'next_attempt_at']),
                   models.Index(fields=['followup_due_at'])]

    @property
    def follow_gained(self):
        return self.was_follower is False and self.link_sent_at is not None


class TrackedLink(models.Model):
    """The short /go/<slug>/ link an automation's button points at, so clicks are counted."""
    automation = models.OneToOneField(Automation, on_delete=models.CASCADE, related_name='link')
    slug = models.SlugField(max_length=16, unique=True)
    target_url = models.URLField(max_length=1000)


class LinkClick(models.Model):
    link = models.ForeignKey(TrackedLink, on_delete=models.CASCADE, related_name='clicks')
    run = models.ForeignKey(AutomationRun, on_delete=models.SET_NULL, null=True, blank=True,
                            related_name='clicks')
    platform = models.CharField(max_length=20, blank=True)
    user_agent = models.CharField(max_length=300, blank=True)
    clicked_at = models.DateTimeField(auto_now_add=True)


class LeadCapture(models.Model):
    """The DM lead form: name, business, then WhatsApp number, one message each."""
    STEP_CHOICES = [('name', 'Asked name'), ('business', 'Asked business'),
                    ('phone', 'Asked number'), ('done', 'Done')]
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='lead_captures')
    automation = models.ForeignKey(Automation, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='lead_captures')
    step = models.CharField(max_length=8, choices=STEP_CHOICES, default='name')
    name = models.CharField(max_length=200, blank=True)
    business = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    crm_lead = models.ForeignKey('crm.Lead', on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']


class AuditLog(models.Model):
    LABELS = {
        'post.create': 'created a post', 'post.edit': 'edited a post', 'post.submit': 'sent a post for approval',
        'post.schedule': 'scheduled a post', 'post.approve': 'approved a post',
        'post.changes': 'asked for changes', 'post.reschedule': 'moved a post', 'post.delete': 'deleted a post',
        'post.retry': 'retried a post', 'post.published': 'published', 'post.failed': 'could not publish',
        'reply.draft': 'drafted a reply', 'reply.sent': 'sent a reply', 'reply.template': 'sent a template',
        'media.upload': 'added media', 'media.delete': 'removed media',
        'account.connect': 'connected an account', 'account.reconnect': 'reconnected an account',
        'account.disconnect': 'disconnected an account', 'account.delete': 'removed an account',
        'workspace.save': 'updated the client', 'report.download': 'downloaded a report',
        'automation.save': 'saved a comment automation', 'automation.toggle': 'switched a comment automation',
    }
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, null=True, blank=True,
                                  related_name='audit')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                             null=True, blank=True, related_name='+')
    actor = models.CharField(max_length=120, blank=True, help_text='Shown name, e.g. a client reviewer')
    via = models.CharField(max_length=10, default='web')  # web, mcp, link, worker
    action = models.CharField(max_length=60)
    summary = models.CharField(max_length=300, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def label(self):
        return self.LABELS.get(self.action, self.action)
