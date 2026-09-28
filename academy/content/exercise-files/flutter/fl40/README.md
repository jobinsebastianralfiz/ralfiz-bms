# Lesson 7.2 lab: News Reader, async UI

## Setup
    flutter create news_reader_async
    cd news_reader_async
    flutter pub add http

Copy start/lib/main.dart to lib/main.dart and run it.

## Find the bug first
1. Run the app with the debug console open.
2. Tap "Rebuild 0" in the app bar a few times.
3. Every tap prints "fetchPosts called" and the spinner comes back.
   The future is created inside build(), so each rebuild starts a new request.

## Tasks
- TODO(1) Create the future once in initState and pass the stored future
  to FutureBuilder.
- TODO(2) Handle error, loading and data. A failed request must show a
  message, not an empty list.
- TODO(3) Add pull-to-refresh with RefreshIndicator. onRefresh must return
  a Future that completes when loading is finished. The error view must be
  scrollable too, or you cannot pull to retry.
- TODO(4) Add a StreamBuilder that shows "Updated N s ago" and restarts
  from 0 after each refresh.

## Acceptance criteria
- Tapping "Rebuild" 5 times prints "fetchPosts called" only once
  (the starter prints it on every tap).
- Pulling down shows the refresh spinner, prints "fetchPosts called" once,
  and the list stays visible while it reloads.
- "Updated N s ago" counts up every second and returns to 0 after a refresh.
- In airplane mode the error message appears, and pulling down after
  turning the connection back on loads the posts.
