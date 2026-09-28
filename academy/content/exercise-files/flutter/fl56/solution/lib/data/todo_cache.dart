import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:hive_ce/hive_ce.dart';

// SOLUTION - lesson 10.2: a Hive CE response cache and a cache-then-network
// repository for TaskFlow todos (https://dummyjson.com/todos).

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
    // Read fields in exactly the order write() wrote them.
    final body = reader.readString();
    final millis = reader.readInt();
    return CachedResponse(
        body: body, savedAt: DateTime.fromMillisecondsSinceEpoch(millis));
  }

  @override
  void write(BinaryWriter writer, CachedResponse obj) {
    writer.writeString(obj.body);
    writer.writeInt(obj.savedAt.millisecondsSinceEpoch);
  }
}

class CacheStore {
  CacheStore._(this._box);
  final Box<CachedResponse> _box;

  static Future<CacheStore> open() async {
    if (!Hive.isAdapterRegistered(1)) {
      Hive.registerAdapter(CachedResponseAdapter());
    }
    final box = await Hive.openBox<CachedResponse>('api_cache');
    return CacheStore._(box);
  }

  CachedResponse? read(String key) => _box.get(key);

  Future<void> write(String key, Object? json) => _box.put(
      key, CachedResponse(body: jsonEncode(json), savedAt: DateTime.now()));

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

  /// Cache-then-network: emit the cached copy at once (if any), then fetch
  /// from the network unless the copy is still fresh and [force] is false.
  Stream<TodosResult> watchTodos({bool force = false}) async* {
    final cached = _cache.read(_key);
    if (cached != null) {
      yield TodosResult(_parse(cached.body),
          fromCache: true, savedAt: cached.savedAt);
      if (!force && cached.age < ttl) return;
    }
    try {
      final res = await _dio.get<String>('/todos',
          queryParameters: {'limit': 20},
          options: Options(responseType: ResponseType.plain));
      final body = res.data!;
      final todos = _parse(body); // parse first: never cache a broken body
      await _cache.write(_key, jsonDecode(body));
      yield TodosResult(todos, fromCache: false, savedAt: DateTime.now());
    } on DioException {
      if (cached == null) rethrow; // nothing to show: let the UI show the error
      yield TodosResult(_parse(cached.body),
          fromCache: true,
          savedAt: cached.savedAt,
          warning: 'Offline: showing saved data');
    }
  }
}