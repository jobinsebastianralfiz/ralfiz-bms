"""Allow-list cleaner for lesson HTML.

The package's lesson HTML is ours, but it is stored and rendered with |safe,
so anything outside the documented element set is dropped here, at import.
Headings get ids on the way through so the lesson page can build its
"On this page" chips.
"""
import re
from html import escape
from html.parser import HTMLParser

ALLOWED_TAGS = {
    'h3', 'p', 'ul', 'ol', 'li', 'strong', 'em', 'code', 'pre',
    'table', 'thead', 'tbody', 'tr', 'th', 'td', 'div', 'br',
}
VOID_TAGS = {'br'}
# Only these class values survive, and only on these tags.
ALLOWED_CLASSES = {'pre': {'code'}, 'div': {'example', 'callout', 'warn'}}
# Content of these is dropped along with the tag.
DROP_WITH_CONTENT = {'script', 'style', 'iframe', 'object', 'embed', 'template'}


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
