"""HR screens for MCQ tests: upload a JSON file of questions, give the test to
interns, and see who took it and what they scored. Interns take the test on the
staff portal (employees/portal_views.assessment_take)."""
import json

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_POST

from employees import mcq
from employees.models import Employee, McqTest

from .enrolment_web_views import enrolment_admin

MAX_UPLOAD_BYTES = 2 * 1024 * 1024


def _interns():
    return (Employee.objects.select_related('user')
            .filter(status='active', employment_type='intern').order_by('user__first_name'))


def _read_upload(request):
    f = request.FILES.get('file')
    if not f:
        raise mcq.McqFormatError('Choose a .json file to upload.')
    if f.size > MAX_UPLOAD_BYTES:
        raise mcq.McqFormatError('The file is too big (2 MB max).')
    return mcq.parse_upload(f.read())


@enrolment_admin
def mcq_test_list(request):
    if request.method == 'POST':
        try:
            data = _read_upload(request)
        except mcq.McqFormatError as e:
            messages.error(request, f'Could not read the file: {e}')
            return redirect('mcq_test_list')
        title = (request.POST.get('title') or '').strip() or data['title']
        if not title:
            messages.error(request, 'Give the test a title (in the form or as "title" in the file).')
            return redirect('mcq_test_list')
        duration = request.POST.get('duration_minutes', '').strip()
        test = McqTest.objects.create(
            title=title[:255], description=data['description'],
            duration_minutes=int(duration) if duration.isdigit() else data['duration_minutes'],
            questions=data['questions'], created_by=request.user,
        )
        messages.success(request, f'"{test.title}" created with {test.question_count} questions. '
                                  f'Now give it to interns.')
        return redirect('mcq_test_detail', pk=test.pk)

    tests = McqTest.objects.all()
    rows = []
    for t in tests:
        given = list(t.assessments.all())
        done = [a for a in given if a.submitted_at]
        rows.append({
            't': t, 'given': len(given), 'done': len(done),
            'avg': round(sum(a.percentage or 0 for a in done) / len(done), 1) if done else None,
        })
    return render(request, 'hr/mcq_test_list.html', {
        'rows': rows, 'sample': json.dumps(mcq.SAMPLE, indent=2, ensure_ascii=False),
    })


@enrolment_admin
def mcq_test_sample(request):
    resp = HttpResponse(json.dumps(mcq.SAMPLE, indent=2, ensure_ascii=False),
                        content_type='application/json; charset=utf-8')
    resp['Content-Disposition'] = 'attachment; filename="mcq-test-sample.json"'
    return resp


@enrolment_admin
def mcq_test_detail(request, pk):
    test = get_object_or_404(McqTest, pk=pk)
    given = list(test.assessments.select_related('employee__user').order_by('-submitted_at', 'employee__user__first_name'))
    have = {a.employee_id for a in given}
    done = [a for a in given if a.submitted_at]
    questions = [{'num': n, 'question': q['question'], 'marks': q.get('marks', 1),
                  'explanation': q.get('explanation', ''),
                  'options': [{'letter': mcq.LETTERS[j], 'text': o, 'right': j == q['answer']}
                              for j, o in enumerate(q['options'])]}
                 for n, q in enumerate(test.questions, start=1)]
    return render(request, 'hr/mcq_test_detail.html', {
        'test': test, 'given': given, 'done_count': len(done),
        'avg': round(sum(a.percentage or 0 for a in done) / len(done), 1) if done else None,
        'available': [e for e in _interns() if e.pk not in have],
        'questions': questions, 'locked': bool(done),
    })


@enrolment_admin
@require_POST
def mcq_test_assign(request, pk):
    test = get_object_or_404(McqTest, pk=pk)
    ids = request.POST.getlist('employees')
    people = list(_interns().filter(pk__in=ids)) if ids else []
    if not people:
        messages.error(request, 'Pick at least one intern.')
        return redirect('mcq_test_detail', pk=pk)
    if not test.is_active:
        test.is_active = True
        test.save(update_fields=['is_active', 'updated_at'])
    created = mcq.assign(test, people, by=request.user, due_date=parse_date(request.POST.get('due_date') or ''))
    messages.success(request, f'Test given to {len(created)} intern{"s" if len(created) != 1 else ""}. '
                              f'It is on their staff dashboard now.')
    return redirect('mcq_test_detail', pk=pk)


@enrolment_admin
@require_POST
def mcq_test_update(request, pk):
    test = get_object_or_404(McqTest, pk=pk)
    action = request.POST.get('action')
    if action == 'settings':
        test.title = (request.POST.get('title') or test.title).strip()[:255]
        test.description = (request.POST.get('description') or '').strip()
        d = (request.POST.get('duration_minutes') or '0').strip()
        test.duration_minutes = int(d) if d.isdigit() else test.duration_minutes
        test.shuffle_questions = bool(request.POST.get('shuffle_questions'))
        test.show_answers = bool(request.POST.get('show_answers'))
        test.is_active = bool(request.POST.get('is_active'))
        test.save()
        # Untaken copies follow the test's title.
        test.assessments.filter(submitted_at__isnull=True).update(title=test.title, description=test.description)
        messages.success(request, 'Test settings saved.')
    elif action == 'replace':
        if test.assessments.filter(submitted_at__isnull=False).exists():
            messages.error(request, 'Someone has already taken this test, so its questions can no longer change. '
                                    'Upload it as a new test instead.')
            return redirect('mcq_test_detail', pk=pk)
        try:
            data = _read_upload(request)
        except mcq.McqFormatError as e:
            messages.error(request, f'Could not read the file: {e}')
            return redirect('mcq_test_detail', pk=pk)
        test.questions = data['questions']
        test.save(update_fields=['questions', 'updated_at'])
        test.assessments.filter(submitted_at__isnull=True).update(max_score=test.total_marks, started_at=None)
        messages.success(request, f'Questions replaced ({test.question_count} questions).')
    elif action == 'remove':
        a = test.assessments.filter(pk=request.POST.get('assessment_id'), submitted_at__isnull=True).first()
        if a:
            a.delete()
            messages.success(request, f'Test taken back from {a.employee.full_name}.')
    elif action == 'reset':
        a = test.assessments.filter(pk=request.POST.get('assessment_id')).first()
        if a:
            a.answers, a.scored, a.started_at, a.submitted_at = {}, None, None, None
            a.save()
            messages.success(request, f'{a.employee.full_name} can take the test again.')
    return redirect('mcq_test_detail', pk=pk)


@enrolment_admin
@require_POST
def mcq_test_delete(request, pk):
    test = get_object_or_404(McqTest, pk=pk)
    # Untaken copies go with it; finished ones keep their score on the intern's record.
    test.assessments.filter(submitted_at__isnull=True).delete()
    title = test.title
    test.delete()
    messages.success(request, f'"{title}" deleted. Scores already earned stay on each intern\'s record.')
    return redirect('mcq_test_list')
