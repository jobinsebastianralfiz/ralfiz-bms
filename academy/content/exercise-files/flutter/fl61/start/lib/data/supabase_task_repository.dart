import 'package:supabase_flutter/supabase_flutter.dart';

// ---------------- domain (normally lib/features/tasks/domain) ----------------
class Task {
  const Task({required this.id, required this.projectId, required this.title,
      required this.done, required this.createdAt});
  final String id;
  final String projectId;
  final String title;
  final bool done;
  final DateTime createdAt;

  Task copyWith({bool? done}) => Task(id: id, projectId: projectId, title: title,
      done: done ?? this.done, createdAt: createdAt);
}

sealed class TaskFailure implements Exception {
  const TaskFailure(this.message);
  final String message;
  @override
  String toString() => message;
}

class NotAllowed extends TaskFailure {
  const NotAllowed() : super('You are not allowed to do that.');
}

class ServerFailure extends TaskFailure {
  const ServerFailure(super.message);
}

abstract interface class TaskRepository {
  Future<String> inboxProjectId();
  Future<List<Task>> fetchPage(String projectId, {required int page, int pageSize});
  Future<Task> add(String projectId, String title);
  Future<void> setDone(String id, bool done);
  Future<void> delete(String id);
}

// ---------------- data (normally lib/features/tasks/data) ----------------
class SupabaseTaskRepository implements TaskRepository {
  SupabaseTaskRepository(this._db);
  final SupabaseClient _db;
  static const _columns = 'id, project_id, title, done, created_at';

  // TODO(1): build a Task from a row. created_at arrives as an ISO string,
  // so use DateTime.parse(row['created_at'] as String).
  static Task _fromRow(Map<String, dynamic> row) => throw UnimplementedError('TODO(1)');

  // TODO(1): wrap body in try/catch. On PostgrestException:
  // code '42501' -> throw const NotAllowed(); otherwise ServerFailure(e.message).
  Future<T> _guard<T>(Future<T> Function() body) => body();

  // TODO(2): select('id') from projects, eq name 'Inbox', limit 1.
  // If found, return its id. Otherwise insert {'name': 'Inbox'},
  // chain .select('id').single() and return the new id.
  // Do NOT filter by owner: RLS does it.
  @override
  Future<String> inboxProjectId() => _guard(() async {
        throw UnimplementedError('TODO(2) ' + _db.toString());
      });

  // TODO(2): from = page * pageSize, to = from + pageSize - 1 (inclusive).
  // select(_columns), eq project_id, order created_at descending, range.
  @override
  Future<List<Task>> fetchPage(String projectId, {required int page, int pageSize = 20}) =>
      _guard(() async {
        throw UnimplementedError('TODO(2) ' + _columns);
      });

  // TODO(3): insert {'project_id': ..., 'title': ...}, then
  // .select(_columns).single(), and return _fromRow(row).
  @override
  Future<Task> add(String projectId, String title) => _guard(() async {
        return _fromRow(const {});
      });

  // TODO(3): update {'done': done}, eq id, .select('id').
  // An empty list means RLS hid the row: throw const NotAllowed().
  @override
  Future<void> setDone(String id, bool done) => _guard(() async {
        throw UnimplementedError('TODO(3)');
      });

  // TODO(3): delete(), eq id, .select('id'); empty list -> NotAllowed.
  @override
  Future<void> delete(String id) => _guard(() async {
        throw UnimplementedError('TODO(3)');
      });
}
