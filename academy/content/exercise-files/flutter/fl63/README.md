# Lesson 12.4 - Edge Functions and going to production

Start from your lesson 12.3 TaskFlow project.

## 1. Supabase CLI and the function
Install the Supabase CLI (see the Supabase docs for your OS), then in the
Flutter project root:

    supabase login
    supabase init
    supabase link --project-ref YOUR_DEV_REF
    supabase functions new project-report

Replace supabase/functions/project-report/index.ts with the file from this
folder. Optional Slack setup: create an Incoming Webhook in a Slack test
workspace and store its URL as a secret (skip this and the report still
works, with posted: false):

    supabase secrets set SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
    supabase functions deploy project-report

## 2. Flutter
Copy start/lib/project_report_card.dart to lib/. In your tasks page, add an
app bar action that opens it for the current project:

    IconButton(
      icon: const Icon(Icons.insights),
      onPressed: () => showModalBottomSheet<void>(
        context: context,
        builder: (context) => ProjectReportCard(projectId: _projectId!),
      ),
    ),

Finish:
- TODO(1) call functions.invoke('project-report', body: {'projectId': ...}).
- TODO(2) read total, done and posted with a map pattern into _report.
- TODO(3) catch FunctionException: 401 -> "Please sign in again.",
  anything else -> "Report failed (<status>)."

## 3. Environments
Create a second Supabase project for prod. Make env/prod.json next to
env/dev.json, each with APP_ENV, SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY.
Turn the SQL from lessons 12.2 and 12.3 into migrations:

    supabase migration new taskflow_schema     # paste the SQL into the new file
    supabase db push                           # dev (linked)
    supabase link --project-ref YOUR_PROD_REF
    supabase db push                           # prod
    supabase functions deploy project-report   # prod

Build prod with:

    flutter build appbundle --release --dart-define-from-file=env/prod.json --obfuscate --split-debug-info=build/symbols

## 4. Production checklist
Tick each item in your own notes and fix anything that fails:
- Only URL + publishable key in the app; no secret or service_role key anywhere in lib/.
- RLS enabled with policies on projects, tasks and storage.objects; Security Advisor clean.
- Private bucket for task files; signed URLs only.
- Email confirmation on, prod redirect URLs set, custom SMTP configured.
- Every function checks the caller; secrets set separately in dev and prod.
- Schema in prod came only from migrations.
- Backup terms of your plan read; restore practised in dev.

## Acceptance criteria
- Tapping "Send report" shows a progress bar, then Total, Done and Open numbers.
- With the Slack secret set, the Slack channel receives the summary and the
  card shows "Posted to Slack"; without it the card shows "Slack not configured".
- Calling the function with curl and no Authorization header returns 401.
- When the function answers 401 (for example, the session was revoked and
  could not be refreshed), the card shows "Please sign in again."
- Searching lib/ for "service_role" or "hooks.slack.com" finds nothing.
