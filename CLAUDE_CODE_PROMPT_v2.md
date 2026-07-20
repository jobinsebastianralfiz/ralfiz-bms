# Claude Code Build Prompt — Ralfiz BMS · PULSE Command Center
### (corrected for the real stack: Django 5 + DRF + SimpleJWT, server-rendered templates, SQLite dev / PostgreSQL prod)

> Paste the block below into Claude Code, running from inside `prjmanagemnt_ralfiz`.
> You already ran discovery, so this prompt encodes what you found. Run ONE phase,
> review, then say "go" for the next. Do not let it build everything at once.

---

## CONTEXT (confirmed — do not re-discover, but verify as you go)

This is **Ralfiz BMS**: Django 5.x + Django REST Framework + SimpleJWT, drf-spectacular
for docs, server-rendered **Django templates** (`templates/`, `templates/base.html`) with
**plain CSS + vanilla JS** (`static/css/styles.css`, `static/js/app.js`). Chart.js, Font
Awesome, Inter via CDN. **SQLite in dev, PostgreSQL in prod** (dj-database-url). Deployed on
Railway with gunicorn + whitenoise. Apps: `core` (projects/invoices/quotes), `crm`,
`employees`, `licensing`, `retailease`, `client_portal`, `eduflow_licensing`,
`gympro_licensing`, `interiodesk`.

I'm adding a **voice- and text-controlled command center**: one screen where I type or
speak a question and an AI supervisor routes it to read-only handlers over my real data,
plus RAG over uploaded documents. Visual style: dark, premium, a glowing central orb with
data cards (I have a separate HTML mockup to match in spirit).

### Decisions already made — implement exactly these
- Orchestration: **LangChain / LangGraph** as an intent-routing supervisor.
- **Queryable apps: `core`, `crm`, `employees` only.** Do NOT expose `licensing`,
  face-recognition, or the per-product licensing apps to the AI.
- **Embeddings: API-based** (Anthropic-compatible). Keep it behind an interface so a local
  model can be swapped in later.
- **Vector store must be swappable by database backend**: detect the DB at runtime —
  use a **numpy-based cosine-similarity store when on SQLite (dev)** and **pgvector when on
  PostgreSQL (prod)**. Same ingestion/retrieval interface for both. This is essential:
  pgvector cannot run on the SQLite dev DB.

### Hard rules (my standards — non-negotiable)
- New code lives in a NEW app called `pulse`. Additive only — do not rename, refactor, or
  alter existing models, migrations, routes, templates, or the global stylesheet.
- Reuse the EXISTING SimpleJWT auth. Do not invent new auth. Reject unauthenticated calls.
- No default Django admin for anything user-facing.
- The AI may only touch the DB through EXPLICIT, whitelisted, READ-ONLY query functions.
  Never let the model compose or execute raw SQL. No writes, no deletes.
- Every query and every document retrieval is scoped to the requesting user's permissions.
- Secrets (ANTHROPIC_API_KEY etc.) from env only, via the project's existing settings
  pattern. Never hardcoded.

---

## PHASE 0.5 — MODEL MAP (read-only; write no feature code yet)

Before building, read `core`, `crm`, and `employees` and report back:
- The concrete models + key fields I'd want queryable (projects, their status/blocked
  state, clients, invoices, quotes, CRM leads, employees/team).
- How a project's "status" or "blocked" state is actually represented (field names,
  choices) — I need to know this to write honest query functions, not invented ones.
- How to get the current user and their allowed scope inside a DRF view here.
- Confirm the DB-detection point (where settings choose SQLite vs Postgres) so the vector
  store can branch on it.
Then give me a short, revised plan for Phases 1–4. STOP and wait for "go".

---

## PHASE 1 — `pulse` APP + READ-ONLY DATA TOOLS + SUPERVISOR

- Create the `pulse` app, registered the project's normal way.
- DRF endpoint `POST /api/pulse/ask/` → `{ "query": "..." }` returns
  `{ "answer": "...", "intent": "...", "data": {...} }`. Reuse SimpleJWT auth.
- Whitelisted read-only query functions over `core`/`crm`/`employees` based on the REAL
  fields from Phase 0.5 — e.g. `get_blocked_projects(user)`, `get_project_summary(user,id)`,
  `get_team_for_project(user,id)`, `count_active_projects(user)`, `get_hot_leads(user)`.
  Each filters by the user's permissions. These are the ONLY DB access paths for the AI.
- LangGraph supervisor: classify intent → call the matching whitelisted tool → compose a
  concise natural-language answer + the structured `data`. No free-form SQL, ever.
- Tests for each query function + one end-to-end `/api/pulse/ask/` test.
- Add deps the project's normal way (requirements). STOP, demo 3 queries, wait for "go".

---

## PHASE 2 — RAG OVER DOCUMENTS (swappable vector store)

- `pulse` models `Document` + `DocumentChunk` (project FK to the real `core` project model;
  store source, chunk text, embedding). Don't touch existing models.
- A **VectorStore interface** with two implementations chosen at runtime by DB backend:
  - SQLite/dev: store embeddings as arrays, similarity via **numpy cosine** (numpy is
    already installed).
  - PostgreSQL/prod: **pgvector** (include the extension migration + a note that prod must
    enable it). Retrieval API identical to the numpy one.
- An **EmbeddingProvider interface** (API-based default) so it's swappable later.
- Ingestion command/endpoint: file or text → chunk → embed → store, scoped to a project the
  user can access.
- Retrieval tool the supervisor can call: embed query → top-k search → return chunks WITH
  citations. Scoped to docs the user may see.
- Extend `/api/pulse/ask/` so document questions route here and answers cite their source.
- Tests: ingestion, retrieval on BOTH stores (numpy + pgvector if available), and
  access-scoping (user A cannot retrieve user B's private docs). STOP, demo a cited answer.

---

## PHASE 3 — COMMAND CENTER UI (Django template + vanilla JS, text first)

- New Django template (extending `base.html`) at a new route, plus a self-contained JS file
  under `static/js/` (e.g. `pulse.js`) and scoped CSS — do NOT edit `styles.css` or `app.js`.
- Dark premium layout: central animated element (canvas orb is fine), data cards, and a
  bottom command bar (text input + Execute). On submit, call `/api/pulse/ask/` with the JWT,
  render the answer, reflect returned `data` in the cards. Clear loading/empty/error states
  in-UI (no raw tracebacks). STOP, show the text flow end-to-end, wait for "go".

---

## PHASE 4 — VOICE LAYER (Web Speech API, browser-only)

- Mic button + "space to talk" using browser SpeechRecognition (`en-IN`), typed fallback,
  and a clear "voice not supported" message where unavailable.
- Optional SpeechSynthesis read-back (toggle). Voice is INPUT only — same `/api/pulse/ask/`.
- STOP and summarize: files added/changed, how to run locally, env vars, and manual prod
  setup (enable pgvector on Railway Postgres, migrations, keys).

---

## EVERY PHASE
- Small commits, clear messages. After each phase list files added/changed and why.
- If my request conflicts with the real repo, STOP and ask — don't guess or refactor around it.
- If a choice is ambiguous, state options + your recommendation, pick a changeable default.
- Remember WeasyPrint PDF rendering is broken on this machine (missing GTK) — if any step
  touches PDFs, verify at the HTML layer, don't rely on PDF output locally.
