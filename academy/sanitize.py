"""Allow-list cleaner for lesson HTML.

The package's lesson HTML is ours, but it is stored and rendered with |safe,
so anything outside the documented element set is dropped here, at import.
Headings get ids on the way through so the lesson page can build its
"On this page" chips. The only attributes beyond class and cell spans are the
three widget placeholders: the phone mock, <div class="mock-slot" data-mock="N">,
whose data check_mocks() vets for flutter-mocks.js, the live code playground,
<div class="play-slot" data-play="N">, whose data check_plays() vets for
dom-play.js, and the interactive solver, <div class="solver-slot"
data-solver="N">, mounted by ugc-solvers.js from the names check_solvers() vets.
"""
import re
from html import escape
from html.parser import HTMLParser

ALLOWED_TAGS = {
    'h3', 'p', 'ul', 'ol', 'li', 'strong', 'em', 'code', 'pre',
    'table', 'thead', 'tbody', 'tr', 'th', 'td', 'div', 'br', 'kbd', 'sub', 'sup',
}
VOID_TAGS = {'br'}
# Only these class values survive, and only on these tags.
ALLOWED_CLASSES = {'pre': {'code'}, 'div': {'example', 'callout', 'warn'}}
# Content of these is dropped along with the tag.
DROP_WITH_CONTENT = {'script', 'style', 'iframe', 'object', 'embed', 'template'}


SLOTS = (('mock-slot', 'data-mock'), ('play-slot', 'data-play'), ('solver-slot', 'data-solver'))


def _slot(attrs):
    """A widget placeholder, exactly <div class="mock-slot" data-mock="N">,
    <div class="play-slot" data-play="N"> or <div class="solver-slot" data-solver="N">
    (N < 100): its clean tag, else None."""
    a = dict(attrs)
    for cls, name in SLOTS:
        if a.get('class') == cls and set(a) == {'class', name}:
            n = a[name] or ''
            return f'<div class="{cls}" {name}="{int(n)}">' if re.fullmatch(r'[0-9]{1,2}', n) else None
    return None


class _Cleaner(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.dropped = set()
        self.skip_depth = 0
        self.h3_count = 0

    def handle_starttag(self, tag, attrs):
        if tag in DROP_WITH_CONTENT:
            self.skip_depth += 1
            self.dropped.add(tag)
            return
        if self.skip_depth:
            return
        if tag not in ALLOWED_TAGS:
            self.dropped.add(tag)
            return
        parts = [tag]
        if tag == 'h3':
            self.h3_count += 1
            parts.append(f'id="sec-{self.h3_count}"')
        if tag in ('td', 'th'):
            # Spanning cells keep their layout; only small whole numbers pass.
            for name in ('colspan', 'rowspan'):
                value = dict(attrs).get(name) or ''
                if value.isdigit() and 1 < int(value) <= 20:
                    parts.append(f'{name}="{int(value)}"')
        slot = _slot(attrs) if tag == 'div' else None
        if slot is not None:
            self.out.append(slot)
            return
        allowed = ALLOWED_CLASSES.get(tag)
        if allowed:
            classes = [c for c in (dict(attrs).get('class') or '').split() if c in allowed]
            if classes:
                parts.append(f'class="{" ".join(classes)}"')
        self.out.append(f'<{" ".join(parts)}>')

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag in ALLOWED_TAGS and tag not in VOID_TAGS and not self.skip_depth:
            self.out.append(f'</{tag}>')

    def handle_endtag(self, tag):
        if tag in DROP_WITH_CONTENT:
            self.skip_depth = max(0, self.skip_depth - 1)
            return
        if self.skip_depth or tag not in ALLOWED_TAGS or tag in VOID_TAGS:
            return
        self.out.append(f'</{tag}>')

    def handle_data(self, data):
        if not self.skip_depth:
            self.out.append(escape(data, quote=False))


def clean_html(html):
    """Return (clean_html, set of dropped tag names)."""
    cleaner = _Cleaner()
    cleaner.feed(html or '')
    cleaner.close()
    return ''.join(cleaner.out), cleaner.dropped


_H3 = re.compile(r'<h3 id="(sec-\d+)">(.*?)</h3>', re.S)
_TAG = re.compile(r'<[^>]+>')


def headings(clean):
    """[(anchor id, plain text)] for every h3 in cleaned HTML."""
    from html import unescape
    return [(anchor, unescape(_TAG.sub('', text)).strip()) for anchor, text in _H3.findall(clean)]


# Mock data is drawn by static/academy/flutter-mocks.js with innerHTML. Text
# fields are escaped there, but colours, sizes and alignments are written into
# style and class attributes as they are, so those must be plain tokens.
MOCK_TEXT_KEYS = {
    't', 'title', 'caption', 'code', 'file', 'label', 'hint', 'value', 'subtitle', 'error',
    'helper', 'content', 'child', 'action', 'actions', 'items', 'tabs', 'i', 'icon',
    'leading', 'trailing', 'suffix', 'w',
}
_MOCK_TOKEN = re.compile(r'[\w#.%(), -]*')


def check_mocks(mocks):
    """Problems (list of strings) with a lesson's phone-mock data; empty if it is safe to draw."""
    problems = []

    def walk(value, key, path):
        if isinstance(value, dict):
            for k, v in value.items():
                walk(v, k, f'{path}.{k}')
        elif isinstance(value, list):
            for n, v in enumerate(value):
                walk(v, key, f'{path}[{n}]')
        elif isinstance(value, str):
            if key not in MOCK_TEXT_KEYS and not _MOCK_TOKEN.fullmatch(value):
                problems.append(f'{path}: {value[:40]!r} is not a plain value')
        elif not (value is None or isinstance(value, (bool, int, float))):
            problems.append(f'{path}: unexpected {type(value).__name__}')

    if not isinstance(mocks, list):
        return ['mocks must be a list']
    for n, mock in enumerate(mocks):
        if not isinstance(mock, dict):
            problems.append(f'mocks[{n}] must be an object')
        else:
            walk(mock, None, f'mocks[{n}]')
    return problems


# A playground's HTML, CSS and JavaScript run only inside a sandboxed iframe
# (no same-origin access), so they may hold anything. The fields dom-play.js
# writes into the lesson page itself are escaped there, except the preview
# height, which goes into a style attribute and must be a number.
PLAY_TEXT_KEYS = {'title', 'url', 'caption', 'html', 'css', 'js', 'tab'}
# Preview height in pixels; wait is a delay in milliseconds.
LIMITS = {'height': 2000, 'wait': 60000}


def check_plays(plays):
    """Problems (list of strings) with a lesson's playground data; empty if it is safe to mount."""
    if not isinstance(plays, list):
        return ['plays must be a list']
    problems = []
    for n, play in enumerate(plays):
        if not isinstance(play, dict):
            problems.append(f'plays[{n}] must be an object')
            continue
        for k, v in play.items():
            ok = (isinstance(v, str) if k in PLAY_TEXT_KEYS
                  else isinstance(v, bool) if k in ('module', 'autorun', 'expectError')
                  else isinstance(v, int) and not isinstance(v, bool) and 0 <= v <= LIMITS[k] if k in LIMITS
                  else False)
            if not ok:
                problems.append(f'plays[{n}].{k}: {str(v)[:40]!r} is not allowed')
    return problems


# Solver names are looked up in ugc-solvers.js's registry; anything else is refused.
_SOLVER_NAME = re.compile(r'[a-z][a-z0-9]{1,23}')


def check_solvers(solvers):
    """Problems (list of strings) with a lesson's solver names; empty if they are plain names."""
    if not isinstance(solvers, list):
        return ['solvers must be a list']
    return [f'solvers[{n}]: {str(v)[:40]!r} is not a solver name'
            for n, v in enumerate(solvers) if not (isinstance(v, str) and _SOLVER_NAME.fullmatch(v))]


# Exam-format question parts. They are rendered by templates with autoescaping,
# so only the shape is checked here.
STEM_TEXT_KEYS = {'passage', 'passageTitle', 'code', 'after'}


def check_stem(stem):
    """Problems (list of strings) with a question's stem parts; empty if the shape is right."""
    if not isinstance(stem, dict):
        return ['stem must be an object']
    problems = []
    strings = lambda v: isinstance(v, list) and all(isinstance(x, str) for x in v)
    for k, v in stem.items():
        if k in STEM_TEXT_KEYS:
            ok = isinstance(v, str)
        elif k == 'stmts':
            ok = strings(v)
        elif k == 'lists':
            ok = (isinstance(v, dict) and strings(v.get('a')) and strings(v.get('b'))
                  and (v.get('h') is None or (strings(v['h']) and len(v['h']) == 2)))
        elif k == 'data':
            ok = (isinstance(v, dict) and strings(v.get('head'))
                  and isinstance(v.get('rows'), list) and all(isinstance(r, list) for r in v['rows'])
                  and all(isinstance(v.get(x, ''), str) for x in ('caption', 'note')))
        else:
            ok = False
        if not ok:
            problems.append(f'stem.{k}: not allowed or wrong shape')
    return problems
