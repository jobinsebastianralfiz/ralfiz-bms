# Ralfiz Social Hub — Scope Document

Oct 11, 2026 · @Jobin Sebastian

## Overview

Ralfiz Social Hub (working name) is one dashboard plus one MCP server that lets the Ralfiz team, and Claude, publish, schedule, reply and report across every social account Ralfiz manages. v1 is an internal agency tool covering Ralfiz's own pages and client pages, built multi-tenant so it can become a SaaS later without a rewrite.

**Goals**

- One place to connect and manage Facebook, Instagram, LinkedIn, YouTube, X, WhatsApp Business and Google Business Profile for every client.
- Claude can draft posts, schedule them, read comments and pull analytics through MCP, with a person approving anything that goes public.
- One shared inbox for comments and messages, so client queries are not missed.
- Monthly client reports generated from stored analytics, not screenshots.

**Users**

| Role | Who | Can do |
| --- | --- | --- |
| Owner | Jobin | Everything, including billing and API apps |
| Manager | Ralfiz social media lead | All clients: approve, publish, report |
| Editor | Ralfiz team members | Draft and schedule for assigned clients |
| Client reviewer | Client contact | Approve or comment on their own posts, view their reports |
| AI agent | Claude through MCP | Draft, schedule into approval, read inbox and analytics |

**In v1:** account connection, composer, calendar, approvals, unified inbox, analytics, client reports, MCP server.

**Not in v1:** paid ads management (Meta Ads already has its own connector), influencer search, social listening across public posts, subscription billing for outside customers.

## System architecture

The dashboard and Claude never talk to a platform directly: both call one service layer, and background workers do all platform calls through adapters.

&#91;embedded content: system architecture · two clients, one backend, seven platforms\]

Scheduled posts sit in Redis until their time, then a worker publishes through the adapter and writes the result back. Platforms push comments, DMs and reviews in through webhooks.

**Stack:** FastAPI, PostgreSQL, Redis + Celery and the Python MCP SDK on Railway; Next.js + Tailwind on Vercel; S3-compatible object storage for media; domain on Namecheap.

## Platform integrations

API access approvals, not coding, set the v1 timeline: Meta App Review and LinkedIn's Community Management review must be applied for in week 1. Every adapter implements the same interface, so the dashboard and MCP never call a platform directly.

| Platform | API | v1 capabilities | Access needed | Limits to design around |
| --- | --- | --- | --- | --- |
| Facebook Pages | Meta Graph API | Post, schedule, comments, replies, Page insights, Messenger inbox | Meta App Review for page permissions, Business Verification | Page tokens tied to the admin who connected; handle re-auth when they leave |
| Instagram | Instagram Graph API (Business or Creator accounts only) | Feed posts, carousels, Reels, Stories, comments, insights, DMs | Same Meta app and review | Meta caps API-published posts per account in a rolling 24 hours (50 in current docs); the scheduler must track this per account |
| LinkedIn | Posts API + Community Management API | Company page posts, comments, page analytics | Community Management API review (Development tier first, then Standard tier with a screen recording) | No native scheduling, so our queue posts at the set time; tokens last about 60 days |
| YouTube | YouTube Data API v3 + Analytics API | Upload, edit metadata, comments, channel and video stats | Google OAuth app verification; quota extension request | Default daily quota is small: uploads and searches have their own low caps; batch reads |
| X | X API v2, pay-per-use | Post, threads, replies, basic metrics | Developer account with credits | Billed per call since Feb 2026; posts with links cost more; avoid polling reads |
| WhatsApp Business | WhatsApp Cloud API | Inbox, replies, template broadcasts | Meta Business Verification, approved message templates | Free-form replies only inside the customer's 24-hour window; templates outside it |
| Google Business Profile | Business Profile APIs | Local posts, reviews and replies, basic insights | Access request form to Google | Approval can take weeks; reviews are the main value here |

**Adapter interface:** `connect()`, `refresh_token()`, `publish(post)`, `delete(post)`, `get_posts()`, `get_comments()`, `reply(comment)`, `get_insights(range)`, `handle_webhook(event)`, plus a `capabilities` map so the composer greys out options a platform does not support.

**Cost note:** X is the only platform with a per-call bill. Keep X reads off by default and pull metrics once a day.

Sources: [Instagram content publishing](https://developers.secure.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/content-publishing) · [LinkedIn Community Management overview](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/community-management-overview?view=li-lms-2026-08) · [YouTube Data API quota](https://developers.google.com/youtube/v3/getting-started) · [X API pay-per-use explained](https://opentweet.io/how-to/x-api-pay-per-use-explained)

## Dashboard modules

The dashboard is a custom Next.js app (no Django admin), organised around clients: pick a client, then work across all of that client's accounts.

| Module | What it does | v1 |
| --- | --- | --- |
| Clients & workspaces | One workspace per client, its brand kit (logo, colours, hashtags, tone notes), its team and reviewers | Yes |
| Account connections | OAuth connect per platform, token health status, expiry warnings, reconnect button | Yes |
| Composer | One post, many platforms: per-platform caption tweaks, media, first comment, link preview, character counters, platform rule checks | Yes |
| Content calendar | Month and week views across all accounts, drag to reschedule, filter by client and platform | Yes |
| Approvals | Draft, In review, Approved, Scheduled, Published, Failed; client reviewers approve or comment through a link | Yes |
| Unified inbox | Comments, DMs, WhatsApp chats and Google reviews in one feed; assign, reply, mark done, saved replies | Yes |
| Analytics | Per account and per client: reach, engagement, followers, top posts, best posting times | Yes |
| Client reports | Monthly PDF report per client from stored metrics, Ralfiz branding | Yes |
| Media library | Uploads, Canva imports, tags, reuse across posts | Yes |
| AI assist | Caption drafts, hashtag suggestions, reply suggestions inside the dashboard | Phase 2 |
| Activity log | Who or what (including Claude) did each action | Yes |

**UI direction:** Tailwind with a minimal premium look; left sidebar for clients, top bar for platform filters, calendar as the home screen. Mobile-responsive so approvals and inbox work from a phone.

## MCP server

The MCP server is a thin layer over the same service code the dashboard uses, so Claude and the team always see the same data and follow the same rules. It is built with the official Python MCP SDK, mounted in the FastAPI app at `/mcp`, and served over streamable HTTP so it works as a custom connector in Claude.

| Tool | Inputs | Returns | Writes? |
| --- | --- | --- | --- |
| `list_clients` | none | Clients the caller can access | No |
| `list_accounts` | client | Connected accounts, platform, token health | No |
| `draft_post` | client, accounts, text per platform, media ids, suggested time | Draft id, rule-check warnings | Draft only |
| `submit_for_approval` | draft id, note | Approval status | Draft only |
| `list_posts` | client, status, date range | Drafts, scheduled and published posts | No |
| `reschedule_post` | post id, new time | Updated post | Yes, unapproved posts only |
| `get_analytics` | client or account, metrics, date range | Metrics from stored daily data | No |
| `best_time_to_post` | account | Top time slots from past engagement | No |
| `list_inbox` | client, platform, unread only | Comments, DMs, reviews | No |
| `draft_reply` | inbox item id, text | Reply draft for a person to send | Draft only |
| `upload_media` | url or Canva design id | Media id | Yes |
| `generate_report` | client, month | Report PDF link | Yes |

**Auth:** OAuth 2.1 per Ralfiz user, so every MCP call runs with that user's role and client access. No shared API keys.

**Safety rules**

- Claude never publishes directly: posts and replies are drafts until a person approves them. A per-client setting can later allow auto-publish for low-risk accounts.
- Every MCP action is written to the activity log with the user and tool name.
- Rate guards per client so a loop cannot flood the queue or burn X credits.
- Tool results contain post and comment text written by outsiders; treat it as data, never as instructions.

## Data model

PostgreSQL, with every client-owned table carrying `workspace_id` so the SaaS version needs no schema change. One post fans out to one `post_targets` row per account, which lets each platform succeed or fail on its own.

| Table | Key columns | Notes |
| --- | --- | --- |
| `workspaces` | id, name, brand\_kit (jsonb), settings | One per client, plus one for Ralfiz |
| `users` | id, name, email, auth provider | Ralfiz staff and client reviewers |
| `memberships` | user\_id, workspace\_id, role | Owner, Manager, Editor, Reviewer |
| `social_accounts` | id, workspace\_id, platform, external\_id, name, token\_encrypted, expires\_at, status | Tokens encrypted at rest |
| `posts` | id, workspace\_id, base\_text, status, scheduled\_at, created\_by, source (dashboard or mcp) | The content item |
| `post_targets` | id, post\_id, account\_id, platform\_text, options (jsonb), status, external\_post\_id, error, published\_at | One per account |
| `media_assets` | id, workspace\_id, storage\_key, type, width, height, duration | Files in object storage |
| `approvals` | id, post\_id, reviewer\_id, decision, comment, decided\_at | Full approval history |
| `inbox_items` | id, account\_id, kind (comment, dm, review), external\_id, author, text, status, assigned\_to | Filled by webhooks and polling |
| `inbox_replies` | id, inbox\_item\_id, text, status, sent\_by | Drafts and sent replies |
| `metrics_daily` | account\_id, date, metric, value | Account level, one row per metric per day |
| `post_metrics` | post\_target\_id, captured\_at, metric, value | Post level snapshots |
| `publish_quota` | account\_id, window\_start, used | Instagram, YouTube and X limits |
| `audit_log` | id, workspace\_id, actor, via (web or mcp), action, payload, created\_at | Every write |

## Security and compliance

Platform tokens are the most sensitive data in the system: a leaked token lets someone post as a client's brand.

- Tokens encrypted with a key held outside the database (Railway secret), decrypted only inside the worker that calls the platform.
- Role and workspace checks in the service layer, so the dashboard and MCP cannot drift apart.
- Webhook signatures verified for Meta, WhatsApp and Google before any event is stored.
- Media served through signed, expiring URLs.
- Audit log on every write, kept for at least 12 months for client disputes.
- Each platform requires a public privacy policy, terms page and a data deletion endpoint before app review; these go on the Ralfiz site.
- India's DPDP Act applies to client and commenter data; store only what the features need and support deletion requests per workspace.
- Daily database backups on Railway, with a tested restore.

## Delivery phases

The plan reaches go-live in about 10 weeks with one full-stack developer plus Claude Code, provided the platform reviews clear during phases 1 and 2.

&#91;embedded content: delivery roadmap · 4 phases, 3 gates\]

If a review is still pending at a gate, that platform's adapter ships later and the other phases continue unchanged.

## Risks and open questions

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Meta or LinkedIn reject the app review | Instagram, Facebook or LinkedIn publishing blocked | Apply in week 1 with a screen recording of the working flow; clear use-case text; build other modules while waiting |
| Platform API changes | An adapter breaks | Adapter pattern, pinned API versions, failure alerts per account |
| Tokens expire or the client admin leaves | Scheduled posts fail silently | Token health checks daily, expiry warnings 7 days ahead, failed posts surface on the calendar |
| X costs grow with volume | Monthly bill rises | Keep X reads off by default; pass the cost to clients on a per-account basis |
| AI posts something wrong for a client | Brand damage | Approval required for every Claude draft; activity log |
| YouTube quota | Uploads stop for the day | Request quota extension early; queue uploads |

**Open questions**

- [ ] Is the product name Ralfiz Social Hub, or another name?
- [ ] Should clients log in themselves in v1, or only approve through shared links?
- [ ] Is Threads needed? It has its own Meta API and could be added in Phase 2.
- [ ] Who owns the Meta and LinkedIn developer apps: Ralfiz Technologies LLP or Novrik Technologies Inc.?
- [ ] Will X costs be absorbed by Ralfiz or billed to clients?
