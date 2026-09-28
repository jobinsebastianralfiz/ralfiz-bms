import 'package:flutter/material.dart';

import 'data/app_database.dart';

// Lesson 10.1: TaskFlow with a Drift database. This screen is finished:
// the same file works with the starter and the solution database.
void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(TaskFlowApp(db: AppDatabase()));
}

class TaskFlowApp extends StatelessWidget {
  const TaskFlowApp({super.key, required this.db});
  final AppDatabase db;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'TaskFlow',
      theme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: Colors.indigo)),
      home: TaskListPage(db: db),
    );
  }
}

class TaskListPage extends StatefulWidget {
  const TaskListPage({super.key, required this.db});
  final AppDatabase db;

  @override
  State<TaskListPage> createState() => _TaskListPageState();
}

class _TaskListPageState extends State<TaskListPage> {
  bool _hideDone = false;
  // Create streams once, not in build(): a new stream restarts the query.
  late Stream<List<TaskWithProject>> _tasks = widget.db.taskDao.watchTasks();
  late final Stream<int> _openCount = widget.db.taskDao.watchOpenCount();

  void _setHideDone(bool value) {
    setState(() {
      _hideDone = value;
      _tasks = widget.db.taskDao.watchTasks(hideDone: value);
    });
  }

  Future<void> _addTask() async {
    final title = await showDialog<String>(
      context: context,
      builder: (context) => const NewTaskDialog(),
    );
    if (title == null || title.trim().isEmpty) return;
    // Project 1 is the Inbox created in beforeOpen.
    await widget.db.taskDao.addTask(title.trim(), projectId: 1);
  }

  Future<void> _deleteDone() async {
    final removed = await widget.db.taskDao.deleteDone();
    if (!mounted) return;
    ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(content: Text('Deleted $removed done tasks')));
  }

  @override
  Widget build(BuildContext context) {
    final dao = widget.db.taskDao;
    return Scaffold(
      appBar: AppBar(
        title: StreamBuilder<int>(
          stream: _openCount,
          builder: (context, snap) {
            final open = snap.data ?? 0;
            return Text('TaskFlow ($open open)');
          },
        ),
        actions: [
          IconButton(
            tooltip: 'Delete done tasks',
            icon: const Icon(Icons.delete_sweep),
            onPressed: _deleteDone,
          ),
        ],
      ),
      body: Column(
        children: [
          SwitchListTile(
            title: const Text('Hide done'),
            value: _hideDone,
            onChanged: _setHideDone,
          ),
          Expanded(
            child: StreamBuilder<List<TaskWithProject>>(
              stream: _tasks,
              builder: (context, snap) {
                if (snap.hasError) return Center(child: Text('Error: ' + snap.error.toString()));
                if (!snap.hasData) return const Center(child: CircularProgressIndicator());
                final items = snap.data!;
                if (items.isEmpty) {
                  return const Center(child: Text('No tasks yet. Tap + to add one.'));
                }
                return ListView.builder(
                  itemCount: items.length,
                  itemBuilder: (context, i) {
                    final (:task, :project) = items[i];
                    return CheckboxListTile(
                      value: task.done,
                      onChanged: (_) => dao.toggleDone(task),
                      title: Text(
                        task.title,
                        style: task.done
                            ? const TextStyle(decoration: TextDecoration.lineThrough)
                            : null,
                      ),
                      subtitle: Text(project?.name ?? 'No project'),
                    );
                  },
                );
              },
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _addTask,
        child: const Icon(Icons.add),
      ),
    );
  }
}

class NewTaskDialog extends StatefulWidget {
  const NewTaskDialog({super.key});

  @override
  State<NewTaskDialog> createState() => _NewTaskDialogState();
}

class _NewTaskDialogState extends State<NewTaskDialog> {
  final _title = TextEditingController();

  @override
  void dispose() {
    _title.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('New task'),
      content: TextField(
        controller: _title,
        autofocus: true,
        decoration: const InputDecoration(labelText: 'Title'),
        onSubmitted: (value) => Navigator.pop(context, value),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
        FilledButton(
          onPressed: () => Navigator.pop(context, _title.text),
          child: const Text('Add'),
        ),
      ],
    );
  }
}