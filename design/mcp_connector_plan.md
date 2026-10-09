# Ralfiz BMS — Claude connector plan

Drafted 2026-10-07, revised the same day: the connector does **not** build on
PULSE (too limited). It covers the whole backend.

Goal: add "Ralfiz BMS" as a custom connector on claude.ai, log in once with the
BMS owner account, then read and change BMS data from Claude web, desktop,
mobile (text, and voice if the app allows) and Claude Code. Same experience as
the Gmail connector.

## Status

**Phase 1 built 2026-10-07** (not yet committed/deployed): `connector/` app, 46 tools,
MCP endpoint at `/mcp`, OAuth via django-oauth-toolkit 3.4 (its built-in RFC 8414/9728
metadata, DCR and RFC 8707 resource support). 44 connector tests; full suite 645 green.
Verified against a copy of the dev DB (every read tool, no secrets leaked), with the
official MCP Inspector client, and the consent page in a browser. Fixed on the way:
`AdminWorkAssignView` returned 500 whenever a due date was given.

## The key decision: wrap the existing owner API, not the database

The Flutter owner app already talks to ~120 DRF endpoints under
`/api/employees/` (`owner/…`, `admin/…`, `crm/…`, `certificates/…`). They hold
all the business rules we've already paid for: `IsOwnerOrPartner`, GST-only
`Invoice.objects`, leave approval notifications, lead status history, payment
→ invoice status updates, etc.

Each connector tool calls one of those views **in-process**: build a DRF
request with `APIRequestFactory`, `force_authenticate(request, user)` as the
OAuth user, call the view, return its JSON. No HTTP hop, no duplicated logic,
and every permission check runs exactly as it does for the Flutter app. When a
view changes, the connector changes with it.

PULSE is untouched. Its `/api/pulse/ask/` keeps serving the in-app command
centre.

## Architecture

```
claude.ai (web / desktop / mobile)  ──┐
Claude Code (synced connector)      ──┤ HTTPS JSON-RPC (MCP streamable HTTP, stateless)
                                      ▼
POST /mcp/                         new `connector` Django app
  Bearer <OAuth token> → user        django-oauth-toolkit
  tools/list  → tool catalogue       connector/tools/*.py (one module per area)
  tools/call  → in-process call      APIRequestFactory → existing owner/admin/crm view
                                      ▼
                         existing DRF views + serializers + models
```

### Transport: a plain Django view

The official `mcp` Python SDK is ASGI; prod is gunicorn WSGI. Stateless MCP is
"POST a JSON-RPC message, get JSON back", so one Django view handles it and
we keep a single Railway service.

| JSON-RPC method | Response |
|---|---|
| `initialize` | protocol version, `capabilities: {tools: {}}`, `serverInfo: {name: "Ralfiz BMS"}`, `instructions` (amounts are INR, Indian digit grouping; look up names with `search` before asking for an ID; leads have integer IDs, everything else UUIDs) |
| `notifications/initialized` | 202, no body |
| `ping` | `{}` |
| `tools/list` | the catalogue below, each with `inputSchema` + `annotations` (`readOnlyHint` / `destructiveHint`) |
| `tools/call` | `content: [{type: "text", text: <json>}]` + `structuredContent`; DRF 400/403/404 → `isError: true` with the serializer's error message so Claude can fix its arguments |
| other | JSON-RPC `-32601` |

No token → 401 with
`WWW-Authenticate: Bearer resource_metadata="https://ralfizdigital.in/.well-known/oauth-protected-resource"`
(this is how claude.ai knows to open the login window).

## Auth (what makes it feel like Gmail)

django-oauth-toolkit as the authorization server.

```
GET  /.well-known/oauth-protected-resource       RFC 9728
GET  /.well-known/oauth-authorization-server     RFC 8414
POST /oauth/register/                             RFC 7591 dynamic client registration (small custom view)
GET  /oauth/authorize/   POST /oauth/token/       DOT, auth code + PKCE S256, public clients
```

- Login = existing Django login page, then a consent page in the Ralfiz theme:
  "Allow Claude to read and update Ralfiz BMS?"
- Only users passing `IsOwnerOrPartner` (or `is_staff`) can approve.
- Registration only accepts redirect URIs on `claude.ai`, `claude.com` and
  `localhost` (Claude Code / MCP Inspector).
- Scopes: `bms:read`, `bms:write`. Write tools check `bms:write`.
- Access token 1 h, refresh 30 days; "Connected apps" list on the owner
  settings page to revoke.

Audit: every `tools/call` → `ConnectorCallLog` row (user, tool, args, status,
ms). Admin list view. Writes also land in the existing `ActivityLog` because
the wrapped views already log.

## Tool catalogue

Names are what Claude sees. Each row = one existing endpoint.

### Phase 1 — read everything + everyday writes

**Find & overview**
| Tool | Endpoint |
|---|---|
| `search` (name → clients, projects, leads, employees, invoices, quotes with IDs) | new, small — the only tool with its own query |
| `get_dashboard` | `owner/dashboard/` |
| `get_financial_report` (period) | `owner/financial-report/` |
| `get_dues` | `owner/dues/` |

**Clients & projects**
| `list_clients` / `get_client` | `owner/clients/`, `owner/clients/<id>/` |
| `list_projects` (status filter) / `get_project` | `owner/projects/`, `owner/projects/<id>/` |
| `get_project_board` | `owner/project-board/` |
| `update_project_status` ✏️ | `owner/projects/<id>/status/` |

**Money (read)**
| `list_invoices` / `get_invoice` | `owner/invoices/…` |
| `list_quotes` / `get_quote` | `owner/quotes/…` |
| `list_expenses` | `owner/expenses/` |
| `list_bank_accounts` / `list_transfers` | `owner/accounts/`, `owner/transfers/` |
| `list_amc_contracts` / `get_amc_contract` | `owner/amc/…` |
| `list_expiring_renewals` | `owner/credentials/expiring/` — **dates and names only**, secrets stripped |

**CRM**
| `get_crm_dashboard` | `crm/dashboard/` |
| `list_leads` / `get_lead` / `get_lead_timeline` | `crm/leads/…` |
| `list_upcoming_followups` | `crm/follow-ups/upcoming/` |
| `list_demos` | `crm/demos/` |
| `create_lead` ✏️ (runs `check-duplicate` first) | `crm/leads/` POST |
| `update_lead_status` ✏️ | `crm/leads/<id>/status/` |
| `add_lead_note` ✏️ | `crm/leads/<id>/notes/` |
| `schedule_followup` ✏️ / `complete_followup` ✏️ | `crm/leads/<id>/follow-ups/`, `crm/follow-ups/<id>/` |

**People**
| `list_employees` / `get_employee` | `owner/employees/…` |
| `get_attendance` (date) / `get_attendance_report` (range) | `owner/attendance/`, `admin/attendance/report/` |
| `list_leave_requests` | `admin/leaves/` |
| `review_leave_request` ✏️ (approve/reject + note) | `admin/leaves/<id>/review/` |
| `list_work_assignments` / `assign_work` ✏️ | `admin/work/…` |
| `list_daily_tasks` / `add_daily_task` ✏️ | `owner/daily-tasks/` |
| `list_daily_reports` / `list_missing_daily_reports` | `admin/daily-reports/…` |
| `send_notification` ✏️ (push to staff) | `admin/notifications/send/` |

✏️ = write tool: `readOnlyHint: false`, so Claude shows a confirm-before-running
prompt. ~45 tools.

### Phase 2 — money writes

**Built 2026-10-09.** All tools below, plus `create_client` / `create_project`.
Inputs are checked before the view runs (client/project exist and match, invoice
is in the GST series, payment not above balance unless `allow_overpayment`).
PDF links: `connector/files.py`, signed with Django signing, 1 hour, re-checks
owner access on download. Fixed on the way: the app's payment route crashed on
its `pk` kwarg; invoice/payment/expense create passed `None` to non-null dates;
line items and invoice totals broke on string/float numbers. Academy and
licence read tools not done.

| `create_quote` ✏️ / `update_quote` ✏️ | `owner/quotes/create/`, `…/edit/` |
| `create_invoice` ✏️ | `owner/invoices/create/` (GST series only) |
| `record_payment` ✏️ | `owner/invoices/<id>/payments/` |
| `add_expense` ✏️ | `owner/expenses/create/` |
| `record_amc_payment` ✏️ | `owner/amc/<id>/record-payment/` |
| `create_client` ✏️ / `create_project` ✏️ | `owner/clients/create/`, `owner/projects/create/` |
| `get_invoice_pdf` / `get_quote_pdf` | returns a short-lived signed download link, not the bytes |

Plus read tools for Academy (students, enrolments, progress) and the product
licences (RalfPOS / GymPro / EduFlow / RetailEase lookups).

### Never exposed

Deletes of any kind, `all_objects` / no-GST ledger, renumbering, credential
passwords and secrets, payroll, user/role changes, licence signing keys.

## Build steps (Phase 1)

1. `pip install django-oauth-toolkit`; settings + migrate.
2. `connector/` app: `mcp.py` (JSON-RPC view), `oauth.py` (metadata, DCR,
   consent template), `registry.py` (tool spec: name, description, pydantic
   args, view + method + path builder, read/write), `tools/{overview,projects,money,crm,people}.py`,
   `models.py` (`ConnectorCallLog`).
3. `dispatch(user, view, method, kwargs, data)` helper: `APIRequestFactory` →
   `force_authenticate` → call → unwrap `Response`; follows the view's
   pagination by passing `page`/`page_size` through as tool args.
4. Tool descriptions written for Claude ("Call when…"), each tested once by
   hand in the MCP Inspector for a natural question.
5. Tests:
   - initialize / tools/list / tools/call with a DOT token
   - 401 + header without token; intern token refused at consent and at call
   - `bms:read` token can't call a ✏️ tool
   - DCR rejects a foreign redirect URI
   - every registry entry resolves to a real URL name (catches drift when
     `employees/urls.py` changes)
   - credential tool output contains no secret fields
   - one round-trip per area against fixtures (lead create → note → follow-up;
     leave approve; assign work)
6. Local: MCP Inspector + `claude mcp add --transport http ralfiz-dev http://localhost:8000/mcp/`.
7. Deploy to Railway; claude.ai → Settings → Connectors → Add custom connector
   → `https://ralfizdigital.in/mcp/` → log in.
8. Verify on prod: web chat, Claude Code (`mcp__claude_ai_Ralfiz_BMS__…`), and
   the phone app — including one question in voice mode.

Estimate: Phase 1 ≈ 3 days (OAuth ½–1 day, transport ½ day, 45 tools + tests
1½ days). Phase 2 ≈ 1–1½ days.

## Risks / open questions

- **Voice mode + connectors on the phone** — unverified; checked in step 8.
- **Paid Claude plan** needed for custom connectors.
- **Data goes to Anthropic** as conversation content (client names, amounts) —
  fine for owner use; decide before ever giving staff access.
- **Response size** — list endpoints are paginated at 20; tools pass
  `page`/filters rather than dumping everything.
- **Views that read `request.FILES` or return PDFs** — not wrapped directly;
  PDFs via signed links (Phase 2), uploads not supported.
- **MCP spec drift** — confirm protocol version and Claude's OAuth callback
  URLs at build time; keep both as constants.
