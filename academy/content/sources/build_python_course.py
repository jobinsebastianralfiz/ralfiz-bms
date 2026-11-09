"""Build the Complete Python Tutorial (track `python`) from ralfiz-python-tutorial.html.

The tutorial is a single self-contained page (one <section class="view"> per lesson,
code in <script type="text/plain" class="code">, exercises in <div class="ex"> with
<details> solutions). This script converts it to the Academy package format:

- each section becomes a lesson; its data-group becomes the domain
- markup is mapped onto the tags academy/sanitize.py keeps (h2 -> h3, b -> strong,
  callouts, cards -> example boxes, details -> plain text)
- each exercise becomes a lab step, and its solution is printed at the end of the lesson
- the runnable examples of each lesson are written to exercise-files/python/<n>_<slug>.py
  so a learner can download and run them (the Academy page has no in-browser runner)
- the quiz questions come from python_course_quiz.py

    python academy/content/sources/build_python_course.py
"""
import json
import re
import sys
import textwrap
from html import escape
from html.parser import HTMLParser
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONTENT = HERE.parent
SOURCE = HERE / 'ralfiz-python-tutorial.html'
FILES_DIR = CONTENT / 'exercise-files' / 'python'

sys.path.insert(0, str(HERE))
from python_course_quiz import QUIZ_PUBLIC as QUIZ, TERMS  # noqa: E402

VOID = {'br', 'meta', 'link', 'input', 'img', 'hr'}


class Node:
    def __init__(self, tag, attrs, parent=None):
        self.tag, self.attrs, self.parent, self.children = tag, dict(attrs), parent, []

    @property
    def classes(self):
        return (self.attrs.get('class') or '').split()

    def find_all(self, pred):
        for c in self.children:
            if isinstance(c, Node):
                if pred(c):
                    yield c
                yield from c.find_all(pred)

    def find(self, pred):
        return next(self.find_all(pred), None)

    def text(self):
        return ''.join(c if isinstance(c, str) else c.text() for c in self.children)


class TreeBuilder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = self.cur = Node('root', {})

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs, self.cur)
        self.cur.children.append(node)
        if tag not in VOID:
            self.cur = node

    def handle_endtag(self, tag):
        n = self.cur
        while n is not None and n.tag != tag:
            n = n.parent
        if n is not None and n.parent is not None:
            self.cur = n.parent

    def handle_data(self, data):
        self.cur.children.append(data)


def plain(node):
    """Text of a node for a lab step: whitespace collapsed, except inside <code>."""
    out = []
    for c in node.children:
        if isinstance(c, str):
            out.append(re.sub(r'\s+', ' ', c))
        elif c.tag == 'code':
            out.append(c.text())
        elif c.tag == 'br':
            out.append(' ')
        elif c.tag not in ('script', 'details'):
            out.append(plain(c))
    return re.sub(r' +(?=[ /])|^ +| +$', '', ''.join(out)).strip()


def norm(s):
    return re.sub(r'\s+', ' ', s).strip()


def code_text(node):
    return textwrap.dedent(node.text().strip('\n')).rstrip()


def is_code(n):
    return n.tag == 'script' and 'code' in n.classes


def pre(node):
    title = node.attrs.get('data-title', '')
    body = code_text(node)
    lang = node.attrs.get('data-lang', 'python')
    if title and title != 'solution':
        mark = '#' if lang in ('python', 'bash', 'text') else '//'
        if lang == 'python' or lang == 'bash':
            body = f'{mark} {title}\n{body}'
    runnable = lang == 'python' and 'data-run' in node.attrs
    return f'<pre class="{"code run" if runnable else "code"}">{escape(body)}</pre>'


class Converter:
    """Inline/blocks to Academy-safe HTML. Exercise solutions are collected, not rendered."""

    def __init__(self):
        self.solutions = []

    def inline(self, node):
        out = []
        for c in node.children:
            if isinstance(c, str):
                out.append(escape(c, quote=False))
                continue
            t = c.tag
            if t in ('b', 'strong'):
                out.append(f'<strong>{self.inline(c)}</strong>')
            elif t == 'em':
                out.append(f'<em>{self.inline(c)}</em>')
            elif t == 'i':
                out.append(f'<em>{self.inline(c)}</em>' if norm(c.text()) else '')
            elif t == 'code':
                out.append(f'<code>{escape(c.text(), quote=False)}</code>')
            elif t == 'kbd':
                out.append(f'<kbd>{escape(c.text(), quote=False)}</kbd>')
            elif t == 'br':
                out.append('<br>')
            elif t == 'a':
                label = self.inline(c)
                href = c.attrs.get('href', '')
                out.append(label if not href or norm(c.text()) in href else f'{label} ({escape(href)})')
            elif t in ('details', 'script'):
                continue
            else:
                out.append(self.inline(c))
        return ''.join(out)

    def callout(self, node):
        kind = 'warn' if {'bad', 'warn'} & set(node.classes) else 'callout'
        parts = []
        for c in node.children:
            if isinstance(c, Node) and c.tag == 'b' and not parts:
                parts.append(f'<strong>{self.inline(c)}:</strong> ')
            elif isinstance(c, Node) and is_code(c):
                parts.append(pre(c))
            else:
                parts.append(c if isinstance(c, str) and not c.strip() else
                             escape(c, quote=False) if isinstance(c, str) else self.inline_node(c))
        return f'<div class="{kind}">{"".join(parts).strip()}</div>'

    def inline_node(self, c):
        holder = Node('span', {})
        holder.children = [c]
        return self.inline(holder)

    def table(self, node):
        rows = []
        for tr in node.find_all(lambda n: n.tag == 'tr'):
            cells = ''.join(f'<{td.tag}>{self.inline(td).strip()}</{td.tag}>'
                            for td in tr.children if isinstance(td, Node) and td.tag in ('td', 'th'))
            rows.append((tr.parent.tag, f'<tr>{cells}</tr>'))
        head = ''.join(r for p, r in rows if p == 'thead')
        body = ''.join(r for p, r in rows if p != 'thead')
        return f'<table>{f"<thead>{head}</thead>" if head else ""}<tbody>{body}</tbody></table>'

    def listing(self, node):
        items = []
        for li in node.children:
            if isinstance(li, Node) and li.tag == 'li':
                inner = self.inline(li).strip()
                codes = ''.join(pre(s) for s in li.children if isinstance(s, Node) and is_code(s))
                items.append(f'<li>{inner}{codes}</li>')
        return f'<{node.tag}>{"".join(items)}</{node.tag}>'

    def exercises(self, node, heading='Exercise'):
        """An <div class="ex"> block: the list items become lab steps, solutions go to the end."""
        steps = []
        ol = node.find(lambda n: n.tag == 'ol')
        for i, li in enumerate((c for c in ol.children if isinstance(c, Node) and c.tag == 'li'), start=1):
            text = plain(Converter._without(li, 'details'))
            steps.append(text)
            html = self.inline(li).strip()
            sol = ''.join(pre(s) for s in li.find_all(is_code))
            extra = ''
            details = li.find(lambda n: n.tag == 'details')
            if details is not None:
                extra = ''.join(f'<p>{self.inline(p)}</p>' for p in details.children
                                if isinstance(p, Node) and p.tag == 'p')
            self.solutions.append(f'<p><strong>{heading} {i}.</strong> {html}</p>{extra}{sol}')
        return steps

    @staticmethod
    def _without(node, tag):
        copy = Node(node.tag, node.attrs)
        copy.children = [c for c in node.children if not (isinstance(c, Node) and c.tag == tag)]
        return copy

    def blocks(self, node, depth=0):
        out = []
        for c in node.children:
            if isinstance(c, str):
                if c.strip():
                    out.append(f'<p>{escape(norm(c), quote=False)}</p>')
                continue
            t, cls = c.tag, set(c.classes)
            if t == 'script':
                if is_code(c):
                    out.append(pre(c))
            elif t in ('h1', 'h2'):
                out.append(f'<h3>{self.inline(c)}</h3>')
            elif t in ('h3', 'h4'):
                out.append(f'<p><strong>{self.inline(c)}</strong></p>')
            elif t == 'p':
                html = self.inline(c).strip()
                if html:
                    out.append(f'<p>{html}</p>')
            elif t in ('ul', 'ol'):
                out.append(self.listing(c))
            elif t == 'table':
                out.append(self.table(c))
            elif t == 'details':
                summary = c.find(lambda n: n.tag == 'summary')
                out.append(f'<p><strong>{self.inline(summary) if summary else "Solution"}</strong></p>')
                rest = Node('div', {})
                rest.children = [x for x in c.children if x is not summary]
                out.extend(self.blocks(rest, depth + 1))
            elif t == 'div' and 'callout' in cls:
                out.append(self.callout(c))
            elif t == 'div' and 'card' in cls:
                inner = self.inline(c).strip()
                codes = ''.join(pre(s) for s in c.find_all(is_code))
                lists = ''.join(self.listing(x) for x in c.children if isinstance(x, Node) and x.tag in ('ul', 'ol'))
                inner = self.inline(Converter._without(Converter._without(c, 'ul'), 'ol')).strip()
                out.append(f'<div class="example">{inner}{lists}{codes}</div>')
            elif t == 'div' and 'flow' in cls:
                spans = [self.inline(s) for s in c.children if isinstance(s, Node) and s.tag == 'span']
                out.append(f'<p><strong>{" → ".join(spans)}</strong></p>')
            elif t == 'div' and ('chips' in cls or 'lessons-grid' in cls or 'markdone' in cls):
                continue
            elif t == 'div' and 'ex' in cls:
                raise ValueError('exercise blocks are handled by the caller')
            elif t in ('div', 'span', 'section'):
                out.extend(self.blocks(c, depth + 1))
            elif t == 'button':
                continue
            else:
                html = self.inline_node(c).strip()
                if html:
                    out.append(f'<p>{html}</p>')
        return out


def slug(s):
    return re.sub(r'[^a-z0-9]+', '_', s.lower()).strip('_')[:40]


GROUPS = [
    # (data-group in the source, domain id, name, weight, blurb)
    ('Start', 'pyd0', 'Start here', 'Start', 'How the tutorial works and the suggested six-day pace.'),
    ('1 · Basics', 'pyd1', 'Basics', 'Day 1',
     'Setup, variables, operators, strings, input and output, conditions and loops.'),
    ('2 · Data structures', 'pyd2', 'Data structures', 'Day 2',
     'Lists, tuples, sets, dictionaries and comprehensions for real data.'),
    ('3 · Functions & modules', 'pyd3', 'Functions & modules', 'Day 3',
     'Reusable functions, modules, files and errors.'),
    ('4 · Object-oriented Python', 'pyd4', 'Object-oriented Python', 'Day 4',
     'Model business objects with classes, inheritance, properties and dataclasses.'),
    ('5 · Advanced Python', 'pyd5', 'Advanced Python', 'Day 5',
     'Generators, decorators, context managers, type hints, regex and concurrency.'),
    ('6 · Real-world Python', 'pyd6', 'Real-world Python', 'Day 6',
     'Dates and money, SQLite, APIs and JSON, testing and logging.'),
    ('Projects', 'pyd7', 'Projects', 'Projects', 'Four complete programs that use everything above.'),
    ('Wrap-up', 'pyd8', 'Wrap-up', 'Wrap-up', 'Interview questions and a one-page cheat sheet.'),
]


def lesson_from(section, number, num_label):
    sid = section.attrs['id'].removeprefix('v-')
    hero = section.find(lambda n: 'hero' in n.classes)
    eyebrow = norm(hero.find(lambda n: 'eyebrow' in n.classes).text())
    title = TITLES.get(sid) or norm(hero.find(lambda n: n.tag == 'h1').text())
    summary_p = hero.find(lambda n: n.tag == 'p')
    conv = Converter()
    summary = f'<p>{conv.inline(summary_p).strip()}</p>' if summary_p else ''
    m = re.search(r'(\d+)\s*min', eyebrow)
    h = re.search(r'(\d+)\s*hour', eyebrow)
    minutes = int(m.group(1)) if m else int(h.group(1)) * 60 if h else 30

    body, steps = [], []
    for c in section.children:
        if isinstance(c, Node) and c is hero:
            continue
        if isinstance(c, Node) and 'ex' in c.classes:
            steps += conv.exercises(c)
            continue
        if isinstance(c, Node) and 'project' in c.classes:
            body.extend(project_blocks(conv, c, steps))
            continue
        holder = Node('div', {})
        holder.children = [c]
        body.extend(conv.blocks(holder))

    # Runnable examples (not solutions, not shell sessions) go into a download.
    examples = [n for n in section.find_all(is_code)
                if n.attrs.get('data-lang', 'python') == 'python' and 'data-run' in n.attrs
                and n.attrs.get('data-title') != 'solution' and not in_details(n)]
    lab_files, file_entry = [], None
    if examples:
        fname = f'{number:02d}_{slug(sid)}.py'
        parts = [f'"""{title}: the runnable examples from lesson {num_label} of the Complete Python Tutorial.\n\n'
                 f'Run it with:  python3 {fname}\nThen change the code and run it again."""\n']
        for n in examples:
            src = code_text(n)
            for old, new in FILE_PATCHES.get(sid, []):
                src = src.replace(old, new)
            parts.append(f'\n# {"-" * 70}\n# {n.attrs.get("data-title", "example")}\n# {"-" * 70}\n'
                         f'{src}\n')
        file_entry = (f'python/{fname}', ''.join(parts), f'Lesson {num_label}: every runnable example from “{title}”.')
        lab_files = [file_entry[0]]
        steps.insert(0, f'Download {fname}, run it with python3 {fname} and compare the output with the lesson.')

    if not conv.solutions and 'project' not in sid and sid in DIY_STEPS:
        steps += DIY_STEPS[sid]
    if 'project' in sid and not any('Build' in st for st in steps):
        steps += PROJECT_STEPS
    if conv.solutions:
        body.append('<h3>Exercise solutions</h3>')
        body.append('<p>Try each exercise yourself first. Then compare with these.</p>')
        body.extend(conv.solutions)
    return {
        'id': None, 'num': num_label, 'title': title, 'minutes': minutes,
        'summaryHtml': summary, 'contentHtml': '\n'.join(body),
        'terms': TERMS.get(sid, []), 'examTip': '',
        'lab': {'files': lab_files, 'steps': steps or EXTRA_STEPS.get(sid, ['Read the lesson and try every example.']),
                'check': []},
        'quiz': QUIZ.get(sid, []), 'widget': None, 'sorter': None,
    }, sid, file_entry


def in_details(n):
    p = n.parent
    while p is not None:
        if p.tag == 'details':
            return True
        p = p.parent
    return False


def project_blocks(conv, node, steps):
    """A project card: requirements as content, its numbered steps as lab steps, solution shown in full."""
    out = []
    current = None
    for c in node.children:
        if not isinstance(c, Node):
            continue
        if c.tag == 'h3':
            current = norm(c.text())
            out.append(f'<h3>{conv.inline(c)}</h3>')
        elif c.tag == 'ol' and current and current.lower().startswith('step'):
            for li in c.children:
                if isinstance(li, Node) and li.tag == 'li':
                    steps.append(norm(li.text()))
            out.append(conv.listing(c))
        elif c.tag == 'details':
            out.append('<h3>Full solution</h3>')
            out.append('<p>Build it yourself first. Open this only to compare.</p>')
            for s in c.find_all(is_code):
                out.append(pre(s))
        else:
            holder = Node('div', {})
            holder.children = [c]
            out.extend(conv.blocks(holder))
    return out


# In the one-file download, an example that crashes on purpose would stop every example after it.
FILE_PATCHES = {
    'exceptions': [('get_price(prices, "clock")      # run this and read the output from the bottom',
                    '# get_price(prices, "clock")    # uncomment to see the traceback, then read it from the bottom')],
}

TITLES = {'home': 'Welcome and how to use this tutorial'}

PROJECT_STEPS = [
    'Build the program from the requirements above in your own file, without looking at the solution.',
    'Test it with your own data, including empty and wrong input, and fix what breaks.',
    'Compare your version with the full solution and write down two things you would change in yours.',
]

DIY_STEPS = {
    'context': ['Write a Timer context manager (class-based) that prints how long the with-block took.',
                'Rewrite it with @contextmanager and check both print a time.'],
    'typing': ['Add type hints to three functions you wrote in earlier lessons.',
               'Install mypy (pip install mypy), run mypy on the file and fix every error it reports.'],
    'concurrency': ['On your computer, download 5 URLs one after another, then with ThreadPoolExecutor, and compare the times.'],
    'datetime': ['Print the number of days until 31 March of the current financial year.',
                 'Add 18% GST to Decimal("999.99") and round it to 2 places with ROUND_HALF_UP.'],
    'sqlite': ['Create a products table, insert five rows with placeholders, and print the three most expensive.',
               'Wrap two inserts in a transaction, make the second one fail, and check the first was rolled back.'],
    'apis': ['On your computer, call a public JSON API with requests (with a timeout) and print two fields from the response.',
             'Save the response to a .json file and load it back with json.load.'],
    'testing': ['Write three pytest tests for a function from an earlier lesson, including one with pytest.raises.',
                'Replace the print() calls in one script with logging at the right levels.'],
}

EXTRA_STEPS = {
    'home': ['Read the suggested pace and agree your daily target with your trainer.',
             'Install Python 3.12 or newer and VS Code with the Python extension (lesson 1 shows how).'],
    'interview': ['Answer each question aloud in under a minute before reading the answer.',
                  'Mark the questions you could not answer and re-read the lesson they come from.',
                  'Practise the hardest five with a friend or your trainer as a mock interview.'],
    'cheatsheet': ['Keep the cheat sheet open while you build the four projects.'],
}


LESSON_REF = re.compile(r'\b([Ll]esson)s? (\d+)(?:\s*[–-]\s*(\d+))?')


def renumber_refs(lesson, renumber):
    """'Lesson 16' in the tutorial's text -> 'Lesson 3.5', the number the Academy shows."""
    def fix(m):
        word, a, b = m.group(1), m.group(2), m.group(3)
        if b:
            return f'{word}s {renumber[a]} to {renumber[b]}'
        return f'{word} {renumber[a]}'
    for key in ('contentHtml', 'summaryHtml'):
        lesson[key] = LESSON_REF.sub(fix, lesson[key])
    lesson['lab']['steps'] = [LESSON_REF.sub(fix, s) for s in lesson['lab']['steps']]
    for old, new in TEXT_PATCHES.get(lesson['id'], []):
        if old not in lesson['contentHtml'] and old not in lesson['summaryHtml']:
            raise SystemExit(f'{lesson["id"]}: text patch not found: {old[:60]}')
        lesson['contentHtml'] = lesson['contentHtml'].replace(old, new)
        lesson['summaryHtml'] = lesson['summaryHtml'].replace(old, new)


# Lesson ranges in the start page's pace table, and wording about the standalone page's own buttons.
TEXT_PATCHES = {
    'py0': [
        ('<td>1 – 7 (Basics)</td>', '<td>1.1 – 1.7 (Basics)</td>'),
        ('<td>8 – 11 (Data structures)</td>', '<td>2.1 – 2.4 (Data structures)</td>'),
        ('<td>12 – 16 (Functions, modules, files, errors)</td>', '<td>3.1 – 3.5 (Functions, modules, files, errors)</td>'),
        ('<td>17 – 20 (OOP)</td>', '<td>4.1 – 4.4 (OOP)</td>'),
        ('<td>21 – 26 (Advanced)</td>', '<td>5.1 – 5.6 (Advanced)</td>'),
        ('<td>27 – 30 + Projects</td>', '<td>6.1 – 6.4 + Projects 7.1 – 7.4</td>'),
        ('Try each one yourself before opening the solution. Then press <strong>Mark lesson complete</strong>.',
         'Each exercise is a lab step. Try it yourself before reading the solution at the end of the lesson, '
         'then tick it off. Tick every step and pass the quiz to finish the lesson.'),
        ('Some examples (network calls, threads, user <code>input()</code>) are marked "run on your computer".',
         'Some examples (network calls, threads, user <code>input()</code>) are marked "run on your computer". '
         'Every lesson also has a .py file with all its examples to download.'),
    ],
}


def build():
    tb = TreeBuilder()
    tb.feed(SOURCE.read_text(encoding='utf-8'))
    sections = list(tb.root.find_all(lambda n: n.tag == 'section' and 'view' in n.classes))
    by_group = {g[0]: [] for g in GROUPS}
    group_no = {g[0]: n for n, g in enumerate(GROUPS)}
    files = []
    lesson_no = 0
    project_no = 0
    renumber = {}   # the tutorial's own lesson numbers (1-30) -> Academy numbers (1.1-6.4)
    for sec in sections:
        group = sec.attrs['data-group']
        if group not in by_group:
            raise SystemExit(f'unknown group {group!r}')
        by_group[group].append(sec)
        sec.label = f'{group_no[group]}.{len(by_group[group])}'
        if group[0].isdigit():
            lesson_no += 1
            renumber[str(lesson_no)] = sec.label
        elif group == 'Projects':
            project_no += 1
    by_group = {g[0]: [] for g in GROUPS}
    for i, sec in enumerate(sections):
        group = sec.attrs['data-group']
        lesson, sid, file_entry = lesson_from(sec, i, sec.label)
        renumber_refs(lesson, renumber)
        lesson['id'] = f'py{i}'
        by_group[group].append(lesson)
        if file_entry:
            files.append(file_entry)

    domains = [{'id': did, 'name': name, 'weight': weight, 'blurb': blurb, 'lessons': by_group[g]}
               for g, did, name, weight, blurb in GROUPS]
    lessons = [l for d in domains for l in d['lessons']]
    used_quiz = sum(len(l['quiz']) for l in lessons)
    if used_quiz != sum(len(v) for v in QUIZ.values()):
        raise SystemExit('a QUIZ key does not match any section id')

    FILES_DIR.mkdir(parents=True, exist_ok=True)
    for old in FILES_DIR.glob('*.py'):
        old.unlink()
    for fid, text, _ in files:
        (CONTENT / 'exercise-files' / fid).write_text(text, encoding='utf-8')

    track = {
        'id': 'python',
        'code': 'Python',
        'name': 'Complete Python Tutorial',
        'level': 'Beginner to job-ready',
        'status': 'Live',
        'outline': 'Nov 2026',
        'order': 'Start here, then lessons 1 to 30, then the four projects',
        'blurb': ('From your first print() to classes, generators, decorators, databases and testing. Thirty lessons '
                  'with runnable examples and exercises, four real-world projects, and the interview questions '
                  'junior Python developers are asked most.'),
        'facts': [[str(lesson_no), 'lessons from basics to real-world Python'],
                  [str(sum(len(l['lab']['steps']) for l in lessons)), 'exercises and lab steps'],
                  [str(used_quiz), 'quiz questions with explanations'],
                  [str(project_no), 'complete projects with full solutions']],
        'tool': 'Python 3.12+ and VS Code',
        'guide': 'https://docs.python.org/3/tutorial/',
        'note': 'Written for Python 3.12 and newer (November 2026). Examples that use the network, threads or input() '
                'are meant to be run on your own computer.',
        'data': [f[0] for f in files],
        'category': 'development',
        'domains': domains,
        'questionBank': [],
    }
    (CONTENT / 'python.json').write_text(json.dumps(track, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')

    index_path = CONTENT / 'files-index.json'
    index = json.loads(index_path.read_text(encoding='utf-8'))
    index = {k: v for k, v in index.items() if not k.startswith('python/')}
    for fid, _, desc in files:
        index[fid] = {'path': fid.removeprefix('python/'), 'description': desc}
    index_path.write_text(json.dumps(index, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'python.json: {len(domains)} domains, {len(lessons)} lessons, {used_quiz} questions, '
          f'{sum(len(l["lab"]["steps"]) for l in lessons)} lab steps; {len(files)} example files.')


if __name__ == '__main__':
    build()
