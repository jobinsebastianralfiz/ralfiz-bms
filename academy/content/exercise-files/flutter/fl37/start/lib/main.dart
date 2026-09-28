import 'package:equatable/equatable.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

// STARTER - lesson 6.4. Runs as it is: you can add tasks.
// Work through TODO(1) to TODO(5), then the tests in test/task_bloc_test.dart.

void main() => runApp(const TaskApp());

class Task extends Equatable {
  const Task({required this.id, required this.title, this.done = false});
  final int id;
  final String title;
  final bool done;

  Task copyWith({bool? done}) =>
      Task(id: id, title: title, done: done ?? this.done);

  @override
  List<Object?> get props => [id, title, done];
}

sealed class TaskEvent {
  const TaskEvent();
}

final class TaskAdded extends TaskEvent {
  const TaskAdded(this.title);
  final String title;
}

final class TaskToggled extends TaskEvent {
  const TaskToggled(this.id);
  final int id;
}

final class TaskDeleted extends TaskEvent {
  const TaskDeleted(this.id);
  final int id;
}

class TaskState extends Equatable {
  const TaskState({this.tasks = const [], this.lastDeleted});
  final List<Task> tasks;
  final Task? lastDeleted;

  @override
  List<Object?> get props => [tasks, lastDeleted];
}

class TaskBloc extends Bloc<TaskEvent, TaskState> {
  TaskBloc() : super(const TaskState()) {
    on<TaskAdded>(_onAdded);
    on<TaskToggled>(_onToggled);
    on<TaskDeleted>(_onDeleted);
  }

  int _nextId = 1;

  void _onAdded(TaskAdded event, Emitter<TaskState> emit) {
    final title = event.title.trim();
    if (title.isEmpty) return;
    final task = Task(id: _nextId++, title: title);
    emit(TaskState(tasks: [...state.tasks, task]));
  }

  void _onToggled(TaskToggled event, Emitter<TaskState> emit) {
    // TODO(1): emit a new TaskState where the task with event.id has
    // done flipped. Build a NEW list (collection for + copyWith).
  }

  void _onDeleted(TaskDeleted event, Emitter<TaskState> emit) {
    // TODO(2): find the task (where + firstOrNull), return if it is null,
    // then emit a state without it and with lastDeleted set to it.
  }
}

// TODO(3): add enum TaskFilter { all, active, done } and a FilterCubit
// with a select(TaskFilter) method. Provide it next to TaskBloc with
// MultiBlocProvider in TaskApp.

class TaskApp extends StatelessWidget {
  const TaskApp({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => TaskBloc(),
      child: MaterialApp(
        title: 'Task Tracker',
        theme: ThemeData(
            colorScheme: ColorScheme.fromSeed(seedColor: Colors.indigo)),
        home: const TaskPage(),
      ),
    );
  }
}

class TaskPage extends StatefulWidget {
  const TaskPage({super.key});

  @override
  State<TaskPage> createState() => _TaskPageState();
}

class _TaskPageState extends State<TaskPage> {
  final _controller = TextEditingController();

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _add() {
    context.read<TaskBloc>().add(TaskAdded(_controller.text));
    _controller.clear();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Task Tracker')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(12),
            child: TextField(
              controller: _controller,
              decoration: InputDecoration(
                labelText: 'New task',
                suffixIcon:
                    IconButton(icon: const Icon(Icons.add), onPressed: _add),
              ),
              onSubmitted: (_) => _add(),
            ),
          ),
          // TODO(4): add a SegmentedButton<TaskFilter> here and filter the
          // list below with a switch expression on the selected filter.
          Expanded(
            // TODO(5): change this to BlocConsumer and show a SnackBar
            // 'Deleted "<title>"' when lastDeleted changes (use listenWhen).
            child: BlocBuilder<TaskBloc, TaskState>(
              builder: (context, state) {
                if (state.tasks.isEmpty) {
                  return const Center(child: Text('No tasks here yet'));
                }
                return ListView(
                  children: [
                    for (final task in state.tasks)
                      CheckboxListTile(
                        controlAffinity: ListTileControlAffinity.leading,
                        value: task.done,
                        title: Text(task.title),
                        onChanged: (_) =>
                            context.read<TaskBloc>().add(TaskToggled(task.id)),
                        secondary: IconButton(
                          icon: const Icon(Icons.delete_outline),
                          onPressed: () =>
                              context.read<TaskBloc>().add(TaskDeleted(task.id)),
                        ),
                      ),
                  ],
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
