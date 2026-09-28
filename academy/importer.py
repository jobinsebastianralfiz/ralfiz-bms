"""Load an Academy Labs content package into the database.

Idempotent: tracks, domains, lessons and files are upserted by id; questions
are matched on (track, lesson, question text) so learners' answers survive a
re-import. A package whose hash matches the last import is skipped.
"""
import hashlib
import json
from pathlib import Path

from django.db import transaction

from .models import (
    ContentImport, Domain, ExerciseFile, Lesson, LessonFile, Question, Track,
)
from .sanitize import clean_html

TRACK_ORDER = ['pl900', 'ab410', 'pl300', 'ab400', 'flutter']
DEFAULT_PACKAGE_DIR = Path(__file__).resolve().parent / 'content'
SHARED_PREFIXES = ('hd', 'pbi')


class ImportFailed(Exception):
    pass


def file_disk_path(root, file_id):
    if file_id.split('/', 1)[0] in SHARED_PREFIXES:
        return root / 'exercise-files' / 'shared-data' / file_id
    return root / 'exercise-files' / file_id


def _read_package(root):
    """Parse and validate everything before touching the database."""
    # Either the unzipped package (content/ and exercise-files/ side by side)
    # or the bundled copy (the JSON and exercise-files/ in one folder).
    pkg_root = Path(root)
    content = pkg_root / 'content' if (pkg_root / 'content' / 'files-index.json').exists() else pkg_root
    index_path = content / 'files-index.json'
    if not index_path.exists():
        raise ImportFailed(f'No files-index.json under {pkg_root}')

    index = json.loads(index_path.read_text(encoding='utf-8'))
    tracks = []
    for tid in TRACK_ORDER:
        path = content / f'{tid}.json'
        if path.exists():
            tracks.append(json.loads(path.read_text(encoding='utf-8')))
    extra = sorted(p.stem for p in content.glob('*.json')
                   if p.stem not in TRACK_ORDER and p.name != 'files-index.json')
    for tid in extra:
        tracks.append(json.loads((content / f'{tid}.json').read_text(encoding='utf-8')))
    if not tracks:
        raise ImportFailed('No track files found.')

    errors = []
    files = {}
    for fid, meta in index.items():
        disk = file_disk_path(pkg_root, fid)
        if not disk.exists():
            errors.append(f'file {fid}: missing on disk at {disk}')
            continue
        raw = disk.read_bytes()
        files[fid] = {
            'zip_path': meta.get('path') or fid.rsplit('/', 1)[-1],
            'description': meta.get('description', ''),
            'content': raw.decode('utf-8', errors='replace'),
            'size_bytes': len(raw),
            'sha256': hashlib.sha256(raw).hexdigest(),
            'track_ids': set(),
        }

    seen_lessons = set()
    for t in tracks:
        for fid in t.get('data', []):
            if fid not in index:
                errors.append(f'{t["id"]}: course data file {fid} not in files-index')
            elif fid in files:
                files[fid]['track_ids'].add(t['id'])
        for d in t['domains']:
            for lesson in d['lessons']:
                lid = lesson['id']
                if lid in seen_lessons:
                    errors.append(f'lesson id {lid} is not unique')
                seen_lessons.add(lid)
                for fid in lesson.get('lab', {}).get('files', []):
                    if fid not in index:
                        errors.append(f'{lid}: lab file {fid} not in files-index')
                    elif fid in files:
                        files[fid]['track_ids'].add(t['id'])
                for q in lesson.get('quiz', []):
                    if not 0 <= q['answer'] < len(q['options']) or q['answer'] > 3:
                        errors.append(f'{lid}: answer {q["answer"]} out of range')
                sorter = lesson.get('sorter')
                if sorter:
                    for item in sorter.get('items', []):
                        if not 0 <= item['a'] < len(sorter['options']):
                            errors.append(f'{lid}: sorter answer {item["a"]} out of range')
        for q in t.get('questionBank', []):
            if not 0 <= q['answer'] < len(q['options']) or q['answer'] > 3:
                errors.append(f'{t["id"]} bank: answer {q["answer"]} out of range')
    for t in tracks:
        for q in t.get('questionBank', []):
            if q.get('lesson') and q['lesson'] not in seen_lessons:
                errors.append(f'{t["id"]} bank: unknown lesson {q["lesson"]}')
    if errors:
        raise ImportFailed('Validation failed:\n  ' + '\n  '.join(errors))

    digest = hashlib.sha256()
    digest.update(index_path.read_bytes())
    for t in tracks:
        digest.update(json.dumps(t, sort_keys=True).encode())
    for fid in sorted(files):
        digest.update(fid.encode() + files[fid]['sha256'].encode())
    return tracks, files, digest.hexdigest()


def run_import(root=DEFAULT_PACKAGE_DIR, content_version='2026-09', force=False, dry_run=False, log=print):
    tracks, files, package_sha = _read_package(root)

    last = ContentImport.objects.first()
    if last and last.package_sha256 == package_sha and not force and not dry_run:
        log(f'Package unchanged since {last.imported_at:%Y-%m-%d %H:%M}; nothing to do.')
        return last.counts

    counts = {'tracks': 0, 'domains': 0, 'lessons': 0, 'files': 0, 'questions': 0,
              'questions_added': 0, 'questions_retired': 0, 'files_changed': 0}
    stripped = set()

    with transaction.atomic():
        existing_sha = dict(ExerciseFile.objects.values_list('id', 'sha256'))
        for fid, f in files.items():
            if existing_sha.get(fid) != f['sha256']:
                counts['files_changed'] += 1
            ExerciseFile.objects.update_or_create(id=fid, defaults={
                **{k: v for k, v in f.items() if k != 'track_ids'},
                'track_ids': sorted(f['track_ids']),
            })
            counts['files'] += 1

        kept_question_ids = set()
        for t_order, t in enumerate(tracks):
            track, created = Track.objects.update_or_create(id=t['id'], defaults={
                'code': t['code'], 'name': t['name'], 'level': t.get('level', ''),
                'status': t.get('status', ''), 'outline_date': t.get('outline', ''),
                'order_hint': t.get('order', ''), 'blurb': t.get('blurb', ''),
                'facts': t.get('facts', []), 'tool': t.get('tool', ''),
                'guide_url': t.get('guide', ''), 'note': t.get('note', ''),
                'data_file_ids': t.get('data', []), 'sort_order': t_order,
                'content_version': content_version,
            })
            if created and t.get('category'):
                # Staff can recategorise a course in BMS; only a new course takes the package's value.
                track.category = t['category']
                track.save(update_fields=['category'])
            counts['tracks'] += 1
            existing = {(q.lesson_id, q.question): q for q in Question.objects.filter(track=track)}

            def upsert_question(lesson_id, source, order, q):
                obj = existing.get((lesson_id, q['question']))
                fields = {'source': source, 'sort_order': order, 'options': q['options'],
                          'answer': q['answer'], 'explanation': q.get('explanation', ''),
                          'is_active': True}
                if obj is None:
                    obj = Question.objects.create(track=track, lesson_id=lesson_id,
                                                  question=q['question'], **fields)
                    counts['questions_added'] += 1
                else:
                    for k, v in fields.items():
                        setattr(obj, k, v)
                    obj.save()
                kept_question_ids.add(obj.pk)
                counts['questions'] += 1

            for d_order, d in enumerate(t['domains']):
                Domain.objects.update_or_create(id=d['id'], defaults={
                    'track': track, 'name': d['name'], 'weight': d.get('weight', ''),
                    'blurb': d.get('blurb', ''), 'sort_order': d_order,
                })
                counts['domains'] += 1
                for l_order, raw in enumerate(d['lessons']):
                    summary, dropped_a = clean_html(raw.get('summaryHtml', ''))
                    body, dropped_b = clean_html(raw.get('contentHtml', ''))
                    stripped |= dropped_a | dropped_b
                    lab = raw.get('lab') or {}
                    lesson, _ = Lesson.objects.update_or_create(id=raw['id'], defaults={
                        'track': track, 'domain_id': d['id'], 'num': raw.get('num', ''),
                        'title': raw['title'], 'minutes': raw.get('minutes') or 0,
                        'summary_html': summary, 'content_html': body,
                        'terms': raw.get('terms', []), 'exam_tip': raw.get('examTip') or '',
                        'widget': raw.get('widget') or '', 'sorter': raw.get('sorter'),
                        'lab_steps': lab.get('steps', []), 'lab_check': lab.get('check', []),
                        'sort_order': l_order,
                    })
                    counts['lessons'] += 1
                    LessonFile.objects.filter(lesson=lesson).delete()
                    LessonFile.objects.bulk_create([
                        LessonFile(lesson=lesson, file_id=fid, sort_order=i)
                        for i, fid in enumerate(lab.get('files', []))
                    ])
                    for q_order, q in enumerate(raw.get('quiz', [])):
                        upsert_question(lesson.id, 'lesson', q_order, q)

            for b_order, q in enumerate(t.get('questionBank', [])):
                upsert_question(q.get('lesson'), 'bank', b_order, q)

        retired = (Question.objects.filter(is_active=True, track_id__in=[t['id'] for t in tracks])
                   .exclude(pk__in=kept_question_ids))
        counts['questions_retired'] = retired.update(is_active=False)

        if dry_run:
            transaction.set_rollback(True)
        else:
            ContentImport.objects.create(package_sha256=package_sha,
                                         content_version=content_version, counts=counts)

    if stripped:
        log(f'Note: removed tags not on the allow-list: {", ".join(sorted(stripped))}')
    log(('DRY RUN (rolled back): ' if dry_run else 'Imported: ') +
        f'{counts["tracks"]} tracks, {counts["domains"]} domains, {counts["lessons"]} lessons, '
        f'{counts["files"]} files ({counts["files_changed"]} new or changed), '
        f'{counts["questions"]} questions ({counts["questions_added"]} new, '
        f'{counts["questions_retired"]} retired).')
    return counts
