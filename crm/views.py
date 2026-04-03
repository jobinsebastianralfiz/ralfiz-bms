from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.contrib.auth.models import User
from django.utils import timezone

from .models import InternProfile, Lead, LeadNote, DailyActivity, Demo
from employees.models import Employee

from datetime import timedelta


def is_admin(user):
    return user.is_superuser or user.is_staff


def is_intern(user):
    """Check if user is an intern via Employee profile"""
    try:
        return user.employee_profile.employment_type == 'intern'
    except Employee.DoesNotExist:
        # Fallback to legacy InternProfile for backwards compat
        return hasattr(user, 'intern_profile')


def can_access_crm(user):
    return is_admin(user) or is_intern(user)


# ─── Dashboard ────────────────────────────────────────────────────────

@login_required
def crm_dashboard(request):
    if not can_access_crm(request.user):
        messages.error(request, 'Access denied. Insufficient permissions.')
        return redirect('dashboard')

    if is_admin(request.user):
        return redirect('crm:intern_list')
    else:
        return redirect('crm:lead_list')


# ─── Leads ────────────────────────────────────────────────────────────

@login_required
def lead_list(request):
    if not can_access_crm(request.user):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    leads = Lead.objects.select_related('assigned_to', 'created_by')

    if is_intern(request.user):
        leads = leads.filter(assigned_to=request.user)

    search = request.GET.get('search', '')
    if search:
        leads = leads.filter(
            Q(contact_person__icontains=search) |
            Q(company_name__icontains=search) |
            Q(phone__icontains=search) |
            Q(email__icontains=search)
        )

    status_filter = request.GET.get('status', '')
    if status_filter:
        leads = leads.filter(status=status_filter)

    source_filter = request.GET.get('source', '')
    if source_filter:
        leads = leads.filter(source=source_filter)

    assigned_filter = request.GET.get('assigned_to', '')
    if assigned_filter:
        leads = leads.filter(assigned_to_id=assigned_filter)

    # Date filters
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        leads = leads.filter(created_at__date__gte=date_from)
    if date_to:
        leads = leads.filter(created_at__date__lte=date_to)

    # Sorting
    sort_by = request.GET.get('sort', '-created_at')
    valid_sorts = {
        'created_at': 'created_at',
        '-created_at': '-created_at',
        'status': 'status',
        '-status': '-status',
        'contact_person': 'contact_person',
        '-contact_person': '-contact_person',
        'closing_probability': 'closing_probability',
        '-closing_probability': '-closing_probability',
        'next_follow_up_date': 'next_follow_up_date',
        '-next_follow_up_date': '-next_follow_up_date',
    }
    if sort_by in valid_sorts:
        leads = leads.order_by(valid_sorts[sort_by])

    # Build date-wise submission summary (for admin)
    datewise_summary = []
    if not is_intern(request.user):
        from django.db.models.functions import TruncDate
        from django.db.models import Count
        from collections import defaultdict

        summary_qs = leads  # use the same filtered queryset
        date_intern_groups = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        for lead in summary_qs.select_related('created_by').all():
            d = lead.created_at.date()
            creator = lead.created_by.get_full_name() if lead.created_by else 'Unknown'
            date_intern_groups[d][creator][lead.status] += 1

        for d in sorted(date_intern_groups.keys(), reverse=True)[:30]:
            for intern_name, statuses in date_intern_groups[d].items():
                datewise_summary.append({
                    'date': d,
                    'submitted_by': intern_name,
                    'count': sum(statuses.values()),
                    'status_breakdown': dict(statuses),
                })

    paginator = Paginator(leads, 20)
    page_number = request.GET.get('page')
    leads = paginator.get_page(page_number)

    interns = User.objects.filter(employee_profile__employment_type='intern', is_active=True)

    context = {
        'leads': leads,
        'search': search,
        'status_filter': status_filter,
        'source_filter': source_filter,
        'assigned_filter': assigned_filter,
        'date_from': date_from,
        'date_to': date_to,
        'sort_by': sort_by,
        'status_choices': Lead.STATUS_CHOICES,
        'source_choices': Lead.SOURCE_CHOICES,
        'interns': interns,
        'datewise_summary': datewise_summary,
    }
    return render(request, 'crm/leads/list.html', context)


@login_required
def lead_create(request):
    if not can_access_crm(request.user):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    if request.method == 'POST':
        contact_person = request.POST.get('contact_person', '').strip()
        phone = request.POST.get('phone', '').strip()

        if not contact_person or not phone:
            messages.error(request, 'Contact person and phone are required.')
            return render(request, 'crm/leads/form.html', _lead_form_context(request))

        duplicates = Lead.check_duplicate(phone=phone, email=request.POST.get('email', ''))
        if duplicates:
            messages.warning(
                request,
                f'Possible duplicate found: {duplicates[0].contact_person} ({duplicates[0].phone}). Lead was still created.'
            )

        lead = Lead.objects.create(
            contact_person=contact_person,
            company_name=request.POST.get('company_name', '').strip(),
            phone=phone,
            email=request.POST.get('email', '').strip(),
            status=request.POST.get('status', 'new'),
            source=request.POST.get('source', 'other'),
            assigned_to_id=request.POST.get('assigned_to') or None,
            next_follow_up_date=request.POST.get('next_follow_up_date') or None,
            closing_probability=int(request.POST.get('closing_probability', 0) or 0),
            notes=request.POST.get('notes', '').strip(),
            created_by=request.user,
        )

        if is_intern(request.user) and not lead.assigned_to:
            lead.assigned_to = request.user
            lead.save()

        messages.success(request, f'Lead "{lead.contact_person}" created successfully.')
        return redirect('crm:lead_detail', pk=lead.pk)

    context = _lead_form_context(request)
    context['form_title'] = 'Create New Lead'
    return render(request, 'crm/leads/form.html', context)


@login_required
def lead_detail(request, pk):
    if not can_access_crm(request.user):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    lead = get_object_or_404(Lead.objects.select_related('assigned_to', 'created_by'), pk=pk)

    if is_intern(request.user) and lead.assigned_to != request.user:
        messages.error(request, 'You can only view your own leads.')
        return redirect('crm:lead_list')

    notes = lead.lead_notes.select_related('created_by').all()
    demos = lead.demos.select_related('conducted_by').all()

    context = {
        'lead': lead,
        'notes': notes,
        'demos': demos,
        'status_choices': Lead.STATUS_CHOICES,
    }
    return render(request, 'crm/leads/detail.html', context)


@login_required
def lead_edit(request, pk):
    if not can_access_crm(request.user):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    lead = get_object_or_404(Lead, pk=pk)

    if is_intern(request.user) and lead.assigned_to != request.user:
        messages.error(request, 'You can only edit your own leads.')
        return redirect('crm:lead_list')

    if request.method == 'POST':
        lead.contact_person = request.POST.get('contact_person', '').strip()
        lead.company_name = request.POST.get('company_name', '').strip()
        lead.phone = request.POST.get('phone', '').strip()
        lead.email = request.POST.get('email', '').strip()
        lead.status = request.POST.get('status', lead.status)
        lead.source = request.POST.get('source', lead.source)
        lead.assigned_to_id = request.POST.get('assigned_to') or None
        lead.next_follow_up_date = request.POST.get('next_follow_up_date') or None
        lead.closing_probability = int(request.POST.get('closing_probability', 0) or 0)
        lead.notes = request.POST.get('notes', '').strip()
        lead.save()

        messages.success(request, f'Lead "{lead.contact_person}" updated successfully.')
        return redirect('crm:lead_detail', pk=lead.pk)

    context = _lead_form_context(request)
    context['lead'] = lead
    context['form_title'] = f'Edit: {lead.contact_person}'
    return render(request, 'crm/leads/form.html', context)


@login_required
def lead_change_status(request, pk):
    if request.method != 'POST':
        return redirect('crm:lead_detail', pk=pk)

    if not can_access_crm(request.user):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    lead = get_object_or_404(Lead, pk=pk)
    new_status = request.POST.get('status')

    if new_status and new_status in dict(Lead.STATUS_CHOICES):
        lead.status = new_status
        lead.save()
        messages.success(request, f'Lead status changed to {lead.get_status_display()}.')
    else:
        messages.error(request, 'Invalid status.')

    return redirect('crm:lead_detail', pk=pk)


@login_required
def lead_note_create(request, lead_pk):
    if request.method != 'POST':
        return redirect('crm:lead_detail', pk=lead_pk)

    if not can_access_crm(request.user):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    lead = get_object_or_404(Lead, pk=lead_pk)
    note_text = request.POST.get('note', '').strip()

    if note_text:
        LeadNote.objects.create(lead=lead, note=note_text, created_by=request.user)
        messages.success(request, 'Note added successfully.')
    else:
        messages.error(request, 'Note cannot be empty.')

    return redirect('crm:lead_detail', pk=lead_pk)


@login_required
def lead_check_duplicate(request):
    if not can_access_crm(request.user):
        return JsonResponse({'error': 'Access denied'}, status=403)

    phone = request.GET.get('phone', '')
    email = request.GET.get('email', '')

    duplicates = Lead.check_duplicate(phone=phone, email=email)
    results = [{
        'id': d.pk,
        'contact_person': d.contact_person,
        'company_name': d.company_name,
        'phone': d.phone,
        'email': d.email,
        'status': d.get_status_display(),
    } for d in duplicates]

    return JsonResponse({'duplicates': results})


def _lead_form_context(request):
    interns = User.objects.filter(employee_profile__employment_type='intern', is_active=True)
    return {
        'status_choices': Lead.STATUS_CHOICES,
        'source_choices': Lead.SOURCE_CHOICES,
        'interns': interns,
    }


# ─── Activities ───────────────────────────────────────────────────────

@login_required
def activity_list(request):
    if not can_access_crm(request.user):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    activities = DailyActivity.objects.select_related('intern', 'approved_by')

    if is_intern(request.user):
        activities = activities.filter(intern=request.user)

    date_filter = request.GET.get('date', '')
    if date_filter:
        activities = activities.filter(date=date_filter)

    intern_filter = request.GET.get('intern', '')
    if intern_filter and is_admin(request.user):
        activities = activities.filter(intern_id=intern_filter)

    approval_filter = request.GET.get('approval_status', '')
    if approval_filter:
        activities = activities.filter(approval_status=approval_filter)

    paginator = Paginator(activities, 20)
    page_number = request.GET.get('page')
    activities = paginator.get_page(page_number)

    interns = User.objects.filter(employee_profile__employment_type='intern', is_active=True)

    context = {
        'activities': activities,
        'date_filter': date_filter,
        'intern_filter': intern_filter,
        'approval_filter': approval_filter,
        'approval_choices': DailyActivity.APPROVAL_STATUS_CHOICES,
        'interns': interns,
    }
    return render(request, 'crm/activities/list.html', context)


@login_required
def activity_create(request):
    if not can_access_crm(request.user):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    today = timezone.now().date()

    if is_intern(request.user):
        existing = DailyActivity.objects.filter(intern=request.user, date=today).first()
        if existing:
            messages.info(request, "You already have an entry for today. Editing existing entry.")
            return redirect('crm:activity_edit', pk=existing.pk)

    intern_type = 'digital'
    if is_intern(request.user):
        intern_type = getattr(request.user.employee_profile, 'intern_type', 'digital') or 'digital'

    if request.method == 'POST':
        activity_date = request.POST.get('date', str(today))
        activity_intern_type = request.POST.get('intern_type', intern_type)

        if is_intern(request.user):
            intern_user = request.user
        else:
            intern_id = request.POST.get('intern')
            if not intern_id:
                messages.error(request, 'Please select an intern.')
                return render(request, 'crm/activities/form.html', _activity_form_context(request, intern_type))
            intern_user = get_object_or_404(User, pk=intern_id)

        if DailyActivity.objects.filter(intern=intern_user, date=activity_date).exists():
            messages.error(request, f'Activity entry already exists for {intern_user} on {activity_date}.')
            return render(request, 'crm/activities/form.html', _activity_form_context(request, intern_type))

        DailyActivity.objects.create(
            intern=intern_user,
            date=activity_date,
            intern_type=activity_intern_type,
            social_media_posts=int(request.POST.get('social_media_posts', 0) or 0),
            reels_created=int(request.POST.get('reels_created', 0) or 0),
            dms_sent=int(request.POST.get('dms_sent', 0) or 0),
            digital_leads_generated=int(request.POST.get('digital_leads_generated', 0) or 0),
            calls_made=int(request.POST.get('calls_made', 0) or 0),
            visits_done=int(request.POST.get('visits_done', 0) or 0),
            demos_conducted=int(request.POST.get('demos_conducted', 0) or 0),
            field_leads_generated=int(request.POST.get('field_leads_generated', 0) or 0),
            remarks=request.POST.get('remarks', '').strip(),
        )

        messages.success(request, 'Daily activity logged successfully.')
        return redirect('crm:activity_list')

    context = _activity_form_context(request, intern_type)
    context['form_title'] = 'Log Daily Activity'
    return render(request, 'crm/activities/form.html', context)


@login_required
def activity_edit(request, pk):
    if not can_access_crm(request.user):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    activity = get_object_or_404(DailyActivity, pk=pk)

    if is_intern(request.user):
        if activity.intern != request.user:
            messages.error(request, 'You can only edit your own activities.')
            return redirect('crm:activity_list')
        if not activity.is_editable:
            messages.error(request, 'This activity can no longer be edited (24-hour window expired).')
            return redirect('crm:activity_list')

    if request.method == 'POST':
        activity.intern_type = request.POST.get('intern_type', activity.intern_type)
        activity.social_media_posts = int(request.POST.get('social_media_posts', 0) or 0)
        activity.reels_created = int(request.POST.get('reels_created', 0) or 0)
        activity.dms_sent = int(request.POST.get('dms_sent', 0) or 0)
        activity.digital_leads_generated = int(request.POST.get('digital_leads_generated', 0) or 0)
        activity.calls_made = int(request.POST.get('calls_made', 0) or 0)
        activity.visits_done = int(request.POST.get('visits_done', 0) or 0)
        activity.demos_conducted = int(request.POST.get('demos_conducted', 0) or 0)
        activity.field_leads_generated = int(request.POST.get('field_leads_generated', 0) or 0)
        activity.remarks = request.POST.get('remarks', '').strip()

        if is_intern(request.user):
            activity.approval_status = 'pending'

        activity.save()
        messages.success(request, 'Activity updated successfully.')
        return redirect('crm:activity_list')

    context = _activity_form_context(request, activity.intern_type)
    context['activity'] = activity
    context['form_title'] = f'Edit Activity: {activity.date}'
    return render(request, 'crm/activities/form.html', context)


@login_required
def activity_approve(request, pk):
    if request.method != 'POST':
        return redirect('crm:activity_list')

    if not is_admin(request.user):
        messages.error(request, 'Access denied.')
        return redirect('crm:activity_list')

    activity = get_object_or_404(DailyActivity, pk=pk)
    action = request.POST.get('action')

    if action == 'approve':
        activity.approval_status = 'approved'
        activity.approved_by = request.user
        activity.save()
        messages.success(request, 'Activity approved.')
    elif action == 'reject':
        activity.approval_status = 'rejected'
        activity.approved_by = request.user
        activity.save()
        messages.warning(request, 'Activity rejected.')

    return redirect('crm:activity_list')


@login_required
def activity_weekly_summary(request):
    if not can_access_crm(request.user):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    start_date = request.GET.get('start_date', str(week_start))
    end_date = request.GET.get('end_date', str(week_end))

    activities = DailyActivity.objects.filter(
        date__gte=start_date, date__lte=end_date
    ).select_related('intern')

    if is_intern(request.user):
        activities = activities.filter(intern=request.user)

    summary = activities.values(
        'intern__id', 'intern__username', 'intern__first_name', 'intern__last_name'
    ).annotate(
        total_posts=Sum('social_media_posts'),
        total_reels=Sum('reels_created'),
        total_dms=Sum('dms_sent'),
        total_digital_leads=Sum('digital_leads_generated'),
        total_calls=Sum('calls_made'),
        total_visits=Sum('visits_done'),
        total_demos=Sum('demos_conducted'),
        total_field_leads=Sum('field_leads_generated'),
        days_logged=Count('id'),
    )

    context = {
        'summary': summary,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'crm/activities/weekly_summary.html', context)


def _activity_form_context(request, intern_type='digital'):
    interns = User.objects.filter(employee_profile__employment_type='intern', is_active=True)
    return {
        'intern_type_choices': DailyActivity.INTERN_TYPE_CHOICES,
        'default_intern_type': intern_type,
        'interns': interns,
        'today': timezone.now().date(),
        'is_admin_user': is_admin(request.user),
    }


# ─── Demos ────────────────────────────────────────────────────────────

@login_required
def demo_list(request):
    if not can_access_crm(request.user):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    demos = Demo.objects.select_related('lead', 'conducted_by', 'created_by')

    if is_intern(request.user):
        demos = demos.filter(
            Q(conducted_by=request.user) | Q(lead__assigned_to=request.user)
        )

    status_filter = request.GET.get('status', '')
    if status_filter:
        demos = demos.filter(status=status_filter)

    date_filter = request.GET.get('date', '')
    if date_filter:
        demos = demos.filter(scheduled_date__date=date_filter)

    conductor_filter = request.GET.get('conducted_by', '')
    if conductor_filter:
        demos = demos.filter(conducted_by_id=conductor_filter)

    paginator = Paginator(demos, 20)
    page_number = request.GET.get('page')
    demos = paginator.get_page(page_number)

    interns = User.objects.filter(employee_profile__employment_type='intern', is_active=True)

    context = {
        'demos': demos,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'conductor_filter': conductor_filter,
        'status_choices': Demo.STATUS_CHOICES,
        'interns': interns,
    }
    return render(request, 'crm/demos/list.html', context)


@login_required
def demo_create(request):
    if not can_access_crm(request.user):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    if request.method == 'POST':
        lead_id = request.POST.get('lead')
        scheduled_date = request.POST.get('scheduled_date')

        if not lead_id or not scheduled_date:
            messages.error(request, 'Lead and scheduled date are required.')
            return render(request, 'crm/demos/form.html', _demo_form_context(request))

        lead = get_object_or_404(Lead, pk=lead_id)

        demo = Demo.objects.create(
            lead=lead,
            scheduled_date=scheduled_date,
            status=request.POST.get('status', 'scheduled'),
            conducted_by_id=request.POST.get('conducted_by') or None,
            closing_probability=int(request.POST.get('closing_probability', 0) or 0),
            outcome_notes=request.POST.get('outcome_notes', '').strip(),
            location=request.POST.get('location', '').strip(),
            created_by=request.user,
        )

        if lead.status not in ('converted', 'lost'):
            lead.status = 'demo_scheduled'
            lead.save()

        messages.success(request, 'Demo scheduled successfully.')
        return redirect('crm:demo_detail', pk=demo.pk)

    context = _demo_form_context(request)
    context['form_title'] = 'Schedule New Demo'
    return render(request, 'crm/demos/form.html', context)


@login_required
def demo_detail(request, pk):
    if not can_access_crm(request.user):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    demo = get_object_or_404(
        Demo.objects.select_related('lead', 'lead__assigned_to', 'conducted_by', 'created_by'),
        pk=pk
    )

    if is_intern(request.user):
        if demo.conducted_by != request.user and demo.lead.assigned_to != request.user:
            messages.error(request, 'Access denied.')
            return redirect('crm:demo_list')

    context = {
        'demo': demo,
        'status_choices': Demo.STATUS_CHOICES,
    }
    return render(request, 'crm/demos/detail.html', context)


@login_required
def demo_edit(request, pk):
    if not can_access_crm(request.user):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    demo = get_object_or_404(Demo, pk=pk)

    if request.method == 'POST':
        demo.scheduled_date = request.POST.get('scheduled_date', demo.scheduled_date)
        demo.status = request.POST.get('status', demo.status)
        demo.conducted_by_id = request.POST.get('conducted_by') or None
        demo.closing_probability = int(request.POST.get('closing_probability', 0) or 0)
        demo.outcome_notes = request.POST.get('outcome_notes', '').strip()
        demo.location = request.POST.get('location', '').strip()
        demo.save()

        messages.success(request, 'Demo updated successfully.')
        return redirect('crm:demo_detail', pk=demo.pk)

    context = _demo_form_context(request)
    context['demo'] = demo
    context['form_title'] = f'Edit Demo: {demo.lead.contact_person}'
    return render(request, 'crm/demos/form.html', context)


@login_required
def demo_update_status(request, pk):
    if request.method != 'POST':
        return redirect('crm:demo_detail', pk=pk)

    if not can_access_crm(request.user):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    demo = get_object_or_404(Demo, pk=pk)
    new_status = request.POST.get('status')

    if new_status and new_status in dict(Demo.STATUS_CHOICES):
        demo.status = new_status
        demo.save()

        if new_status == 'converted':
            demo.lead.status = 'converted'
            demo.lead.save()
        elif new_status == 'completed' and demo.lead.status == 'demo_scheduled':
            demo.lead.status = 'follow_up'
            demo.lead.save()

        messages.success(request, f'Demo status changed to {demo.get_status_display()}.')
    else:
        messages.error(request, 'Invalid status.')

    return redirect('crm:demo_detail', pk=pk)


def _demo_form_context(request):
    if is_intern(request.user):
        leads = Lead.objects.filter(assigned_to=request.user)
    else:
        leads = Lead.objects.all()

    interns = User.objects.filter(employee_profile__employment_type='intern', is_active=True)

    return {
        'leads': leads,
        'status_choices': Demo.STATUS_CHOICES,
        'interns': interns,
    }


# ─── Interns ──────────────────────────────────────────────────────────

@login_required
def intern_list(request):
    if not is_admin(request.user):
        messages.error(request, 'Access denied.')
        return redirect('crm:lead_list')

    employees = Employee.objects.filter(
        employment_type='intern'
    ).select_related('user', 'supervisor')

    intern_data = []
    for emp in employees:
        lead_count = Lead.objects.filter(assigned_to=emp.user).count()
        activity_count = DailyActivity.objects.filter(intern=emp.user).count()
        demo_count = Demo.objects.filter(conducted_by=emp.user).count()
        intern_data.append({
            'profile': emp,
            'lead_count': lead_count,
            'activity_count': activity_count,
            'demo_count': demo_count,
        })

    context = {'intern_data': intern_data}
    return render(request, 'crm/interns/list.html', context)


@login_required
def intern_create(request):
    if not is_admin(request.user):
        messages.error(request, 'Access denied.')
        return redirect('crm:lead_list')

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if not first_name or not username or not password:
            messages.error(request, 'First name, username, and password are required.')
            return render(request, 'crm/interns/form.html', _intern_form_context(request))

        if User.objects.filter(username=username).exists():
            messages.error(request, f'Username "{username}" already exists.')
            return render(request, 'crm/interns/form.html', _intern_form_context(request))

        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email,
        )

        # Generate employee_id
        last_emp = Employee.objects.order_by('-employee_id').first()
        if last_emp and last_emp.employee_id.startswith('EMP'):
            try:
                num = int(last_emp.employee_id[3:]) + 1
            except ValueError:
                num = 1
        else:
            num = 1
        employee_id = f'EMP{num:03d}'

        profile = Employee.objects.create(
            user=user,
            employee_id=employee_id,
            employment_type='intern',
            role='intern',
            department='marketing',
            designation='Intern',
            phone=phone,
            intern_type=request.POST.get('intern_type', 'digital'),
            supervisor_id=request.POST.get('supervisor') or None,
            commission_percentage=request.POST.get('default_commission_percentage', 5.00) or 5.00,
            status=request.POST.get('status', 'active'),
            joining_date=request.POST.get('joining_date') or None,
        )

        # Also create legacy InternProfile for backwards compat
        InternProfile.objects.create(
            user=user,
            intern_type=request.POST.get('intern_type', 'digital'),
            supervisor_id=request.POST.get('supervisor') or None,
            default_commission_percentage=request.POST.get('default_commission_percentage', 5.00) or 5.00,
            status=request.POST.get('status', 'active'),
            joining_date=request.POST.get('joining_date') or None,
        )

        messages.success(request, f'Intern "{user.get_full_name()}" added successfully with login account.')
        return redirect('crm:intern_profile_detail', pk=profile.pk)

    context = _intern_form_context(request)
    context['form_title'] = 'Add New Intern'
    return render(request, 'crm/interns/form.html', context)


@login_required
def intern_profile_detail(request, pk):
    if not is_admin(request.user):
        messages.error(request, 'Access denied.')
        return redirect('crm:lead_list')

    profile = get_object_or_404(Employee.objects.select_related('user', 'supervisor'), pk=pk)

    leads = Lead.objects.filter(assigned_to=profile.user).order_by('-created_at')[:10]
    recent_activities = DailyActivity.objects.filter(intern=profile.user).order_by('-date')[:7]
    demos = Demo.objects.filter(conducted_by=profile.user).order_by('-scheduled_date')[:10]

    lead_stats = Lead.objects.filter(assigned_to=profile.user).aggregate(
        total=Count('id'),
        converted=Count('id', filter=Q(status='converted')),
    )

    context = {
        'profile': profile,
        'leads': leads,
        'recent_activities': recent_activities,
        'demos': demos,
        'lead_stats': lead_stats,
    }
    return render(request, 'crm/interns/detail.html', context)


@login_required
def intern_profile_edit(request, pk):
    if not is_admin(request.user):
        messages.error(request, 'Access denied.')
        return redirect('crm:lead_list')

    profile = get_object_or_404(Employee.objects.select_related('user'), pk=pk)

    if request.method == 'POST':
        # Update user personal details
        user = profile.user
        user.first_name = request.POST.get('first_name', user.first_name).strip()
        user.last_name = request.POST.get('last_name', user.last_name).strip()
        user.email = request.POST.get('email', user.email).strip()
        user.save()

        # Update employee profile (intern fields)
        profile.intern_type = request.POST.get('intern_type', profile.intern_type)
        profile.status = request.POST.get('status', profile.status)
        profile.supervisor_id = request.POST.get('supervisor') or None
        profile.commission_percentage = request.POST.get(
            'default_commission_percentage', profile.commission_percentage
        ) or profile.commission_percentage
        profile.joining_date = request.POST.get('joining_date') or None
        profile.save()

        messages.success(request, f'Profile for {profile.user.get_full_name() or profile.user.username} updated successfully.')
        return redirect('crm:intern_profile_detail', pk=profile.pk)

    context = _intern_form_context(request)
    context['profile'] = profile
    context['form_title'] = f'Edit: {profile.user.get_full_name() or profile.user.username}'
    return render(request, 'crm/interns/form.html', context)


def _intern_form_context(request):
    supervisors = User.objects.filter(is_superuser=True, is_active=True) | User.objects.filter(is_staff=True, is_active=True)
    return {
        'intern_type_choices': Employee.INTERN_TYPE_CHOICES,
        'status_choices': [
            ('active', 'Active'),
            ('inactive', 'Inactive'),
            ('completed', 'Completed'),
        ],
        'supervisors': supervisors.distinct(),
    }
