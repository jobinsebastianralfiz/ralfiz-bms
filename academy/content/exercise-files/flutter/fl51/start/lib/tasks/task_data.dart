// TaskFlow - lesson 9.3: typed failures, Result<T> and the task repository.
// lib/tasks/task_data.dart. This file is complete and is the same in the solution.
import 'package:equatable/equatable.dart';

import '../api/api_client.dart';

// ------------------------------ failures ------------------------------
sealed class Failure extends Equatable {
  const Failure();
  @override
  List<Object?> get props => [];
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
  @override
  List<Object?> get props => [statusCode];
}

final class UnknownFailure extends Failure {
  const UnknownFailure();
}

/// The only place that turns a failure into words for the user.
String failureMessage(Failure failure) => switch (failure) {
      NetworkFailure() => 'You are offline. Check your connection.',
      TimeoutFailure() => 'The server is slow right now. Try again.',
      UnauthorizedFailure() => 'Please sign in again.',
      CancelledFailure() => 'Cancelled.',
      ServerFailure(statusCode: final int code) when code >= 500 =>
        'TaskFlow is having trouble. Try again soon.',
      ServerFailure() => 'That request did not work.',
      UnknownFailure() => 'Something went wrong.',
    };

Failure failureFromException(AppException e) => switch (e) {
      NetworkException() => const NetworkFailure(),
      RequestTimeoutException() => const TimeoutFailure(),
      UnauthorizedException() => const UnauthorizedFailure(),
      CancelledException() => const CancelledFailure(),
      ServerException(:final statusCode) => ServerFailure(statusCode),
      UnknownException() => const UnknownFailure(),
    };

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

/// Runs [body] and converts expected errors into Err.
Future<Result<T>> guard<T>(Future<T> Function() body) async {
  try {
    return Ok(await body());
  } on AppException catch (e) {
    return Err(failureFromException(e));
  } on FormatException {
    // Not const: Err<T> uses the type parameter T.
    return Err(const UnknownFailure()); // the JSON was not what we expected
  }
}

// ------------------------------ models ------------------------------
class Task extends Equatable {
  const Task({required this.id, required this.title, required this.completed});

  factory Task.fromJson(Map<String, dynamic> json) {
    if (json case {'id': final int id, 'todo': final String title, 'completed': final bool done}) {
      return Task(id: id, title: title, completed: done);
    }
    throw FormatException('Unexpected task JSON: $json');
  }

  final int id;
  final String title;
  final bool completed;

  @override
  List<Object?> get props => [id, title, completed];
}

class TaskPage {
  const TaskPage({required this.tasks, required this.total, required this.skip});

  factory TaskPage.fromJson(Map<String, dynamic> json) {
    if (json case {'todos': final List<dynamic> items, 'total': final int total, 'skip': final int skip}) {
      return TaskPage(
        tasks: [for (final item in items) Task.fromJson(item as Map<String, dynamic>)],
        total: total,
        skip: skip,
      );
    }
    throw const FormatException('Unexpected page JSON');
  }

  final List<Task> tasks;
  final int total;
  final int skip;

  bool get hasMore => skip + tasks.length < total;
}

// ------------------------------ repository ------------------------------
abstract interface class TaskRepository {
  Future<Result<TaskPage>> fetchTasks({
    required int skip,
    required int limit,
    bool forceRefresh = false,
  });
}

class ApiTaskRepository implements TaskRepository {
  ApiTaskRepository(this._api, {this.ttl = const Duration(minutes: 2)});

  final ApiClient _api;
  final Duration ttl;

  /// A tiny in-memory cache: key "skip:limit" -> page and the time it arrived.
  final _cache = <String, ({TaskPage page, DateTime at})>{};

  @override
  Future<Result<TaskPage>> fetchTasks({
    required int skip,
    required int limit,
    bool forceRefresh = false,
  }) async {
    if (forceRefresh) _cache.clear();
    final key = '$skip:$limit';
    final cached = _cache[key];
    if (cached != null && DateTime.now().difference(cached.at) < ttl) {
      return Ok(cached.page);
    }
    final result = await guard(() async {
      final json = await _api.get<Map<String, dynamic>>(
        '/auth/todos',
        query: {'skip': skip, 'limit': limit},
      );
      return TaskPage.fromJson(json);
    });
    if (result case Ok(value: final page)) {
      _cache[key] = (page: page, at: DateTime.now());
    }
    return result;
  }
}
