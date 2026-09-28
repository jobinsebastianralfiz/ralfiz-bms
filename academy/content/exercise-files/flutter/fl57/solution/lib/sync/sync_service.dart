import 'dart:async';
import 'dart:math' show Random, min;

// SOLUTION - lesson 10.3: offline-first writes with an outbox, plus a pull
// that resolves conflicts with last-write-wins. Pure Dart: no Flutter
// imports, so it runs in unit tests.

enum SyncState { synced, pending, failed }

enum OutboxOp { create, update, delete }

class Task {
  const Task({required this.id, required this.title, this.done = false,
      required this.updatedAt, this.syncState = SyncState.synced});
  final String id; // made on the device, so offline creates have a stable id
  final String title;
  final bool done;
  final DateTime updatedAt;
  final SyncState syncState;

  Task copyWith({String? title, bool? done, DateTime? updatedAt, SyncState? syncState}) =>
      Task(
          id: id,
          title: title ?? this.title,
          done: done ?? this.done,
          updatedAt: updatedAt ?? this.updatedAt,
          syncState: syncState ?? this.syncState);
}

/// One queued change. [task] is a snapshot of what to send.
class OutboxEntry {
  const OutboxEntry({required this.seq, required this.op, required this.task,
      this.attempts = 0});
  final int seq;
  final OutboxOp op;
  final Task task;
  final int attempts;
}

/// The request did not reach the server, or timed out. Retry later.
class NetworkException implements Exception {}

/// The server answered and refused (a 4xx). Retrying will not help.
class RejectedException implements Exception {
  RejectedException(this.message);
  final String message;
}

/// The local database. In TaskFlow this is AppDatabase (Drift), where
/// writeWithOutbox is one transaction.
abstract interface class TaskStore {
  Stream<List<Task>> watchTasks();
  Future<List<Task>> allTasks();
  Future<void> putTask(Task task);
  Future<void> removeTask(String id);
  Future<void> setSyncState(String id, SyncState state);
  Future<void> writeWithOutbox(OutboxOp op, Task task);
  Future<OutboxEntry?> nextInOutbox();
  Future<bool> hasOutboxFor(String taskId);
  Future<void> removeFromOutbox(int seq);
  Future<void> dropOutboxFor(String taskId);
  Future<void> bumpAttempts(int seq);
}

abstract interface class TaskApi {
  Future<List<Task>> fetchAll();
  Future<void> send(OutboxOp op, Task task);
}

class SyncService {
  SyncService(this._store, this._api);
  final TaskStore _store;
  final TaskApi _api;
  bool _flushing = false;
  Timer? _retry;
  int _counter = 0;

  String _newId() {
    _counter++;
    final micros = DateTime.now().microsecondsSinceEpoch;
    return 'local-$micros-$_counter';
  }

  // Writes only touch the local store. The UI updates from watchTasks().
  Future<void> addTask(String title) => _store.writeWithOutbox(
      OutboxOp.create,
      Task(id: _newId(), title: title, updatedAt: DateTime.now(),
          syncState: SyncState.pending));

  Future<void> toggle(Task task) => _store.writeWithOutbox(
      OutboxOp.update,
      task.copyWith(done: !task.done, updatedAt: DateTime.now(),
          syncState: SyncState.pending));

  Future<void> delete(Task task) => _store.writeWithOutbox(OutboxOp.delete, task);

  /// 1 s, 2 s, 4 s ... capped at 60 s, plus up to 500 ms of random jitter.
  static Duration retryDelay(int attempts) {
    final seconds = min(60, 1 << min(attempts, 6));
    return Duration(seconds: seconds, milliseconds: Random().nextInt(500));
  }

  /// Sends queued changes oldest first. Returns how many were sent.
  Future<int> flush() async {
    if (_flushing) return 0; // one flush at a time keeps the order
    _flushing = true;
    _retry?.cancel();
    var sent = 0;
    try {
      while (true) {
        final entry = await _store.nextInOutbox();
        if (entry == null) break;
        try {
          await _api.send(entry.op, entry.task);
          await _store.removeFromOutbox(entry.seq);
          sent++;
          final id = entry.task.id;
          if (entry.op != OutboxOp.delete && !await _store.hasOutboxFor(id)) {
            await _store.setSyncState(id, SyncState.synced);
          }
        } on NetworkException {
          await _store.bumpAttempts(entry.seq);
          _retry = Timer(retryDelay(entry.attempts), flush);
          break; // keep the queue in order; try again later
        } on RejectedException {
          await _store.removeFromOutbox(entry.seq); // retrying cannot help
          await _store.setSyncState(entry.task.id, SyncState.failed);
        }
      }
    } finally {
      _flushing = false;
    }
    return sent;
  }

  /// Pushes local changes, then pulls the server list and merges it.
  /// Conflict rule: last write wins, by updatedAt.
  Future<void> refresh() async {
    await flush();
    final remote = await _api.fetchAll(); // throws NetworkException offline
    final local = {for (final t in await _store.allTasks()) t.id: t};
    for (final r in remote) {
      final mine = local.remove(r.id);
      final keepMine = mine != null &&
          mine.syncState != SyncState.synced &&
          !r.updatedAt.isAfter(mine.updatedAt);
      if (!keepMine) {
        await _store.dropOutboxFor(r.id); // the server copy is newer
        await _store.putTask(r);
      }
    }
    // Left over: tasks the server no longer has. Remove them unless they
    // are local changes that have not been sent yet.
    for (final t in local.values) {
      if (t.syncState == SyncState.synced) await _store.removeTask(t.id);
    }
  }

  void dispose() => _retry?.cancel();
}