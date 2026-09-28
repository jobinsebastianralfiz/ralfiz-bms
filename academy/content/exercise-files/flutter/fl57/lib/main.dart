import 'dart:async';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/material.dart';

import 'sync/sync_service.dart';

// Lesson 10.3: TaskFlow offline-first, with in-memory fakes for store and server.
void main() => runApp(MaterialApp(title: 'TaskFlow', home: const TasksPage(),
    theme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple))));

class InMemoryTaskStore implements TaskStore {
  final _tasks = <String, Task>{};
  final _outbox = <OutboxEntry>[];
  final _changes = StreamController<List<Task>>.broadcast();
  int _seq = 0;

  List<Task> get _list =>
      _tasks.values.toList()..sort((a, b) => b.updatedAt.compareTo(a.updatedAt));
  void _emit() => _changes.add(_list);

  @override
  Stream<List<Task>> watchTasks() async* {
    yield _list; // current value first, then every change
    yield* _changes.stream;
  }
  @override
  Future<List<Task>> allTasks() async => _list;
  @override
  Future<void> putTask(Task task) async { _tasks[task.id] = task; _emit(); }
  @override
  Future<void> removeTask(String id) async { _tasks.remove(id); _emit(); }
  @override
  Future<void> setSyncState(String id, SyncState state) async {
    final t = _tasks[id];
    if (t != null) await putTask(t.copyWith(syncState: state));
  }
  @override
  Future<void> writeWithOutbox(OutboxOp op, Task task) async {
    // No await between the two changes, so nobody sees one without the other.
    if (op == OutboxOp.delete) { _tasks.remove(task.id); } else { _tasks[task.id] = task; }
    _outbox.add(OutboxEntry(seq: ++_seq, op: op, task: task));
    _emit();
  }
  @override
  Future<OutboxEntry?> nextInOutbox() async => _outbox.isEmpty ? null : _outbox.first;
  @override
  Future<bool> hasOutboxFor(String taskId) async => _outbox.any((e) => e.task.id == taskId);
  @override
  Future<void> removeFromOutbox(int seq) async => _outbox.removeWhere((e) => e.seq == seq);
  @override
  Future<void> dropOutboxFor(String taskId) async => _outbox.removeWhere((e) => e.task.id == taskId);
  @override
  Future<void> bumpAttempts(int seq) async {
    final i = _outbox.indexWhere((e) => e.seq == seq);
    if (i < 0) return;
    final e = _outbox[i];
    _outbox[i] = OutboxEntry(seq: seq, op: e.op, task: e.task, attempts: e.attempts + 1);
  }
}

/// A pretend server. Switch [reachable] off to simulate "Wi-Fi but no internet".
class FakeTaskApi implements TaskApi {
  bool reachable = true;
  final _server = <String, Task>{
    's1': Task(id: 's1', title: 'Review pull request', updatedAt: DateTime(2026, 9, 1)),
    's2': Task(id: 's2', title: 'Plan sprint', updatedAt: DateTime(2026, 9, 2))};

  Future<void> _call() async {
    await Future<void>.delayed(const Duration(milliseconds: 400));
    if (!reachable) throw NetworkException();
  }

  @override
  Future<List<Task>> fetchAll() async { await _call(); return _server.values.toList(); }
  @override
  Future<void> send(OutboxOp op, Task task) async {
    await _call();
    if (task.title.length > 40) throw RejectedException('Title longer than 40 characters');
    if (op == OutboxOp.delete) { _server.remove(task.id); return; }
    final current = _server[task.id]; // last write wins on the server too:
    if (current != null && current.updatedAt.isAfter(task.updatedAt)) return;
    _server[task.id] = task.copyWith(syncState: SyncState.synced);
  }

  /// Another device renames the first server task, right now.
  void editFromOtherDevice() {
    final first = _server.values.first;
    _server[first.id] = first.copyWith(title: first.title + ' (edited)', updatedAt: DateTime.now());
  }
}

class TasksPage extends StatefulWidget {
  const TasksPage({super.key});
  @override State<TasksPage> createState() => _TasksPageState();
}

class _TasksPageState extends State<TasksPage> {
  final _store = InMemoryTaskStore();
  final _api = FakeTaskApi();
  late final _sync = SyncService(_store, _api);
  late final Stream<List<Task>> _tasks = _store.watchTasks();
  StreamSubscription<List<ConnectivityResult>>? _net;
  bool _deviceOffline = false;
  final _title = TextEditingController();

  bool get _offline => _deviceOffline || !_api.reachable;

  @override
  void initState() {
    super.initState();
    _net = Connectivity().onConnectivityChanged.listen((results) {
      final none = results.every((r) => r == ConnectivityResult.none);
      setState(() => _deviceOffline = none);
      if (!none) _sync.flush(); // a hint to retry, not proof we are online
    });
    _refresh();
  }

  @override
  void dispose() {
    _net?.cancel(); _sync.dispose(); _title.dispose();
    super.dispose();
  }

  Future<void> _refresh() async {
    try {
      await _sync.refresh();
    } on NetworkException {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Offline: showing saved tasks')));
    }
  }

  /// Every write: save locally (instant), then try to send in the background.
  Future<void> _write(Future<void> localWrite) async {
    await localWrite;
    unawaited(_sync.flush()); // sends now if possible, stays queued otherwise
  }

  void _add() {
    final text = _title.text.trim();
    if (text.isEmpty) return;
    _title.clear();
    _write(_sync.addTask(text));
  }

  Widget _stateIcon(SyncState s) => switch (s) {
        SyncState.synced => const Icon(Icons.cloud_done, color: Colors.green),
        SyncState.pending => const Icon(Icons.cloud_upload, color: Colors.orange),
        SyncState.failed => const Icon(Icons.error, color: Colors.red) };

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('TaskFlow'), actions: [
        IconButton(tooltip: 'Edit on another device', icon: const Icon(Icons.devices),
            onPressed: _api.editFromOtherDevice),
        IconButton(tooltip: 'Sync now', icon: const Icon(Icons.sync), onPressed: _refresh),
      ]),
      body: StreamBuilder<List<Task>>(
        stream: _tasks,
        builder: (context, snap) {
          final tasks = snap.data ?? const <Task>[];
          final pending = tasks.where((t) => t.syncState == SyncState.pending).length;
          return Column(children: [
            SwitchListTile(title: const Text('Server reachable'), value: _api.reachable,
                onChanged: (v) {
                  setState(() => _api.reachable = v);
                  if (v) _sync.flush();
                }),
            if (_offline)
              MaterialBanner(
                content: Text('You are offline. Waiting to sync: $pending'),
                leading: const Icon(Icons.cloud_off),
                actions: [TextButton(onPressed: _refresh, child: const Text('Retry'))],
              ),
            Padding(
              padding: const EdgeInsets.all(12),
              child: TextField(controller: _title, onSubmitted: (_) => _add(),
                  decoration: const InputDecoration(labelText: 'New task')),
            ),
            Expanded(
              child: ListView(children: [
                for (final t in tasks)
                  ListTile(
                    leading: Checkbox(value: t.done, onChanged: (_) => _write(_sync.toggle(t))),
                    title: Text(t.title),
                    trailing: _stateIcon(t.syncState),
                    onLongPress: () => _write(_sync.delete(t)),
                  ),
              ]),
            ),
          ]);
        },
      ),
    );
  }
}