"""Ralfiz Academy: certification courses for students.

Content (tracks, lessons, questions, exercise files) comes from the Academy
Labs package through `manage.py import_labs`. A student is a login with a
`Student` profile, the same way interns have an Employee and clients a Client.
Learner data hangs off the User so the owner can preview courses too.
"""
import uuid

from django.contrib.auth.models import User
from django.db import models


# ---- Content -----------------------------------------------------------------

def _rupees(amount):
    """'₹14,999' in Indian digit grouping, 'Free' for 0, '' when unset."""
    if amount is None:
        return ''
    if amount == 0:
        return 'Free'
    s = str(amount)
    head, tail = s[:-3], s[-3:]
    groups = []
    while len(head) > 2:
        groups.insert(0, head[-2:])
        head = head[:-2]
    if head:
        groups.insert(0, head)
    return '₹' + ','.join(groups + [tail])


class Track(models.Model):
    id = models.CharField(primary_key=True, max_length=20)          # "pl900"
    code = models.CharField(max_length=20)                           # "PL-900"
    name = models.CharField(max_length=200)
    level = models.CharField(max_length=50)
    status = models.CharField(max_length=200)
    outline_date = models.CharField(max_length=50)
    order_hint = models.CharField(max_length=100)
    blurb = models.TextField()
    facts = models.JSONField(default=list)
    tool = models.CharField(max_length=200)
    guide_url = models.URLField()
    note = models.TextField()
    data_file_ids = models.JSONField(default=list)
    sort_order = models.PositiveSmallIntegerField(default=0)
    is_published = models.BooleanField(default=True)
    content_version = models.CharField(max_length=20, blank=True)
    # YouTube playlist the Lesson Videos page syncs links from. Set by staff, never by the importer.
    video_playlist = models.URLField(max_length=300, blank=True)
    # Set by staff in BMS (Academy → Courses), never by the importer.
    CATEGORIES = [('certification', 'Microsoft certification'), ('development', 'App development')]
    category = models.CharField(max_length=20, choices=CATEGORIES, default='certification')
    price = models.PositiveIntegerField(null=True, blank=True, help_text='Rupees. Empty hides the price; 0 shows Free.')
    offer_price = models.PositiveIntegerField(null=True, blank=True, help_text='Rupees. Shown with the full price struck through.')
    price_note = models.CharField(max_length=120, blank=True, help_text='e.g. One-time fee · lifetime access')

    class Meta:
        ordering = ['sort_order']

    # Plain glyphs per track (Font Awesome). Deliberately not Microsoft's
    # product logos: the portal says it is not affiliated with Microsoft.
    ICONS = {'pl900': 'fa-cubes', 'ab410': 'fa-wand-magic-sparkles',
             'pl300': 'fa-chart-column', 'ab400': 'fa-code', 'flutter': 'fa-mobile-screen-button'}

    @property
    def icon(self):
        return self.ICONS.get(self.id, 'fa-graduation-cap')

    @property
    def is_certification(self):
        return self.category == 'certification'

    @property
    def price_label(self):
        return _rupees(self.price)

    @property
    def offer_label(self):
        # Only a real discount counts as an offer.
        if self.offer_price is not None and self.price and self.offer_price < self.price:
            return _rupees(self.offer_price)
        return ''

    @property
    def selling_price(self):
        return self.offer_price if self.offer_label else self.price

    def __str__(self):
        return f'{self.code} {self.name}'


class Domain(models.Model):
    id = models.CharField(primary_key=True, max_length=20)          # "q1"
    track = models.ForeignKey(Track, on_delete=models.CASCADE, related_name='domains')
    name = models.CharField(max_length=200)
    weight = models.CharField(max_length=50)
    blurb = models.TextField(blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['sort_order']

    @property
    def is_exam_weight(self):
        return '%' in self.weight

    def __str__(self):
        return self.name


class Lesson(models.Model):
    id = models.CharField(primary_key=True, max_length=20)          # "a6"
    track = models.ForeignKey(Track, on_delete=models.CASCADE, related_name='lessons')
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, related_name='lessons')
    num = models.CharField(max_length=20)
    title = models.CharField(max_length=300)
    minutes = models.PositiveSmallIntegerField(default=0)
    summary_html = models.TextField(blank=True)
    content_html = models.TextField(blank=True)
    terms = models.JSONField(default=list)
    exam_tip = models.TextField(blank=True)
    widget = models.CharField(max_length=20, blank=True)
    sorter = models.JSONField(null=True, blank=True)
    lab_steps = models.JSONField(default=list)
    lab_check = models.JSONField(default=list)
    # Phone-screen mocks drawn by static/academy/flutter-mocks.js into the
    # <div class="mock-slot" data-mock="N"> placeholders of content_html.
    mocks = models.JSONField(default=list, blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    # Set from the admin, never by import_labs, so re-imports keep it.
    # YouTube, Vimeo or a direct .mp4/.webm link.
    video_url = models.URLField(max_length=500, blank=True)

    class Meta:
        ordering = ['track__sort_order', 'domain__sort_order', 'sort_order']

    @property
    def video(self):
        from .video import embed
        return embed(self.video_url)

    def __str__(self):
        return f'{self.num} {self.title}'


class ExerciseFile(models.Model):
    """One exercise file. They are all small text files (1.4 MB for the
    whole package), so the text lives in the database rather than in media
    storage, which Railway wipes on redeploy."""
    id = models.CharField(primary_key=True, max_length=300)         # "ab400/v9/start/X.cs"
    zip_path = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    content = models.TextField(blank=True)
    size_bytes = models.PositiveIntegerField(default=0)
    sha256 = models.CharField(max_length=64, blank=True)
    # Tracks whose lessons or course data use this file, for access checks.
    track_ids = models.JSONField(default=list)

    @property
    def filename(self):
        return self.zip_path.rsplit('/', 1)[-1]

    @property
    def ext(self):
        return self.zip_path.rsplit('.', 1)[-1].lower() if '.' in self.zip_path else ''

    def __str__(self):
        return self.id


class LessonFile(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='lesson_files')
    file = models.ForeignKey(ExerciseFile, on_delete=models.PROTECT, related_name='+')
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['sort_order']


class Question(models.Model):
    SOURCE_CHOICES = [('lesson', 'Lesson quiz'), ('bank', 'Question bank')]

    track = models.ForeignKey(Track, on_delete=models.CASCADE, related_name='questions')
    lesson = models.ForeignKey(Lesson, null=True, blank=True, on_delete=models.SET_NULL,
                               related_name='questions')
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default='lesson')
    sort_order = models.PositiveSmallIntegerField(default=0)
    question = models.TextField()
    options = models.JSONField(default=list)
    answer = models.PositiveSmallIntegerField()                      # 0-based, never sent early
    explanation = models.TextField(blank=True)
    # A question dropped from a later package is retired, not deleted, so
    # old test attempts can still show it.
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self):
        return self.question[:80]


class ContentImport(models.Model):
    """One run of import_labs, so an unchanged package is skipped."""
    package_sha256 = models.CharField(max_length=64)
    content_version = models.CharField(max_length=20, blank=True)
    counts = models.JSONField(default=dict)
    imported_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-imported_at']


# ---- Students ----------------------------------------------------------------

class Student(models.Model):
    STATUS_CHOICES = [('active', 'Active'), ('inactive', 'Inactive')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    phone = models.CharField(max_length=20, blank=True)
    batch = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    notes = models.TextField(blank=True)
    last_lesson = models.ForeignKey(Lesson, null=True, blank=True, on_delete=models.SET_NULL,
                                    related_name='+')
    # Trainer override: skip course and lesson locks for this student.
    unlock_all = models.BooleanField(default=False)
    # Badge keys already announced, so each "new badge" pop-up shows once.
    seen_badges = models.JSONField(default=list, blank=True)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL,
                                   related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['user__first_name', 'user__username']

    @property
    def name(self):
        return self.user.get_full_name() or self.user.username

    @property
    def is_active(self):
        return self.status == 'active' and self.user.is_active

    def __str__(self):
        return self.name


class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    track = models.ForeignKey(Track, on_delete=models.CASCADE, related_name='enrollments')
    batch = models.CharField(max_length=100, blank=True)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'track')
        ordering = ['track__sort_order']


# ---- Learner data --------------------------------------------------------------

class LabProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='academy_lab_progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='+')
    ticked_steps = models.JSONField(default=list)                    # e.g. [0, 1, 3]
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'lesson')


class QuizAnswer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='academy_quiz_answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='+')
    last_choice = models.PositiveSmallIntegerField()
    ever_correct = models.BooleanField(default=False)
    attempts = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'question')


class TestAttempt(models.Model):
    PASS_MARK = 700

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='academy_tests')
    track = models.ForeignKey(Track, on_delete=models.CASCADE, related_name='+')
    question_ids = models.JSONField(default=list)                    # frozen order
    answers = models.JSONField(default=dict)                         # {"index": choice}
    correct_count = models.PositiveSmallIntegerField(null=True, blank=True)
    score = models.PositiveSmallIntegerField(null=True, blank=True)  # 0-1000
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at']

    @property
    def passed(self):
        return self.score is not None and self.score >= self.PASS_MARK

    @property
    def size(self):
        return len(self.question_ids)


class LearningDay(models.Model):
    """One row per user per day with learning activity, for streaks."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='academy_days')
    date = models.DateField()

    class Meta:
        unique_together = ('user', 'date')
        ordering = ['-date']
