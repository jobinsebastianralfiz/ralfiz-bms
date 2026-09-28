import 'package:equatable/equatable.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

// SOLUTION - lesson 6.5. One file to paste; each header names its real file.

// ===== lib/features/tasks/domain/task.dart =====
class Task extends Equatable {
  const Task({required this.id, required this.title, this.done = false});
  final int id;
  final String title;
  final bool done;
  @override
  List<Object?> get props => [id, title, done];
}

// ===== lib/features/tasks/domain/task_repository.dart =====
abstract interface class TaskRepository {
  Future<List<Task>> fetchTasks();
  Future<Task> addTask(String title);
}

// ===== lib/features/tasks/data/in_memory_task_repository.dart =====
class InMemoryTaskRepository implements TaskRepository {
  final List<Task> _tasks = [
    const Task(id: 1, title: 'Plan sprint'),
    const Task(id: 2, title: 'Review pull request', done: true),
  ];
  @override
  Future<List<Task>> fetchTasks() async {
    await Future<void>.delayed(const Duration(milliseconds: 600));
    return List<Task>.unmodifiable(_tasks);
  }

  @override
  Future<Task> addTask(String title) async {
    await Future<void>.delayed(const Duration(milliseconds: 300));
    final task = Task(id: _tasks.length + 1, title: title);
    _tasks.add(task);
    return task;
  }
}

// ===== lib/features/tasks/presentation/tasks_cubit.dart =====
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

final class TasksFailure extends TasksState {
  const TasksFailure(this.message);
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
      emit(const TasksFailure('Could not load tasks.'));
    }
  }

  Future<void> add(String title) async {
    if (title.trim().isEmpty) return;
    try {
      await _repository.addTask(title.trim());
      emit(TasksLoaded(await _repository.fetchTasks()));
    } catch (_) {
      emit(const TasksFailure('Could not save the task.'));
    }
  }
}

// ===== lib/features/tasks/presentation/tasks_page.dart =====
class TasksPage extends StatelessWidget {
  const TasksPage({super.key});
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Task Tracker')),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _showAddDialog(context),
        child: const Icon(Icons.add),
      ),
      body: BlocBuilder<TasksCubit, TasksState>(
        builder: (context, state) => switch (state) {
          TasksInitial() || TasksLoading() => const Center(child: CircularProgressIndicator()),
          TasksFailure(:final message) => Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(message),
                  const SizedBox(height: 12),
                  FilledButton(
                    onPressed: () => context.read<TasksCubit>().load(),
                    child: const Text('Retry'),
                  ),
                ],
              ),
            ),
          TasksLoaded(:final tasks) => ListView(
              children: [
                for (final task in tasks)
                  ListTile(
                    leading: Icon(task.done ? Icons.check_circle : Icons.radio_button_unchecked),
                    title: Text(task.title),
                  ),
              ],
            ),
        },
      ),
    );
  }

  Future<void> _showAddDialog(BuildContext context) async {
    final cubit = context.read<TasksCubit>();
    var text = '';
    final title = await showDialog<String>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('New task'),
        content: TextField(autofocus: true, onChanged: (v) => text = v),
        actions: [
          TextButton(onPressed: () => Navigator.pop(dialogContext), child: const Text('Cancel')),
          FilledButton(onPressed: () => Navigator.pop(dialogContext, text), child: const Text('Add')),
        ],
      ),
    );
    if (title != null) await cubit.add(title);
  }
}

// ===== lib/app.dart and lib/main.dart (composition root) =====
void main() {
  runApp(App(taskRepository: InMemoryTaskRepository()));
}

class App extends StatelessWidget {
  const App({super.key, required this.taskRepository});
  final TaskRepository taskRepository;
  @override
  Widget build(BuildContext context) {
    return RepositoryProvider<TaskRepository>.value(
      value: taskRepository,
      child: MaterialApp(
        title: 'Task Tracker',
        theme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: Colors.teal)),
        home: BlocProvider(
          create: (context) => TasksCubit(context.read<TaskRepository>())..load(),
          child: const TasksPage(),
        ),
      ),
    );
  }
}
