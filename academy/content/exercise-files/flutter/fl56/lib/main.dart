import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:hive_ce/hive_ce.dart';
import 'package:hive_ce_flutter/hive_ce_flutter.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'data/todo_cache.dart';

// Lesson 10.2: three kinds of local storage in one small screen.
// - shared_preferences: the dark mode switch (a tiny setting)
// - Hive CE: cached API responses (key-value, custom type adapter)
// - network: https://dummyjson.com/todos through Dio
Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Hive.initFlutter(); // picks an app folder for the box files
  final cache = await CacheStore.open();
  final prefs = SharedPreferencesAsync();
  final dark = await prefs.getBool('darkMode') ?? false;
  final dio = Dio(BaseOptions(
    baseUrl: 'https://dummyjson.com',
    connectTimeout: const Duration(seconds: 5),
    receiveTimeout: const Duration(seconds: 5),
  ));
  runApp(TaskFlowApp(
      repo: TodoRepository(dio, cache), cache: cache, prefs: prefs, initialDark: dark));
}

class TaskFlowApp extends StatefulWidget {
  const TaskFlowApp(
      {super.key, required this.repo, required this.cache, required this.prefs, required this.initialDark});
  final TodoRepository repo;
  final CacheStore cache;
  final SharedPreferencesAsync prefs;
  final bool initialDark;

  @override
  State<TaskFlowApp> createState() => _TaskFlowAppState();
}

class _TaskFlowAppState extends State<TaskFlowApp> {
  late bool _dark = widget.initialDark;

  Future<void> _toggleDark() async {
    setState(() => _dark = !_dark);
    await widget.prefs.setBool('darkMode', _dark);
  }

  @override
  Widget build(BuildContext context) {
    ColorScheme scheme(Brightness b) =>
        ColorScheme.fromSeed(seedColor: Colors.teal, brightness: b);
    return MaterialApp(
      title: 'TaskFlow',
      theme: ThemeData(colorScheme: scheme(Brightness.light)),
      darkTheme: ThemeData(colorScheme: scheme(Brightness.dark)),
      themeMode: _dark ? ThemeMode.dark : ThemeMode.light,
      home: TodosPage(repo: widget.repo, cache: widget.cache, onToggleDark: _toggleDark),
    );
  }
}

class TodosPage extends StatefulWidget {
  const TodosPage(
      {super.key, required this.repo, required this.cache, required this.onToggleDark});
  final TodoRepository repo;
  final CacheStore cache;
  final VoidCallback onToggleDark;

  @override
  State<TodosPage> createState() => _TodosPageState();
}

class _TodosPageState extends State<TodosPage> {
  late Stream<TodosResult> _todos = widget.repo.watchTodos();

  void _refresh() => setState(() => _todos = widget.repo.watchTodos(force: true));

  Future<void> _clearCache() async {
    await widget.cache.clear();
    if (!mounted) return;
    ScaffoldMessenger.of(context)
        .showSnackBar(const SnackBar(content: Text('Cache cleared')));
  }

  static String _ageText(DateTime savedAt) {
    final minutes = DateTime.now().difference(savedAt).inMinutes;
    return minutes < 1 ? 'just now' : '$minutes min ago';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('TaskFlow todos'),
        actions: [
          IconButton(tooltip: 'Dark mode', icon: const Icon(Icons.dark_mode), onPressed: widget.onToggleDark),
          IconButton(tooltip: 'Clear cache', icon: const Icon(Icons.delete_outline), onPressed: _clearCache),
          IconButton(tooltip: 'Refresh', icon: const Icon(Icons.refresh), onPressed: _refresh),
        ],
      ),
      body: StreamBuilder<TodosResult>(
        stream: _todos,
        builder: (context, snap) {
          if (snap.hasError) {
            return Center(
              child: Column(mainAxisSize: MainAxisSize.min, children: [
                const Text('Could not load todos. Check your connection.'),
                const SizedBox(height: 12),
                FilledButton(onPressed: _refresh, child: const Text('Retry')),
              ]),
            );
          }
          if (!snap.hasData) return const Center(child: CircularProgressIndicator());
          final result = snap.data!;
          final age = _ageText(result.savedAt);
          final source = result.fromCache ? 'From cache, saved $age' : 'Fresh from the network';
          final colors = Theme.of(context).colorScheme;
          return Column(children: [
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              color: result.warning != null ? colors.errorContainer : colors.secondaryContainer,
              child: Text(result.warning ?? source),
            ),
            Expanded(
              child: ListView.builder(
                itemCount: result.todos.length,
                itemBuilder: (context, i) {
                  final todo = result.todos[i];
                  return ListTile(
                    leading: Icon(todo.done ? Icons.check_circle : Icons.radio_button_unchecked),
                    title: Text(todo.title),
                  );
                },
              ),
            ),
          ]);
        },
      ),
    );
  }
}