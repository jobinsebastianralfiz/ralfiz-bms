import 'package:flutter/material.dart';

// STARTER - lesson 6.5. It works, but everything lives in one widget:
// the data, the fake network delay and the UI. Refactor it into layers.

void main() => runApp(const App());

class App extends StatelessWidget {
  const App({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Task Tracker',
      theme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: Colors.teal)),
      home: const TasksPage(),
    );
  }
}

// TODO(1): move the task data into an immutable Task model
// (id, title, done) that extends Equatable.
// TODO(2): declare abstract interface class TaskRepository with
// Future<List<Task>> fetchTasks() and Future<Task> addTask(String title).
// TODO(3): implement InMemoryTaskRepository with the delays below.
// TODO(4): add a sealed TasksState (Initial, Loading, Loaded, Failure) and a
// TasksCubit that receives a TaskRepository in its constructor.

class TasksPage extends StatefulWidget {
  const TasksPage({super.key});

  @override
  State<TasksPage> createState() => _TasksPageState();
}

class _TasksPageState extends State<TasksPage> {
  // Data, loading flag and "network" all mixed into the UI. Not testable.
  final List<(String, bool)> _tasks = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    await Future<void>.delayed(const Duration(milliseconds: 600));
    if (!mounted) return;
    setState(() {
      _tasks.addAll([('Plan sprint', false), ('Review pull request', true)]);
      _loading = false;
    });
  }

  Future<void> _add() async {
    var text = '';
    final title = await showDialog<String>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('New task'),
        content: TextField(autofocus: true, onChanged: (v) => text = v),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(dialogContext, text),
            child: const Text('Add'),
          ),
        ],
      ),
    );
    if (title == null || title.trim().isEmpty) return;
    await Future<void>.delayed(const Duration(milliseconds: 300));
    if (!mounted) return;
    setState(() => _tasks.add((title.trim(), false)));
  }

  @override
  Widget build(BuildContext context) {
    // TODO(5): in App, provide the repository with RepositoryProvider and
    // create TasksCubit with context.read<TaskRepository>()..load().
    // TODO(6): make this page a StatelessWidget that uses
    // BlocBuilder<TasksCubit, TasksState> and a switch expression,
    // including a Retry button for the failure state.
    return Scaffold(
      appBar: AppBar(title: const Text('Task Tracker')),
      floatingActionButton: FloatingActionButton(
        onPressed: _add,
        child: const Icon(Icons.add),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              children: [
                for (final (title, done) in _tasks)
                  ListTile(
                    leading: Icon(
                        done ? Icons.check_circle : Icons.radio_button_unchecked),
                    title: Text(title),
                  ),
              ],
            ),
    );
  }
}

// TODO(7): in test/tasks_cubit_test.dart, write a FakeTaskRepository and
// blocTests for load (success and failure) and add.
