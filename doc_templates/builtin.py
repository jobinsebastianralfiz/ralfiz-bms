"""Built-in templates, written as TipTap JSON with small helpers.

`manage.py sync_templates` adds new ones to the database (and with --force overwrites the
content of existing ones). Keep slugs stable: they link a database row to its definition here."""

# --- TipTap JSON helpers -------------------------------------------------------------------

def t(text, *marks, color=None):
    """A text node. Marks: "bold", "italic", "underline"…; `color` adds a textStyle colour."""
    node = {"type": "text", "text": text}
    mark_list = [{"type": m} for m in marks]
    if color:
        mark_list.append({"type": "textStyle", "attrs": {"color": color}})
    if mark_list:
        node["marks"] = mark_list
    return node


def b(text):
    return t(text, "bold")


def _inline(parts):
    return [t(p) if isinstance(p, str) else p for p in parts if p != ""]


def p(*parts, align=None):
    node = {"type": "paragraph"}
    if align:
        node["attrs"] = {"textAlign": align}
    content = _inline(parts)
    if content:
        node["content"] = content
    return node


def h(level, *parts, align=None):
    attrs = {"level": level}
    if align:
        attrs["textAlign"] = align
    return {"type": "heading", "attrs": attrs, "content": _inline(parts)}


def _items(item_type, items):
    return [{"type": item_type, "content": [p(*(i if isinstance(i, tuple) else (i,)))]} for i in items]


def ul(*items):
    return {"type": "bulletList", "content": _items("listItem", items)}


def ol(*items):
    return {"type": "orderedList", "attrs": {"start": 1}, "content": _items("listItem", items)}


def tasks(*items):
    """Items are text, or (text, checked)."""
    out = []
    for item in items:
        text, checked = item if isinstance(item, tuple) else (item, False)
        out.append({"type": "taskItem", "attrs": {"checked": checked}, "content": [p(text)]})
    return {"type": "taskList", "content": out}


def table(rows, header=True, shade=None, header_color="#e8eaf6", first_width=None):
    """`rows` are lists of cells; a cell is text, a node list, or a dict {"text"/"nodes", "colspan", "bg"}.
    `shade` colours the first column of body rows; `first_width` (px) narrows the first column, e.g. "#"."""
    out = []
    for r, row in enumerate(rows):
        is_header = header and r == 0
        cells = []
        for c, cell in enumerate(row):
            spec = cell if isinstance(cell, dict) else {"text": cell}
            if "nodes" in spec:
                content = spec["nodes"]
            else:
                text = spec.get("text", "")
                content = [p(b(text) if spec.get("bold") else text)]
            colspan = spec.get("colspan", 1)
            attrs = {"colspan": colspan, "rowspan": 1, "colwidth": None}
            if first_width and c == 0 and colspan == 1:
                attrs["colwidth"] = [first_width]
            bg = spec.get("bg") or (header_color if is_header else (shade if c == 0 and shade else None))
            if bg:
                attrs["backgroundColor"] = bg
            cells.append({"type": "tableHeader" if is_header else "tableCell", "attrs": attrs, "content": content})
        out.append({"type": "tableRow", "content": cells})
    return {"type": "table", "content": out}


def hr():
    return {"type": "horizontalRule"}


def page_break():
    return {"type": "pageBreak"}


def quote(*parts):
    return {"type": "blockquote", "content": [p(*parts)]}


def doc(*nodes):
    return {"type": "doc", "content": list(nodes)}


ACCENT = "#3949ab"
MUTED = "#6b7280"


def section(title):
    """Resume-style section heading in the accent colour."""
    return h(2, t(title.upper(), color=ACCENT))


def pages(margin=20, show_title=False, **extra):
    return {
        "margins": {"top": margin, "right": margin, "bottom": margin, "left": margin},
        "show_title": show_title,
        **extra,
    }


# --- Templates -----------------------------------------------------------------------------

SIMPLE_RESUME = doc(
    h(1, "Your Name", align="center"),
    p(t("Kochi, Kerala  ·  +91 98765 43210  ·  you@example.com  ·  linkedin.com/in/yourname", color=MUTED), align="center"),
    section("Summary"),
    p("Two or three lines about who you are, what you're good at and the kind of role you want. "
      "Keep it specific: years of experience, your field and one strong achievement."),
    section("Experience"),
    h(3, "Job Title — Company Name"),
    p(t("Month 2022 – Present  ·  City", "italic", color=MUTED)),
    ul(
        "Start each point with a verb and show the result: “Cut invoice processing time by 40%”.",
        "Mention tools, team size or budgets when they help.",
        "Three to five points per role is plenty.",
    ),
    h(3, "Previous Job Title — Company Name"),
    p(t("Month 2019 – Month 2022  ·  City", "italic", color=MUTED)),
    ul("Your main responsibility and what changed because of your work.", "A project you led or a skill you built."),
    section("Education"),
    p(b("Degree, Subject"), " — College or University, Year"),
    section("Skills"),
    p("Skill one · Skill two · Skill three · Skill four · Skill five"),
    section("Languages"),
    p("English (fluent) · Malayalam (native) · Hindi (conversational)"),
)

PROFESSIONAL_RESUME = doc(
    h(1, t("YOUR NAME", color=ACCENT)),
    p(b("Senior Product Designer")),
    p(t("+91 98765 43210  ·  you@example.com  ·  portfolio.example.com  ·  Bengaluru", color=MUTED)),
    hr(),
    section("Profile"),
    p("Designer with 7 years of experience shipping web and mobile products used by millions. "
      "Known for turning messy requirements into simple, tested interfaces and for mentoring junior designers."),
    section("Key skills"),
    table(
        [
            [{"text": "Design", "bold": True}, "User research, interaction design, prototyping, design systems"],
            [{"text": "Tools", "bold": True}, "Figma, Framer, Adobe Creative Cloud, Notion, Jira"],
            [{"text": "Leadership", "bold": True}, "Mentoring, workshop facilitation, stakeholder management"],
        ],
        header=False,
        shade="#eef0fb",
    ),
    section("Experience"),
    h(3, "Senior Product Designer · Company Name"),
    p(t("2021 – Present  ·  Bengaluru", "italic", color=MUTED)),
    ul(
        "Led the redesign of the checkout flow, lifting conversion by 18%.",
        "Built and maintained a design system used by 6 product teams.",
        "Ran monthly usability studies and turned findings into a prioritised backlog.",
    ),
    h(3, "Product Designer · Company Name"),
    p(t("2018 – 2021  ·  Kochi", "italic", color=MUTED)),
    ul("Designed the first version of the mobile app (4.6★ on the Play Store).", "Worked with engineers to ship weekly."),
    section("Education"),
    table(
        [
            ["Qualification", "Institution", "Year"],
            ["B.Des, Communication Design", "National Institute of Design", "2018"],
            ["Higher Secondary", "School Name, Kerala", "2014"],
        ]
    ),
    section("Certifications & awards"),
    ul("Google UX Design Certificate (2020)", "Company Design Excellence Award (2023)"),
)

ACADEMIC_CV = doc(
    h(1, "Dr. Your Name", align="center"),
    p(t("Assistant Professor, Department of Physics · University Name", color=MUTED), align="center"),
    p(t("you@university.edu  ·  +91 98765 43210  ·  ORCID 0000-0000-0000-0000", color=MUTED), align="center"),
    section("Research interests"),
    p("Condensed matter physics, thin films, renewable energy materials."),
    section("Education"),
    table(
        [
            ["Degree", "Institution", "Year"],
            ["Ph.D., Physics", "Indian Institute of Science", "2019"],
            ["M.Sc., Physics", "University of Kerala", "2013"],
            ["B.Sc., Physics", "College Name", "2011"],
        ]
    ),
    section("Academic positions"),
    ul(
        (b("Assistant Professor"), ", University Name — 2021 to present"),
        (b("Postdoctoral Fellow"), ", Institute Name — 2019 to 2021"),
    ),
    section("Publications"),
    ol(
        "Author A, Author B. “Title of the paper.” Journal Name 12, 345 (2023). doi:10.0000/xxxx",
        "Author A, Author C. “Title of the paper.” Journal Name 8, 101 (2021).",
        "Author A. “Title of the paper.” Conference Proceedings, 2020.",
    ),
    section("Grants & funding"),
    table(
        [
            ["Project", "Funding agency", "Amount", "Period"],
            ["Project title", "DST-SERB", "₹ 25,00,000", "2022–2025"],
        ]
    ),
    section("Teaching"),
    ul("Quantum Mechanics (M.Sc.) — 2021 to present", "Electronics Lab (B.Sc.) — 2021 to present"),
    section("Conferences & talks"),
    ul("Invited talk, Conference Name, City, 2024", "Poster, Conference Name, City, 2022"),
    section("References"),
    p("Available on request."),
)

COVER_LETTER = doc(
    p(b("Your Name")),
    p("Your address · City, PIN"),
    p("you@example.com · +91 98765 43210"),
    p(),
    p("Date"),
    p(),
    p(b("Hiring Manager")),
    p("Company Name"),
    p("Company address"),
    p(),
    p(b("Subject: Application for the post of [Job Title]")),
    p(),
    p("Dear Hiring Manager,"),
    p("I am writing to apply for the [Job Title] role advertised on [where you saw it]. With [number] years of "
      "experience in [field], I am confident I can help [Company Name] [one goal of the team]."),
    p("In my current role at [Company], I [your strongest achievement, with a number if you can]. I also "
      "[second achievement that matches the job description]."),
    p("I am especially drawn to [Company Name] because [something specific about the company]. I would welcome "
      "the chance to discuss how my skills fit your needs."),
    p("Thank you for your time and consideration."),
    p(),
    p("Yours sincerely,"),
    p(),
    p(b("Your Name")),
)

BUSINESS_LETTER = doc(
    h(2, t("COMPANY NAME", color=ACCENT)),
    p(t("Address line · City, State PIN · +91 00000 00000 · www.example.com", color=MUTED)),
    hr(),
    p("Ref: ABC/2026/001", align="left"),
    p("Date: ", align="left"),
    p(),
    p(b("To,")),
    p("Recipient Name"),
    p("Designation"),
    p("Company Name, Address"),
    p(),
    p(b("Subject: ")),
    p(),
    p("Dear Sir/Madam,"),
    p("Opening paragraph: state why you are writing."),
    p("Main paragraph: the details, facts or request."),
    p("Closing paragraph: what you would like to happen next and by when."),
    p(),
    p("Thanking you,"),
    p("Yours faithfully,"),
    p(),
    p(b("Name")),
    p("Designation"),
)

MEETING_NOTES = doc(
    table(
        [
            [{"text": "Date", "bold": True}, ""],
            [{"text": "Time", "bold": True}, ""],
            [{"text": "Location / link", "bold": True}, ""],
            [{"text": "Attendees", "bold": True}, ""],
        ],
        header=False,
        shade="#f3f4f6",
    ),
    h(2, "Agenda"),
    ol("Topic one", "Topic two", "Any other business"),
    h(2, "Discussion"),
    p("Key points, decisions and the reasons behind them."),
    h(2, "Decisions"),
    ul("Decision one"),
    h(2, "Action items"),
    table(
        [
            ["Action", "Owner", "Due date", "Status"],
            ["", "", "", "Open"],
            ["", "", "", "Open"],
        ]
    ),
    h(2, "Next meeting"),
    p("Date, time and topics."),
)

PROJECT_PLAN = doc(
    h(2, "Overview"),
    p("What is this project, who is it for and why now?"),
    h(2, "Goals"),
    ul("Goal one, with a measurable target", "Goal two"),
    h(2, "Scope"),
    table([["In scope", "Out of scope"], ["", ""]]),
    h(2, "Timeline"),
    table(
        [
            ["Phase", "Deliverable", "Owner", "Start", "End"],
            ["1. Discovery", "Requirements document", "", "", ""],
            ["2. Design", "Approved designs", "", "", ""],
            ["3. Build", "Working release", "", "", ""],
            ["4. Launch", "Go-live and handover", "", "", ""],
        ]
    ),
    h(2, "Risks"),
    table([["Risk", "Impact", "Mitigation"], ["", "High / Medium / Low", ""]]),
    h(2, "Checklist"),
    tasks("Kick-off meeting held", "Budget approved", "Team assigned"),
)

PROPOSAL = doc(
    p(), p(), p(),
    h(1, t("Project Proposal", color=ACCENT), align="center"),
    p(t("Prepared for Client Name", color=MUTED), align="center"),
    p(t("Prepared by Your Company · Date", color=MUTED), align="center"),
    page_break(),
    h(2, "1. Executive summary"),
    p("In one paragraph: the client's problem, your solution and the outcome they can expect."),
    h(2, "2. Understanding of the requirement"),
    p("Show that you understand the client's situation and goals."),
    h(2, "3. Proposed solution"),
    ul("Feature or service one", "Feature or service two", "Feature or service three"),
    h(2, "4. Timeline"),
    table([["Milestone", "Duration", "Deliverable"], ["Discovery", "1 week", "Requirements"], ["Build", "4 weeks", "Release"]]),
    h(2, "5. Investment"),
    table(
        [
            ["Item", "Amount (₹)"],
            ["Design", ""],
            ["Development", ""],
            [{"text": "Total (excl. GST)", "bold": True}, ""],
        ]
    ),
    h(2, "6. Why us"),
    p("Relevant experience, similar clients and what makes you the right choice."),
    h(2, "7. Next steps"),
    ol("Review and approve this proposal", "Sign the agreement", "Kick-off meeting"),
)

SIMPLE_INVOICE = doc(
    h(1, t("INVOICE", color=ACCENT)),
    table(
        [
            [{"nodes": [p(b("From")), p("Your Name / Business"), p("Address"), p("Phone · Email")]},
             {"nodes": [p(b("Bill to")), p("Client Name"), p("Address"), p("Phone · Email")]}],
        ],
        header=False,
    ),
    p(b("Invoice no: "), "INV-001     ", b("Date: "), "     ", b("Due: ")),
    table(
        [
            ["#", "Description", "Qty", "Rate (₹)", "Amount (₹)"],
            ["1", "", "", "", ""],
            ["2", "", "", "", ""],
            ["3", "", "", "", ""],
            [{"text": "Total", "bold": True, "colspan": 4}, {"text": "", "bold": True}],
        ],
        first_width=40,
    ),
    h(3, "Payment details"),
    p("Bank: · A/c no: · IFSC: · UPI: "),
    p(t("Thank you for your business!", "italic", color=MUTED)),
)

GST_INVOICE = doc(
    h(1, t("TAX INVOICE", color=ACCENT), align="center"),
    table(
        [
            [{"nodes": [p(b("Your Company Pvt Ltd")), p("Address line, City, State PIN"), p("GSTIN: 32ABCDE1234F1Z5"),
                        p("State: Kerala (32)")]},
             {"nodes": [p(b("Invoice no: "), "INV/2026/001"), p(b("Invoice date: ")), p(b("Place of supply: ")),
                        p(b("Reverse charge: "), "No")]}],
            [{"nodes": [p(b("Billed to")), p("Client Name"), p("Address"), p("GSTIN: ")]},
             {"nodes": [p(b("Shipped to")), p("Client Name"), p("Address"), p("State code: ")]}],
        ],
        header=False,
    ),
    table(
        [
            ["#", "Description", "HSN/SAC", "Qty", "Rate", "Taxable value"],
            ["1", "", "", "", "", ""],
            ["2", "", "", "", "", ""],
            [{"text": "Taxable total", "bold": True, "colspan": 5}, ""],
            [{"text": "CGST @ 9%", "colspan": 5}, ""],
            [{"text": "SGST @ 9%", "colspan": 5}, ""],
            [{"text": "Grand total (₹)", "bold": True, "colspan": 5, "bg": "#eef0fb"}, {"text": "", "bg": "#eef0fb"}],
        ],
        first_width=40,
    ),
    p(b("Amount in words: "), "Rupees … only"),
    p(t("For inter-state supplies, replace CGST and SGST with IGST @ 18%.", "italic", color=MUTED)),
    table(
        [
            [{"nodes": [p(b("Bank details")), p("Bank: "), p("A/c no: "), p("IFSC: ")]},
             {"nodes": [p(b("For Your Company Pvt Ltd")), p(), p(), p("Authorised signatory")]}],
        ],
        header=False,
    ),
)

QUOTATION = doc(
    h(1, t("QUOTATION", color=ACCENT)),
    p(b("Quotation no: "), "QT-001     ", b("Date: "), "     ", b("Valid until: ")),
    table(
        [
            [{"nodes": [p(b("From")), p("Your Company"), p("Address"), p("GSTIN: ")]},
             {"nodes": [p(b("To")), p("Client Name"), p("Address"), p("Contact person")]}],
        ],
        header=False,
    ),
    table(
        [
            ["#", "Item / service", "Qty", "Unit price (₹)", "Total (₹)"],
            ["1", "", "", "", ""],
            ["2", "", "", "", ""],
            [{"text": "Subtotal", "colspan": 4}, ""],
            [{"text": "GST @ 18%", "colspan": 4}, ""],
            [{"text": "Total", "bold": True, "colspan": 4}, ""],
        ],
        first_width=40,
    ),
    h(3, "Terms & conditions"),
    ol("50% advance, balance on delivery.", "Prices are valid until the date above.", "Delivery within __ days of confirmation."),
    p(), p(b("Authorised signatory")),
)

WEEKLY_PLANNER = doc(
    h(2, "Top 3 priorities this week"),
    tasks("Priority one", "Priority two", "Priority three"),
    h(2, "Plan"),
    table(
        [
            ["Day", "Must do", "Notes"],
            ["Monday", "", ""],
            ["Tuesday", "", ""],
            ["Wednesday", "", ""],
            ["Thursday", "", ""],
            ["Friday", "", ""],
            ["Weekend", "", ""],
        ],
        shade="#f3f4f6",
    ),
    h(2, "Habits"),
    table([["Habit", "M", "T", "W", "T", "F", "S", "S"], ["Exercise", "", "", "", "", "", "", ""], ["Reading", "", "", "", "", "", "", ""]]),
    h(2, "Reflection"),
    p("What went well? What will I change next week?"),
)

TODO_LIST = doc(
    h(2, "Today"),
    tasks("First thing to do", "Second thing to do", "Third thing to do"),
    h(2, "This week"),
    tasks("Something for this week"),
    h(2, "Later"),
    tasks("An idea for later"),
    h(2, "Done"),
    tasks(("Something already finished", True)),
)

MONTHLY_BUDGET = doc(
    p(b("Month: "), "        ", b("Opening balance: "), "₹"),
    h(2, "Income"),
    table([["Source", "Expected (₹)", "Actual (₹)"], ["Salary", "", ""], ["Other", "", ""], [{"text": "Total", "bold": True}, "", ""]]),
    h(2, "Expenses"),
    table(
        [
            ["Category", "Budget (₹)", "Spent (₹)", "Difference (₹)"],
            ["Rent / EMI", "", "", ""],
            ["Groceries", "", "", ""],
            ["Electricity, water, gas", "", "", ""],
            ["Phone & internet", "", "", ""],
            ["Transport / fuel", "", "", ""],
            ["School fees", "", "", ""],
            ["Medical", "", "", ""],
            ["Eating out & entertainment", "", "", ""],
            [{"text": "Total", "bold": True}, "", "", ""],
        ],
        shade="#f3f4f6",
    ),
    h(2, "Savings & investments"),
    table([["Where", "Amount (₹)"], ["SIP / mutual funds", ""], ["Recurring deposit", ""], ["Emergency fund", ""]]),
    h(2, "Notes"),
    p("Big expenses coming up, things to cut back on."),
)

LESSON_PLAN = doc(
    table(
        [
            [{"text": "Subject", "bold": True}, "", {"text": "Class", "bold": True}, ""],
            [{"text": "Topic", "bold": True}, "", {"text": "Duration", "bold": True}, "40 minutes"],
            [{"text": "Teacher", "bold": True}, "", {"text": "Date", "bold": True}, ""],
        ],
        header=False,
    ),
    h(2, "Learning objectives"),
    p("By the end of the lesson, students will be able to:"),
    ol("Objective one", "Objective two"),
    h(2, "Materials"),
    ul("Textbook pages", "Worksheet", "Projector / board"),
    h(2, "Lesson flow"),
    table(
        [
            ["Time", "Activity", "Teacher does", "Students do"],
            ["5 min", "Introduction", "Recap the last lesson", "Answer questions"],
            ["20 min", "Main activity", "", ""],
            ["10 min", "Practice", "", ""],
            ["5 min", "Wrap-up", "Summarise, set homework", ""],
        ]
    ),
    h(2, "Assessment"),
    p("How you'll check that students met the objectives."),
    h(2, "Homework"),
    p(""),
    h(2, "Reflection (after the lesson)"),
    p("What worked, what to change next time."),
)

STUDY_NOTES = doc(
    p(b("Subject: "), "        ", b("Chapter: "), "        ", b("Date: ")),
    h(2, "Key ideas"),
    ul("Main idea in your own words"),
    h(2, "Definitions"),
    table([["Term", "Meaning"], ["", ""], ["", ""]], shade="#f3f4f6"),
    h(2, "Notes"),
    p(""),
    h(2, "Questions to revise"),
    tasks("Question one", "Question two"),
    h(2, "Summary"),
    quote("Summarise the chapter in three sentences."),
)

# slug: (name, description, category, premium, sort_order, note title, content, page settings)
BUILTIN = {
    "simple-resume": ("Simple resume", "Clean one-page resume for any job.", "resume", False, 10, "Resume", SIMPLE_RESUME, pages(15, page_numbers=False)),
    "professional-resume": ("Professional resume", "Accent colours, skills table and education grid.", "resume", True, 11, "Resume", PROFESSIONAL_RESUME, pages(15, page_numbers=False)),
    "academic-cv": ("Academic CV", "Publications, grants and teaching for academic roles.", "resume", True, 12, "Curriculum Vitae", ACADEMIC_CV, pages(18, page_numbers=False)),
    "cover-letter": ("Cover letter", "A job application letter with prompts for each paragraph.", "letters", False, 20, "Cover letter", COVER_LETTER, pages(25, page_numbers=False)),
    "business-letter": ("Business letter", "Formal letter on a simple letterhead.", "letters", False, 21, "Letter", BUSINESS_LETTER, pages(20, page_numbers=False)),
    "meeting-notes": ("Meeting notes", "Agenda, decisions and action items.", "business", False, 30, "Meeting notes", MEETING_NOTES, pages(20, show_title=True)),
    "project-plan": ("Project plan", "Goals, scope, timeline and risks.", "business", False, 31, "Project plan", PROJECT_PLAN, pages(20, show_title=True)),
    "simple-invoice": ("Invoice", "A simple invoice for freelancers and small shops.", "business", False, 32, "Invoice", SIMPLE_INVOICE, pages(18, page_numbers=False)),
    "gst-invoice": ("GST tax invoice", "Indian tax invoice with GSTIN, HSN/SAC, CGST and SGST.", "business", True, 33, "Tax invoice", GST_INVOICE, pages(15, page_numbers=False)),
    "quotation": ("Quotation", "Price quote with GST and terms.", "business", True, 34, "Quotation", QUOTATION, pages(18, page_numbers=False)),
    "project-proposal": ("Project proposal", "Cover page, solution, timeline and pricing.", "business", True, 35, "Project proposal", PROPOSAL, pages(22)),
    "weekly-planner": ("Weekly planner", "Priorities, a day-by-day plan and a habit tracker.", "personal", False, 40, "Weekly plan", WEEKLY_PLANNER, pages(15, show_title=True, orientation="landscape")),
    "todo-list": ("To-do list", "Today, this week and later.", "personal", False, 41, "To-do", TODO_LIST, pages(20, show_title=True)),
    "monthly-budget": ("Monthly budget", "Income, expenses and savings in rupees.", "personal", True, 42, "Monthly budget", MONTHLY_BUDGET, pages(18, show_title=True)),
    "lesson-plan": ("Lesson plan", "Objectives, lesson flow and assessment for teachers.", "education", False, 50, "Lesson plan", LESSON_PLAN, pages(18, show_title=True)),
    "study-notes": ("Study notes", "Key ideas, definitions and revision questions.", "education", False, 51, "Study notes", STUDY_NOTES, pages(20, show_title=True)),
}


def sync(Template, force=False):
    """Create missing built-in templates; with force, also reset existing ones to these definitions.
    Takes the model class so data migrations can pass their historical model."""
    created = updated = 0
    for slug, (name, description, category, premium, order, note_title, content, page_settings) in BUILTIN.items():
        values = {
            "name": name, "description": description, "category": category, "premium": premium,
            "sort_order": order, "note_title": note_title, "content": content, "page_settings": page_settings,
        }
        obj = Template.objects.filter(slug=slug).first()
        if obj is None:
            obj = Template(slug=slug, **values)
            created += 1
        elif force:
            for key, value in values.items():
                setattr(obj, key, value)
            updated += 1
        else:
            continue
        if not hasattr(obj, "builtin"):
            # Historical models in migrations don't run Template.save(), so derive the preview here.
            from notes.text import extract_text, make_preview

            obj.preview = make_preview(extract_text("doc", content))
        obj.save()
    return created, updated
