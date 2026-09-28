import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:get_it/get_it.dart';

// ---------- Configuration ----------
enum AppEnv { dev, staging, prod }

class AppConfig {
  const AppConfig({required this.env, required this.apiBaseUrl});

  factory AppConfig.fromEnvironment() {
    const envName = String.fromEnvironment('ENV', defaultValue: 'dev');
    const baseUrl = String.fromEnvironment('API_BASE_URL',
        defaultValue: 'https://dummyjson.com');
    return AppConfig(env: AppEnv.values.byName(envName), apiBaseUrl: baseUrl);
  }

  final AppEnv env;
  final String apiBaseUrl;
  bool get isProd => env == AppEnv.prod;
}

// ---------- Data ----------
class Task {
  const Task({required this.id, required this.title, required this.completed});
  final int id;
  final String title;
  final bool completed;

  factory Task.fromJson(Map<String, dynamic> json) => Task(
        id: json['id'] as int,
        title: json['todo'] as String,
        completed: json['completed'] as bool? ?? false,
      );
}

/// A slimmed-down stand-in for the ApiClient from lesson 9.1, with the same
/// constructor: ApiClient(httpClient: dio).
class ApiClient {
  ApiClient({required Dio httpClient}) : _dio = httpClient;
  final Dio _dio;

  Future<Map<String, dynamic>> getJson(String path,
      {Map<String, dynamic>? query}) async {
    final response =
        await _dio.get<Map<String, dynamic>>(path, queryParameters: query);
    return response.data ?? const {};
  }
}

abstract interface class TaskRepository {
  Future<List<Task>> fetchTasks();
}

class RemoteTaskRepository implements TaskRepository {
  RemoteTaskRepository(this._api);
  final ApiClient _api;

  @override
  Future<List<Task>> fetchTasks() async {
    final json = await _api.getJson('/todos', query: {'limit': 20, 'skip': 0});
    final list = json['todos'] as List<dynamic>? ?? const [];
    return [for (final e in list) Task.fromJson(e as Map<String, dynamic>)];
  }
}

// ---------- Presentation logic ----------
sealed class TasksState {
  const TasksState();
}

final class TasksLoading extends TasksState {
  const TasksLoading();
}

final class TasksLoaded extends TasksState {
  const TasksLoaded(this.tasks);
  final List<Task> tasks;
}

final class TasksFailure extends TasksState {
  const TasksFailure(this.message);
  final String message;
}

class TasksCubit extends Cubit<TasksState> {
  TasksCubit(this._repository) : super(const TasksLoading());
  final TaskRepository _repository;

  Future<void> load() async {
    emit(const TasksLoading());
    try {
      final tasks = await _repository.fetchTasks();
      if (!isClosed) emit(TasksLoaded(tasks));
    } catch (_) {
      if (!isClosed) emit(const TasksFailure('Could not load tasks.'));
    }
  }
}

// ---------- Composition root ----------
final getIt = GetIt.instance;

void setupDependencies(AppConfig config, {TaskRepository? taskRepository}) {
  getIt
    ..registerSingleton<AppConfig>(config)
    ..registerLazySingleton<Dio>(() => Dio(BaseOptions(
          baseUrl: config.apiBaseUrl,
          connectTimeout: const Duration(seconds: 10),
          receiveTimeout: const Duration(seconds: 10),
        )))
    ..registerLazySingleton<ApiClient>(() => ApiClient(httpClient: getIt<Dio>()))
    ..registerLazySingleton<TaskRepository>(
        () => taskRepository ?? RemoteTaskRepository(getIt<ApiClient>()))
    // A factory: BlocProvider closes each cubit it creates.
    ..registerFactory<TasksCubit>(() => TasksCubit(getIt<TaskRepository>()));
}

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  setupDependencies(AppConfig.fromEnvironment());
  runApp(const App());
}

// ---------- UI ----------
class App extends StatelessWidget {
  const App({super.key});

  @override
  Widget build(BuildContext context) {
    final config = getIt<AppConfig>();
    final envName = config.env.name.toUpperCase();
    final baseUrl = config.apiBaseUrl;
    return MaterialApp(
      theme: ThemeData(colorSchemeSeed: const Color(0xFF00897B)),
      home: Scaffold(
        appBar: AppBar(title: const Text('TaskFlow')),
        body: Column(
          children: [
            if (!config.isProd)
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(8),
                color: Colors.amber.shade200,
                child: Text('$envName · $baseUrl'),
              ),
            Expanded(
              child: BlocProvider(
                create: (_) => getIt<TasksCubit>()..load(),
                child: const TasksView(),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class TasksView extends StatelessWidget {
  const TasksView({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<TasksCubit, TasksState>(
      builder: (context, state) => switch (state) {
        TasksLoading() => const Center(child: CircularProgressIndicator()),
        TasksFailure(:final message) => Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              spacing: 12,
              children: [
                Text(message),
                FilledButton(
                  onPressed: () => context.read<TasksCubit>().load(),
                  child: const Text('Retry'),
                ),
              ],
            ),
          ),
        TasksLoaded(:final tasks) => ListView(
            children: [
              for (final t in tasks)
                ListTile(
                  leading: Icon(t.completed
                      ? Icons.check_circle
                      : Icons.radio_button_unchecked),
                  title: Text(t.title),
                ),
            ],
          ),
      },
    );
  }
}
