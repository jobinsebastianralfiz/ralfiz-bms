// Domain layer: pure Dart. No Flutter, no Dio, no JSON.
// Result and Failure are the ones from lesson 9.3 (task_data.dart). In a bigger
// app they live in lib/core/. Lesson 9.3's Failure extends Equatable; here it
// stays import-free, so the domain file has no dependencies at all.

// ------------------------------ failures ------------------------------
// The data layer says WHAT went wrong; the UI decides how to say it
// (failureMessage in main.dart).
sealed class Failure {
  const Failure();
}

final class NetworkFailure extends Failure {
  const NetworkFailure();
}

final class TimeoutFailure extends Failure {
  const TimeoutFailure();
}

final class UnauthorizedFailure extends Failure {
  const UnauthorizedFailure();
}

final class CancelledFailure extends Failure {
  const CancelledFailure();
}

final class ServerFailure extends Failure {
  const ServerFailure(this.statusCode);
  final int? statusCode;
}

final class UnknownFailure extends Failure {
  const UnknownFailure();
}

// ------------------------------ Result ------------------------------
sealed class Result<T> {
  const Result();
}

final class Ok<T> extends Result<T> {
  const Ok(this.value);
  final T value;
}

final class Err<T> extends Result<T> {
  const Err(this.failure);
  final Failure failure;
}

/// The business idea of a task, independent of any API or database.
class Task {
  const Task({
    required this.id,
    required this.title,
    required this.isCompleted,
    required this.ownerId,
  });

  final int id;
  final String title;
  final bool isCompleted;
  final int ownerId;

  Task copyWith({bool? isCompleted}) => Task(
        id: id,
        title: title,
        isCompleted: isCompleted ?? this.isCompleted,
        ownerId: ownerId,
      );

  @override
  bool operator ==(Object other) =>
      other is Task &&
      other.id == id &&
      other.title == title &&
      other.isCompleted == isCompleted &&
      other.ownerId == ownerId;

  @override
  int get hashCode => Object.hash(id, title, isCompleted, ownerId);
}

/// Contracts the domain needs. The data layer implements them.
abstract interface class TaskRepository {
  Future<Result<List<Task>>> tasksForUser(int userId);
  Future<Result<Task>> setCompleted(Task task, bool completed);
}

/// A slice of the AuthRepository from lesson 9.2.
abstract interface class AuthRepository {
  Future<int> currentUserId();
}

/// Use case: combines two repositories and owns the "open first" rule.
class GetMyTasks {
  GetMyTasks(this._auth, this._tasks);
  final AuthRepository _auth;
  final TaskRepository _tasks;

  Future<Result<List<Task>>> call() async {
    final userId = await _auth.currentUserId();
    final result = await _tasks.tasksForUser(userId);
    return switch (result) {
      Ok(:final value) => Ok(sortOpenFirst(value)),
      Err() => result,
    };
  }

  /// Open tasks first, then alphabetical by title.
  static List<Task> sortOpenFirst(List<Task> tasks) => [...tasks]
    ..sort((a, b) => a.isCompleted == b.isCompleted
        ? a.title.compareTo(b.title)
        : (a.isCompleted ? 1 : -1));
}

// No ToggleTask use case on purpose: it would only forward
// TaskRepository.setCompleted. The cubit calls the repository directly.
