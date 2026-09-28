// Lab 6.3 starter: complete TODO(1) to TODO(4) here, then TODO(5) to TODO(7) in main.dart.
import 'package:bloc/bloc.dart'; // plain Dart: no Flutter import in business logic
import 'package:equatable/equatable.dart';

// ---------- Model and states ----------
class Task extends Equatable {
  const Task({required this.id, required this.title, this.done = false});
  final int id;
  final String title;
  final bool done;
  Task copyWith({bool? done}) => Task(id: id, title: title, done: done ?? this.done);
  // TODO(1): with only id in props, a task and its toggled copy are "equal", so
  //          the Cubit ignores the new state and the checkbox seems dead.
  //          Include every field: [id, title, done].
  @override
  List<Object?> get props => [id];
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
    // TODO(2): emit TasksLoading, await _loadTasks(), then emit TasksLoaded.
    //          On an exception emit TasksLoadFailure('Could not load tasks').
    //          Check isClosed before emitting after the await.
  }

  void add(String title) {
    // TODO(3): if the state is TasksLoaded and the trimmed title is not empty,
    //          emit a copy whose tasks list is a NEW list: [...s.tasks, newTask].
    //          Use Task(id: _nextId++, title: text).
  }

  void toggle(int id) {
    // TODO(4): emit a copy with a new list where the matching task has done flipped.
  }

  void delete(int id) {
    // TODO(4): emit TasksLoaded without the task, keeping the filter and setting
    //          lastDeleted to the removed task (the UI listens for this).
  }

  void undoDelete() {
    // TODO(4): put lastDeleted back (sorted by id) and emit.
  }

  void setFilter(TaskFilter filter) {
    // TODO(4): emit a copy with the new filter.
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
