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

  static Task _fromRow(Map<String, dynamic> row) => Task(
        id: row['id'] as String,
        projectId: row['project_id'] as String,
        title: row['title'] as String,
        done: row['done'] as bool,
        createdAt: DateTime.parse(row['created_at'] as String),
      );

  Future<T> _guard<T>(Future<T> Function() body) async {
    try {
      return await body();
    } on PostgrestException catch (e) {
      if (e.code == '42501') throw const NotAllowed(); // RLS rejected a write
      throw ServerFailure(e.message);
    }
  }

  @override
  Future<String> inboxProjectId() => _guard(() async {
        // No owner filter: RLS only returns this user's projects.
        final rows = await _db.from('projects').select('id').eq('name', 'Inbox').limit(1);
        if (rows.isNotEmpty) return rows.first['id'] as String;
        final created = await _db.from('projects').insert({'name': 'Inbox'}).select('id').single();
        return created['id'] as String;
      });

  @override
  Future<List<Task>> fetchPage(String projectId, {required int page, int pageSize = 20}) =>
      _guard(() async {
        final from = page * pageSize;
        final to = from + pageSize - 1; // range() is inclusive
        final rows = await _db
            .from('tasks')
            .select(_columns)
            .eq('project_id', projectId)
            .order('created_at', ascending: false)
            .range(from, to);
        return rows.map(_fromRow).toList();
      });

  @override
  Future<Task> add(String projectId, String title) => _guard(() async {
        // user_id is filled by the column default auth.uid().
        final row = await _db
            .from('tasks')
            .insert({'project_id': projectId, 'title': title})
            .select(_columns)
            .single();
        return _fromRow(row);
      });

  @override
  Future<void> setDone(String id, bool done) => _guard(() async {
        final rows = await _db.from('tasks').update({'done': done}).eq('id', id).select('id');
        if (rows.isEmpty) throw const NotAllowed(); // not found or hidden by RLS
      });

  @override
  Future<void> delete(String id) => _guard(() async {
        final rows = await _db.from('tasks').delete().eq('id', id).select('id');
        if (rows.isEmpty) throw const NotAllowed();
      });
}
