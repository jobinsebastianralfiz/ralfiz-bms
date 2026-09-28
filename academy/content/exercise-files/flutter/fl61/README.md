# Lesson 12.2 - TaskFlow on Supabase with Row Level Security

You will replace TaskFlow's REST task repository with a SupabaseTaskRepository
and protect the data with Row Level Security (RLS).

Files:
- lib/main.dart - app, sign-in page and paged task screen (finished, shared)
- start/lib/data/supabase_task_repository.dart - domain types + repository with TODOs
- solution/lib/data/supabase_task_repository.dart - finished repository

In the full TaskFlow app, Task and TaskRepository live in the domain layer and
the repository in the data layer (lesson 9.6). Here they share one file so
the exercise stays small.

## 1. Database (Supabase SQL editor)
Run this whole block once:

    create table if not exists public.projects (
      id uuid primary key default gen_random_uuid(),
      owner_id uuid not null default auth.uid() references auth.users (id) on delete cascade,
      name text not null check (char_length(name) between 1 and 80),
      created_at timestamptz not null default now()
    );
    create table if not exists public.tasks (
      id uuid primary key default gen_random_uuid(),
      project_id uuid not null references public.projects (id) on delete cascade,
      user_id uuid not null default auth.uid() references auth.users (id) on delete cascade,
      title text not null check (char_length(title) between 1 and 200),
      done boolean not null default false,
      created_at timestamptz not null default now()
    );
    create index if not exists projects_owner_idx on public.projects (owner_id);
    create index if not exists tasks_user_idx on public.tasks (user_id);
    create index if not exists tasks_project_created_idx on public.tasks (project_id, created_at desc);

    alter table public.projects enable row level security;
    alter table public.tasks enable row level security;

    create policy "Read own projects" on public.projects
      for select to authenticated using ((select auth.uid()) = owner_id);
    create policy "Create own projects" on public.projects
      for insert to authenticated with check ((select auth.uid()) = owner_id);
    create policy "Update own projects" on public.projects
      for update to authenticated
      using ((select auth.uid()) = owner_id) with check ((select auth.uid()) = owner_id);
    create policy "Delete own projects" on public.projects
      for delete to authenticated using ((select auth.uid()) = owner_id);

    create policy "Read own tasks" on public.tasks
      for select to authenticated using ((select auth.uid()) = user_id);
    create policy "Create own tasks in own projects" on public.tasks
      for insert to authenticated
      with check (
        (select auth.uid()) = user_id
        and exists (select 1 from public.projects p
                    where p.id = project_id and p.owner_id = (select auth.uid()))
      );
    create policy "Update own tasks" on public.tasks
      for update to authenticated
      using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
    create policy "Delete own tasks" on public.tasks
      for delete to authenticated using ((select auth.uid()) = user_id);

## 2. Flutter project
    flutter pub add supabase_flutter

Create env/dev.json (keep env/ out of git as a habit; these values are public):

    {
      "SUPABASE_URL": "https://YOUR-PROJECT.supabase.co",
      "SUPABASE_PUBLISHABLE_KEY": "YOUR-PUBLISHABLE-OR-ANON-KEY"
    }

Older projects call this key the "anon" key. Both names mean the public
client key. NEVER put the service_role or secret key in the app.
For quick testing you may turn off "Confirm email" in the Auth settings.

Copy lib/main.dart to lib/main.dart and start/lib/data/... to lib/data/..., then:

    flutter run --dart-define-from-file=env/dev.json

## 3. Your tasks
- TODO(1) _fromRow and _guard: map rows to Task; PostgrestException code
  42501 becomes NotAllowed, anything else ServerFailure(e.message).
- TODO(2) inboxProjectId and fetchPage: find or create the "Inbox" project;
  load pages with eq + order(created_at, descending) + range.
- TODO(3) add, setDone, delete: insert and return the new row; update and
  delete add .select('id') and throw NotAllowed when nothing came back.
Never filter by user id in Dart. RLS does that.

## 4. Test the policies in SQL
Copy a user id from Authentication > Users, then run:

    begin;
    set local role authenticated;
    select set_config('request.jwt.claims',
      '{"sub":"PUT-USER-UUID-HERE","role":"authenticated"}', true);
    select count(*) from public.tasks;   -- only that user's rows
    rollback;

## Acceptance criteria
- A new account sees an Inbox with the text "No tasks yet".
- With 25 tasks, a fresh start shows 20 and "Load more"; tapping it shows
  all 25 and the button disappears.
- A ticked task stays ticked after a hot restart.
- A second account never sees the first account's tasks.
- Break it on purpose: "alter table public.tasks disable row level security;"
  makes every task visible to the second account. Re-enable it right away.
