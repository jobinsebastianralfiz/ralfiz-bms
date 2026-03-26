# GymPro License System

API-based licensing system for GymPro gym management deployments, built as a Django app (`gympro_licensing`).

---

## Overview

GymPro licenses are **online, API-validated** keys tied to a specific domain. Each gym deployment calls back to this server to validate its license on startup and periodically (every 4 hours). Unlike the RetailEase licensing system (which uses RSA-signed offline codes), GymPro relies on live server validation and domain binding.

**License Key Format:** `GYM-XXXX-XXXX-XXXX` (random hex segments, auto-generated on creation)

---

## Models

### GymLicense

The core license record for a gym deployment.

| Field | Type | Description |
|---|---|---|
| `gym_name` | CharField | Name of the gym |
| `gym_owner_name` | CharField | Owner's name |
| `gym_email` | EmailField | Contact email |
| `gym_phone` | CharField | Contact phone |
| `gym_address` | TextField | Physical address |
| `license_key` | CharField (unique, indexed) | Auto-generated key (`GYM-XXXX-XXXX-XXXX`) |
| `api_domain` | CharField (unique) | Bound domain (e.g., `api.fitzone.com`) |
| `landing_domain` | CharField (optional) | Frontend/landing page domain |
| `license_type` | CharField | `trial`, `monthly`, `quarterly`, `half_yearly`, `yearly`, `lifetime` |
| `status` | CharField | `active`, `expired`, `suspended`, `revoked` |
| `billing_cycle` | CharField | `monthly`, `quarterly`, `half_yearly`, `yearly`, `lifetime` |
| `valid_from` / `valid_until` | DateTimeField | License validity window |
| `grace_period_days` | IntegerField | Days after expiry before full lockout (default: 7) |
| `auto_renew` | BooleanField | Whether license auto-renews |
| `enabled_modules` | JSONField | List of enabled module keys (empty = all enabled) |
| `max_members` / `max_trainers` | IntegerField | Usage limits (0 = unlimited) |
| `server_ip` | CharField | Deployment server IP |
| `client` | ForeignKey to `core.Client` | Optional link to a client record |
| `last_check_at` / `last_check_ip` / `total_checks` | — | Tracking fields for validation calls |

**Available Modules:** `members`, `trainers`, `schedules`, `attendance`, `fees`, `store`, `salary`, `expenses`, `notifications`, `reports`

**Key Methods:**
- `is_valid()` — Returns `True` if status is active and current date is within validity window
- `is_in_grace_period()` — `True` if expired but still within grace period
- `days_remaining()` — Days until expiry (negative if overdue)
- `validate_domain(domain)` — Normalizes and checks domain match (strips protocol, trailing slashes, port numbers)
- `renew(extend_days)` — Extends `valid_until`, increments `renewal_count`
- `record_check(ip_address)` — Updates `last_check_at`, `last_check_ip`, increments `total_checks`

### GymLicenseLog

Audit trail for all license events.

| Field | Type | Description |
|---|---|---|
| `license` | ForeignKey | Link to GymLicense |
| `event` | CharField | Event type (see below) |
| `status` | CharField | License status at time of event |
| `ip_address` | CharField | Request IP |
| `domain` | CharField | Request domain |
| `details` | JSONField | Additional event data |
| `created_at` | DateTimeField | Timestamp |

**Event Types:** `validate`, `check`, `renew`, `expire`, `revoke`, `suspend`, `reactivate`, `create`, `update`, `domain_mismatch`

---

## API Endpoints

Base path: `/api/gympro/`

### Public Endpoints (No Auth)

#### POST `/api/gympro/validate/`
First-time activation and ongoing validation. Binds the license to a domain on first call.

```json
// Request
{
  "license_key": "GYM-XXXX-XXXX-XXXX",
  "domain": "api.fitzone.com"
}

// Response
{
  "valid": true,
  "license_key": "GYM-XXXX-XXXX-XXXX",
  "gym_name": "FitZone Gym",
  "license_type": "yearly",
  "status": "active",
  "valid_until": "2027-03-26T00:00:00Z",
  "days_remaining": 365,
  "in_grace_period": false,
  "enabled_modules": ["members", "trainers", ...],
  "max_members": 500,
  "max_trainers": 20
}
```

**Domain Binding:** If `api_domain` is empty on first validation, the domain from the request is bound to the license. On subsequent calls, the domain must match or the request is rejected and a `domain_mismatch` event is logged.

#### POST `/api/gympro/check/`
Periodic validation call (recommended every 4 hours).

```json
// Request
{
  "license_key": "GYM-XXXX-XXXX-XXXX",
  "domain": "api.fitzone.com"  // optional
}

// Response
{
  "valid": true,
  "status": "active",
  "days_remaining": 340,
  "in_grace_period": false,
  "valid_until": "2027-03-26T00:00:00Z",
  "renewed": false
}
```

#### GET `/api/gympro/status/?license_key=GYM-XXXX-XXXX-XXXX`
Lightweight status check.

```json
// Response
{
  "valid": true,
  "status": "active",
  "days_remaining": 340,
  "in_grace_period": false,
  "valid_until": "2027-03-26T00:00:00Z"
}
```

### Admin Endpoints (Require `GYMPRO_ADMIN_KEY`)

All admin endpoints require the `admin_key` field in the request body. The key is read from `settings.GYMPRO_ADMIN_KEY` (falls back to `settings.LICENSE_ADMIN_KEY`).

#### POST `/api/gympro/renew/`
Extend license validity after payment.

```json
{
  "license_key": "GYM-XXXX-XXXX-XXXX",
  "admin_key": "your-admin-key",
  "extend_days": 365,
  "payment_reference": "PAY-12345"
}
```

#### POST `/api/gympro/revoke/`
Permanently revoke a license.

```json
{
  "license_key": "GYM-XXXX-XXXX-XXXX",
  "admin_key": "your-admin-key",
  "reason": "Terms of service violation"
}
```

#### POST `/api/gympro/suspend/`
Temporarily suspend a license (can be reactivated).

```json
{
  "license_key": "GYM-XXXX-XXXX-XXXX",
  "admin_key": "your-admin-key",
  "reason": "Payment overdue"
}
```

#### POST `/api/gympro/reactivate/`
Reactivate a suspended or expired license (only if still within validity/grace period).

```json
{
  "license_key": "GYM-XXXX-XXXX-XXXX",
  "admin_key": "your-admin-key"
}
```

---

## Admin Interface

Accessible at `/admin/gympro_licensing/`.

### GymLicense Admin
- **List view:** Gym name, license key, domain, type, status, expiry, days remaining (color-coded), member limit, total checks, last check time
- **Search:** By gym name, email, license key, domain
- **Filters:** Status, license type, billing cycle
- **Inline:** GymLicenseLog entries (read-only audit trail)
- **Bulk actions:** Mark as expired, Mark as active, Mark as suspended
- **Auto-generated fields:** License key (on creation), validity dates (based on license type)

### GymLicenseLog Admin
- Read-only audit log viewer
- Filterable by event type and status

---

## License Lifecycle

```
[Created] → [Active] → [Expired] → [Grace Period] → [Locked Out]
              ↓   ↑          ↑
         [Suspended]    [Renewed]
              ↓
         [Revoked] (terminal)
```

1. **Created** — Admin creates license in Django admin. Key is auto-generated, `valid_until` is calculated from `license_type`.
2. **Active** — Gym deployment calls `/validate/` with the key. Domain is bound on first call. Periodic `/check/` calls every 4 hours.
3. **Expired** — `valid_until` has passed. Grace period begins (default 7 days). Gym app can still function with warnings.
4. **Grace Period End** — After grace period, license is fully invalid. Gym app should lock features.
5. **Renewed** — Admin calls `/renew/` after payment. `valid_until` is extended, status returns to active.
6. **Suspended** — Admin suspends via `/suspend/`. Can be reactivated.
7. **Revoked** — Admin revokes via `/revoke/`. Terminal state, cannot be reactivated.

---

## Domain Validation

Domains are normalized before comparison:
- Protocol stripped (`https://api.gym.com` → `api.gym.com`)
- Trailing slashes removed
- Port numbers stripped (`api.gym.com:8000` → `api.gym.com`)

This ensures flexible matching regardless of how the gym deployment reports its domain.

---

## Module Control

Licenses can restrict which GymPro modules are available. The `enabled_modules` field is a JSON list of module keys. If the list is empty, **all modules are enabled**.

Example restricted license:
```json
{
  "enabled_modules": ["members", "attendance", "fees"]
}
```

The gym deployment should call the validate endpoint and check the returned `enabled_modules` list to show/hide features.

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `GYMPRO_ADMIN_KEY` | Falls back to `LICENSE_ADMIN_KEY` | Secret key for admin API endpoints |
| `LICENSE_ADMIN_KEY` | `retailease-admin-secret` | Shared admin key (fallback) |

---

## File Structure

```
gympro_licensing/
├── __init__.py
├── apps.py
├── models.py          # GymLicense, GymLicenseLog
├── views.py           # 7 API endpoints
├── web_views.py       # HTML views (work-in-progress)
├── urls.py            # URL routing
├── admin.py           # Django admin config
└── migrations/
```
