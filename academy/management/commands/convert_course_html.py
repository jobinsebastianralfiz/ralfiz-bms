"""Convert a standalone Ralfiz Academy course HTML file into the import package.

The single-file course apps (e.g. ralfiz-flutter-academy.html) keep their data
as JavaScript, not JSON: a data <script> with LESSONS.push({...}), FILES, EX,
QBANK and DEEP, and the app <script> with the TRACKS list and DOMAINS.push(...).
The file is built from the Microsoft-course template, so it still carries the
template's domains (d0-d5, p0-p4 and so on); only the requested track's
domains and lessons are written.

Node evaluates the data (no DOM needed); the mapping to the package format
(academy/content/<track>.json, exercise-files/<track>/..., files-index.json)
is done here. Parts of the app that have no place in the package are turned
into allow-listed HTML:

- phone screen mocks (div.mock-slot) keep a placeholder,
  <div class="mock-slot" data-mock="N">, holding a worked-example panel with the
  screen title, its Dart code and the caption; the mock data itself goes into
  the lesson's "mocks" list, and the lesson page draws the phone over the panel
  with static/academy/flutter-mocks.js (the panel stays if JavaScript is off);
- predict-the-output drills (widget "predict") become a "Predict the output"
  section at the end of the lesson, answers last;
- concept animations (div.anim-slot) are JavaScript-only and are removed.

Safe to re-run: the track's JSON, its exercise-files folder and its
files-index entries are replaced. Run import_labs afterwards.

    python manage.py convert_course_html ralfiz-flutter-academy.html --track flutter
"""
import json
import re
import shutil
import subprocess
from html import escape
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from academy.importer import DEFAULT_PACKAGE_DIR, SHARED_PREFIXES
from academy.sanitize import clean_html

NODE_EVAL = r"""
const vm = require('vm');
const src = JSON.parse(require('fs').readFileSync(0, 'utf8'));
const box = {};
vm.runInNewContext(src.data + '\n;\n' + src.meta +
  '\n;__out = JSON.stringify({FILES, EX, QBANK, DEEP, LESSONS, DOMAINS, TRACKS});', box);
process.stdout.write(box.__out);
"""

SCRIPT_RE = re.compile(r'<script>(.*?)</script>', re.S)
MOCK_SLOT = re.compile(r'<div class="mock-slot" data-i="(\d+)"></div>')
ANIM_SLOT = re.compile(r'\n?<div class="anim-slot" data-a="[\w-]+"></div>\n?')
# A numbered list interrupted by a mock and resumed with <ol start="n">: the
# sanitizer drops the start attribute, so keep one list with the mock inside
# the last item instead.
SPLIT_LIST = re.compile(r'</li>\s*</ol>\s*(<div class="mock-slot" data-i="\d+"></div>)\s*<ol start="\d+">\s*')
ATTR = re.compile(r'<\w+\s+([^>]*)>')


def esc(s):
    return escape(str(s), quote=False)


def read_js(html_path):
    html = Path(html_path).read_text(encoding='utf-8')
    scripts = SCRIPT_RE.findall(html)
    data = next((s for s in scripts if 'LESSONS.push(' in s), None)
    app = next((s for s in scripts if 'const TRACKS=' in s), None)
    if data is None or app is None:
        raise CommandError('Could not find the data script (LESSONS.push) and the app script (const TRACKS=).')
    start, end = app.find('const TRACKS='), app.find('const TRACK_ORDER=')
    if end < start:
        raise CommandError('Could not find the TRACKS / DOMAINS block in the app script.')
    try:
        out = subprocess.run(['node', '-e', NODE_EVAL], input=json.dumps({'data': data, 'meta': app[start:end]}),
                             capture_output=True, text=True, check=True, timeout=120)
    except FileNotFoundError:
        raise CommandError('Node.js is needed to evaluate the course data (node not found on PATH).')
    except subprocess.CalledProcessError as e:
        raise CommandError(f'Node could not evaluate the course data:\n{e.stderr}')
    return json.loads(out.stdout)


def mock_html(i, m):
    head = f'<p><strong>Screen {i + 1}: {esc(m.get("title", ""))}</strong>'
    if m.get('file'):
        head += f' <code>{esc(m["file"])}</code>'
    parts = [head + '</p>']
    if m.get('code'):
        parts.append(f'<pre class="code">{esc(m["code"])}</pre>')
    caption = m.get('caption', '')
    frames = [f.get('label') for f in m.get('frames') or [] if f.get('label')]
    if frames:
        caption = (caption + ' ' if caption else '') + 'States: ' + ' → '.join(frames) + '.'
    if caption:
        parts.append(f'<p>{esc(caption)}</p>')
    return (f'<div class="mock-slot" data-mock="{i}"><div class="example">\n' + '\n'.join(parts)
            + '\n</div></div>')


def option_html(o):
    return f'<pre class="code">{esc(o)}</pre>' if '\n' in o else f'<code>{esc(o)}</code>'


def predict_html(items):
    letters = 'ABCD'
    out = ['<h3>Predict the output</h3>',
           '<p>Read each snippet and decide what it prints before you run it. '
           'The answers are at the end of this section.</p>']
    for n, it in enumerate(items, 1):
        opts = ''.join(f'<li><strong>{letters[j]}</strong> {option_html(o)}</li>' for j, o in enumerate(it['o']))
        out.append(f'<div class="example">\n<p><strong>Snippet {n}.</strong> {esc(it.get("q") or "What does this print?")}</p>\n'
                   f'<pre class="code">{esc(it["code"])}</pre>\n<ul>{opts}</ul>\n</div>')
    answers = ''.join(f'<li><strong>{letters[it["a"]]}.</strong> {esc(it["w"])}</li>' for it in items)
    out.append(f'<div class="callout">\n<p><strong>Answers</strong></p>\n<ol>{answers}</ol>\n</div>')
    return '\n'.join(out)


def lesson_content(deep, mocks, predict):
    html = SPLIT_LIST.sub(r'\n\1</li>\n', deep)
    used = set()

    def slot(m):
        i = int(m.group(1))
        if i >= len(mocks):
            return ''
        used.add(i)
        return mock_html(i, mocks[i])

    html = MOCK_SLOT.sub(slot, html)
    rest = [i for i in range(len(mocks)) if i not in used]
    if rest:
        html += '\n\n<h3>Screen examples</h3>\n' + '\n'.join(mock_html(i, mocks[i]) for i in rest)
    html = ANIM_SLOT.sub('\n', html)
    if predict:
        html += '\n\n' + predict_html(predict)
    return html.strip()


class Command(BaseCommand):
    help = 'Convert a standalone course HTML file into academy/content/<track>.json and its exercise files.'

    def add_arguments(self, parser):
        parser.add_argument('html', help='Path to the course HTML file.')
        parser.add_argument('--track', required=True, help='Track id to extract, e.g. flutter.')
        parser.add_argument('--out', default=str(DEFAULT_PACKAGE_DIR), help='Package folder (default: academy/content).')

    def handle(self, *args, **opts):
        tid, out = opts['track'], Path(opts['out'])
        if tid in SHARED_PREFIXES:
            raise CommandError(f'{tid} is reserved for shared datasets.')
        js = read_js(opts['html'])

        track = next((t for t in js['TRACKS'] if t['id'] == tid), None)
        if track is None:
            raise CommandError(f'No track {tid!r} in the file. Tracks: {", ".join(t["id"] for t in js["TRACKS"])}')
        domains = [d for d in js['DOMAINS'] if d.get('track') == tid]
        dom_ids = {d['id'] for d in domains}
        lessons = [l for l in js['LESSONS'] if l['d'] in dom_ids]
        others = [l['id'] for l in js['LESSONS'] if l['d'] not in dom_ids]
        orphans = {l['d'] for l in js['LESSONS']} - {d['id'] for d in js['DOMAINS']}
        if orphans:
            raise CommandError(f'Lessons point at undefined domains: {", ".join(sorted(orphans))}')

        warnings = []
        file_ids = list(track.get('data') or [])
        out_domains = []
        for d in domains:
            ls = [l for l in lessons if l['d'] == d['id']]
            if not ls:
                continue
            out_lessons = []
            for l in ls:
                ex = js['EX'].get(l['id']) or {}
                steps = ex.get('steps') or l.get('lab') or []
                files = ex.get('files') or []
                file_ids += files
                widget = l.get('widget')
                predict = l.get('predict') if widget == 'predict' else None
                if widget and widget != 'predict':
                    warnings.append(f'{l["id"]}: widget {widget!r} kept as-is')
                content = lesson_content(js['DEEP'].get(l['id'], ''), l.get('mocks') or [], predict)
                for label, html in (('summary', l['learn']), ('content', content)):
                    attrs = {a for a in ATTR.findall(html)
                             if not re.fullmatch(r'(class="[^"]*"|(col|row)span="\d+"|class="mock-slot" data-mock="\d+")', a)}
                    _, dropped = clean_html(html)
                    if dropped or attrs:
                        warnings.append(f'{l["id"]} {label}: sanitizer will drop {sorted(dropped)} {sorted(attrs)}')
                out_lessons.append({
                    'id': l['id'], 'num': l['num'], 'title': l['title'], 'minutes': l.get('min') or 0,
                    'summaryHtml': l['learn'], 'contentHtml': content,
                    'terms': [{'term': t[0], 'definition': t[1]} for t in l.get('terms', [])],
                    'examTip': l.get('tip') or '',
                    'widget': widget if widget and widget != 'predict' else None,
                    'sorter': l.get('sorter'),
                    'lab': {'files': files, 'steps': steps, 'check': ex.get('check') or []},
                    'mocks': l.get('mocks') or [],
                    'quiz': [{'question': q['q'], 'options': q['o'], 'answer': q['a'], 'explanation': q['w']}
                             for q in l.get('quiz', [])],
                })
            out_domains.append({'id': d['id'], 'name': d['name'], 'weight': d.get('weight', ''),
                                'blurb': d.get('blurb', ''), 'lessons': out_lessons})

        doc = {k: track.get(src, dflt) for k, src, dflt in [
            ('id', 'id', ''), ('code', 'code', ''), ('name', 'name', ''), ('level', 'level', ''),
            ('status', 'status', ''), ('outline', 'outline', ''), ('order', 'order', ''),
            ('blurb', 'blurb', ''), ('facts', 'facts', []), ('tool', 'tool', ''),
            ('guide', 'guide', ''), ('note', 'note', ''), ('data', 'data', [])]}
        # A course without an exam lists with app development, not the Microsoft certifications.
        doc['category'] = 'certification' if track.get('exam', True) else 'development'
        # The concept animations are removed above, so no fact may promise them.
        doc['facts'] = [f for f in doc['facts'] if 'animation' not in str(f[1]).lower()]
        if len(doc['facts']) < 4:
            quiz = sum(len(l['quiz']) for d in out_domains for l in d['lessons'])
            doc['facts'].append([str(quiz), 'quiz questions with explanations'])
        doc['domains'] = out_domains
        doc['questionBank'] = [{'question': q['q'], 'options': q['o'], 'answer': q['a'],
                                'explanation': q.get('w', ''), 'lesson': q.get('l')}
                               for q in (js['QBANK'].get(tid) or [])]

        missing = [f for f in file_ids if f not in js['FILES']]
        if missing:
            raise CommandError(f'Files referenced but not in FILES: {", ".join(missing)}')
        bad = [f for f in file_ids if f.split('/', 1)[0] != tid]
        if bad:
            raise CommandError(f'File ids outside {tid}/ are not supported: {", ".join(bad)}')

        # Write: <track>.json, exercise-files/<track>/, files-index.json entries.
        (out / f'{tid}.json').write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding='utf-8')
        ex_root = out / 'exercise-files' / tid
        if ex_root.exists():
            shutil.rmtree(ex_root)
        index_path = out / 'files-index.json'
        index = json.loads(index_path.read_text(encoding='utf-8')) if index_path.exists() else {}
        index = {k: v for k, v in index.items() if k.split('/', 1)[0] != tid}
        for fid in dict.fromkeys(file_ids):
            f = js['FILES'][fid]
            disk = out / 'exercise-files' / fid
            disk.parent.mkdir(parents=True, exist_ok=True)
            disk.write_text(f['text'], encoding='utf-8')
            parts = fid.split('/')
            index[fid] = {'path': '/'.join(parts[2:]) or parts[-1], 'description': f.get('desc', '')}
        index_path.write_text(json.dumps(index, indent=1, ensure_ascii=False), encoding='utf-8')

        for w in warnings:
            self.stderr.write(f'Warning: {w}')
        n_lessons = sum(len(d['lessons']) for d in out_domains)
        self.stdout.write(
            f'{tid}: {len(out_domains)} domains, {n_lessons} lessons, '
            f'{sum(len(l["quiz"]) for d in out_domains for l in d["lessons"])} quiz questions, '
            f'{len(doc["questionBank"])} bank questions, {len(dict.fromkeys(file_ids))} files. '
            f'Skipped {len(js["DOMAINS"]) - len(domains)} other domains and {len(others)} other lessons.')
