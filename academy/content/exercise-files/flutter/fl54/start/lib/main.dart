// Lesson 9.6 starter: TaskFlow "My tasks" in one widget. It works, but the page
// calls Dio, knows DummyJSON field names, sorts tasks and maps errors itself.
//
// Target (feature-first, see the lesson):
//   lib/features/tasks/domain/tasks_domain.dart   Result, Failure, Task entity,
//                                                 TaskRepository, AuthRepository, GetMyTasks
//   lib/features/tasks/data/tasks_data.dart       TaskDto, toEntity mapper,
//                                                 TaskRemoteDataSource, TaskRepositoryImpl,
//                                                 DemoAuthRepository
//   lib/main.dart                                 get_it setup, TasksCubit, TasksPage
//
// Packages: flutter pub add dio get_it flutter_bloc
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';

void main() => runApp(MaterialApp(
      theme: ThemeData(colorSchemeSeed: const Color(0xFF5E35B1)),
      home: const MyTasksPage(),
    ));

class MyTasksPage extends StatefulWidget {
  const MyTasksPage({super.key});

  @override
  State<MyTasksPage> createState() => _MyTasksPageState();
}

class _MyTasksPageState extends State<MyTasksPage> {
  // TODO(5): Dio belongs in the data layer (TaskRemoteDataSource).
  final _dio = Dio(BaseOptions(baseUrl: 'https://dummyjson.com'));

  // TODO(1): raw JSON maps leak the API shape into the UI. Use a Task entity.
  List<Map<String, dynamic>> _tasks = [];
  String? _error;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      // TODO(3): the current user comes from AuthRepository in GetMyTasks.
      const userId = 152;
      final response =
          await _dio.get<Map<String, dynamic>>('/todos/user/$userId');
      final list = (response.data?['todos'] as List<dynamic>? ?? const [])
          .cast<Map<String, dynamic>>()
          .toList();
      // TODO(3): "open tasks first, then by title" is a business rule.
      list.sort((a, b) {
        final aDone = a['completed'] as bool;
        final bDone = b['completed'] as bool;
        if (aDone != bDone) return aDone ? 1 : -1;
        return (a['todo'] as String).compareTo(b['todo'] as String);
      });
      if (!mounted) return;
      setState(() {
        _tasks = list;
        _loading = false;
      });
    } on DioException catch (e) {
      // TODO(4): map DioException to a Failure in TaskRepositoryImpl.
      if (!mounted) return;
      setState(() {
        _error = e.message ?? 'Request failed';
        _loading = false;
      });
    }
  }

  Future<void> _toggle(Map<String, dynamic> task, bool done) async {
    final id = task['id'] as int;
    await _dio.put<Map<String, dynamic>>('/todos/$id', data: {'completed': done});
    if (!mounted) return;
    setState(() => task['completed'] = done); // TODO(6): never mutate state.
  }

  @override
  Widget build(BuildContext context) {
    // TODO(7): TasksPage should only switch on a TasksState from TasksCubit.
    Widget body;
    if (_loading) {
      body = const Center(child: CircularProgressIndicator());
    } else if (_error != null) {
      body = Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(_error!),
            FilledButton(onPressed: _load, child: const Text('Retry')),
          ],
        ),
      );
    } else {
      body = ListView(
        children: [
          for (final task in _tasks)
            CheckboxListTile(
              value: task['completed'] as bool,
              title: Text(task['todo'] as String),
              onChanged: (v) => _toggle(task, v ?? false),
            ),
        ],
      );
    }
    return Scaffold(appBar: AppBar(title: const Text('My tasks')), body: body);
  }
}
