"""Rewrite a certificate body so the recipient's name can be set large.

The print layout promotes the name to a heading, but only when the body has
not already spent it (see `employees.certificate_pdf.build_context`). Bodies
written for the old layout open with a full certifying clause:

    This is to certify that {salutation} {student_name} (Register No.
    {register_number}), a student of {college_name}, has successfully
    completed an internship with **Ralfiz Technologies**...

Everything up to "has successfully completed" is now printed above the body:
the name as the heading, the register number and college on the line beneath
it. Stripping that clause leaves a body that reads as a continuation of the
name, which is the traditional certificate construction:

    Ms. Fathima Nasrin
    ------------------
    has successfully completed an internship with Ralfiz Technologies...
"""

import re

# "This is to certify that", "We hereby certify that", "Certify" ...
_LEAD_IN = re.compile(
    r'^\s*(?:this\s+is\s+to\s+certify\s+that'
    r'|this\s+certifies\s+that'
    r'|we\s+(?:hereby\s+)?certify\s+that'
    r'|it\s+is\s+hereby\s+certified\s+that'
    r'|certified\s+that'
    r'|certify(?:ing)?(?:\s+that)?)\s+',
    re.IGNORECASE,
)

# The recipient placeholder. The Experience template calls it {employee_name};
# both resolve to the same person.
_NAME_PLACEHOLDERS = ('{student_name}', '{employee_name}')

# The name itself, optionally preceded by the salutation and, as the shipped
# templates all do, wrapped in `**bold**`.
_NAME = re.compile(
    r'^\*{0,2}(?:\{salutation\}\s*)?\*{0,2}\{(?:student|employee)_name\}\*{0,2}\s*',
    re.IGNORECASE,
)

# "(Register No. {register_number})" - already printed under the heading.
_REGISTER = re.compile(r'^\((?=[^)]*\{register_number\})[^)]*\)\s*', re.IGNORECASE)

# ", a student of **{college_name}**," - also printed under the heading.
_COLLEGE = re.compile(
    r'^[,\s]*(?:an?\s+)?(?:student|intern|candidate)?\s*'
    r'(?:of|from|at|studying\s+at)\s+\*{0,2}\{college_name\}\*{0,2}\s*',
    re.IGNORECASE,
)

# A trailing "Date: {issue_date}" line. The design prints the issue date in
# its header, so leaving it in the body sets it twice.
_TRAILING_DATE = re.compile(
    r'\n\s*(?:date|dated)\s*[:\-]\s*\{issue_date\}\s*$',
    re.IGNORECASE,
)

# A body that already continues from the name needs no capital letter.
_CONTINUES = re.compile(
    r'^(?:has|have|had|was|were|is|are|been|did|does|successfully|completed|'
    r'worked|served|participated|attended|underwent|joined|received|earned|'
    r'secured|obtained|took|demonstrated|showed|of|from)\b',
    re.IGNORECASE,
)


def rewrite_body(body_text):
    """Return the body with its opening name clause removed.

    Returns the input unchanged when there is nothing to promote - no
    `{student_name}` placeholder, or it is not in the opening sentence.
    """
    if not body_text or not any(n in body_text for n in _NAME_PLACEHOLDERS):
        return body_text

    # Only the first paragraph carries the certifying clause.
    body = body_text.replace('\r\n', '\n').replace('\r', '\n')
    body = _TRAILING_DATE.sub('', body)
    head, sep, tail = body.partition('\n\n')

    rest = _LEAD_IN.sub('', head, count=1)
    stripped, count = _NAME.subn('', rest, count=1)
    if not count:
        # The name is somewhere in the middle of the sentence; rewriting that
        # would need judgement about the prose, so leave it to a human.
        return body_text

    stripped = _REGISTER.sub('', stripped, count=1)
    stripped = _COLLEGE.sub('', stripped, count=1)
    stripped = stripped.lstrip(' ,;-–—')
    # A bold run that opened around the name can be left dangling by the cut.
    if stripped.startswith('**') and stripped.count('**') % 2:
        stripped = stripped[2:].lstrip(' ,;')

    if not stripped:
        return body_text

    if not _CONTINUES.match(stripped):
        stripped = stripped[0].upper() + stripped[1:]

    return stripped + sep + tail


def name_still_in_body(body_text):
    """True when the name would still be printed inside the prose."""
    return any(n in (body_text or '') for n in _NAME_PLACEHOLDERS)
