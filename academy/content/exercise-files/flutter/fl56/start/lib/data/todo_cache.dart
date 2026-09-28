import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:hive_ce/hive_ce.dart';

// STARTER - lesson 10.2: a Hive CE response cache for TaskFlow todos.
// It runs as it is, but every start goes to the network and nothing is
// saved, so the list is empty (with an error) when you are offline.

class Todo {
  const Todo({required this.id, required this.title, required this.done});
  final int id;
  final String title;
  final bool done;

  factory Todo.fromJson(Map<String, dynamic> json) => Todo(
        id: json['id'] as int,
        title: json['todo'] as String,
        done: json['completed'] as bool,
      );
}

/// One cached API response: the raw JSON text and when it was saved.
class CachedResponse {
  const CachedResponse({required this.body, required this.savedAt});
  final String body;
  final DateTime savedAt;

  Duration get age => DateTime.now().difference(savedAt);
}

/// Tells Hive how to turn a CachedResponse into bytes and back.
class CachedResponseAdapter extends TypeAdapter<CachedResponse> {
  @override
  final int typeId = 1; // unique per app and never reused

  @override
  CachedResponse read(BinaryReader reader) {
    // TODO(1): read the body with reader.readString(), then the time with
    // reader.readInt() (milliseconds since epoch), in the same order as write.
    throw UnimplementedError('TODO(1)');
  }

  @override
  void write(BinaryWriter writer, CachedResponse obj) {
    // TODO(2): writer.writeString(obj.body), then
    // writer.writeInt(obj.savedAt.millisecondsSinceEpoch).
  }
}

class CacheStore {
  CacheStore._(this._box);
  final Box<CachedResponse> _box;

  static Future<CacheStore> open() async {
    // TODO(3): register CachedResponseAdapter (only if typeId 1 is not
    // registered yet), before opening the box.
    final box = await Hive.openBox<CachedResponse>('api_cache');
    return CacheStore._(box);
  }

  // TODO(4): return _box.get(key).
  CachedResponse? read(String key) => null;

  Future<void> write(String key, Object? json) async {
    // TODO(5): put a CachedResponse with jsonEncode(json) and DateTime.now().
  }

  int get length => _box.length;

  /// Call this on logout: cached data belongs to the signed-in user.
  Future<void> clear() => _box.clear();
}

/// What the UI shows: the todos plus where they came from.
class TodosResult {
  const TodosResult(this.todos,
      {required this.fromCache, required this.savedAt, this.warning});
  final List<Todo> todos;
  final bool fromCache;
  final DateTime savedAt;
  final String? warning;
}

class TodoRepository {
  TodoRepository(this._dio, this._cache);
  final Dio _dio;
  final CacheStore _cache;

  static const _key = 'GET /todos?limit=20';
  static const ttl = Duration(minutes: 5);

  static List<Todo> _parse(String body) {
    final json = jsonDecode(body) as Map<String, dynamic>;
    return (json['todos'] as List)
        .map((e) => Todo.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Stream<TodosResult> watchTodos({bool force = false}) async* {
    // TODO(6): read the cache first. If there is a copy, yield it with
    // fromCache: true, and stop here when it is younger than ttl and
    // force is false.
    final res = await _dio.get<String>('/todos',
        queryParameters: {'limit': 20},
        options: Options(responseType: ResponseType.plain));
    final body = res.data!;
    final todos = _parse(body);
    // TODO(7): save the response with _cache.write(_key, jsonDecode(body)).
    yield TodosResult(todos, fromCache: false, savedAt: DateTime.now());
    // TODO(8): wrap the network part in try/on DioException. When it fails
    // and there is a cached copy, yield it again with
    // warning: 'Offline: showing saved data'. With no copy, rethrow.
  }
}