import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Employee(models.Model):
    """Employee profile linked to Django User"""
    EMPLOYMENT_TYPE_CHOICES = [
        ('intern', 'Intern'),
        ('fulltime', 'Full-Time'),
        ('parttime', 'Part-Time'),
    ]

    ROLE_CHOICES = [
        ('employee', 'Employee'),
        ('intern', 'Intern'),
        ('owner', 'Owner'),
        ('partner', 'Partner'),
    ]

    INTERN_TYPE_CHOICES = [
        ('digital', 'Digital Marketing'),
        ('field', 'Field Marketing'),
    ]

    WORK_MODE_CHOICES = [
        ('onsite', 'Onsite'),
        ('hybrid', 'Hybrid'),
        ('remote', 'Remote'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('terminated', 'Terminated'),
        ('on_leave', 'On Leave'),
    ]

    DEPARTMENT_CHOICES = [
        ('engineering', 'Engineering'),
        ('design', 'Design'),
        ('marketing', 'Marketing'),
        ('sales', 'Sales'),
        ('hr', 'Human Resources'),
        ('operations', 'Operations'),
        ('finance', 'Finance'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile')
    employee_id = models.CharField(max_length=20, unique=True, help_text='Employee ID (e.g., EMP001)')
    employment_type = models.CharField(max_length=10, choices=EMPLOYMENT_TYPE_CHOICES)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='employee')
    department = models.CharField(max_length=20, choices=DEPARTMENT_CHOICES, default='engineering')
    designation = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    emergency_contact = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    joining_date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='active')

    # Compensation
    monthly_salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Face recognition - reference photo stored on server, ML Kit runs on device
    face_photo = models.ImageField(upload_to='employees/faces/', blank=True, null=True,
                                   help_text='Reference photo for face recognition')
    face_encoding = models.JSONField(null=True, blank=True,
                                     help_text='Face encoding/embedding data for server-side verification')

    # Office location for geo-fenced attendance
    office_latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    office_longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    allowed_radius_meters = models.IntegerField(default=100,
                                                 help_text='Allowed distance from office for attendance')
    work_mode = models.CharField(max_length=10, choices=WORK_MODE_CHOICES, default='onsite',
                                 help_text='Onsite, Hybrid, or fully Remote. Hybrid/remote can check in without QR/geo-fence.')

    profile_photo = models.ImageField(upload_to='employees/photos/', blank=True, null=True)
    notes = models.TextField(blank=True)

    # Intern-specific fields (migrated from CRM InternProfile)
    intern_type = models.CharField(max_length=10, choices=INTERN_TYPE_CHOICES, blank=True, default='',
                                    help_text='Digital or Field marketing (for interns)')
    commission_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=5.00,
                                                 help_text='Default commission percentage (for interns)')
    supervisor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='supervised_employees',
                                    help_text='Supervisor (for interns)')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['employee_id']

    def __str__(self):
        return f"{self.employee_id} - {self.user.get_full_name() or self.user.username}"

    @property
    def full_name(self):
        return self.user.get_full_name() or self.user.username


class DeviceToken(models.Model):
    """FCM device tokens for push notifications"""
    PLATFORM_CHOICES = [
        ('android', 'Android'),
        ('ios', 'iOS'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='device_tokens')
    token = models.TextField(unique=True)
    platform = models.CharField(max_length=10, choices=PLATFORM_CHOICES)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.employee.employee_id} - {self.platform}"


class Attendance(models.Model):
    """Daily attendance records"""
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('half_day', 'Half Day'),
        ('late', 'Late'),
        ('work_from_home', 'Work From Home'),
    ]

    VERIFICATION_METHOD_CHOICES = [
        ('face', 'Face Recognition'),
        ('qr', 'QR Code'),
        ('location', 'Location'),
        ('face_qr', 'Face + QR'),
        ('face_location', 'Face + Location'),
        ('face_local', 'Face (On-Device) + QR'),
        ('remote', 'Remote (Face only)'),
        ('manual', 'Manual (Admin)'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField(default=timezone.now)
    check_in = models.DateTimeField(null=True, blank=True)
    check_out = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='present')
    verification_method = models.CharField(max_length=15, choices=VERIFICATION_METHOD_CHOICES, default='manual')

    # Location data
    check_in_latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    check_in_longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    check_out_latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    check_out_longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)

    # Face verification
    face_verified = models.BooleanField(default=False)
    face_confidence = models.FloatField(null=True, blank=True, help_text='Face match confidence (0-1)')
    face_photo = models.ImageField(upload_to='employees/attendance_faces/', blank=True, null=True,
                                   help_text='Selfie taken during check-in')

    # QR verification
    qr_verified = models.BooleanField(default=False)

    # Daily hours policy snapshot + shortfall tracking
    required_hours = models.DecimalField(max_digits=4, decimal_places=2, default=6.00,
                                         help_text='Required working hours for this day (snapshot from OfficeConfig)')
    worked_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                       help_text='Actual hours worked, set at check-out')
    pending_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0,
                                        help_text='Shortfall = required_hours - worked_hours (0 if worked >= required)')
    is_force_checkout = models.BooleanField(default=False,
                                            help_text='True if employee force-checked-out before completing required hours')
    is_remote = models.BooleanField(default=False,
                                    help_text='True if checked in remotely (hybrid/remote employees)')

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-check_in']
        unique_together = ['employee', 'date']
        verbose_name_plural = 'Attendances'

    def __str__(self):
        return f"{self.employee.employee_id} - {self.date} - {self.status}"

    @property
    def working_hours(self):
        if self.check_in and self.check_out:
            delta = self.check_out - self.check_in
            return round(delta.total_seconds() / 3600, 2)
        return 0

    def minimum_checkout_time(self, floor_time=None):
        """Earliest timestamp when check-out is allowed.

        Returns max(check_in + required_hours, today_floor). floor_time is a
        datetime.time (e.g. 16:00). If not provided, falls back to OfficeConfig.
        """
        if not self.check_in:
            return None
        from datetime import datetime, time as dtime, timedelta
        from django.utils import timezone as tz
        required_delta = self.check_in + timedelta(hours=float(self.required_hours))
        if floor_time is None:
            cfg = OfficeConfig.objects.first()
            floor_time = cfg.min_checkout_time_floor if cfg else dtime(16, 0)
        local_check_in = tz.localtime(self.check_in) if tz.is_aware(self.check_in) else self.check_in
        floor_naive = datetime.combine(local_check_in.date(), floor_time)
        if tz.is_aware(self.check_in):
            floor_dt = tz.make_aware(floor_naive, tz.get_current_timezone())
        else:
            floor_dt = floor_naive
        return max(required_delta, floor_dt)

    def is_checkout_allowed(self, now=None, floor_time=None):
        if not self.check_in:
            return False
        from django.utils import timezone as tz
        now = now or tz.now()
        min_time = self.minimum_checkout_time(floor_time=floor_time)
        return min_time is not None and now >= min_time

    def seconds_until_eligible(self, now=None, floor_time=None):
        if not self.check_in:
            return None
        from django.utils import timezone as tz
        now = now or tz.now()
        min_time = self.minimum_checkout_time(floor_time=floor_time)
        if min_time is None:
            return None
        remaining = (min_time - now).total_seconds()
        return max(int(remaining), 0)


class LateCheckInGrant(models.Model):
    """One-time permission for an employee to check in after the daily cutoff."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='late_checkin_grants')
    date = models.DateField(help_text='Date this grant applies to')
    reason = models.TextField(help_text='Reason the employee is being allowed to check in late')
    granted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='granted_late_checkins')
    consumed_at = models.DateTimeField(null=True, blank=True,
                                       help_text='Set when the employee uses this grant to check in')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['employee', 'date']

    def __str__(self):
        return f"{self.employee.employee_id} - {self.date} - {'consumed' if self.consumed_at else 'pending'}"

    @property
    def is_consumed(self):
        return self.consumed_at is not None


class LeaveType(models.Model):
    """Types of leave available"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)
    days_allowed = models.IntegerField(default=12, help_text='Max days per year')
    is_paid = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class LeaveRequest(models.Model):
    """Employee leave requests"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.SET_NULL, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='reviewed_leaves')
    review_notes = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee.employee_id} - {self.leave_type} ({self.start_date} to {self.end_date})"

    @property
    def total_days(self):
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return 0


class WorkAssignment(models.Model):
    """Work/tasks assigned to employees from admin"""
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    STATUS_CHOICES = [
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('on_hold', 'On Hold'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    assigned_to = models.ManyToManyField(Employee, related_name='work_assignments')
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_work')
    project = models.ForeignKey('core.Project', on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='employee_assignments')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='assigned')
    due_date = models.DateField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    attachment = models.FileField(upload_to='employees/work_assignments/', blank=True, null=True,
                                  help_text='PDF or document attached to this task')
    notes = models.TextField(blank=True, help_text='Employee can add progress notes')
    confidentiality_disclaimer = models.TextField(
        blank=True,
        help_text='Confidentiality notice or disclaimer shown to assigned employees'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        employees = ', '.join(e.employee_id for e in self.assigned_to.all()[:3])
        return f"{self.title} -> {employees}"

    @property
    def is_overdue(self):
        if self.due_date and self.status not in ['completed', 'cancelled']:
            return timezone.now().date() > self.due_date
        return False


class WorkUpdate(models.Model):
    """Status updates on work assignments by employees"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assignment = models.ForeignKey(WorkAssignment, on_delete=models.CASCADE, related_name='updates')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='work_updates')
    message = models.TextField()
    attachment = models.FileField(upload_to='employees/work_updates/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Update on {self.assignment.title} by {self.employee.employee_id}"


class Notification(models.Model):
    """Push notification records"""
    TYPE_CHOICES = [
        ('general', 'General'),
        ('attendance', 'Attendance'),
        ('leave', 'Leave'),
        ('work', 'Work Assignment'),
        ('announcement', 'Announcement'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='notifications',
                                  null=True, blank=True, help_text='Null = broadcast to all')
    title = models.CharField(max_length=255)
    body = models.TextField()
    notification_type = models.CharField(max_length=15, choices=TYPE_CHOICES, default='general')
    data = models.JSONField(null=True, blank=True, help_text='Extra data payload for the app')
    is_read = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        target = self.employee.employee_id if self.employee else 'All'
        return f"[{target}] {self.title}"


class OfficeConfig(models.Model):
    """Office configuration for attendance - singleton"""
    from datetime import time as _dtime
    qr_code = models.CharField(max_length=255, unique=True, help_text='Static QR code value for office sticker')
    office_name = models.CharField(max_length=100, default='Main Office')
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)

    # Attendance policy
    daily_required_hours = models.DecimalField(max_digits=4, decimal_places=2, default=6.00,
                                               help_text='Required working hours per day (default 6)')
    check_in_deadline = models.TimeField(default=_dtime(10, 15),
                                         help_text='Check-in cutoff time. After this only admin can add check-in.')
    min_checkout_time_floor = models.TimeField(default=_dtime(16, 0),
                                               help_text='Earliest time employees may check out (e.g. 4:00 PM)')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Office Configuration'

    def __str__(self):
        return f"{self.office_name} - {self.qr_code[:20]}"

    def save(self, *args, **kwargs):
        # Ensure only one config exists per office name
        super().save(*args, **kwargs)


class QRCode(models.Model):
    """Daily QR codes generated by admin for attendance"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=255, unique=True)
    date = models.DateField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"QR: {self.date} - {'Active' if self.is_active else 'Expired'}"

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at


class ScheduledClass(models.Model):
    """Scheduled classes/training sessions for interns"""
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    instructor = models.CharField(max_length=255, blank=True, help_text='Name of the instructor/trainer')
    location = models.CharField(max_length=255, blank=True, help_text='Room, link, or address')
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='scheduled')
    interns = models.ManyToManyField(Employee, related_name='scheduled_classes', blank=True,
                                     help_text='Leave empty to include all interns')
    attachment = models.FileField(upload_to='employees/class_materials/', blank=True, null=True,
                                  help_text='Study material or agenda')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_classes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date', 'start_time']
        verbose_name_plural = 'Scheduled Classes'

    def __str__(self):
        return f"{self.title} - {self.date}"

    @property
    def is_upcoming(self):
        today = timezone.now().date()
        if self.date > today:
            return True
        if self.date == today and self.end_time > timezone.now().time():
            return True
        return False


class InternAssessment(models.Model):
    """A test/assessment given to an intern, with score and downloadable files.

    Created by admins from the HR employee detail page; the intern can view
    their own assessments (score, test paper, answer key) from their login.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name='assessments',
        help_text='The intern this assessment belongs to'
    )
    title = models.CharField(max_length=255, help_text='e.g. "Aptitude Test 1"')
    description = models.TextField(blank=True)
    date = models.DateField(default=timezone.localdate, help_text='Date the test was taken')
    max_score = models.DecimalField(max_digits=6, decimal_places=2, help_text='Total marks (out of)')
    scored = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True,
        help_text='Marks the intern scored (leave blank if not yet graded)'
    )
    test_file = models.FileField(
        upload_to='employees/assessments/papers/', blank=True, null=True,
        help_text='The test paper (PDF)'
    )
    answer_key_file = models.FileField(
        upload_to='employees/assessments/answer_keys/', blank=True, null=True,
        help_text='The answer key (PDF) — visible to the intern'
    )
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_assessments'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'Intern Assessment'
        verbose_name_plural = 'Intern Assessments'

    def __str__(self):
        return f"{self.title} - {self.employee.full_name}"

    @property
    def is_graded(self):
        return self.scored is not None

    @property
    def percentage(self):
        if self.scored is None or not self.max_score:
            return None
        return round(float(self.scored) / float(self.max_score) * 100, 1)


class Payroll(models.Model):
    """Monthly payroll/stipend record for an employee"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('paid', 'Paid'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='payrolls')
    month = models.IntegerField(help_text='Month (1-12)')
    year = models.IntegerField()

    # Base pay
    base_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                                       help_text='Monthly salary or stipend')

    # Attendance
    working_days = models.IntegerField(default=0, help_text='Total working days in the month')
    days_present = models.IntegerField(default=0)
    days_absent = models.IntegerField(default=0, help_text='Unpaid leave / absent days')
    total_pending_hours = models.DecimalField(max_digits=7, decimal_places=2, default=0,
                                              help_text='Sum of shortfall hours across the month (from Attendance.pending_hours)')

    # Leave deductions
    paid_leave_days = models.IntegerField(default=0)
    unpaid_leave_days = models.IntegerField(default=0)
    leave_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                                           help_text='Amount deducted for unpaid leave')

    # Additions & deductions
    bonus = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                                      help_text='Other deductions (tax, etc.)')

    # Final
    net_pay = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField(blank=True)

    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-year', '-month']
        unique_together = ['employee', 'month', 'year']

    def __str__(self):
        return f"{self.employee.employee_id} - {self.month}/{self.year} - {self.net_pay}"

    def calculate(self):
        """Calculate net pay based on salary, attendance, and leave.

        Also rolls up Attendance.pending_hours for the month into total_pending_hours.
        """
        from django.db.models import Sum
        pending_sum = Attendance.objects.filter(
            employee=self.employee,
            date__year=self.year,
            date__month=self.month,
        ).aggregate(total=Sum('pending_hours'))['total'] or 0
        self.total_pending_hours = pending_sum

        if self.working_days > 0:
            per_day = self.base_salary / self.working_days
            self.leave_deduction = per_day * self.unpaid_leave_days
        else:
            self.leave_deduction = 0
        self.net_pay = self.base_salary - self.leave_deduction + self.bonus - self.deductions


class CertificateTemplate(models.Model):
    """Editable templates for certificate content"""
    CERTIFICATE_TYPE_CHOICES = [
        ('inter', 'Internship'),
        ('exp', 'Experience'),
        ('course', 'Course Completion'),
        ('merit', 'Merit'),
        ('particip', 'Participation'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, help_text='e.g. Internship - Student, Internship - Professional')
    certificate_type = models.CharField(max_length=10, choices=CERTIFICATE_TYPE_CHOICES, default='inter')
    title = models.CharField(max_length=200, help_text='Certificate title, e.g. INTERNSHIP CERTIFICATE')
    body_text = models.TextField(
        help_text='Certificate body with placeholders: {salutation}, {student_name}, {college_name}, '
                  '{course_name}, {start_date}, {end_date}, {duration_days}, {mode}, {skills}, '
                  '{pronoun}, {pronoun_cap}, {possessive}, {object_pronoun}'
    )
    wish_text = models.TextField(
        default='We wish {pronoun} success in {possessive} future academic and professional endeavors.',
        help_text='Use {pronoun} for him/her and {possessive} for his/her'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['certificate_type', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_certificate_type_display()})"


class Certificate(models.Model):
    """Standalone certificate for interns/students - not linked to any user model"""
    SALUTATION_CHOICES = [
        ('Mr.', 'Mr.'),
        ('Ms.', 'Ms.'),
        ('Mrs.', 'Mrs.'),
    ]

    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]

    MODE_CHOICES = [
        ('offline', 'Offline'),
        ('online', 'Online'),
        ('hybrid', 'Hybrid'),
    ]

    CERTIFICATE_TYPE_CHOICES = CertificateTemplate.CERTIFICATE_TYPE_CHOICES

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    certificate_number = models.CharField(max_length=50, unique=True, blank=True)
    verification_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    template = models.ForeignKey(CertificateTemplate, on_delete=models.SET_NULL, null=True, blank=True,
                                 help_text='Template used - body_text is copied from template on create')
    certificate_type = models.CharField(max_length=10, choices=CERTIFICATE_TYPE_CHOICES, default='inter',
                                        help_text='Determines ref number prefix')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    title = models.CharField(max_length=200, default='INTERNSHIP CERTIFICATE')

    # Student info
    salutation = models.CharField(max_length=10, choices=SALUTATION_CHOICES, default='Mr.')
    student_name = models.CharField(max_length=200)
    register_number = models.CharField(max_length=50, blank=True,
                                       help_text='College/university register number, e.g. BAI247966 ({register_number})')
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='male')
    college_name = models.CharField(max_length=300, blank=True)

    # Course info
    course_name = models.CharField(max_length=200, blank=True, help_text='e.g. Web Development Internship')
    position = models.CharField(max_length=200, blank=True,
                                help_text='Role held, e.g. Flutter Developer Intern ({position}). '
                                          'Falls back to course_name when blank.')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    duration_days = models.PositiveIntegerField(null=True, blank=True, help_text='Total duration in days')
    mode = models.CharField(max_length=10, choices=MODE_CHOICES, default='offline')

    # Certificate content
    body_text = models.TextField(
        blank=True,
        help_text='Full certificate body content. Use placeholders: {salutation}, {student_name}, '
                  '{register_number}, {college_name}, {course_name}, {position}, {start_date}, {end_date}, '
                  '{duration_days}, {mode}, {skills}, {pronoun} (he/she), {pronoun_cap} (He/She), '
                  '{possessive} (his/her), {object_pronoun} (him/her). Unknown placeholders render literally.'
    )
    skills = models.JSONField(default=list, blank=True, help_text='List of skills (rendered as bullet points in body_text {skills} placeholder)')
    wish_text = models.TextField(
        default='We wish {pronoun} success in {possessive} future academic and professional endeavors.',
        help_text='Use {pronoun} for him/her and {possessive} for his/her'
    )

    # Issuance
    date_of_issuance = models.DateField()
    issued_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.certificate_number} - {self.student_name}"

    @property
    def pronoun(self):
        return 'she' if self.gender == 'female' else 'he'

    @property
    def pronoun_cap(self):
        return 'She' if self.gender == 'female' else 'He'

    @property
    def possessive(self):
        return 'her' if self.gender == 'female' else 'his'

    @property
    def object_pronoun(self):
        return 'her' if self.gender == 'female' else 'him'

    @staticmethod
    def _format_date(d):
        day = d.day
        if 4 <= day <= 20 or 24 <= day <= 30:
            suffix = "th"
        else:
            suffix = ["st", "nd", "rd"][day % 10 - 1]
        return f"{day}{suffix} {d.strftime('%B %Y')}"

    def _skills_html(self):
        from django.utils.html import escape
        if not self.skills:
            return ''
        items = ''.join(f'<li>{escape(s)}</li>' for s in self.skills)
        return f'<ul class="skills-list">{items}</ul>'

    def placeholder_values(self):
        return {
            'salutation': self.salutation,
            'student_name': self.student_name,
            'register_number': self.register_number or '',
            'college_name': self.college_name or '',
            'course_name': self.course_name or '',
            # Bodies predating the position field used {position} to mean course_name.
            'position': self.position or self.course_name or '',
            'start_date': self._format_date(self.start_date) if self.start_date else '',
            'end_date': self._format_date(self.end_date) if self.end_date else '',
            'duration_days': self.duration_days or '',
            'mode': self.get_mode_display() if self.mode else '',
            'skills': self._skills_html(),
            'pronoun': self.pronoun,
            'pronoun_cap': self.pronoun_cap,
            'possessive': self.possessive,
            'pronoun_possessive': self.possessive,
            'object_pronoun': self.object_pronoun,
            'pronoun_object': self.object_pronoun,
        }

    @staticmethod
    def _substitute(text, values):
        """Fill known placeholders, leaving unknown ones visible as literal {name}.

        str.format is all-or-nothing: a single unknown name raises and would
        otherwise cost us every substitution in the text.
        """
        class _Missing(dict):
            def __missing__(self, key):
                return '{' + key + '}'
        try:
            return text.format_map(_Missing(values))
        except (IndexError, ValueError):
            return text

    def render_body_html(self):
        import re
        body = self._substitute(self.body_text or '', self.placeholder_values())
        body = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', body)
        # Browsers submit textarea newlines as CRLF; normalise so blank-line
        # paragraph splitting works on stored bodies.
        body = body.replace('\r\n', '\n').replace('\r', '\n')

        html = ''
        for p in body.split('\n\n'):
            p = p.strip()
            if not p:
                continue
            html += p if p.startswith('<ul') else f'<p class="body-text">{p}</p>'
        return html

    def render_wish_text(self):
        return self._substitute(self.wish_text or '', {
            'pronoun': self.object_pronoun,
            'possessive': self.possessive,
        })

    def save(self, *args, **kwargs):
        if isinstance(self.date_of_issuance, str):
            from datetime import datetime
            self.date_of_issuance = datetime.strptime(self.date_of_issuance, '%Y-%m-%d').date()
        if not self.certificate_number:
            year = str(self.date_of_issuance.year)[-2:]
            type_code = self.certificate_type  # inter, exp, course, merit, particip
            prefix = f"RT/PR/{year}/{type_code}/"
            last = Certificate.objects.filter(
                certificate_number__startswith=prefix
            ).order_by('-certificate_number').first()
            if last:
                try:
                    last_num = int(last.certificate_number.split('/')[-1])
                except ValueError:
                    last_num = 0
                self.certificate_number = f"{prefix}{str(last_num + 1).zfill(3)}"
            else:
                self.certificate_number = f"{prefix}001"
        super().save(*args, **kwargs)


# Agreement e-signing (templates + signable requests)
from .agreement_models import AgreementTemplate, AgreementRequest  # noqa: E402,F401
