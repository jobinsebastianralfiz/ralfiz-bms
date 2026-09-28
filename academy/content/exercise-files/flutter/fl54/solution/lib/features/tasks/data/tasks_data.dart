import 'package:dio/dio.dart';

import '../domain/tasks_domain.dart';

/// Mirrors DummyJSON's todo JSON exactly. In your project you can generate
/// this with freezed and json_serializable (lesson 9.4).
class TaskDto {
  const TaskDto({
    required this.id,
    required this.todo,
    required this.completed,
    required this.userId,
  });

  factory TaskDto.fromJson(Map<String, dynamic> json) => TaskDto(
        id: json['id'] as int,
        todo: json['todo'] as String,
        completed: json['completed'] as bool? ?? false,
        userId: json['userId'] as int,
      );

  final int id;
  final String todo;
  final bool completed;
  final int userId;
}

/// Mapper: API model -> domain entity.
extension TaskDtoMapper on TaskDto {
  Task toEntity() => Task(
        id: id,
        title: todo.trim(),
        isCompleted: completed,
        ownerId: userId,
      );
}

/// Talks to one source only: the DummyJSON REST API.
class TaskRemoteDataSource {
  TaskRemoteDataSource(this._dio);
  final Dio _dio;

  Future<List<TaskDto>> fetchForUser(int userId) async {
    final path = '/todos/user/$userId';
    final response = await _dio.get<Map<String, dynamic>>(path);
    final list = response.data?['todos'] as List<dynamic>? ?? const [];
    return [
      for (final item in list) TaskDto.fromJson(item as Map<String, dynamic>),
    ];
  }

  /// Returns the completed flag the server stored.
  Future<bool> updateCompleted(int id, bool completed) async {
    final path = '/todos/$id';
    final response = await _dio.put<Map<String, dynamic>>(
      path,
      data: {'completed': completed},
    );
    return response.data?['completed'] as bool? ?? completed;
  }
}

/// DioException -> domain Failure. Only the data layer knows about Dio.
Failure failureFromDio(DioException e) => switch (e.type) {
      DioExceptionType.connectionError => const NetworkFailure(),
      DioExceptionType.connectionTimeout ||
      DioExceptionType.sendTimeout ||
      DioExceptionType.receiveTimeout =>
        const TimeoutFailure(),
      DioExceptionType.cancel => const CancelledFailure(),
      DioExceptionType.badResponse => e.response?.statusCode == 401
          ? const UnauthorizedFailure()
          : ServerFailure(e.response?.statusCode),
      _ => const UnknownFailure(), // badCertificate, unknown, future types
    };

class TaskRepositoryImpl implements TaskRepository {
  TaskRepositoryImpl(this._remote);
  final TaskRemoteDataSource _remote;

  @override
  Future<Result<List<Task>>> tasksForUser(int userId) => _guard(() async {
        final dtos = await _remote.fetchForUser(userId);
        return [for (final dto in dtos) dto.toEntity()];
      });

  @override
  Future<Result<Task>> setCompleted(Task task, bool completed) =>
      _guard(() async {
        final saved = await _remote.updateCompleted(task.id, completed);
        return task.copyWith(isCompleted: saved);
      });

  Future<Result<T>> _guard<T>(Future<T> Function() body) async {
    try {
      return Ok(await body());
    } on DioException catch (e) {
      return Err(failureFromDio(e));
    } catch (_) {
      // Parsing errors (TypeError, FormatException) end up here.
      // Not const: Err<T> uses the type parameter T.
      return Err(const UnknownFailure());
    }
  }
}

/// Stands in for the real AuthRepository from lesson 9.2, which would ask
/// /auth/me for the signed-in user's id.
class DemoAuthRepository implements AuthRepository {
  const DemoAuthRepository(this.userId);
  final int userId;

  @override
  Future<int> currentUserId() async => userId;
}
