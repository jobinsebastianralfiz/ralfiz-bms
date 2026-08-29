# Internship Continuation Agreement — e-Sign Plan

**Goal:** HR selects current interns/employees, generates a private link per person,
sends it (WhatsApp/copy). The person opens it on their phone, reads the full
agreement, and clicks **Continue** (fills details + signs) or **Discontinue**.
HR sees every response in one dashboard.

Source document: `Ralfiz_Internship_Continuation_Agreement.pdf` (3 pages).

---

## 1. What the PDF actually contains (drives the schema)

| # | Section | Notes |
|---|---------|-------|
| — | Letterhead | RALFIZ TECHNOLOGIES, KIMS Avenue Perinthalmanna, +91 98956 63498, www.ralfiz.com |
| 1 | Internship Continuation | Continue / Discontinue choice |
| 2 | Monthly Internship Fee | **Rs.750 / month**, "Rupees Seven Hundred and Fifty only" + 6 bullets on what it covers |
| 3 | Schedule & Holidays | Sat/Sun holidays, college-declared holidays |
| 4 | Attendance & Punctuality | 4 bullets |
| 5 | Work & Learning Responsibilities | 6 bullets |
| 6 | Learning Materials | + amber callout: no redistribution |
| 7 | Professional Conduct | 5 bullets |
| 8 | Confidentiality | prose |
| 9 | Completion & Continuation | 6 bullets + company's right to discontinue |
| 10 | Confirmation | dark callout re-stating the Rs.750 commitment |
| — | **Intern Details** | Full Name, College, Course/Department, Internship Domain, Date, Signature |
| — | **Continuation Decision** | YES / NO |
| — | Signature blocks | Intern Signature + For Ralfiz Technologies |

Everything below section 10 is exactly the form we need to build. Sections 1-10 are
the read-only body.

---

## 2. Codebase facts this plan relies on

- `employees.Employee` already covers interns: `employment_type` in
  {intern, fulltime, parttime}, `role` in {employee, intern, owner, partner},
  `intern_type`, `status`, `phone`, `joining_date`, UUID pk, `user` OneToOne.
  This is the selection list. (`crm.InternProfile` is the legacy model - ignore it.)
- Public no-login page precedent exists: `certificates/verify/<uuid:verification_id>/`.
- Template-snapshot precedent exists: `CertificateTemplate` -> `Certificate` copies
  `body_text` at create time so later template edits don't rewrite issued documents.
  We copy that pattern exactly.
- HR web UI lives in `core/views.py` + `core/urls.py` (`/hr/...`) + `templates/hr/`.
- **No SMTP is configured** (`EMAIL_BACKEND`/`EMAIL_HOST` absent from settings).
  So v1 delivery = copy link + WhatsApp deep link (`wa.me/<phone>?text=...`).
  Email is a small add-on once SMTP creds exist.
- WeasyPrint can't render locally (missing GTK); verify the signed-copy PDF at the
  HTML layer, confirm the real PDF on Railway.
- Django `{# #}` comments are single-line only.
- Whitenoise serves unhashed statics -> bump `?v=N` on any new/edited CSS.

---

## 3. Data model (new file `employees/agreement_models.py`, imported into `employees/models.py`)

### `AgreementTemplate`
Editable master copy so the wording/fee can change without a deploy.

| field | type |
|---|---|
| `id` | UUID pk |
| `name` | CharField ("Internship Continuation & Learning Agreement") |
| `version` | CharField ("v1.0") |
| `agreement_type` | choices: `internship_continuation` (room to grow) |
| `intro_html` | TextField (the "Dear Intern..." block) |
| `sections` | JSONField: `[{no, title, body, bullets[], callout{style,text}}]` |
| `monthly_fee` | Decimal (750.00) |
| `fee_in_words` | CharField |
| `confirmation_html` | TextField (section 10 dark callout) |
| `require_college_fields` | Bool (interns yes / staff no) |
| `is_active`, `created_at`, `updated_at` | |

Seeded by a management command `seed_internship_agreement` transcribing the PDF verbatim.

### `AgreementRequest` — one row per person per send
| field | type | notes |
|---|---|---|
| `id` | UUID pk | |
| `token` | CharField(64, unique, db_index) | `secrets.token_urlsafe(32)` - the URL secret |
| `employee` | FK -> `employees.Employee` (PROTECT) | who it's for |
| `template` | FK -> AgreementTemplate (SET_NULL) | provenance only |
| **snapshot** | `snapshot_json`, `snapshot_fee`, `snapshot_version` | frozen at send; the page always renders the snapshot, never the live template |
| `status` | pending / viewed / accepted / declined / cancelled / expired | |
| `sent_by`, `sent_at`, `expires_at` | default +14 days | |
| `first_viewed_at`, `view_count` | | |
| **response** | `decision` (continue/discontinue), `responded_at` | |
| | `full_name`, `college_name`, `course_department`, `internship_domain` | prefilled from Employee, editable by signer |
| | `signature_image` (ImageField `agreements/signatures/`) | drawn on canvas, saved PNG |
| | `signed_date` (Date), `agreed_to_terms` (Bool), `decline_reason` (Text, blank) | |
| **evidence** | `ip_address`, `user_agent`, `submitted_hash` | tamper-evident audit trail |
| `hr_notes` | Text | |

Properties: `is_open`, `is_expired`, `public_url`, `whatsapp_url`, `status_badge`.

One migration in `employees/` (next number after 0023).

---

## 4. URLs

**Public (no login, no sidebar):** registered in `config/urls.py` as `path('agreement/', include('employees.agreement_urls'))`

- `GET  /agreement/<token>/` - read + sign page (marks `viewed`)
- `POST /agreement/<token>/` - submit decision
- `GET  /agreement/<token>/done/` - receipt (also what a re-visit after signing shows)

**HR (login_required, in `core/urls.py` + `core/views.py`):**

- `/hr/agreements/` - dashboard: filter by status/type, counters (Pending / Continuing / Discontinued / Expired)
- `/hr/agreements/send/` - **the selection screen**: checkbox list of active
  employees (default filter `employment_type=intern`, `status=active`), select-all,
  choose template + expiry -> creates one link per person
- `/hr/agreements/sent/<batch>/` - result table: name, phone, link + **Copy** button + **WhatsApp** button
- `/hr/agreements/<uuid:pk>/` - detail: full signed record, signature image, IP/time audit
- `/hr/agreements/<uuid:pk>/resend/` , `/cancel/`
- `/hr/agreements/<uuid:pk>/pdf/` - signed copy (WeasyPrint, mirrors `certificate_pdf`)
- `/hr/agreement-templates/` + `/create/` + `/<pk>/` - edit wording/fee

Also: a "Continuation" status chip on `hr/employee_detail.html` and a column on `hr/employee_list.html`.

---

## 5. The public signing page (`templates/agreements/sign.html`)

Standalone template - **does not extend `base.html`** (no sidebar/navbar), light
document styling that mirrors the PDF: dark letterhead bar, blue section numbers,
bullet lists, amber + dark callouts. Mobile-first, since it arrives over WhatsApp.

Flow:
1. Header: "Hi &lt;Name&gt;" + employee ID + a "please read fully" line.
2. Full agreement body rendered from `snapshot_json` (sections 1-10), fee shown in
   a highlighted card exactly like the PDF.
3. **Read gate:** the decision buttons stay disabled until the reader scrolls past
   the last section AND ticks "I have read and understood the terms above."
   (IntersectionObserver on a sentinel div - no library.)
4. Two large buttons: **Continue my internship** / **Discontinue**.
   - *Continue* -> reveals the Intern Details form: Full Name (prefilled), College,
     Course/Department, Internship Domain, Date (today, read-only), **signature pad**
     (HTML canvas, touch + mouse, Clear button, saved as PNG data-URL), and the
     Rs.750 confirmation checkbox. Submit -> `accepted`.
   - *Discontinue* -> confirm dialog + optional reason -> `declined`.
5. Receipt page: decision, timestamp, reference number, "Download your copy" (PDF).

Edge states, all with a friendly branded page: invalid token (404 page, no hint),
expired, cancelled, already responded (read-only receipt), employee inactive.

---

## 6. Rules & safeguards

- Token is 43-char URL-safe random - unguessable, no enumeration.
- Decision is **one-time**. Changing it needs HR to `resend` (which creates a *new*
  request row and marks the old one superseded) - so the audit trail is never overwritten.
- Snapshot means an HR edit to the template never silently changes what someone
  already signed.
- Every view logs `view_count`/`first_viewed_at`; every submit stores IP + user agent
  + a SHA-256 of the rendered body -> proof of *what* they agreed to.
- Expiry default 14 days, configurable per send.
- CSRF on the POST (standard Django); simple per-token submit throttle.
- Nothing sensitive on the page beyond the person's own name/employee ID.

---

## 7. Build order

1. Models + migration + `seed_internship_agreement` command (PDF text verbatim). *(~1)*
2. Public sign view + template + signature pad + read gate + all edge states. *(~2)*
3. HR select-and-send screen + WhatsApp/copy links. *(~3)*
4. HR dashboard + detail + resend/cancel + employee-page status chip. *(~4)*
5. Signed-copy PDF (HTML verified locally, PDF confirmed on Railway). *(~5)*
6. Template editor screens. *(~6)*
7. Tests: token access, read-gate bypass attempt, one-time submit, decline path,
   expired/cancelled tokens, snapshot immutability, HR filters, WhatsApp URL build. *(~7)*
8. Deploy: migration on Railway, `?v=N` bump, smoke-test one real link end to end.

---

## 8. Decisions (settled 2026-08-29)

1. **Who gets it** - **interns + all employees.** The send screen defaults its filter
   to active interns but any active person can be selected. College / Course /
   Internship Domain fields are shown only when the recipient is an intern
   (`require_college_fields` on the template, overridden per-request by
   `employee.employment_type`); for staff the block collapses to Full Name + Date.
2. **Signature** - **both.** Typed full name is required (that is the legal
   signature); a drawn canvas signature is offered above it and is optional, so a
   phone where the canvas misbehaves can never block a submission. Store the typed
   name in `signed_name` and the drawing in `signature_image` (nullable).
3. **Delivery** - **WhatsApp + copy link only.** No SMTP work in this pass. Each row
   in the send-result table gets a Copy button and a WhatsApp button
   (`wa.me/<phone>?text=<prefilled message + link>`). Rows with no phone on file show
   Copy only, plus a warning.
4. **Content** - **transcribed into an editable `AgreementTemplate`,** seeded verbatim
   from the PDF by `seed_internship_agreement`. Fee and wording editable from an HR
   screen with no deploy; every sent request still snapshots the text it showed.

---

## 9. Deliberately out of scope (say if you want them)

- Collecting the Rs.750 payment / linking accepted agreements to invoices or dues.
- Countersignature by Ralfiz (the "For Ralfiz Technologies" block) - v1 records the
  intern's side; add an HR countersign button later if you want it on the PDF.
- Reminder nudges for unopened links.
- Flutter app consumption of these endpoints.
