# Web Portal for Interns & Employees — Plan

_Drafted 2026-06-09. Status: **awaiting two decisions** (see end) before build._

## Goal (plain language)

Today, **interns and employees** use the **phone app** (Flutter) to mark attendance,
apply for leave, see salary slips, etc. **Owners/admins** use the existing **website**.

**Problem:** staff without a compatible phone can't use the phone app, so they can't do
any of this.

**Ask:** a **website version of the phone app, just for interns and employees**, so they
can open any browser (Chrome on any Android phone, a laptop, an old phone) and do the same
things — no special phone required. The owners'/admins' existing website is unchanged and
out of scope.

## Who it's for and what they get

**All staff (employees + interns):**
- Attendance (check-in / check-out, history)
- Leave (request, cancel, see balance)
- Work assignments + status updates
- Payslips
- Profile / change password
- Notifications, ID card

**Interns get the above plus:**
- Classes (schedule + materials)
- Assessments (scores + download test paper / answer key — feature shipped 2026-06-09)
- CRM leads (marketing interns only)

Login is **role-aware**: an employee lands on the employee portal, an intern also sees the
intern tiles, an owner/admin still goes to the existing admin website. One login system.

## Why this is feasible now

- The backend is **already API-complete** for everything interns/employees do.
- Interns and employees **already have `User` accounts** (`Employee.user` one-to-one).
- Face-match for attendance is done **server-side** (`employees/utils.compare_faces`), so a
  browser selfie can be verified the same way the app is.
- The web app already has session login, a base layout, deploy pipeline, and media storage.

So we are **only adding a browser front-end** for staff — no new business logic.

## Approach options

| Option | What it is | Effort | Verdict |
|---|---|---|---|
| **A. Django staff portal (server-rendered)** | New mobile-friendly templates + views inside the existing web app (e.g. `/portal/…`), session login, reusing the same models the mobile API uses. | Low–Med | **Recommended** |
| **B. Flutter Web** | Compile the existing phone app to web. | Med | Fast to "all screens," but heavy bundle and on-device face attendance breaks on web (needs rework anyway). |
| **C. Separate JS SPA (React/Vue)** | New JS app on the JWT API. | High | New stack to maintain for no real gain. |

**Recommendation: Option A** — works on any browser, one repo, one deploy, no new toolchain.

## Feature parity on web

Easy (plain pages/forms, reuse existing logic): Leave, Work assignments, Classes,
Assessments, Payslips, Profile, Notifications, ID card, CRM leads.

**The one tricky feature is Attendance** (phone uses on-device face + GPS + QR). On web:
- **GPS** → browser Geolocation API → same check-in endpoint.
- **QR** → JS camera scanner (e.g. html5-qrcode) or type the daily code; backend already validates.
- **Face** → browser camera selfie → existing server-side `compare_faces`. Optional for v1.

## Suggested phases

1. **Phase 1** — Login routing + role-aware dashboard, Profile, Payslips, Classes, Assessments (read-heavy, zero risk).
2. **Phase 2** — Leave (request/cancel) + Work assignments (status updates).
3. **Phase 3** — Attendance (start with QR + GPS; add browser-camera face after).
4. **Phase 4** — CRM leads for marketing interns (largest; can defer).

## Where it lives

New views + responsive templates in `core`/`employees` (e.g. `templates/portal/…`), sharing
existing CSS. The mobile API and Flutter app stay untouched and keep working.

## Open decisions (needed before build)

1. **Approach** — confirm **Option A (Django staff portal)**, or specifically want Flutter Web?
2. **Web attendance** — pick one:
   - (a) **Easiest:** QR + GPS only for now (no face)
   - (b) **Full parity:** browser-camera selfie verified by `compare_faces` from day one
   - (c) **Skip attendance** on web for now (everything else only)

Once these are answered, turn this into a concrete build plan (routes, templates, phase-1 scope) and start.
