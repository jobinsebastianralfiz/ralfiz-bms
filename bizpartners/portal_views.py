"""The partner's own portal at /partner/. Shows only that partner's projects."""
from functools import wraps

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import JointUpdateForm
from .models import BusinessPartner, JointPayment, JointProject, JointQuote
from .views import ITEMS, send_item_file


def _company():
    from core.models import CompanySettings
    c = CompanySettings.get_settings()
    return {'company_name': c.company_name, 'company_email': c.email}


def partner_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{reverse('bizpartners_portal:login')}?next={request.path}")
        partner = getattr(request.user, 'business_partner_profile', None)
        if partner is None or not partner.is_active:
            logout(request)
            messages.error(request, 'This account has no partner portal access.')
            return redirect('bizpartners_portal:login')
        request.partner = partner
        return view(request, *args, **kwargs)
    return wrapper


def _ctx(request, nav, **extra):
    return {'partner': request.partner, 'active_nav': nav, **_company(), **extra}


def _username(login_name):
    if '@' not in login_name:
        return login_name
    p = BusinessPartner.objects.filter(email__iexact=login_name, user__isnull=False).select_related('user').first()
    return p.user.username if p else login_name


def portal_login(request):
    if request.user.is_authenticated and getattr(request.user, 'business_partner_profile', None):
        return redirect('bizpartners_portal:dashboard')
    ctx = _company()
    if request.method == 'POST':
        name = request.POST.get('username', '').strip()
        user = authenticate(request, username=_username(name), password=request.POST.get('password', ''))
        partner = getattr(user, 'business_partner_profile', None) if user else None
        if user is None:
            ctx.update(error='Wrong username or password.', username=name)
        elif partner is None or not partner.is_active:
            ctx.update(error='This account has no partner portal access.', username=name)
        else:
            login(request, user)
            if not request.POST.get('remember'):
                request.session.set_expiry(0)  # ends when the browser closes
            from core.security import safe_next
            return redirect(safe_next(request, request.GET.get('next'), 'bizpartners_portal:dashboard'))
    return render(request, 'bizpartners/portal/login.html', ctx)


def portal_logout(request):
    logout(request)
    return redirect('bizpartners_portal:login')


def _projects(partner):
    projects = list(partner.projects.prefetch_related('payments', 'expenses'))
    for p in projects:
        p.m = p.money()
    return projects


@partner_required
def dashboard(request):
    partner = request.partner
    projects = _projects(partner)
    live = [p for p in projects if p.status != 'cancelled']
    t = partner.totals(live)
    hour = timezone.localtime().hour
    return render(request, 'bizpartners/portal/dashboard.html', _ctx(
        request, 'dashboard', t=t,
        greeting='Good morning' if hour < 12 else ('Good afternoon' if hour < 17 else 'Good evening'),
        active=[p for p in live if p.status in JointProject.ACTIVE],
        projects=live[:6],
        recent_payments=JointPayment.objects.filter(project__partner=partner).select_related('project')[:6],
    ))


@partner_required
def projects(request):
    items = _projects(request.partner)
    status = request.GET.get('status', '')
    if status:
        items = [p for p in items if p.status == status]
    return render(request, 'bizpartners/portal/projects.html', _ctx(
        request, 'projects', projects=items, status=status, statuses=JointProject.STATUS_CHOICES))


@partner_required
def project_detail(request, pk):
    project = get_object_or_404(JointProject, pk=pk, partner=request.partner)
    if request.method == 'POST':
        form = JointUpdateForm(request.POST)
        if form.is_valid():
            u = form.save(commit=False)
            u.project, u.author, u.from_partner = project, request.user, True
            u.save()
            messages.success(request, 'Message sent to the Ralfiz team.')
        return redirect(reverse('bizpartners_portal:project', args=[pk]) + '#updates')
    return render(request, 'bizpartners/portal/project_detail.html', _ctx(
        request, 'projects', project=project, m=project.money(),
        quotes=project.quotes.exclude(status='draft'), payments=project.payments.all(),
        expenses=project.expenses.all(), updates=project.updates.select_related('author'),
        update_form=JointUpdateForm()))


@partner_required
def payments(request):
    pays = JointPayment.objects.filter(project__partner=request.partner).select_related('project')
    return render(request, 'bizpartners/portal/payments.html', _ctx(
        request, 'payments', payments=pays, t=request.partner.totals()))


@partner_required
def quotes(request):
    qs = JointQuote.objects.filter(project__partner=request.partner).exclude(status='draft').select_related('project')
    return render(request, 'bizpartners/portal/quotes.html', _ctx(request, 'quotes', quotes=qs))


@partner_required
def item_file(request, project_pk, kind, pk):
    if kind not in ITEMS:
        raise Http404
    obj = get_object_or_404(ITEMS[kind][0], pk=pk, project_id=project_pk, project__partner=request.partner)
    if kind == 'quote' and obj.status == 'draft':
        raise Http404
    return send_item_file(obj, kind)


@partner_required
def change_password(request):
    form = PasswordChangeForm(request.user, request.POST or None)
    for f in form.fields.values():
        f.widget.attrs['class'] = 'form-control'
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        messages.success(request, 'Password changed.')
        return redirect('bizpartners_portal:dashboard')
    return render(request, 'bizpartners/portal/password.html', _ctx(request, 'password', form=form))
