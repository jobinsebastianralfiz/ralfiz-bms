# Ralfiz Academy Labs: integration guide for Ralfiz Digital

This guide explains how to add **Ralfiz Academy Labs** (certification courses with in-depth lessons, hands-on labs, exercise files, quizzes and practice tests) to the Ralfiz Digital platform. Developers can follow it directly, or you can hand it to Claude Code as the build spec.

- **Content version:** September 2026
- **Source package:** `ralfiz-academy-labs-package.zip`

---

## 1. What you are integrating

| Track | Exam | Level | Lessons | Quiz questions | Extra question bank | Status (Sep 2026) |
|---|---|---|---|---|---|---|
| `pl900` | PL-900 Power Platform Fundamentals | Fundamentals | 28 | 60 | – | Live |
| `ab410` | AB-410 Intelligent Applications Builder | Associate | 17 | 68 | – | Live, replaced PL-200 |
| `pl300` | PL-300 Power BI Data Analyst | Associate | 15 | 60 | 40 | Live |
| `ab400` | AB-400 Power Platform Developer | Associate | 16 | 64 | – | Exam opens 16 Oct 2026, replaces PL-400 |

**Totals:** 76 lessons, 292 questions, 158 exercise files, 7 in-browser simulator types.

**Suggested path:** PL-900 first. After that, AB-410 (building apps) or PL-300 (analysing data). AB-400 (developer) comes after AB-410.

Every lesson has four parts:

1. **Learn:** a short summary plus in-depth HTML content (about 700 to 1,300 words) with tables, worked examples, common mistakes and "how the exam asks about it".
2. **Hands-on lab:** exercise files, numbered steps and a "check your work" list.
3. **Quiz:** 2 to 4 multiple-choice questions, each with an explanation.
4. **Simulator (optional):** an in-browser widget on 11 lessons.

---

## 2. Package contents

```
ralfiz-academy-labs-package.zip
├── ralfiz-academy-labs.html        # complete working site in one file (reference implementation)
├── README.md
├── RALFIZ-DIGITAL-INTEGRATION.md   # this file
├── content/
│   ├── pl900.json                  # one file per track
│   ├── ab410.json
│   ├── pl300.json
│   ├── ab400.json
│   └── files-index.json            # every exercise file id → path + description
└── exercise-files/
    ├── shared-data/
    │   ├── hd/                     # Campus Help Desk data (PL-900, AB-410, AB-400)
    │   │   ├── tickets.csv         # 28 tickets CHD-1001..CHD-1028
    │   │   ├── categories.csv      # 6 categories
    │   │   ├── students.csv        # 20 students
    │   │   ├── staff.csv           # 6 staff
    │   │   └── feedback.csv        # 12 feedback rows
    │   └── pbi/                    # Power BI data (PL-300)
    │       ├── tickets.csv         # 60 tickets Jan–Jun 2026, messy on purpose
    │       └── categories.csv      # 4 categories
    ├── pl900/<lessonId>/...        # lesson files + LAB.md
    ├── ab410/<lessonId>/...
    ├── pl300/<lessonId>/...
    └── ab400/<lessonId>/...        # includes start/ and solution/ code folders
```

---

## 3. Two ways to integrate

### Option A: quick embed (same day)

Host `ralfiz-academy-labs.html` as a static page, for example `https://<ralfiz-digital-domain>/labs/`.

- **Next.js:** put it at `public/labs/index.html` and link to `/labs/`. On Vercel it is served as-is.
- **Django:** serve it as a static file, or with a `TemplateView` that returns the file unchanged. Don't run it through the template engine, because it contains `{{` characters inside code samples.
- **Deep links:** routes use the URL hash. For example `/labs/#t-ab410` opens a track page, `/labs/#v9` opens lesson D.9 and `/labs/#test-pl300` opens the PL-300 practice test.
- **External resources:** the page needs internet access for Google Fonts and JSZip (`cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js`). If your Content Security Policy is strict, allow `fonts.googleapis.com`, `fonts.gstatic.com` and `cdnjs.cloudflare.com`.
- **Downloads:** they use normal browser downloads. Single files and "Download all (.zip)" both work.

**Limitations of Option A:** progress lives in the browser's localStorage under the key `pl900lab.v1`, so there are no student accounts, no cross-device progress, no trainer reports, and no paywall or enrolment control.

### Option B: native integration (recommended)

Import the JSON into your database and render it in your own UI. You get:

- student accounts and saved progress
- trainer dashboards
- enrolment and batches
- certificates of completion
- content you can edit in your own admin

The rest of this guide covers Option B.

---

## 4. Recommended architecture (Option B)

| Layer | Choice |
|---|---|
| Frontend | Next.js (App Router) + Tailwind CSS, deployed on Vercel or Railway |
| Backend API | Django REST Framework or FastAPI |
| Database | PostgreSQL |
| File storage | Object storage (S3-compatible, e.g. Cloudflare R2 or AWS S3) for exercise files; serve through signed URLs |
| Admin | Custom admin dashboard in Next.js (not the Django default admin) |
| Auth | Your existing Ralfiz Digital auth (JWT/session) |
| Deploy | Railway (API + Postgres), Vercel (Next.js); domain on Namecheap |

```
Next.js (student UI + custom admin)
        │  REST (JWT)
        ▼
Django/FastAPI API ── PostgreSQL (content, progress, attempts)
        │
        └── Object storage (exercise files, signed URLs)
```

---

## 5. Content JSON format

### 5.1 Track file (`content/<trackId>.json`)

```jsonc
{
  "id": "ab410",
  "code": "AB-410",
  "name": "Intelligent Applications Builder",
  "level": "Associate",
  "status": "Live · replaces PL-200",
  "outline": "26 Apr 2026",            // date of the Microsoft outline the content follows
  "order": "After PL-900",
  "blurb": "…",
  "facts": [["700", "score out of 1000 to pass"], …],   // 4 headline facts
  "tool": "your developer environment",                   // where students do the labs
  "guide": "https://learn.microsoft.com/…",               // official study guide
  "note": "…",                                            // footer disclaimer
  "data": ["hd/tickets.csv", …],                          // course-wide datasets (file ids)
  "questionBank": [                                        // extra practice questions (PL-300 only for now)
    { "question": "…", "options": ["…","…","…","…"], "answer": 1, "explanation": "…", "lesson": "b7" }
  ],
  "domains": [
    {
      "id": "q1",
      "name": "Foundation for intelligent apps",
      "weight": "25–30%",                                  // "%" = exam weight; otherwise "Setup"/"Orientation"
      "blurb": "…",
      "lessons": [ /* Lesson objects, in order */ ]
    }
  ]
}
```

### 5.2 Lesson object

```jsonc
{
  "id": "a6",                    // unique across ALL tracks
  "num": "A.6",                  // display number
  "title": "Prompt columns and row summaries",
  "minutes": 50,
  "summaryHtml": "<p>…</p>",     // "At a glance" box
  "contentHtml": "<h3>In plain words</h3>…",  // in-depth lesson
  "terms": [{ "term": "…", "definition": "…" }],
  "examTip": "…",
  "widget": null,                // null | "powerfx" | "flow" | "dataset" | "star" | "dax1" | "dax2" | "sorter"
  "sorter": null,                // present when widget = "sorter" (see 5.4)
  "lab": {
    "files": ["hd/tickets.csv", "ab410/a6/prompt-column-spec.md"],   // file ids (see 5.3)
    "steps": ["Download the exercise files for this lab.", "…"],
    "check": ["The Summary column shows one sentence for each of the 28 tickets.", "…"]
  },
  "quiz": [
    { "question": "…", "options": ["A","B","C","D"], "answer": 2, "explanation": "…" }   // answer = 0-based index
  ]
}
```

### 5.3 File ids and storage paths

- Ids starting with `hd/` or `pbi/` are shared datasets. On disk they live at `exercise-files/shared-data/<id>`.
- All other ids look like `<track>/<lessonId>/<path>`, for example `ab400/v9/start/SetPriorityFromKeywords.cs`. On disk they live at `exercise-files/<id>`.
- `files-index.json` maps each id to `{ path, description }`. `path` is the name used inside a lab's zip. **Use the id as your storage key, never `path`.** The two `tickets.csv` files (`hd/` and `pbi/`) share the same `path` value but never appear in the same lab.
- File types: md 71, txt 29, csv 13, json 12, cs 10, and a few each of ts, tsx, js, yml, xml, csproj, py and css. All are text files, 1.4 MB in total.

### 5.4 Sorter object (widget = `"sorter"`)

```jsonc
{
  "title": "Where should this logic live?",
  "intro": "One sentence.",
  "options": ["Business rule", "Formula column", "…"],
  "items": [ { "t": "Scenario text", "a": 0, "w": "Why this is the best answer." } ]
}
```

Render each item with a dropdown of `options`. On **Check**, compare the chosen index with `a` and show `w`.

### 5.5 Lesson HTML

`summaryHtml` and `contentHtml` use only these elements:

- `h3`, `p`, `ul`, `ol`, `li`, `strong`, `em`, `code`
- `pre class="code"`
- `table`, `thead`, `tbody`, `tr`, `th`, `td`
- `div class="example"`, `div class="callout"`, `div class="callout warn"`

The content was written by us, but sanitise it on render anyway (for example with DOMPurify or `sanitize-html`), using that allow-list.

Suggested styling (Tailwind):

| Element | Style |
|---|---|
| `.example` | tinted panel for worked examples |
| `.callout` | accent left border |
| `.callout.warn` | red left border |
| `pre.code` | monospace, horizontal scroll |
| tables | wrap in an `overflow-x-auto` container |

Build the "On this page" menu from the `h3` headings.

---

## 6. Database schema (PostgreSQL)

Django-style models are shown below. The same tables work with SQLAlchemy.

```python
class Track(models.Model):
    id = models.CharField(primary_key=True, max_length=20)      # "pl900"
    code = models.CharField(max_length=20)                       # "PL-900"
    name = models.CharField(max_length=200)
    level = models.CharField(max_length=50)
    status = models.CharField(max_length=200)
    outline_date = models.CharField(max_length=50)
    order_hint = models.CharField(max_length=100)
    blurb = models.TextField()
    facts = models.JSONField(default=list)
    tool = models.CharField(max_length=200)
    guide_url = models.URLField()
    note = models.TextField()
    data_file_ids = models.JSONField(default=list)
    sort_order = models.PositiveSmallIntegerField(default=0)
    is_published = models.BooleanField(default=True)
    content_version = models.CharField(max_length=20)           # e.g. "2026-09"

class Domain(models.Model):
    id = models.CharField(primary_key=True, max_length=20)      # "q1"
    track = models.ForeignKey(Track, on_delete=models.CASCADE, related_name="domains")
    name = models.CharField(max_length=200)
    weight = models.CharField(max_length=50)
    blurb = models.TextField()
    sort_order = models.PositiveSmallIntegerField()

class Lesson(models.Model):
    id = models.CharField(primary_key=True, max_length=20)      # "a6"
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, related_name="lessons")
    num = models.CharField(max_length=20)
    title = models.CharField(max_length=300)
    minutes = models.PositiveSmallIntegerField()
    summary_html = models.TextField()
    content_html = models.TextField()
    terms = models.JSONField(default=list)
    exam_tip = models.TextField(blank=True)
    widget = models.CharField(max_length=20, blank=True)
    sorter = models.JSONField(null=True, blank=True)
    lab_steps = models.JSONField(default=list)
    lab_check = models.JSONField(default=list)
    sort_order = models.PositiveSmallIntegerField()

class ExerciseFile(models.Model):
    id = models.CharField(primary_key=True, max_length=300)     # "ab400/v9/start/SetPriorityFromKeywords.cs"
    zip_path = models.CharField(max_length=300)
    description = models.TextField()
    storage_key = models.CharField(max_length=400)              # object-storage key
    size_bytes = models.PositiveIntegerField()
    sha256 = models.CharField(max_length=64)

class LessonFile(models.Model):                                 # ordered many-to-many
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="lesson_files")
    file = models.ForeignKey(ExerciseFile, on_delete=models.PROTECT)
    sort_order = models.PositiveSmallIntegerField()

class Question(models.Model):
    track = models.ForeignKey(Track, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, null=True, on_delete=models.SET_NULL)
    source = models.CharField(max_length=10)                    # "lesson" | "bank"
    sort_order = models.PositiveSmallIntegerField(default=0)    # position inside the lesson quiz
    question = models.TextField()
    options = models.JSONField()                                # 4 strings
    answer = models.PositiveSmallIntegerField()                 # 0-based
    explanation = models.TextField()

# ---- learner data ----
class LabProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    ticked_steps = models.JSONField(default=list)               # e.g. [0,1,3]
    updated_at = models.DateTimeField(auto_now=True)
    class Meta: unique_together = ("user", "lesson")

class QuizAnswer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    last_choice = models.PositiveSmallIntegerField()
    ever_correct = models.BooleanField(default=False)
    attempts = models.PositiveIntegerField(default=0)
    class Meta: unique_together = ("user", "question")

class TestAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    track = models.ForeignKey(Track, on_delete=models.CASCADE)
    question_ids = models.JSONField()                           # frozen order
    answers = models.JSONField(default=dict)                    # {index: choice}
    score = models.PositiveSmallIntegerField(null=True)         # 0–1000
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True)

class Enrollment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    track = models.ForeignKey(Track, on_delete=models.CASCADE)
    batch = models.CharField(max_length=100, blank=True)
    enrolled_at = models.DateTimeField(auto_now_add=True)
```

---

## 7. Import script

Write this as an idempotent management command, `python manage.py import_labs <package_dir>`. It should:

1. Read `content/files-index.json`. For each id, read the file from disk (see 5.3 for paths), upload it to object storage under `labs/<content_version>/<id>`, and upsert `ExerciseFile` with its size and sha256. Skip the upload when the sha256 is unchanged.
2. For each `content/<track>.json`, upsert `Track`, then each `Domain` and `Lesson` with `sort_order` taken from array position.
3. Replace the lesson's `LessonFile` rows from `lab.files`, keeping their order.
4. Upsert `Question` rows:
   - lesson quizzes use `source="lesson"`, with `sort_order` set to the question's position in the quiz;
   - `questionBank` items use `source="bank"`, with `lesson` taken from the item's `lesson` field.
   - Match existing questions on (track, lesson, question text) so learners' answers survive re-imports.
5. Validate as you go:
   - every file id in `lab.files` exists;
   - `answer` is between 0 and 3;
   - every `sorter` item's `a` is less than the number of options;
   - lesson ids are unique.
   Fail the import if any check fails.
6. Print a summary. For this package the expected counts are: 4 tracks, 20 domains, 76 lessons, 158 files, 292 questions.

---

## 8. API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/labs/tracks/` | Catalogue: tracks with lesson counts and the user's progress |
| GET | `/api/labs/tracks/{trackId}/` | Track page: domains, lessons (no HTML body), per-lesson status |
| GET | `/api/labs/lessons/{lessonId}/` | Full lesson: HTML, terms, tip, widget, sorter, lab, quiz **without `answer`** |
| POST | `/api/labs/lessons/{lessonId}/lab/` | `{ticked_steps: [..]}`: save lab ticks |
| POST | `/api/labs/questions/{id}/answer/` | `{choice}` → `{correct, answer, explanation}` (grade on the server) |
| GET | `/api/labs/files/{fileId}/` | Returns a short-lived signed URL (check enrolment) |
| GET | `/api/labs/lessons/{lessonId}/zip/` | Streams a zip: the lesson's files + a generated `LAB.md` |
| POST | `/api/labs/tracks/{trackId}/tests/` | `{size: 30 or 50}` → new `TestAttempt` with questions (no answers) |
| PATCH | `/api/labs/tests/{attemptId}/` | Save answers while the student works |
| POST | `/api/labs/tests/{attemptId}/submit/` | Grade on the server → score, per-question result, explanation, source lesson |
| GET | `/api/labs/admin/reports/?track=&batch=` | Trainer view: progress per student and lesson, test scores |

Never send `answer` to the browser before the student answers. The single-file HTML includes answers because it has no server; your platform shouldn't.

---

## 9. Business rules

These match the reference HTML, so behaviour stays the same.

- **Lab complete:** every step index is ticked.
- **Quiz complete:** every question in the lesson has `ever_correct = true`. Wrong answers can be retried, and the explanation shows after each answer.
- **Lesson status:**
  - `done` when the lab and the quiz are both complete;
  - `in_progress` when any step is ticked or any question has been answered;
  - otherwise `not_started`.
- **Track progress:** done lessons ÷ total lessons.
- **Practice test:**
  - Question pool = the track's lesson questions plus its bank questions.
  - Draw a random sample of 30 (or 50 when the pool has at least 50), with no repeats within an attempt.
  - Score = round(correct ÷ total × 1000). Pass line is **700**.
  - After submission, show each question's explanation and a link to its source lesson.
  - Label the score as a guide. It is not Microsoft's scaled score.
- **Certificate of completion (optional):** issue it when every lesson in a track is done and the student has at least one practice test ≥ 700. Name it as a Ralfiz Academy course completion, never as a Microsoft certification.

---

## 10. Frontend pages (Next.js)

| Route | Content |
|---|---|
| `/labs` | Catalogue: hero, suggested path (PL-900 → AB-410 / PL-300 → AB-400), track cards with progress |
| `/labs/[track]` | Track home: facts, skill areas with exam weights, "Continue" button, course datasets |
| `/labs/[track]/[lesson]` | Lesson with tabs **Learn · Hands-on lab · Quiz**, prev/next, sidebar of the track's lessons with status dots |
| `/labs/[track]/test` | Practice test (30 or 50 questions), results review |
| `/admin/labs/...` | Custom admin: tracks, lessons (HTML editor), questions, files, re-import, batch reports |

**Lesson tabs:**

- **Learn:** the summary box, then an "On this page" chip list built from the `h3` headings, the content HTML, key terms, the exam tip and a "Start the hands-on lab" button.
- **Hands-on lab:** the simulator (if any), then the exercise-files panel. Each file row shows a type badge, the path, the description and the size, with **View**, **Copy** and **Download** buttons. The panel also has **Download all (.zip)**. Below it come the numbered steps with checkboxes and the green "Check your work" list.
- **Quiz:** one card per question. After an answer, show correct or wrong, the explanation, and "Try again".

**Track colours** (used in the reference build):

| Track | Light | Dark |
|---|---|---|
| PL-900 | `#0B7A6E` | `#3CC4B2` |
| AB-410 | `#6A4BC4` | `#A993F0` |
| PL-300 | `#B08500` | `#EBC14A` |
| AB-400 | `#2D5FBF` | `#7FA6F2` |

Fonts: Bricolage Grotesque (headings), IBM Plex Sans (body), IBM Plex Mono (code and numbers).

---

## 11. Porting the simulators

The simulators are plain JavaScript inside `ralfiz-academy-labs.html`. Port each one to a React client component (`"use client"`). They need no backend.

| `widget` | Lessons | Source in the HTML | What it does |
|---|---|---|---|
| `powerfx` | PL-900 2.4 | `mountFx`, `runFx`, `TICKETS`, `FX_TASKS` | Power Fx console: tokenizer, parser and evaluator over a 6-row sample table; 7 challenges |
| `flow` | PL-900 4.3 | `mountFlow`, `TRIGGERS`, `ACTIONS`, `SCENARIOS` | Flow builder: pick a trigger and ordered actions for 3 scenarios |
| `dataset` | PL-300 B.1 | `BI.mountDataset` | Copy panel for `tickets.csv` and `categories.csv` |
| `star` | PL-300 B.6 | `BI.mountStar` | Star schema builder: fact/dimension, cardinality, direction, active |
| `dax1`, `dax2` | PL-300 B.7, B.8 | `BI.mountDax`, `BI.run`, `DAX_SETS` | DAX engine with filter context, Campus/Category slicers; 7 + 8 challenges; answers are verified in every slicer context |
| `sorter` | AB-410 A.13, A.17; AB-400 D.2, D.6, D.9 | `mountSorter` + lesson `sorter` data | Scenario → best option drill |

Porting approach:

1. Move the engine functions (`tokenize`, `parse`, `ev`, `run`) into `lib/labs/powerfx.ts` and `lib/labs/dax.ts` unchanged, then add types.
2. Rebuild the UI in React with the same states:
   - challenge chips, showing ✓ when solved;
   - input, then Run;
   - a result card (success or error);
   - Hint and Show answer buttons.
3. Save solved challenges per user through a small endpoint (`POST /api/labs/widgets/{lessonId}/`), or keep them in localStorage, since they aren't graded.
4. Test the engines with the reference answers:
   - Power Fx: 6, 3, 2, 13, "Urgent", "WI-FI DOWN IN LIBRARY", "Open".
   - DAX with no slicers: `COUNTROWS(Tickets)` = 60, `CALCULATE(COUNTROWS(Tickets), Tickets[Priority] = "High")` = 15, `DISTINCTCOUNT(Tickets[AssignedTo])` = 4.

---

## 12. Exercise files: delivery rules

- Store the files privately. Only enrolled users get signed URLs, with a short lifetime (for example 10 minutes).
- Per-lesson zip layout:
  - the files, using each file's `zip_path` (for example `start/SetPriorityFromKeywords.cs`, `data/tickets.csv`);
  - `LAB.md`, containing the title, numbered steps and a checklist from `lab_check`.
- Offer a zip of the whole track's course datasets on the track page.
- Serve every file as a download (`Content-Disposition: attachment`). Never execute or render uploaded code.

---

## 13. Custom admin dashboard

- **Tracks:** publish or unpublish, reorder, edit metadata and facts.
- **Lessons:** edit title, minutes, summary, content HTML (rich editor with an HTML view, using the same allow-list), terms, tip, steps and checks; attach or detach files.
- **Questions:** list and filter by track, lesson and source; edit; add new bank questions; flag questions reported by students.
- **Files:** upload a new version (keep the id, bump the sha), preview text files.
- **Import:** upload a new package zip, run a dry run showing added, changed and removed counts, then apply.
- **Reports:** per batch, a students × lessons matrix (status), average quiz accuracy per lesson, practice test history, and CSV export.

---

## 14. Keeping content current

- Microsoft updates exam outlines several times a year. The content follows these outline dates:
  - PL-900: 24 Jul 2026
  - PL-300: 20 Apr 2026
  - AB-410: 26 Apr 2026
  - AB-400: outline effective 16 Oct 2026
- Show each track's `outline` date and `guide` link on the track page.
- **Known items to review before launch:**
  - AB-400 code samples use placeholder values for choice columns (e.g. `100000002`) and a placeholder code-app service name. Students replace them with their own values; the lessons say so.
  - Some AB-400 topics are in preview at Microsoft and are labelled as preview in the lessons: Dataverse MCP server, Work IQ, background operations and some code-app tooling.
  - The AB-410 free practice assessment from Microsoft wasn't available yet when the content was written.
  - An independent accuracy review of the AB-410 and AB-400 lessons is recommended before launch.
  - PL-900, AB-410 and AB-400 need more bank questions (target 150+ per track) so practice tests don't repeat too often.

---

## 15. Acceptance checklist

- [ ] The import reports 4 tracks, 20 domains, 76 lessons, 158 files, 292 questions, with no validation errors.
- [ ] The catalogue shows 4 track cards in path order, with progress for a logged-in student.
- [ ] Every lesson renders its Learn content; the "On this page" chips scroll to each `h3`.
- [ ] Every lab lists its files. View, Copy, single Download and zip download all work, and the zip contains `LAB.md`.
- [ ] Ticking steps and answering quizzes persists across devices for the same user.
- [ ] Quiz answers are graded on the server; `answer` never appears in lesson API responses.
- [ ] The practice test gives 30 random questions (50 when the pool has at least 50), the score is 0–1000, and the pass mark is 700.
- [ ] All 7 simulator types work, and the Power Fx and DAX reference answers in section 11 match.
- [ ] Pages work at 400 px width with no sideways scrolling; tables and code scroll inside their own box.
- [ ] Light and dark themes both read well.
- [ ] Trainer reports show per-batch progress and export to CSV.

---

## 16. Prompt for Claude Code

Copy this prompt into Claude Code in the Ralfiz Digital repository, with the package unzipped at `./labs-package`:

> Integrate Ralfiz Academy Labs into this project following `labs-package/RALFIZ-DIGITAL-INTEGRATION.md`. Use our existing auth, Next.js App Router frontend with Tailwind, and the Django (or FastAPI) + PostgreSQL backend. Build, in order:
> 1. the models from section 6 and migrations;
> 2. the idempotent `import_labs` command from section 7, uploading files to our object storage;
> 3. the API from section 8, with server-side grading;
> 4. the student pages from section 10;
> 5. the simulators from section 11 as client components, porting the engines from `labs-package/ralfiz-academy-labs.html` unchanged;
> 6. the custom admin from section 13.
>
> Don't use the Django default admin. Run the import and the acceptance checklist in section 15, and report any failures.
