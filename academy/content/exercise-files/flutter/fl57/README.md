# Lesson 10.3 lab: offline-first TaskFlow with an outbox

Every change the user makes is saved locally first and queued in an
outbox. A SyncService sends the queue in order when the server can be
reached, backs off while it cannot, marks rejected changes as failed, and
merges the server list with a last-write-wins rule.

To keep the focus on sync logic, the local store and the server are
in-memory fakes in lib/main.dart (so data resets when the app restarts).
The TaskStore interface matches what the Drift AppDatabase from lesson
10.1 provides in the real app, where writeWithOutbox is one transaction.

## Setup

    flutter create taskflow_sync
    cd taskflow_sync
    flutter pub add connectivity_plus

Copy the files:

- flutter/fl57/lib/main.dart -> lib/main.dart (fakes and finished UI)
- flutter/fl57/start/lib/sync/sync_service.dart -> lib/sync/sync_service.dart

Run on an emulator or device. The "Server reachable" switch simulates a
phone that has Wi-Fi but no working internet. Airplane mode on the device
shows the banner through connectivity_plus.

## Your tasks (TODOs in sync_service.dart)

1. flush: send outbox entries oldest first; mark tasks synced when
   nothing else is queued for them.
2. On NetworkException: count the attempt, schedule a retry, stop.
3. On RejectedException: drop the entry and mark the task failed.
4. retryDelay: exponential backoff with a cap and jitter.
5. refresh: push first, then merge with last write wins.
6. refresh: remove tasks the server deleted (but never unsent ones).

## Test it (create test/sync_service_test.dart)

    import 'package:flutter_test/flutter_test.dart';
    import 'package:taskflow_sync/main.dart';
    import 'package:taskflow_sync/sync/sync_service.dart';

    void main() {
      test('offline writes stay queued and are sent later', () async {
        final store = InMemoryTaskStore();
        final api = FakeTaskApi()..reachable = false;
        final sync = SyncService(store, api);
        await sync.addTask('Write tests');
        expect(await sync.flush(), 0);
        expect((await store.allTasks()).single.syncState, SyncState.pending);
        api.reachable = true;
        expect(await sync.flush(), 1);
        expect((await store.allTasks()).single.syncState, SyncState.synced);
        sync.dispose();
      });

      test('a rejected change is marked failed and not retried', () async {
        final store = InMemoryTaskStore();
        final sync = SyncService(store, FakeTaskApi());
        await sync.addTask('x' * 41);
        await sync.flush();
        expect((await store.allTasks()).single.syncState, SyncState.failed);
        expect(await store.nextInOutbox(), isNull);
      });

      test('a newer edit from another device wins', () async {
        final store = InMemoryTaskStore();
        final api = FakeTaskApi();
        final sync = SyncService(store, api);
        await sync.refresh();
        api.reachable = false;
        final s1 = (await store.allTasks()).firstWhere((t) => t.id == 's1');
        await sync.toggle(s1);
        await Future<void>.delayed(const Duration(milliseconds: 5));
        api.editFromOtherDevice();
        api.reachable = true;
        await sync.refresh();
        final merged = (await store.allTasks()).firstWhere((t) => t.id == 's1');
        expect(merged.title, 'Review pull request (edited)');
        expect(merged.done, isFalse);
        expect(merged.syncState, SyncState.synced);
      });
    }

Run: flutter test

## Acceptance criteria

- On start, Review pull request and Plan sprint appear with a green cloud.
- With Server reachable off, a new task shows an orange upload icon and the
  banner says You are offline. Waiting to sync: 1
- Turning Server reachable back on turns the icon green within a second.
- A task title longer than 40 characters ends with a red error icon and is
  not retried.
- Tap the devices icon, then Sync now: the first task's title ends with
  (edited).
- flutter test reports All tests passed!