import 'package:bloc/bloc.dart'; // plain Dart: no Flutter import in business logic
import 'package:equatable/equatable.dart';

// ---------- Model and states ----------
class Task extends Equatable {
  const Task({required this.id, required this.title, this.done = false});
  final int id;
  final String title;
  final bool done;
  Task copyWith({bool? done}) => Task(id: id, title: title, done: done ?? this.done);
  @override
  List<Object?> get props => [id, title, done];
}

enum TaskFilter { all, active, done }

sealed class TasksState extends Equatable {
  const TasksState();
  @override
  List<Object?> get props => [];
}

final class TasksLoading extends TasksState {
  const TasksLoading();
}

final class TasksLoadFailure extends TasksState {
  const TasksLoadFailure(this.message);
  final String message;
  @override
  List<Object?> get props => [message];
}

final class TasksLoaded extends TasksState {
  const TasksLoaded({required this.tasks, this.filter = TaskFilter.all, this.lastDeleted});
  final List<Task> tasks;
  final TaskFilter filter;
  final Task? lastDeleted; // set only by delete(); copyWith drops it

  List<Task> get visible => switch (filter) {
        TaskFilter.all => tasks,
        TaskFilter.active => tasks.where((t) => !t.done).toList(),
        TaskFilter.done => tasks.where((t) => t.done).toList(),
      };
  int get remaining => tasks.where((t) => !t.done).length;

  TasksLoaded copyWith({List<Task>? tasks, TaskFilter? filter}) =>
      TasksLoaded(tasks: tasks ?? this.tasks, filter: filter ?? this.filter);
  @override
  List<Object?> get props => [tasks, filter, lastDeleted];
}

// ---------- Cubit: all the rules, no widgets ----------
class TaskCubit extends Cubit<TasksState> {
  TaskCubit(this._loadTasks) : super(const TasksLoading());
  final Future<List<Task>> Function() _loadTasks;
  int _nextId = 100;

  Future<void> load() async {
    emit(const TasksLoading());
    try {
      final tasks = await _loadTasks();
      if (!isClosed) emit(TasksLoaded(tasks: tasks));
    } catch (_) {
      if (!isClosed) emit(const TasksLoadFailure('Could not load tasks'));
    }
  }

  void add(String title) {
    final s = state;
    final text = title.trim();
    if (s is! TasksLoaded || text.isEmpty) return;
    emit(s.copyWith(tasks: [...s.tasks, Task(id: _nextId++, title: text)]));
  }

  void toggle(int id) {
    final s = state;
    if (s is! TasksLoaded) return;
    emit(s.copyWith(tasks: [
      for (final t in s.tasks) t.id == id ? t.copyWith(done: !t.done) : t,
    ]));
  }

  void delete(int id) {
    final s = state;
    if (s is! TasksLoaded) return;
    final removed = s.tasks.where((t) => t.id == id).toList();
    if (removed.isEmpty) return;
    emit(TasksLoaded(
        tasks: s.tasks.where((t) => t.id != id).toList(),
        filter: s.filter,
        lastDeleted: removed.first));
  }

  void undoDelete() {
    final s = state;
    if (s is! TasksLoaded || s.lastDeleted == null) return;
    final tasks = [...s.tasks, s.lastDeleted!]..sort((a, b) => a.id.compareTo(b.id));
    emit(s.copyWith(tasks: tasks));
  }

  void setFilter(TaskFilter filter) {
    final s = state;
    if (s is TasksLoaded) emit(s.copyWith(filter: filter));
  }
}

Future<List<Task>> fakeLoad() async {
  await Future<void>.delayed(const Duration(milliseconds: 800)); // pretend storage
  return const [
    Task(id: 1, title: 'Buy milk'),
    Task(id: 2, title: 'Finish Flutter lesson', done: true),
    Task(id: 3, title: 'Call the plumber'),
  ];
}
