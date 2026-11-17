"""Staff side of Business Partners, under /business-partners/."""
import secrets

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import (BusinessPartnerForm, JointExpenseForm, JointPaymentForm, JointProjectForm,
                    JointQuoteForm, JointUpdateForm)
from .models import BusinessPartner, JointExpense, JointPayment, JointProject, JointQuote

# The three ledgers on a joint project share one add/edit/delete flow.
ITEMS = {
    'quote': (JointQuote, JointQuoteForm, 'Quote', 'quotes'),
    'payment': (JointPayment, JointPaymentForm, 'Payment', 'payments'),
    'expense': (JointExpense, JointExpenseForm, 'Expense', 'expenses'),
}
FILE_FIELD = {'quote': 'file', 'payment': 'receipt', 'expense': 'receipt'}


def _item(kind):
    if kind not in ITEMS:
        raise Http404
    return ITEMS[kind]


@login_required
def partner_list(request):
    partners = list(BusinessPartner.objects.select_related('user'))
    grand = {}
    for p in partners:
        p.t = p.totals()
        for k, v in p.t.items():
            grand[k] = grand.get(k, 0) + v
    return render(request, 'bizpartners/list.html', {'partners': partners, 'grand': grand})


@login_required
def partner_form(request, pk=None):
    partner = get_object_or_404(BusinessPartner, pk=pk) if pk else None
    form = BusinessPartnerForm(request.POST or None, instance=partner)
    if request.method == 'POST' and form.is_valid():
        partner = form.save()
        messages.success(request, f'{partner.display_name} saved.')
        return redirect('bizpartners:detail', pk=partner.pk)
    return render(request, 'bizpartners/form.html', {
        'form': form, 'partner': partner,
        'heading': f'Edit {partner.display_name}' if partner else 'New business partner',
        'back': reverse('bizpartners:detail', args=[partner.pk]) if partner else reverse('bizpartners:list'),
    })


@login_required
def partner_detail(request, pk):
    partner = get_object_or_404(BusinessPartner.objects.select_related('user'), pk=pk)
    projects = list(partner.projects.prefetch_related('payments', 'expenses'))
    for p in projects:
        p.m = p.money()
    totals = partner.totals([p for p in projects if p.status != 'cancelled'])
    return render(request, 'bizpartners/detail.html', {
        'partner': partner, 'projects': projects, 't': totals,
        'new_password': request.session.pop('bizpartner_new_password', None),
    })


@login_required
@require_POST
def partner_login(request, pk):
    """Create the partner's portal login, or reset its password."""
    partner = get_object_or_404(BusinessPartner, pk=pk)
    password = request.POST.get('password', '').strip() or secrets.token_urlsafe(8)
    if len(password) < 8:
        messages.error(request, 'Use a password of at least 8 characters.')
        return redirect('bizpartners:detail', pk=pk)
    user = partner.user
    if user is None:
        username = request.POST.get('username', '').strip() or partner.email
        if not username:
            messages.error(request, 'Enter a username, or add an email to the partner first.')
            return redirect('bizpartners:detail', pk=pk)
        if User.objects.filter(username__iexact=username).exists():
            messages.error(request, f'The username "{username}" is already taken.')
            return redirect('bizpartners:detail', pk=pk)
        user = User.objects.create_user(username=username, email=partner.email, first_name=partner.name[:150])
        partner.user = user
        partner.save(update_fields=['user', 'updated_at'])
    user.set_password(password)
    user.is_active = True
    user.save()
    request.session['bizpartner_new_password'] = password
    messages.success(request, f'Portal login ready for {partner.display_name}. Share the password below once; it will not be shown again.')
    return redirect('bizpartners:detail', pk=pk)


@login_required
@require_POST
def partner_login_toggle(request, pk):
    partner = get_object_or_404(BusinessPartner, pk=pk)
    if partner.user:
        partner.user.is_active = not partner.user.is_active
        partner.user.save(update_fields=['is_active'])
        messages.success(request, 'Portal login ' + ('enabled.' if partner.user.is_active else 'disabled.'))
    return redirect('bizpartners:detail', pk=pk)


@login_required
def project_form(request, partner_pk=None, pk=None):
    project = get_object_or_404(JointProject.objects.select_related('partner'), pk=pk) if pk else None
    partner = project.partner if project else get_object_or_404(BusinessPartner, pk=partner_pk)
    initial = {} if project else {'partner_share_percent': partner.default_partner_share}
    form = JointProjectForm(request.POST or None, instance=project, initial=initial)
    if request.method == 'POST' and form.is_valid():
        project = form.save(commit=False)
        project.partner = partner
        project.save()
        messages.success(request, f'"{project.title}" saved.')
        return redirect('bizpartners:project', pk=project.pk)
    return render(request, 'bizpartners/form.html', {
        'form': form, 'partner': partner,
        'heading': f'Edit {project.title}' if project else f'New joint project with {partner.display_name}',
        'back': reverse('bizpartners:project', args=[project.pk]) if project else reverse('bizpartners:detail', args=[partner.pk]),
    })


@login_required
def project_detail(request, pk):
    project = get_object_or_404(JointProject.objects.select_related('partner', 'linked_project'), pk=pk)
    if request.method == 'POST':
        form = JointUpdateForm(request.POST)
        if form.is_valid():
            u = form.save(commit=False)
            u.project, u.author = project, request.user
            u.save()
            messages.success(request, 'Update posted. The partner can see it.')
        return redirect(reverse('bizpartners:project', args=[pk]) + '#updates')
    return render(request, 'bizpartners/project_detail.html', {
        'project': project, 'partner': project.partner, 'm': project.money(),
        'quotes': project.quotes.all(), 'payments': project.payments.all(), 'expenses': project.expenses.all(),
        'updates': project.updates.select_related('author'), 'update_form': JointUpdateForm(),
    })


@login_required
def project_delete(request, pk):
    project = get_object_or_404(JointProject, pk=pk)
    if request.method == 'POST':
        partner_pk = project.partner_id
        project.delete()
        messages.success(request, f'"{project.title}" deleted.')
        return redirect('bizpartners:detail', pk=partner_pk)
    return render(request, 'bizpartners/confirm_delete.html', {
        'thing': f'joint project "{project.title}" with all its quotes, payments and expenses',
        'back': reverse('bizpartners:project', args=[pk]),
    })


@login_required
def item_form(request, project_pk, kind, pk=None):
    model, form_cls, label, anchor = _item(kind)
    project = get_object_or_404(JointProject.objects.select_related('partner'), pk=project_pk)
    obj = get_object_or_404(model, pk=pk, project=project) if pk else None
    form = form_cls(request.POST or None, request.FILES or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.project = project
        obj.save()
        messages.success(request, f'{label} saved.')
        return redirect(reverse('bizpartners:project', args=[project.pk]) + f'#{anchor}')
    return render(request, 'bizpartners/form.html', {
        'form': form, 'partner': project.partner, 'project': project,
        'heading': f'{"Edit" if obj else "Add"} {label.lower()} · {project.title}',
        'currency': project.currency,
        'back': reverse('bizpartners:project', args=[project.pk]) + f'#{anchor}',
    })


@login_required
def item_delete(request, project_pk, kind, pk):
    model, _form, label, anchor = _item(kind)
    obj = get_object_or_404(model, pk=pk, project_id=project_pk)
    back = reverse('bizpartners:project', args=[project_pk]) + f'#{anchor}'
    if request.method == 'POST':
        f = getattr(obj, FILE_FIELD[kind])
        if f:
            f.delete(save=False)
        obj.delete()
        messages.success(request, f'{label} deleted.')
        return redirect(back)
    return render(request, 'bizpartners/confirm_delete.html', {'thing': f'{label.lower()} "{obj}"', 'back': back})


def send_item_file(obj, kind):
    f = getattr(obj, FILE_FIELD[kind])
    if not f:
        raise Http404
    try:
        return FileResponse(f.open('rb'), as_attachment=False, filename=f.name.rsplit('/', 1)[-1].split('_', 1)[-1])
    except FileNotFoundError:
        raise Http404('File missing from storage.')


@login_required
def item_file(request, project_pk, kind, pk):
    model = _item(kind)[0]
    return send_item_file(get_object_or_404(model, pk=pk, project_id=project_pk), kind)
