# Lesson 12.3 - TaskFlow live list and photo attachments

Start from your finished lesson 12.2 project (lib/main.dart and
lib/data/supabase_task_repository.dart).

## 1. Database and storage (Supabase SQL editor)

    -- Realtime for tasks
    alter publication supabase_realtime add table public.tasks;

    -- Where the file path is stored
    alter table public.tasks add column if not exists attachment_path text;

    -- Private bucket
    insert into storage.buckets (id, name, public)
    values ('task-files', 'task-files', false)
    on conflict (id) do nothing;

    -- Each user may only use the folder named after their own id
    create policy "Upload into own folder" on storage.objects
      for insert to authenticated
      with check (bucket_id = 'task-files'
                  and (storage.foldername(name))[1] = (select auth.uid()::text));
    create policy "Read own files" on storage.objects
      for select to authenticated
      using (bucket_id = 'task-files'
             and (storage.foldername(name))[1] = (select auth.uid()::text));
    create policy "Delete own files" on storage.objects
      for delete to authenticated
      using (bucket_id = 'task-files'
             and (storage.foldername(name))[1] = (select auth.uid()::text));

## 2. Flutter project

    flutter pub add image_picker

iOS: add NSPhotoLibraryUsageDescription and NSCameraUsageDescription to
ios/Runner/Info.plist with a short sentence each.

Copy start/lib/live_tasks_page.dart to lib/live_tasks_page.dart. In
lib/main.dart, import it and replace

    TasksPage(key: ValueKey(auth.currentUser?.id), repo: repo)

with

    LiveTasksPage(key: ValueKey(auth.currentUser?.id), repo: repo)

Run with flutter run --dart-define-from-file=env/dev.json.

## 3. Your tasks (live_tasks_page.dart)
- TODO(1) Create the stream once in _start: tasks, primary key id,
  eq project_id, order created_at descending.
- TODO(2) Open the channel: inserts on public.tasks filtered by project_id,
  callback _onInsert, and a subscribe callback that sets _live.
- TODO(3) Remove the channel in dispose().
- TODO(4) _attach: pick an image, upload the bytes to task-files at
  uid/taskId/timestamp.jpg, then save the path in attachment_path.
- TODO(5) _signedUrl: create (and cache) a signed URL valid for 3600 seconds.

## Acceptance criteria
- Adding a task in the Supabase Table editor makes it appear in the app
  within a moment, with the SnackBar "Added on another device: <title>".
- Adding a task in the app does NOT show that SnackBar.
- Ticking a task on one device ticks it on a second signed-in device.
- Attaching a photo shows a progress bar, then a thumbnail; the file is
  listed in Storage under task-files/<your user id>/<task id>/.
- Turning on airplane mode shows "Reconnecting… live updates paused";
  it disappears after reconnecting.
- A second user cannot see the first user's photos.
