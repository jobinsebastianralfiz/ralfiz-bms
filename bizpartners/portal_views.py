"""The partner's own portal at /partner/. Shows only that partner's projects."""
from functools import wraps

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Count, Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.cache import never_cache

from .forms import JointUpdateForm
from .models import BusinessPartner, JointIssue, JointPayment, JointProject, JointQuote, JointUpdate
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
    projects = list(partner.projects.prefetch_related('payments', 'expenses')
                    .annotate(open_issues=Count('issues', filter=Q(issues__is_done=False))))
    for p in projects:
        p.m = p.money()
    return projects


CARD_TONES = ('plum', 'teal', 'coral')


def _calendar(projects, payments, today):
    """Right-hand column: what falls due next, then the latest payments, grouped by date."""
    upcoming = []
    horizon = today.replace(year=today.year + 1)
    for p in projects:
        if p.status in ('completed', 'cancelled') and not p.is_fixed:
            continue
        for line in p.m.get('recurring', []):
            if line['next'] and line['next'] <= horizon:
                upcoming.append({'date': line['next'], 'title': p.title, 'what': f"{line['label']} due",
                                 'amount': line['amount'], 'tone': p.tone})
        if p.deadline and p.deadline >= today and p.status not in ('completed', 'cancelled'):
            upcoming.append({'date': p.deadline, 'title': p.title, 'what': 'Delivery deadline', 'tone': p.tone})
    upcoming.sort(key=lambda e: e['date'])
    tones = {p.pk: p.tone for p in projects}
    recent = [{'date': pay.payment_date, 'title': pay.project.title, 'what': pay.get_kind_display(),
               'amount': pay.amount, 'tone': tones.get(pay.project_id, 'plum')} for pay in payments]

    def group(events):
        out = []
        for e in events:
            if out and out[-1]['date'] == e['date']:
                out[-1]['events'].append(e)
            else:
                out.append({'date': e['date'], 'events': [e]})
        return out
    return group(upcoming[:8]), group(recent)


def _filler_cards(t, upcoming, used):
    """With fewer than three projects the card row would be mostly empty, so the
    free slots show money at a glance: what has been paid, then the next charge
    (or an invitation to start a project)."""
    out = []
    if t['fixed_projects']:
        due, paid = t['fixed_due'], t['fixed_paid']
        out.append({'kind': 'paid', 'amount': paid, 'of': due, 'label': 'Paid to Ralfiz',
                    'pct': min(100, round(paid * 100 / due)) if due else 0})
    elif t['split_projects']:
        cv, rec = t['split_contract_value'], t['received']
        out.append({'kind': 'paid', 'amount': rec, 'of': cv, 'label': 'Received from clients',
                    'pct': min(100, round(rec * 100 / cv)) if cv else 0})
    nxt = next((e for d in upcoming for e in d['events'] if e.get('amount')), None)
    if nxt:
        nxt_date = next(d['date'] for d in upcoming if nxt in d['events'])
        out.append({'kind': 'next', 'amount': nxt['amount'], 'label': nxt['what'], 'title': nxt['title'],
                    'date': nxt_date})
    out.append({'kind': 'new'})
    tones = CARD_TONES[used:] + CARD_TONES
    out = out[:max(0, 3 - used)]
    for i, c in enumerate(out):
        c['tone'] = tones[i]
    return out


@partner_required
def dashboard(request):
    partner = request.partner
    projects = _projects(partner)
    live = [p for p in projects if p.status != 'cancelled']
    # Running projects first, then the rest, newest first within each.
    live.sort(key=lambda p: (p.status not in JointProject.ACTIVE, p.status == 'completed'))
    for i, p in enumerate(live):
        p.tone = CARD_TONES[i % len(CARD_TONES)]
        if p.is_fixed:
            p.to_pay = p.m['fixed_balance']
        else:
            p.to_pay = -p.m['due_to_partner']
    t = partner.totals(live)
    today = timezone.localdate()
    payments = list(JointPayment.objects.filter(project__partner=partner).select_related('project')[:5])
    upcoming, recent = _calendar(live, payments, today)
    cards = live[:3]
    return render(request, 'bizpartners/portal/dashboard.html', _ctx(
        request, 'dashboard', t=t, today=today,
        first_name=partner.name.split()[0] if partner.name else partner.display_name,
        cards=cards, fillers=_filler_cards(t, upcoming, len(cards)),
        projects=live, upcoming=upcoming, recent=recent,
        recent_pays=[{**e, 'date': d['date']} for d in recent for e in d['events']][:3],
        balance=-t['due_to_partner'],
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
@never_cache  # it shows server and domain passwords: never keep a copy in a browser or proxy cache
def project_detail(request, pk):
    from .issue_views import issue_context
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
        expenses=project.expenses.all(), credentials=project.credentials.filter(shared_with_partner=True),
        updates=project.updates.select_related('author'), update_form=JointUpdateForm(),
        **issue_context(project, request.GET)))


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


# Payment kinds as the partner reads them.
YOUR_KIND = {'partner_to_ralfiz': 'You paid Ralfiz', 'ralfiz_to_partner': 'Ralfiz paid you',
             'client_to_ralfiz': 'Client paid Ralfiz', 'client_to_partner': 'Client paid you'}


@partner_required
def alerts(request):
    """What Ralfiz did since the partner last opened the bell: issues done, messages, payments.

    `seen` comes from the browser; a first visit looks back a week so the bell isn't empty
    on day one. Things the partner did themselves never count.
    """
    from .templatetags.sar import sar
    now = timezone.now()
    seen = parse_datetime(request.GET.get('seen') or '') or now - timezone.timedelta(days=7)
    seen = max(seen, now - timezone.timedelta(days=60))
    me, items = request.user, []

    def url(project_id, anchor):
        return reverse('bizpartners_portal:project', args=[project_id]) + '#' + anchor

    done = (JointIssue.objects.filter(project__partner=request.partner, is_done=True, done_at__gt=seen)
            .exclude(done_by=me).select_related('project').order_by('-done_at'))
    groups = {}
    for i in done[:300]:
        g = groups.setdefault(i.project_id, {'kind': 'done', 'at': i.done_at.isoformat(), 'count': 0,
                                             'project': i.project.title, 'url': url(i.project_id, 'issues'),
                                             'detail': i.title[:140]})
        g['count'] += 1
    for g in groups.values():
        g['title'] = f"Ralfiz marked {g['count']} issue{'s' if g['count'] != 1 else ''} done"
        items.append(g)

    for u in (JointUpdate.objects.filter(project__partner=request.partner, from_partner=False, created_at__gt=seen)
              .exclude(author=me).select_related('project').order_by('-created_at')[:20]):
        items.append({'kind': 'message', 'at': u.created_at.isoformat(), 'count': 1, 'title': 'New message from Ralfiz',
                      'project': u.project.title, 'url': url(u.project_id, 'updates'), 'detail': u.message[:140]})

    for p in (JointPayment.objects.filter(project__partner=request.partner, created_at__gt=seen)
              .select_related('project').order_by('-created_at')[:20]):
        items.append({'kind': 'payment', 'at': p.created_at.isoformat(), 'count': 1,
                      'title': f'{YOUR_KIND.get(p.kind, p.get_kind_display())}: {request.partner.currency} {sar(p.amount)}',
                      'project': p.project.title, 'url': url(p.project_id, 'payments'),
                      'detail': p.payment_date.strftime('%d %b %Y')})

    items.sort(key=lambda r: r['at'], reverse=True)
    return JsonResponse({'now': now.isoformat(), 'count': sum(i['count'] for i in items), 'items': items[:12]})
