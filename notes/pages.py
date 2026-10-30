"""Page settings stored on a note: paper size, orientation, margins, header/footer text."""

PAGE_SIZES = {"A4": (210, 297), "Letter": (215.9, 279.4), "Legal": (215.9, 355.6)}
DEFAULTS = {
    "size": "A4",
    "orientation": "portrait",
    "margins": {"top": 20, "right": 20, "bottom": 20, "left": 20},
    "header": "",
    "footer": "",
    "page_numbers": True,
    "show_title": True,
}
MAX_MARGIN_MM = 60
MAX_TEXT = 200


def clean_page_settings(value):
    """Return a complete, validated settings dict; raise ValueError with a readable message."""
    if not isinstance(value, dict):
        raise ValueError("Page settings must be an object.")
    out = {**DEFAULTS, "margins": dict(DEFAULTS["margins"])}

    size = value.get("size", out["size"])
    if size not in PAGE_SIZES:
        raise ValueError(f"Page size must be one of {', '.join(PAGE_SIZES)}.")
    out["size"] = size

    orientation = value.get("orientation", out["orientation"])
    if orientation not in ("portrait", "landscape"):
        raise ValueError("Orientation must be portrait or landscape.")
    out["orientation"] = orientation

    margins = value.get("margins", {})
    if not isinstance(margins, dict):
        raise ValueError("Margins must be an object.")
    for side in out["margins"]:
        if side in margins:
            mm = margins[side]
            if isinstance(mm, bool) or not isinstance(mm, (int, float)) or not 0 <= mm <= MAX_MARGIN_MM:
                raise ValueError(f"Margins must be between 0 and {MAX_MARGIN_MM} mm.")
            out["margins"][side] = round(float(mm), 1)

    for key in ("header", "footer"):
        text = value.get(key, "")
        if not isinstance(text, str) or len(text) > MAX_TEXT:
            raise ValueError(f"The {key} must be text of at most {MAX_TEXT} characters.")
        out[key] = text.strip()

    for key in ("page_numbers", "show_title"):
        flag = value.get(key, out[key])
        if not isinstance(flag, bool):
            raise ValueError(f"{key} must be true or false.")
        out[key] = flag
    return out


def page_dimensions(settings):
    """(width, height) in mm, after orientation."""
    width, height = PAGE_SIZES[settings["size"]]
    return (height, width) if settings["orientation"] == "landscape" else (width, height)
