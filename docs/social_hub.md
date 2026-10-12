# Social Hub: going live

The hub lives at `/social/` (app `social/`). Pages: calendar, approvals, inbox, analytics, reports, media, accounts, activity, clients. Clients approve by a private link at `/social/review/<token>/`. Claude reaches the hub through the existing connector at `/mcp`, using 12 `*_social_*` tools. Claude can draft and submit; a person approves, schedules and sends.

Locally, with no platform keys set, every platform uses a fake adapter (`SOCIAL_FAKE_ADAPTERS=auto` + `DEBUG`). Connecting makes a demo account and publishing returns a made-up id, so the whole flow can be tried without keys.

## 1. Railway variables

| Variable | Needed for | Notes |
| --- | --- | --- |
| `SOCIAL_TOKEN_KEY` | everything | Fernet key; production refuses to start the hub without it. `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`. Never change it: old tokens become unreadable and accounts show "Reconnect needed". |
| `SOCIAL_PUBLIC_BASE_URL` | everything | `https://ralfizdigital.in`. OAuth redirect URIs and the signed media URLs that Meta and Google fetch are built from it. |
| `META_APP_ID`, `META_APP_SECRET` | Facebook, Instagram, webhook | One Meta app. |
| `META_WEBHOOK_VERIFY_TOKEN` | Meta webhook | Any random string; paste the same one into the Meta app. |
| `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET` | YouTube, Business Profile | One Google Cloud OAuth client. |
| `LINKEDIN_CLIENT_ID`, `LINKEDIN_CLIENT_SECRET` | LinkedIn | `LINKEDIN_API_VERSION` defaults to 202609; LinkedIn retires versions after about a year. |
| `X_CLIENT_ID`, `X_CLIENT_SECRET` | X | OAuth 2.0 confidential client. `SOCIAL_X_READS=True` turns on billed reads (mentions, metrics). |
| — | WhatsApp | No variables: connect per client with phone number id, WABA id and a permanent System User token. |

## 2. Worker service

Publishing runs in a separate process. In Railway, add a second service from this repo with the start command:

```
python manage.py social_worker
```

It publishes due posts every minute, syncs inboxes every 10 minutes, and syncs metrics and checks tokens every 6 hours. Without it, scheduled posts never go out.

## 3. Redirect URIs to register

- Meta: `https://ralfizdigital.in/social/oauth/callback/facebook/` and `.../instagram/`
- Google: `.../social/oauth/callback/youtube/` and `.../google_business/`
- LinkedIn: `.../social/oauth/callback/linkedin/`
- X: `.../social/oauth/callback/x/`
- Meta webhook callback: `https://ralfizdigital.in/social/webhooks/meta/` (subscribe Page `feed` + `messages`, Instagram `comments` + `messages`, WhatsApp `messages`)

## 4. Platform approvals (apply in week 1, they gate the timeline)

- **Meta App Review + Business Verification** for the page, Instagram and messaging permissions. The adapters list the exact scopes.
- **LinkedIn Community Management API** (Development tier, then Standard tier with a screen recording).
- **Google:** OAuth verification; a YouTube quota extension (about 6 uploads a day at the default); a Business Profile API access request (a new project starts at 0 quota). Until the YouTube app is audited, uploads are forced to private.
- **X:** developer account with credits.
- Each needs a public privacy policy, terms page and data-deletion URL.

## 5. Unverified against live APIs

Every adapter is tested against mocked HTTP only. Check these on the first real account:

- **Instagram:** the 24-hour publish cap. It is set to 50; the docs say both 50 and 100.
- **Facebook:** whether `caption` on photo posts shows up.
- **LinkedIn:** the `organizationAcls` field name; the follower-statistics shape; whether a video posted right after upload is accepted.
- **X:** the OAuth details, written from memory.
- **Google Business Profile:** review and local-post field names, and the performance API value shape.
