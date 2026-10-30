"""Render stored TipTap JSON to HTML for PDF export.

Note content is user data, so everything is escaped and every style value is checked against
a strict pattern before it reaches the HTML/CSS. Images may only point at the note owner's own
assets (rewritten to `asset:<id>`); anything else is dropped rather than fetched."""
import re
from html import escape

ASSET_SRC = re.compile(r"^/notes/api/assets/([0-9a-f-]{36})/$")
SAFE_COLOR = re.compile(
    r"^(#[0-9a-fA-F]{3,8}|rgba?\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}\s*(,\s*(0|1|0?\.\d+)\s*)?\))$"
)
SAFE_SIZE = re.compile(r"^\d{1,3}(\.\d{1,2})?(px|pt|em|rem)$")
SAFE_FONT = re.compile(r"^[A-Za-z0-9 ,'\"-]{1,120}$")
SAFE_NUMBER = re.compile(r"^\d{1,2}(\.\d{1,2})?$")
SAFE_HREF = re.compile(r"^(https?://|mailto:|tel:)", re.IGNORECASE)
TEXT_ALIGN = {"left", "center", "right", "justify"}
# Callout variants and their icons; must match CALLOUTS in frontend/src/editor/callout.tsx.
CALLOUTS = {"info": "💡", "note": "📝", "success": "✅", "warning": "⚠️", "danger": "🚫"}
VERTICAL_ALIGN = {"top", "middle", "bottom"}


def _attr(value):
    return escape(str(value), quote=True)


def _style(**props):
    """Build a style attribute from already-validated values; empty values are skipped."""
    parts = [f"{name.replace('_', '-')}: {value}" for name, value in props.items() if value]
    return f' style="{_attr("; ".join(parts))}"' if parts else ""


def _check(pattern, value):
    return value if isinstance(value, str) and pattern.match(value.strip()) else None


def _mark_tags(mark):
    """(opening tag, closing tag) for a mark, or None to ignore it."""
    kind = mark.get("type")
    attrs = mark.get("attrs") or {}
    simple = {
        "bold": "strong", "italic": "em", "underline": "u", "strike": "s",
        "code": "code", "subscript": "sub", "superscript": "sup",
    }
    if kind in simple:
        tag = simple[kind]
        return f"<{tag}>", f"</{tag}>"
    if kind == "link":
        href = attrs.get("href") or ""
        if not isinstance(href, str) or not SAFE_HREF.match(href):
            return None
        return f'<a href="{_attr(href)}">', "</a>"
    if kind == "highlight":
        color = _check(SAFE_COLOR, attrs.get("color")) or "#fff59d"
        return f"<mark{_style(background_color=color)}>", "</mark>"
    if kind == "textStyle":
        style = _style(
            color=_check(SAFE_COLOR, attrs.get("color")),
            background_color=_check(SAFE_COLOR, attrs.get("backgroundColor")),
            font_family=_check(SAFE_FONT, attrs.get("fontFamily")),
            font_size=_check(SAFE_SIZE, attrs.get("fontSize")),
            line_height=_check(SAFE_NUMBER, attrs.get("lineHeight")),
        )
        return (f"<span{style}>", "</span>") if style else None
    return None


def _text(node):
    html = escape(node.get("text", ""))
    for mark in reversed(node.get("marks") or []):
        tags = _mark_tags(mark) if isinstance(mark, dict) else None
        if tags:
            html = f"{tags[0]}{html}{tags[1]}"
    return html


class Renderer:
    def __init__(self, asset_ids):
        # Ids of the owner's assets; other images are dropped.
        self.asset_ids = asset_ids

    def children(self, node):
        return "".join(self.node(child) for child in node.get("content") or [] if isinstance(child, dict))

    def node(self, node):
        kind = node.get("type")
        attrs = node.get("attrs") or {}
        inner = self.children(node)
        align = attrs.get("textAlign") if attrs.get("textAlign") in TEXT_ALIGN else None

        if kind == "text":
            return _text(node)
        if kind == "paragraph":
            return f"<p{_style(text_align=align)}>{inner or '<br>'}</p>"
        if kind == "heading":
            level = attrs.get("level") if attrs.get("level") in (1, 2, 3, 4, 5, 6) else 2
            return f"<h{level}{_style(text_align=align)}>{inner}</h{level}>"
        if kind == "bulletList":
            return f"<ul>{inner}</ul>"
        if kind == "orderedList":
            start = attrs.get("start")
            start_attr = f' start="{start}"' if isinstance(start, int) and start != 1 else ""
            return f"<ol{start_attr}>{inner}</ol>"
        if kind == "listItem":
            return f"<li>{inner}</li>"
        if kind == "taskList":
            return f'<ul class="tasks">{inner}</ul>'
        if kind == "taskItem":
            checked = attrs.get("checked") is True
            return f'<li class="task{" done" if checked else ""}"><span class="box"></span><div>{inner}</div></li>'
        if kind == "blockquote":
            return f"<blockquote>{inner}</blockquote>"
        if kind == "codeBlock":
            return f"<pre><code>{inner}</code></pre>"
        if kind == "horizontalRule":
            return "<hr>"
        if kind == "hardBreak":
            return "<br>"
        if kind == "pageBreak":
            return '<div class="page-break"></div>'
        if kind == "image":
            return self.image(attrs)
        if kind == "drawing":
            # The drawing's PNG export; the Excalidraw scene itself is only for editing.
            return f'<div class="drawing">{self.image(attrs)}</div>'
        if kind == "callout":
            variant = attrs.get("variant") if attrs.get("variant") in CALLOUTS else "info"
            return (
                f'<div class="callout callout-{variant}"><span class="callout-icon">{CALLOUTS[variant]}</span>'
                f'<div class="callout-body">{inner}</div></div>'
            )
        if kind == "columns":
            # A table lays columns out reliably in WeasyPrint and keeps them side by side across pages.
            return f'<table class="columns"><tr>{inner}</tr></table>'
        if kind == "column":
            return f"<td>{inner}</td>"
        if kind == "details":
            # Toggles print expanded: a PDF has no way to open them.
            return f'<div class="toggle">{inner}</div>'
        if kind == "detailsSummary":
            return f'<p class="toggle-title">{inner}</p>'
        if kind == "detailsContent":
            return f'<div class="toggle-body">{inner}</div>'
        if kind == "table":
            return f"<table>{inner}</table>"
        if kind == "tableRow":
            return f"<tr>{inner}</tr>"
        if kind in ("tableCell", "tableHeader"):
            return self.cell("th" if kind == "tableHeader" else "td", attrs, inner)
        # Unknown nodes: keep their text rather than lose it.
        return inner

    def image(self, attrs):
        match = ASSET_SRC.match(str(attrs.get("src") or ""))
        if not match or match.group(1) not in self.asset_ids:
            return ""
        width = attrs.get("width")
        style = _style(width=f"{int(width)}px") if isinstance(width, (int, float)) and 0 < width < 5000 else ""
        alt = _attr(attrs.get("alt") or "")
        return f'<img src="asset:{match.group(1)}" alt="{alt}"{style}>'

    def cell(self, tag, attrs, inner):
        spans = ""
        for name in ("colspan", "rowspan"):
            value = attrs.get(name)
            if isinstance(value, int) and 1 < value < 100:
                spans += f' {name}="{value}"'
        widths = attrs.get("colwidth")
        width = None
        if isinstance(widths, list) and widths and all(isinstance(w, (int, float)) for w in widths):
            width = f"{int(sum(widths))}px"
        style = _style(
            width=width,
            background_color=_check(SAFE_COLOR, attrs.get("backgroundColor")),
            vertical_align=attrs.get("verticalAlign") if attrs.get("verticalAlign") in VERTICAL_ALIGN else None,
        )
        return f"<{tag}{spans}{style}>{inner}</{tag}>"


def render_doc(content, asset_ids):
    if not isinstance(content, dict):
        return ""
    return Renderer(asset_ids).children(content)


def referenced_asset_ids(content):
    """Asset ids used by image nodes, so the exporter can look them up in one query."""
    ids = set()

    def walk(node):
        if not isinstance(node, dict):
            return
        if node.get("type") in ("image", "drawing"):
            match = ASSET_SRC.match(str((node.get("attrs") or {}).get("src") or ""))
            if match:
                ids.add(match.group(1))
        for child in node.get("content") or []:
            walk(child)

    walk(content)
    return ids
