"""Issue list on a joint project: the partner follows it at /partner/projects/<id>/,
Ralfiz staff run it at /business-partners/projects/<id>/. Laid out like the
Excel tracker, Done / Not Done only. The partner adds issues; only staff
change status, edit or delete."""
import logging
from io import BytesIO

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .issue_ai import MAX_ISSUES, Feedback, IssueAIError, draft_issues, read_upload
from .models import JointIssue, JointIssueImage, JointProject, JointUpdate
from .portal_views import _ctx, partner_required

logger = logging.getLogger(__name__)

PARTNER_SOURCES = [('client', 'Client feedback'), ('partner', 'Partner')]
PREVIEW_ROWS = 25
MAX_IMAGES = 6                    # per issue
MAX_IMAGE_BYTES = 8 * 1024 * 1024


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _filtered(project, GET):
    qs = project.issues.select_related('done_by').prefetch_related('images')
    status = GET.get('status', '')
    if status == 'open':
        qs = qs.filter(is_done=False)
    elif status == 'done':
        qs = qs.filter(is_done=True)
    page = GET.get('page', '')
    if page:
        qs = qs.filter(page='' if page == 'General' else page)
    q = (GET.get('q') or '').strip()
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(action__icontains=q) | Q(section__icontains=q)
                       | Q(notes__icontains=q))
    return qs


def _summary(project):
    rows, order = {}, []
    total = done = 0
    for page, is_done in project.issues.values_list('page', 'is_done'):
        name = page or 'General'
        if name not in rows:
            rows[name] = {'page': name, 'done': 0, 'open': 0, 'total': 0}
            order.append(name)
        r = rows[name]
        r['total'] += 1
        r['done' if is_done else 'open'] += 1
        total += 1
        done += is_done
    return {'total': total, 'done': done, 'open': total - done, 'pages': [rows[n] for n in order]}


def _pages(project):
    seen = []
    for p in project.issues.exclude(page='').values_list('page', flat=True):
        if p not in seen:
            seen.append(p)
    return seen


def issue_context(project, GET):
    """What `_issues.html` needs. Added to both project detail pages."""
    issues = list(_filtered(project, GET).order_by('-number'))  # newest first on the page; Excel keeps 1, 2, 3
    filters = {k: GET.get(k, '') for k in ('status', 'page', 'q')}
    return {
        'issues': issues, 'issue_summary': _summary(project), 'issue_pages': _pages(project),
        'issue_filters': filters, 'issue_filtered': any(filters.values()),
        'issue_preview': PREVIEW_ROWS, 'issue_export_qs': GET.urlencode(),
        'source_choices': JointIssue.SOURCE_CHOICES,
    }


def save_images(request, issue):
    """Attach the pictures sent as `images` (file input or pasted screenshots).
    Returns a message for the ones that were skipped, or ''."""
    files = request.FILES.getlist('images')
    if not files:
        return ''
    room = MAX_IMAGES - issue.images.count()
    checker = forms.ImageField()
    skipped = []
    for f in files:
        if room <= 0:
            skipped.append(f'{f.name} (an issue holds {MAX_IMAGES} pictures)')
            continue
        if f.size > MAX_IMAGE_BYTES:
            skipped.append(f'{f.name} (over 8 MB)')
            continue
        try:
            checker.clean(f)  # Pillow opens it: rejects files that are not pictures
        except forms.ValidationError:
            skipped.append(f'{f.name} (not a picture)')
            continue
        f.seek(0)
        JointIssueImage.objects.create(issue=issue, image=f, uploaded_by=request.user)
        room -= 1
    return ('Not attached: ' + ', '.join(skipped) + '.') if skipped else ''


def _feedback_from_request(request):
    upload = request.FILES.get('file')
    if upload:
        return read_upload(upload)
    return Feedback(request.POST.get('text', ''))


def _rows_from_post(post, staff=False):
    try:
        count = min(int(post.get('count', 0)), MAX_ISSUES)
    except ValueError:
        count = 0
    rows = []
    for i in range(count):
        if not post.get(f'include_{i}'):
            continue
        row = {k: post.get(f'{k}_{i}', '') for k in ('page', 'section', 'title', 'action')}
        if staff:
            row['source'] = post.get(f'source_{i}', '')
        rows.append(row)
    return rows


def _safe_next(request, default):
    nxt = request.POST.get('next') or request.GET.get('next') or ''
    return nxt if nxt.startswith('/') and not nxt.startswith('//') else default


def export_xlsx(project, issues):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

    F = lambda **kw: Font(name='Arial', **kw)  # noqa: E731
    head_fill = PatternFill('solid', fgColor='1F3A5F')
    green, red = PatternFill('solid', fgColor='DCFCE7'), PatternFill('solid', fgColor='FEE2E2')
    thin = Side(style='thin', color='D1D5DB')
    box = Border(left=thin, right=thin, top=thin, bottom=thin)
    s = _summary(project)

    wb = Workbook()
    ws = wb.active
    ws.title = 'Dashboard'
    ws['B1'] = f'{project.title} – Issues'
    ws['B1'].font = F(bold=True, size=14)
    for col, (label, value, fill) in zip('BCD', (('Total', s['total'], None), ('Done', s['done'], green),
                                               ('Not Done', s['open'], red))):
        ws[f'{col}3'], ws[f'{col}4'] = label, value
        ws[f'{col}3'].font = F(bold=True, color='FFFFFF')
        ws[f'{col}3'].fill = head_fill
        ws[f'{col}4'].font = F(bold=True, size=16)
        for c in (f'{col}3', f'{col}4'):
            ws[c].alignment = Alignment(horizontal='center')
            ws[c].border = box
        if fill:
            ws[f'{col}4'].fill = fill
    for col, label in zip('BCDE', ('Page', 'Done', 'Not Done', 'Total')):
        ws[f'{col}6'] = label
        ws[f'{col}6'].font = F(bold=True, color='FFFFFF')
        ws[f'{col}6'].fill = head_fill
        ws[f'{col}6'].border = box
    for r, row in enumerate(s['pages'], start=7):
        for col, key in zip('BCDE', ('page', 'done', 'open', 'total')):
            ws[f'{col}{r}'] = row[key]
            ws[f'{col}{r}'].font = F()
            ws[f'{col}{r}'].border = box
    for col, w in zip('ABCDE', (3, 22, 12, 12, 12)):
        ws.column_dimensions[col].width = w

    ws = wb.create_sheet('Issue List')
    heads = ['#', 'Page', 'Section', 'Issue', 'Action Required', 'Source', 'Status', 'Notes', 'Added', 'Done on']
    ws.append(heads)
    for c in ws[1]:
        c.font = F(bold=True, color='FFFFFF')
        c.fill = head_fill
        c.border = box
        c.alignment = Alignment(vertical='center', wrap_text=True)
    for i in issues:
        ws.append([i.number, i.page, i.section, i.title, i.action, i.get_source_display(), i.status_label,
                   i.notes, timezone.localtime(i.created_at).date(),
                   timezone.localtime(i.done_at).date() if i.done_at else None])
        row = ws.max_row
        for c in ws[row]:
            c.font = F()
            c.border = box
            c.alignment = Alignment(vertical='top', wrap_text=True)
        st = ws.cell(row=row, column=7)
        st.fill = green if i.is_done else red
        st.font = F(bold=True, color='166534' if i.is_done else '991B1B')
        for col in (9, 10):
            ws.cell(row=row, column=col).number_format = 'DD MMM YYYY'
    for col, w in zip('ABCDEFGHIJ', (6, 14, 18, 45, 55, 15, 11, 35, 12, 12)):
        ws.column_dimensions[col].width = w
    ws.freeze_panes = 'A2'
    ws.auto_filter.ref = f'A1:J{max(ws.max_row, 1)}'

    out = BytesIO()
    wb.save(out)
    slug = ''.join(ch if ch.isalnum() else '_' for ch in project.title).strip('_')[:50] or 'project'
    resp = HttpResponse(out.getvalue(),
                        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    resp['Content-Disposition'] = f'attachment; filename="{slug}_issues_{timezone.localdate():%Y%m%d}.xlsx"'
    return resp


def _norm(h):
    return ' '.join(str(h or '').strip().lower().replace('/', ' / ').split())


HEADERS = {
    'page': ('page',),
    'section': ('section',),
    'title': ('issue', 'title', 'issues'),
    'action': ('action required', 'action', 'actions'),
    'source': ('source',),
    'status': ('status',),
    'notes': ('notes', 'note', 'client decision / notes', 'remarks', 'decision'),
}
SOURCES_IN = {'client feedback': 'client', 'client': 'client', 'claude review': 'review',
              'gemini review': 'review', 'review': 'review', 'ralfiz': 'ralfiz', 'partner': 'partner'}


def read_issue_workbook(data):
    """Excel issue tracker -> list of issue dicts. Finds the first sheet that has an Issue header."""
    from openpyxl import load_workbook
    try:
        wb = load_workbook(BytesIO(data), read_only=True, data_only=True)
    except Exception as exc:  # noqa: BLE001 - openpyxl raises many types for a bad file
        raise IssueAIError('That file could not be opened as an Excel workbook (.xlsx).') from exc
    lookup = {name: key for key, names in HEADERS.items() for name in names}
    for ws in wb.worksheets:
        cols, items = None, []
        for row in ws.iter_rows(values_only=True):
            if cols is None:
                found = {}
                for idx, cell in enumerate(row):
                    key = lookup.get(_norm(cell))
                    if key and key not in found:
                        found[key] = idx
                if 'title' in found:
                    cols = found
                continue
            get = lambda k: (str(row[cols[k]]).strip() if k in cols and cols[k] < len(row)  # noqa: E731
                             and row[cols[k]] is not None else '')
            if not get('title'):
                continue
            items.append({
                'page': get('page'), 'section': get('section'), 'title': get('title'),
                'action': get('action'), 'notes': get('notes'),
                'is_done': get('status').lower() == 'done',
                'undated': True,
                'source': SOURCES_IN.get(get('source').lower(), 'client'),
            })
        if cols is not None:
            wb.close()
            return items
    wb.close()
    raise IssueAIError('No sheet in that file has an "Issue" column.')


def _notify_owners(project, issues, user):
    """Tell the owners the partner added issues. Never blocks the save."""
    try:
        from employees.models import Employee, Notification
        from employees.utils import send_push_notification

        n = len(issues)
        who = project.partner.display_name
        title = f'{who} added {n} issue{"s" if n != 1 else ""}'
        body = f'{project.title}: {issues[0].title[:120]}' + (f' (+{n - 1} more)' if n > 1 else '')
        for owner in Employee.objects.filter(status='active', role__in=('owner', 'partner')):
            Notification.objects.create(
                employee=owner, title=title, body=body, notification_type='general',
                data={'kind': 'joint_issues', 'project_id': str(project.pk)})
            send_push_notification(owner, title, body)
    except Exception:  # noqa: BLE001 - a failed alert must not lose the partner's issues
        logger.exception('Could not notify owners about issues on %s', project.pk)


def _review(request, template, ctx_base, project, drafts, notice, back, save_url, sources, source):
    return render(request, template, {
        **ctx_base, 'project': project, 'drafts': drafts, 'notice': notice, 'back': back,
        'save_url': save_url, 'sources': sources, 'source': source, 'issue_pages': _pages(project),
    })


# ---------------------------------------------------------------------------
# Partner portal
# ---------------------------------------------------------------------------

def _partner_project(request, pk):
    return get_object_or_404(JointProject, pk=pk, partner=request.partner)


def _portal_back(project):
    return reverse('bizpartners_portal:project', args=[project.pk]) + '#issues'


@partner_required
def portal_issue_export(request, pk):
    project = _partner_project(request, pk)
    return export_xlsx(project, _filtered(project, request.GET))


@partner_required
@require_POST
def portal_issue_draft(request, pk):
    project = _partner_project(request, pk)
    back = _portal_back(project)
    try:
        feedback = _feedback_from_request(request)
    except IssueAIError as exc:
        messages.error(request, str(exc))
        return redirect(back)
    if not feedback.text.strip():
        messages.error(request, 'Paste the feedback or choose a file first.')
        return redirect(back)
    drafts, notice = draft_issues(feedback, project, _pages(project))
    source = request.POST.get('source') if request.POST.get('source') in dict(PARTNER_SOURCES) else 'client'
    return _review(request, 'bizpartners/portal/issue_review.html', _ctx(request, 'projects'), project,
                   drafts, notice, back, reverse('bizpartners_portal:issue_add', args=[project.pk]),
                   PARTNER_SOURCES, source)


@partner_required
@require_POST
def portal_issue_add(request, pk):
    project = _partner_project(request, pk)
    source = request.POST.get('source') if request.POST.get('source') in dict(PARTNER_SOURCES) else 'client'
    if 'count' in request.POST:
        rows = _rows_from_post(request.POST)
    else:
        rows = [{k: request.POST.get(k, '') for k in ('page', 'section', 'title', 'action')}]
    created = JointIssue.add_many(project, rows, source=source, user=request.user)
    if created and 'count' not in request.POST:
        skipped = save_images(request, created[0])
        if skipped:
            messages.warning(request, skipped)
    if created:
        _notify_owners(project, created, request.user)
        n = len(created)
        messages.success(request, f'{n} issue{"s" if n != 1 else ""} added. The Ralfiz team has been told.')
    else:
        messages.error(request, 'Nothing was added. Write the issue first.')
    return redirect(_portal_back(project))


# ---------------------------------------------------------------------------
# Staff
# ---------------------------------------------------------------------------

def _staff_back(project):
    return reverse('bizpartners:project', args=[project.pk]) + '#issues'


def _source(value, default='client'):
    return value if value in dict(JointIssue.SOURCE_CHOICES) else default


@login_required
def issue_export(request, pk):
    project = get_object_or_404(JointProject, pk=pk)
    return export_xlsx(project, _filtered(project, request.GET))


@login_required
@require_POST
def issue_toggle(request, pk, issue_id):
    issue = get_object_or_404(JointIssue, pk=issue_id, project_id=pk)
    issue.set_done(request.POST.get('done') == '1', request.user)
    issue.save()
    pct = JointIssue.sync_progress(issue.project)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        resp = HttpResponse(issue.status_label, content_type='text/plain')
        resp['X-Progress'] = str(pct)
        return resp
    return redirect(_safe_next(request, _staff_back(issue.project)))


@login_required
@require_POST
def issue_bulk(request, pk):
    project = get_object_or_404(JointProject, pk=pk)
    done = request.POST.get('done') == '1'
    changed = []
    for issue in project.issues.filter(pk__in=request.POST.getlist('ids'), is_done=not done):
        issue.set_done(done, request.user)
        issue.save()
        changed.append(issue)
    if changed:
        JointIssue.sync_progress(project)
    if changed and done:
        nums = ', '.join(f'#{i.number}' for i in changed[:15]) + (' …' if len(changed) > 15 else '')
        n = len(changed)
        JointUpdate.objects.create(project=project, author=request.user,
                                   message=f'{n} issue{"s" if n != 1 else ""} done: {nums}')
    if changed:
        messages.success(request, f'{len(changed)} marked {"Done" if done else "Not Done"}.')
    return redirect(_safe_next(request, _staff_back(project)))


@login_required
@require_POST
def issue_save(request, pk, issue_id=None):
    project = get_object_or_404(JointProject, pk=pk)
    post = request.POST
    title = (post.get('title') or '').strip()
    if not title:
        messages.error(request, 'Write the issue first.')
        return redirect(_safe_next(request, _staff_back(project)))
    fields = {'page': post.get('page', ''), 'section': post.get('section', ''), 'title': title,
              'action': post.get('action', ''), 'notes': post.get('notes', ''),
              'source': _source(post.get('source')), 'is_done': post.get('done') == '1'}
    if issue_id is None:
        issue = JointIssue.add_many(project, [fields], user=request.user)[0]
        messages.success(request, f'Issue #{issue.number} added.')
    else:
        issue = get_object_or_404(JointIssue, pk=issue_id, project=project)
        issue.page, issue.section = fields['page'].strip()[:80], fields['section'].strip()[:120]
        issue.title, issue.action = title[:500], fields['action'].strip()
        issue.notes, issue.source = fields['notes'].strip(), fields['source']
        issue.set_done(fields['is_done'], request.user)
        issue.save()
        JointIssue.sync_progress(project)
        for img in issue.images.filter(pk__in=post.getlist('remove_image')):
            img.delete()
        messages.success(request, f'Issue #{issue.number} saved.')
    skipped = save_images(request, issue)
    if skipped:
        messages.warning(request, skipped)
    return redirect(_safe_next(request, _staff_back(project)))


@login_required
@require_POST
def issue_delete(request, pk, issue_id):
    issue = get_object_or_404(JointIssue, pk=issue_id, project_id=pk)
    project = issue.project
    issue.delete()
    JointIssue.sync_progress(project)
    messages.success(request, f'Issue #{issue.number} deleted.')
    return redirect(_safe_next(request, _staff_back(project)))


@login_required
@require_POST
def issue_draft(request, pk):
    project = get_object_or_404(JointProject, pk=pk)
    back = _staff_back(project)
    try:
        feedback = _feedback_from_request(request)
    except IssueAIError as exc:
        messages.error(request, str(exc))
        return redirect(back)
    if not feedback.text.strip():
        messages.error(request, 'Paste the feedback or choose a file first.')
        return redirect(back)
    drafts, notice = draft_issues(feedback, project, _pages(project))
    return _review(request, 'bizpartners/issue_review.html', {'partner': project.partner}, project,
                   drafts, notice, back, reverse('bizpartners:issue_add_many', args=[project.pk]),
                   JointIssue.SOURCE_CHOICES, _source(request.POST.get('source')))


@login_required
@require_POST
def issue_add_many(request, pk):
    project = get_object_or_404(JointProject, pk=pk)
    created = JointIssue.add_many(project, _rows_from_post(request.POST, staff=True),
                                  source=_source(request.POST.get('source')), user=request.user)
    n = len(created)
    if n:
        messages.success(request, f'{n} issue{"s" if n != 1 else ""} added.')
    else:
        messages.error(request, 'Nothing was ticked, so nothing was added.')
    return redirect(_staff_back(project))


@login_required
@require_POST
def issue_import(request, pk):
    project = get_object_or_404(JointProject, pk=pk)
    upload = request.FILES.get('file')
    if not upload or not upload.name.lower().endswith('.xlsx'):
        messages.error(request, 'Choose an Excel file (.xlsx).')
        return redirect(_staff_back(project))
    if upload.size > 25 * 1024 * 1024:
        messages.error(request, 'That file is over 25 MB.')
        return redirect(_staff_back(project))
    try:
        items = read_issue_workbook(upload.read())
    except IssueAIError as exc:
        messages.error(request, str(exc))
        return redirect(_staff_back(project))
    created = JointIssue.add_many(project, items, user=request.user)
    done = sum(1 for i in created if i.is_done)
    messages.success(request, f'Imported {len(created)} issues: {done} Done, {len(created) - done} Not Done.')
    return redirect(_staff_back(project))
