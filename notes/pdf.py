"""PDF export with WeasyPrint.

WeasyPrint needs the Pango system libraries (on macOS: `brew install pango` and
DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib), so it is imported lazily and a missing install
becomes a 503 instead of breaking the whole app. The renderer never touches the network or the
filesystem: the only URLs it may load are `asset:<id>` images belonging to the note's owner."""
from html import escape

from rest_framework.exceptions import APIException

from .models import Asset
from .pages import clean_page_settings, page_dimensions
from .render import referenced_asset_ids, render_doc

FONT_STACK = '"Inter", "Helvetica Neue", Arial, "Noto Sans", "Noto Sans Malayalam", "Noto Sans Devanagari", sans-serif'

DOC_CSS = """
body { font-family: FONTS; font-size: 11pt;
       line-height: 1.5; color: #1f2328; margin: 0; }
h1, h2, h3, h4, h5, h6 { line-height: 1.25; margin: 1em 0 0.4em; break-after: avoid; }
h1 { font-size: 22pt; } h2 { font-size: 17pt; } h3 { font-size: 14pt; }
h4, h5, h6 { font-size: 12pt; }
h1.doc-title { margin-top: 0; }
p { margin: 0 0 0.6em; orphans: 2; widows: 2; }
a { color: #2563eb; }
blockquote { margin: 0.8em 0; padding-left: 1em; border-left: 3px solid #d0d7de; color: #57606a; }
pre { background: #f6f8fa; padding: 0.8em; border-radius: 4px; white-space: pre-wrap; font-size: 9.5pt; }
code { font-family: "SFMono-Regular", Menlo, Consolas, monospace; }
hr { border: 0; border-top: 1px solid #d0d7de; margin: 1.2em 0; }
img { max-width: 100%; height: auto; }
mark { padding: 0 0.1em; }
ul.tasks { list-style: none; padding-left: 0.2em; }
li.task { display: flex; gap: 0.5em; }
li.task .box { flex: none; width: 0.8em; height: 0.8em; margin-top: 0.3em; border: 1px solid #57606a; border-radius: 2px; }
li.task.done .box { background: #57606a; }
li.task.done > div { color: #8c959f; text-decoration: line-through; }
li > p, li.task p { margin: 0; }
table { border-collapse: collapse; width: 100%; margin: 0.8em 0; table-layout: fixed; }
td, th { border: 1px solid #9ca3af; padding: 4px 8px; vertical-align: top; overflow-wrap: anywhere; }
th { background: #f3f4f6; font-weight: 600; text-align: left; }
td p, th p { margin: 0; }
tr { break-inside: avoid; }
.page-break { break-after: page; height: 0; }
.callout { display: flex; gap: 0.6em; padding: 0.7em 0.9em; margin: 0.8em 0; border-radius: 6px; border: 1px solid #dbe6fe; background: #eef4ff; break-inside: avoid; }
.callout-note { background: #f4f4f5; border-color: #e4e4e7; }
.callout-success { background: #ecfdf3; border-color: #d1fadf; }
.callout-warning { background: #fffaeb; border-color: #fdeccb; }
.callout-danger { background: #fef3f2; border-color: #fee4e2; }
.callout-icon { flex: none; }
.callout-body { flex: 1; min-width: 0; }
.callout-body > :last-child { margin-bottom: 0; }
table.columns { margin: 0.8em 0; }
table.columns td { border: 0; padding: 0 0.8em 0 0; }
table.columns td:last-child { padding-right: 0; }
table.columns tr { break-inside: auto; }
.toggle { margin: 0.6em 0; }
.toggle-title { font-weight: 600; margin-bottom: 0.3em; }
.toggle-body { padding-left: 1em; border-left: 2px solid #e4e4e7; }
.drawing { margin: 0.8em 0; }
.running-header, .running-footer { font-size: 8.5pt; color: #6e7781; }
.running-header { position: running(header); }
.running-footer { position: running(footer); }
""".replace("FONTS", FONT_STACK)


class PdfUnavailable(APIException):
    status_code = 503
    default_detail = "PDF export isn't available on this server right now."
    default_code = "pdf_unavailable"


def _weasyprint():
    try:
        import weasyprint
    except (ImportError, OSError):
        raise PdfUnavailable()
    return weasyprint


def _page_css(settings):
    width, height = page_dimensions(settings)
    m = settings["margins"]
    rules = [
        f"size: {width}mm {height}mm;",
        f"margin: {m['top']}mm {m['right']}mm {m['bottom']}mm {m['left']}mm;",
        # Margin boxes (page numbers) don't inherit the body font.
        f"font-family: {FONT_STACK};",
    ]
    if settings["header"]:
        rules.append("@top-center { content: element(header); vertical-align: bottom; padding-bottom: 4mm; }")
    if settings["footer"]:
        rules.append("@bottom-center { content: element(footer); vertical-align: top; padding-top: 4mm; }")
    if settings["page_numbers"]:
        rules.append(
            '@bottom-right { content: counter(page) " / " counter(pages); font-size: 8.5pt; color: #6e7781;'
            " vertical-align: top; padding-top: 4mm; }"
        )
    return "@page { " + " ".join(rules) + " }"


def note_html(note, asset_ids):
    settings = clean_page_settings(note.page_settings or {})
    parts = []
    if settings["header"]:
        parts.append(f'<div class="running-header">{escape(settings["header"])}</div>')
    if settings["footer"]:
        parts.append(f'<div class="running-footer">{escape(settings["footer"])}</div>')
    if settings["show_title"] and note.title.strip():
        parts.append(f'<h1 class="doc-title">{escape(note.title)}</h1>')
    parts.append(render_doc(note.content, asset_ids))
    title = escape(note.title or "Untitled")
    return (
        f'<!doctype html><html><head><meta charset="utf-8"><title>{title}</title>'
        f"<style>{_page_css(settings)}{DOC_CSS}</style></head>"
        f"<body>{''.join(parts)}</body></html>"
    )


def _asset_fetcher_class(weasyprint, assets):
    class AssetFetcher(weasyprint.URLFetcher):
        """Serves `asset:<id>` from the owner's images and refuses every other URL."""

        def fetch(self, url, headers=None):
            asset = assets.get(url[len("asset:"):]) if url.startswith("asset:") else None
            if asset is None:
                raise ValueError("Only the note owner's images can be embedded.")
            with asset.file.open("rb") as f:
                body = f.read()
            return weasyprint.urls.URLFetcherResponse(url, body=body, headers={"Content-Type": asset.content_type})

    return AssetFetcher


def build_pdf(notes, owner):
    """Render one or more doc notes (all owned by `owner`) into a single PDF and return its bytes."""
    weasyprint = _weasyprint()

    wanted = set().union(*(referenced_asset_ids(n.content) for n in notes))
    assets = {str(a.id): a for a in Asset.objects.filter(owner=owner, id__in=wanted)} if wanted else {}
    fetcher = _asset_fetcher_class(weasyprint, assets)()

    documents = [
        weasyprint.HTML(string=note_html(note, set(assets)), url_fetcher=fetcher).render()
        for note in notes
    ]
    pages = [page for doc in documents for page in doc.pages]
    return documents[0].copy(pages).write_pdf()
