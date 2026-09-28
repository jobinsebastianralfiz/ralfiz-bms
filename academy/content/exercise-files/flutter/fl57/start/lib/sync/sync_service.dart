import 'dart:async';
import 'dart:math' show Random, min;

// STARTER - lesson 10.3: offline-first writes with an outbox.
// Models, interfaces and local writes are done. It runs, but nothing is ever
// sent to the server: every change stays pending. Finish the TODOs.

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

  /// Backoff for the next retry after [attempts] failures.
  static Duration retryDelay(int attempts) {
    // TODO(4): 1 s, 2 s, 4 s ... doubling per attempt, capped at 60 s, plus
    // Random().nextInt(500) milliseconds of jitter. Hint: 1 << min(attempts, 6).
    return const Duration(seconds: 5);
  }

  /// Sends queued changes oldest first. Returns how many were sent.
  Future<int> flush() async {
    if (_flushing) return 0; // one flush at a time keeps the order
    _flushing = true;
    _retry?.cancel();
    var sent = 0;
    try {
      // TODO(1): loop: take _store.nextInOutbox() (stop when null), send it
      // with _api.send(entry.op, entry.task), remove it from the outbox and
      // count it. For create/update, set the task to SyncState.synced, but
      // only when no other outbox entry for that task is waiting.
      // TODO(2): on NetworkException: bumpAttempts, schedule
      // _retry = Timer(retryDelay(entry.attempts), flush) and break.
      // TODO(3): on RejectedException: remove the entry and mark the task
      // SyncState.failed, then carry on with the next entry.
    } finally {
      _flushing = false;
    }
    return sent;
  }

  /// Pushes local changes, then pulls the server list and merges it.
  Future<void> refresh() async {
    // TODO(5): call flush() first. Then, for each remote task, keep the local
    // copy only when it is not synced AND the remote updatedAt is not after
    // it (last write wins). Otherwise dropOutboxFor(id) and putTask(remote).
    final remote = await _api.fetchAll();
    for (final r in remote) {
      await _store.putTask(r); // naive: the server always wins
    }
    // TODO(6): remove local tasks that the server no longer has, unless they
    // are unsent local changes (syncState is not synced).
  }

  void dispose() => _retry?.cancel();
}