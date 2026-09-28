// TaskFlow - lesson 9.1: a small screen to exercise the ApiClient.
// This file is complete and is the same in the solution.
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';

import 'api/api_client.dart';

class Task {
  const Task({required this.id, required this.title, required this.completed});

  factory Task.fromJson(Map<String, dynamic> json) => Task(
        id: json['id'] as int,
        title: json['todo'] as String, // DummyJSON calls the text "todo"
        completed: json['completed'] as bool,
      );

  final int id;
  final String title;
  final bool completed;
}

class TaskRepository {
  TaskRepository(this._api);
  final ApiClient _api;

  /// [delayMs] asks DummyJSON to answer slowly (0 to 5000 ms).
  Future<List<Task>> fetchTasks({
    int limit = 10,
    int delayMs = 0,
    CancelToken? cancelToken,
    Duration? receiveTimeout,
  }) async {
    final json = await _api.get<Map<String, dynamic>>(
      '/todos',
      query: {'limit': limit, if (delayMs > 0) 'delay': delayMs},
      cancelToken: cancelToken,
      options: Options(receiveTimeout: receiveTimeout),
    );
    final items = json['todos'] as List<dynamic>;
    return [for (final item in items) Task.fromJson(item as Map<String, dynamic>)];
  }
}

void main() {
  runApp(TaskFlowApp(repository: TaskRepository(ApiClient())));
}

class TaskFlowApp extends StatelessWidget {
  const TaskFlowApp({super.key, required this.repository});
  final TaskRepository repository;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'TaskFlow',
      theme: ThemeData(colorSchemeSeed: const Color(0xFF00796B)),
      home: TasksPage(repository: repository),
    );
  }
}

class TasksPage extends StatefulWidget {
  const TasksPage({super.key, required this.repository});
  final TaskRepository repository;

  @override
  State<TasksPage> createState() => _TasksPageState();
}

class _TasksPageState extends State<TasksPage> {
  List<Task> _tasks = const [];
  String? _error;
  bool _loading = false;
  CancelToken? _cancelToken;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _cancelToken?.cancel('Page closed'); // never leave a request running
    super.dispose();
  }

  Future<void> _load({int delayMs = 0, Duration? receiveTimeout}) async {
    _cancelToken?.cancel('Replaced by a new request');
    final token = CancelToken();
    setState(() {
      _cancelToken = token;
      _loading = true;
      _error = null;
    });
    try {
      final tasks = await widget.repository.fetchTasks(
        delayMs: delayMs,
        cancelToken: token,
        receiveTimeout: receiveTimeout,
      );
      // Ignore answers from a request that a newer one replaced.
      if (!mounted || !identical(token, _cancelToken)) return;
      setState(() => _tasks = tasks);
    } on AppException catch (e) {
      if (!mounted || !identical(token, _cancelToken)) return;
      setState(() => _error = e.message);
    } finally {
      if (mounted && identical(token, _cancelToken)) {
        setState(() => _loading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('TaskFlow'),
        actions: [
          IconButton(
            tooltip: 'Slow load (4 s)',
            icon: const Icon(Icons.hourglass_bottom),
            onPressed: () => _load(delayMs: 4000),
          ),
          IconButton(
            tooltip: 'Timeout test',
            icon: const Icon(Icons.timer_off),
            onPressed: () => _load(
              delayMs: 4000,
              receiveTimeout: const Duration(seconds: 2),
            ),
          ),
        ],
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_loading) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          spacing: 16,
          children: [
            const CircularProgressIndicator(),
            OutlinedButton(
              onPressed: () => _cancelToken?.cancel('User tapped Cancel'),
              child: const Text('Cancel'),
            ),
          ],
        ),
      );
    }
    final error = _error;
    if (error != null) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          spacing: 12,
          children: [
            const Icon(Icons.cloud_off, size: 48),
            Text(error, textAlign: TextAlign.center),
            FilledButton(onPressed: _load, child: const Text('Retry')),
          ],
        ),
      );
    }
    return ListView.builder(
      itemCount: _tasks.length,
      itemBuilder: (context, i) {
        final task = _tasks[i];
        return ListTile(
          leading: Icon(task.completed ? Icons.check_circle : Icons.radio_button_unchecked),
          title: Text(task.title),
          subtitle: Text('#' + task.id.toString()),
        );
      },
    );
  }
}
