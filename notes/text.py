"""Plain-text extraction from stored note content, for search and list previews."""

BLOCK_TYPES = {
    "paragraph", "heading", "listItem", "taskItem", "blockquote", "codeBlock",
    "tableRow", "tableCell", "tableHeader", "horizontalRule",
    "callout", "column", "detailsSummary", "detailsContent",
}
MAX_SEARCH_CHARS = 100_000


def _tiptap_text(node, out):
    if not isinstance(node, dict):
        return
    if node.get("type") == "text":
        out.append(node.get("text", ""))
    elif node.get("type") == "hardBreak":
        out.append("\n")
    for child in node.get("content") or []:
        _tiptap_text(child, out)
    if node.get("type") in BLOCK_TYPES:
        out.append("\n")


def _board_text(scene):
    elements = scene.get("elements") if isinstance(scene, dict) else None
    lines = []
    for el in elements or []:
        if isinstance(el, dict) and el.get("type") == "text" and not el.get("isDeleted"):
            lines.append(el.get("originalText") or el.get("text", ""))
    return "\n".join(lines)


def extract_text(kind, content):
    if not content:
        return ""
    if kind == "board":
        text = _board_text(content)
    else:
        out = []
        _tiptap_text(content, out)
        text = "".join(out)
    return text.strip()[:MAX_SEARCH_CHARS]


def make_preview(text, length=200):
    flat = " ".join(text.split())
    return flat if len(flat) <= length else flat[: length - 1].rstrip() + "…"
