import 'package:freezed_annotation/freezed_annotation.dart';

part 'task.freezed.dart';
part 'task.g.dart';

// Run: dart run build_runner build -d
// The two part files above are generated. Do not edit them.

enum TaskPriority {
  @JsonValue('low')
  low,
  @JsonValue('normal')
  normal,
  @JsonValue('high')
  high,
}

@freezed
abstract class Task with _$Task {
  // Private constructor: needed because we add our own getter below.
  const Task._();

  const factory Task({
    required int id,
    @JsonKey(name: 'todo') required String title,
    @Default(false) bool completed,
    required int userId,
    @JsonKey(unknownEnumValue: TaskPriority.normal)
    @Default(TaskPriority.normal)
    TaskPriority priority,
    DateTime? dueDate,
  }) = _Task;

  factory Task.fromJson(Map<String, dynamic> json) => _$TaskFromJson(json);

  bool get isOverdue {
    final due = dueDate;
    return !completed && due != null && due.isBefore(DateTime.now());
  }
}

/// One page of GET /todos?limit=...&skip=... from DummyJSON.
@freezed
abstract class TodosPage with _$TodosPage {
  const TodosPage._();

  const factory TodosPage({
    required List<Task> todos,
    required int total,
    required int skip,
    required int limit,
  }) = _TodosPage;

  factory TodosPage.fromJson(Map<String, dynamic> json) =>
      _$TodosPageFromJson(json);

  bool get hasMore => skip + todos.length < total;
}

/// Screen state as a freezed union. No JSON needed here.
@freezed
sealed class TasksState with _$TasksState {
  const factory TasksState.loading() = TasksLoading;
  const factory TasksState.loaded(List<Task> tasks) = TasksLoaded;
  const factory TasksState.failure(String message) = TasksFailure;
}

String describeState(TasksState state) => switch (state) {
      TasksLoading() => 'Loading',
      TasksLoaded(:final tasks) => 'Tasks: ' + tasks.length.toString(),
      TasksFailure(:final message) => 'Error: ' + message,
    };
