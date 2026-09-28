// Lesson 9.5 starter. Works, but every dependency is created inside the cubit.
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

// TODO(1): add enum AppEnv { dev, staging, prod } and class AppConfig with
// env, apiBaseUrl, isProd and a factory AppConfig.fromEnvironment() that reads
// const String.fromEnvironment('ENV') and ('API_BASE_URL').

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

class RemoteTaskRepository {
  // TODO(2): take an ApiClient in the constructor instead of building Dio here.
  final _dio = Dio(BaseOptions(baseUrl: 'https://dummyjson.com'));

  Future<List<Task>> fetchTasks() async {
    final response = await _dio.get<Map<String, dynamic>>('/todos',
        queryParameters: {'limit': 20, 'skip': 0});
    final list = response.data?['todos'] as List<dynamic>? ?? const [];
    return [for (final e in list) Task.fromJson(e as Map<String, dynamic>)];
  }
}

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
  // TODO(2): receive a TaskRepository (an interface) through the constructor.
  TasksCubit() : super(const TasksLoading());
  final _repository = RemoteTaskRepository();

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

// TODO(3): final getIt = GetIt.instance; and
// void setupDependencies(AppConfig config, {TaskRepository? taskRepository})

void main() {
  // TODO(4): call setupDependencies(AppConfig.fromEnvironment()) first.
  runApp(const App());
}

class App extends StatelessWidget {
  const App({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      theme: ThemeData(colorSchemeSeed: const Color(0xFF00897B)),
      home: Scaffold(
        appBar: AppBar(title: const Text('TaskFlow')),
        // TODO(5): show an environment banner above the list when not prod.
        body: BlocProvider(
          // TODO(4): create the cubit with getIt<TasksCubit>()..load()
          create: (_) => TasksCubit()..load(),
          child: const TasksView(),
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
        TasksFailure(:final message) => Center(child: Text(message)),
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
