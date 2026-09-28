import 'package:equatable/equatable.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

void main() => runApp(TasksApp(repository: InMemoryTaskRepository()));

class Task extends Equatable {
  const Task(this.title, {this.done = false});
  final String title;
  final bool done;

  Task toggled() => Task(title, done: !done);

  @override
  List<Object?> get props => [title, done];
}

/// Text shown above the list. Pure function: easy to unit test.
String summary(List<Task> tasks) {
  final open = tasks.where((t) => !t.done).length;
  return switch (open) {
    0 => 'All done!',
    1 => '1 task left',
    _ => '$open tasks left',
  };
}

abstract interface class TaskRepository {
  Future<List<Task>> fetchTasks();
}

class InMemoryTaskRepository implements TaskRepository {
  @override
  Future<List<Task>> fetchTasks() async {
    await Future<void>.delayed(const Duration(milliseconds: 300));
    return const [Task('Read lesson 8.3'), Task('Write a widget test')];
  }
}

sealed class TasksState extends Equatable {
  const TasksState();

  @override
  List<Object?> get props => [];
}

final class TasksInitial extends TasksState {
  const TasksInitial();
}

final class TasksLoading extends TasksState {
  const TasksLoading();
}

final class TasksLoaded extends TasksState {
  const TasksLoaded(this.tasks);
  final List<Task> tasks;

  @override
  List<Object?> get props => [tasks];
}

final class TasksError extends TasksState {
  const TasksError(this.message);
  final String message;

  @override
  List<Object?> get props => [message];
}

class TasksCubit extends Cubit<TasksState> {
  TasksCubit(this._repository) : super(const TasksInitial());
  final TaskRepository _repository;

  Future<void> load() async {
    emit(const TasksLoading());
    try {
      emit(TasksLoaded(await _repository.fetchTasks()));
    } catch (_) {
      emit(const TasksError('Could not load tasks'));
    }
  }

  void add(String title) {
    final s = state;
    final clean = title.trim();
    if (s is! TasksLoaded || clean.isEmpty) return;
    emit(TasksLoaded([...s.tasks, Task(clean)]));
  }

  void toggle(int index) {
    final s = state;
    if (s is! TasksLoaded) return;
    final tasks = [...s.tasks];
    tasks[index] = tasks[index].toggled();
    emit(TasksLoaded(tasks));
  }
}

class TasksApp extends StatelessWidget {
  const TasksApp({super.key, required this.repository});
  final TaskRepository repository;

  @override
  Widget build(BuildContext context) => MaterialApp(
        title: 'Tasks',
        theme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF3949AB))),
        home: BlocProvider(create: (_) => TasksCubit(repository)..load(), child: const TasksPage()),
      );
}

class TasksPage extends StatefulWidget {
  const TasksPage({super.key});

  @override
  State<TasksPage> createState() => _TasksPageState();
}

class _TasksPageState extends State<TasksPage> {
  final _controller = TextEditingController();

  void _add() {
    context.read<TasksCubit>().add(_controller.text);
    _controller.clear();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Tasks')),
      body: BlocBuilder<TasksCubit, TasksState>(
        builder: (context, state) => switch (state) {
          TasksInitial() || TasksLoading() => const Center(child: CircularProgressIndicator()),
          TasksError(:final message) => Center(
              child: Column(mainAxisSize: MainAxisSize.min, children: [
                Text(message),
                TextButton(onPressed: () => context.read<TasksCubit>().load(), child: const Text('Retry')),
              ]),
            ),
          TasksLoaded(:final tasks) => Column(children: [
              Padding(
                padding: const EdgeInsets.all(16),
                child: Row(children: [
                  Expanded(
                    child: TextField(
                      key: const Key('newTask'),
                      controller: _controller,
                      decoration: const InputDecoration(labelText: 'New task'),
                      onSubmitted: (_) => _add(),
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton.filled(key: const Key('addTask'), icon: const Icon(Icons.add), onPressed: _add),
                ]),
              ),
              Text(summary(tasks)),
              Expanded(
                child: ListView.builder(
                  itemCount: tasks.length,
                  itemBuilder: (context, i) => CheckboxListTile(
                    value: tasks[i].done,
                    title: Text(tasks[i].title),
                    onChanged: (_) => context.read<TasksCubit>().toggle(i),
                  ),
                ),
              ),
            ]),
        },
      ),
    );
  }
}
