// Lesson 9.4 starter: hand-written models. This file compiles as it is.
// Your job: replace them with freezed + json_serializable (TODO 1 to 6).

// TODO(1): import package:freezed_annotation/freezed_annotation.dart
// TODO(2): add the part directives: part 'task.freezed.dart'; part 'task.g.dart';

// TODO(4): add enum TaskPriority { low, normal, high } with @JsonValue('low')
// and so on, then a priority field on Task that defaults to normal and uses
// normal for unknown values (@Default + @JsonKey(unknownEnumValue: ...)).

class Task {
  const Task({
    required this.id,
    required this.title,
    this.completed = false,
    required this.userId,
    this.dueDate,
  });

  // TODO(3): turn Task into
  //   @freezed abstract class Task with _$Task { const factory Task({...}) = _Task; }
  // Use @JsonKey(name: 'todo') for title and @Default(false) for completed.

  final int id;
  final String title;
  final bool completed;
  final int userId;
  final DateTime? dueDate;

  factory Task.fromJson(Map<String, dynamic> json) {
    final due = json['dueDate'] as String?;
    return Task(
      id: json['id'] as int,
      title: json['todo'] as String,
      completed: json['completed'] as bool? ?? false,
      userId: json['userId'] as int,
      dueDate: due == null ? null : DateTime.parse(due),
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'todo': title,
        'completed': completed,
        'userId': userId,
        'dueDate': dueDate?.toIso8601String(),
      };

  // BUG 1: dueDate ?? this.dueDate means you can never clear the date.
  Task copyWith({
    int? id,
    String? title,
    bool? completed,
    int? userId,
    DateTime? dueDate,
  }) {
    return Task(
      id: id ?? this.id,
      title: title ?? this.title,
      completed: completed ?? this.completed,
      userId: userId ?? this.userId,
      dueDate: dueDate ?? this.dueDate,
    );
  }

  // BUG 2: userId and dueDate are missing from == and hashCode.
  @override
  bool operator ==(Object other) =>
      other is Task &&
      other.id == id &&
      other.title == title &&
      other.completed == completed;

  @override
  int get hashCode => Object.hash(id, title, completed);

  // TODO(5): with a private const Task._() constructor, add
  //   bool get isOverdue => not completed, has a dueDate, and dueDate is before now.
}

class TodosPage {
  const TodosPage({
    required this.todos,
    required this.total,
    required this.skip,
    required this.limit,
  });

  // TODO(5): convert TodosPage to freezed as well (List<Task> todos, total, skip, limit).

  final List<Task> todos;
  final int total;
  final int skip;
  final int limit;

  factory TodosPage.fromJson(Map<String, dynamic> json) => TodosPage(
        todos: [
          for (final item in json['todos'] as List<dynamic>)
            Task.fromJson(item as Map<String, dynamic>),
        ],
        total: json['total'] as int,
        skip: json['skip'] as int,
        limit: json['limit'] as int,
      );

  Map<String, dynamic> toJson() => {
        'todos': [for (final t in todos) t.toJson()],
        'total': total,
        'skip': skip,
        'limit': limit,
      };
}

// TODO(6): add a sealed freezed union
//   TasksState.loading() = TasksLoading
//   TasksState.loaded(List<Task> tasks) = TasksLoaded
//   TasksState.failure(String message) = TasksFailure
