import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:get_it/get_it.dart';

import 'features/tasks/data/tasks_data.dart';
import 'features/tasks/domain/tasks_domain.dart';

// ---------- Composition root: the only place that knows concrete classes ----------
final getIt = GetIt.instance;

void setupDependencies() {
  getIt
    ..registerLazySingleton<Dio>(() => Dio(BaseOptions(
          baseUrl: 'https://dummyjson.com',
          connectTimeout: const Duration(seconds: 10),
          receiveTimeout: const Duration(seconds: 10),
        )))
    ..registerLazySingleton<TaskRemoteDataSource>(
        () => TaskRemoteDataSource(getIt()))
    ..registerLazySingleton<TaskRepository>(() => TaskRepositoryImpl(getIt()))
    ..registerLazySingleton<AuthRepository>(() => const DemoAuthRepository(152))
    ..registerFactory<GetMyTasks>(() => GetMyTasks(getIt(), getIt()))
    ..registerFactory<TasksCubit>(() => TasksCubit(getIt(), getIt()));
}

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  setupDependencies();
  runApp(MaterialApp(
    theme: ThemeData(colorSchemeSeed: const Color(0xFF5E35B1)),
    home: BlocProvider(
      create: (_) => getIt<TasksCubit>()..load(),
      child: const TasksPage(),
    ),
  ));
}

// ---------- features/tasks/presentation/failure_message.dart ----------
/// The only place that turns a failure into words (as in lesson 9.3).
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

// ---------- features/tasks/presentation/tasks_cubit.dart ----------
sealed class TasksState {
  const TasksState();
}

final class TasksLoading extends TasksState {
  const TasksLoading();
}

final class TasksLoaded extends TasksState {
  const TasksLoaded(this.tasks, {this.notice});
  final List<Task> tasks;
  final String? notice; // one-off message for a SnackBar
}

final class TasksError extends TasksState {
  const TasksError(this.message);
  final String message;
}

class TasksCubit extends Cubit<TasksState> {
  TasksCubit(this._getMyTasks, this._tasks) : super(const TasksLoading());
  final GetMyTasks _getMyTasks;
  final TaskRepository _tasks;

  Future<void> load() async {
    emit(const TasksLoading());
    final result = await _getMyTasks();
    if (isClosed) return;
    emit(switch (result) {
      Ok(:final value) => TasksLoaded(value),
      Err(:final failure) => TasksError(failureMessage(failure)),
    });
  }

  Future<void> toggle(Task task, bool completed) async {
    final current = state;
    if (current is! TasksLoaded) return;
    final result = await _tasks.setCompleted(task, completed);
    if (isClosed) return;
    switch (result) {
      case Ok(:final value):
        final updated = [
          for (final t in current.tasks) t.id == value.id ? value : t,
        ];
        emit(TasksLoaded(GetMyTasks.sortOpenFirst(updated)));
      case Err(:final failure):
        emit(TasksLoaded(current.tasks, notice: failureMessage(failure)));
    }
  }
}

// ---------- features/tasks/presentation/tasks_page.dart ----------
class TasksPage extends StatelessWidget {
  const TasksPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('My tasks')),
      body: BlocConsumer<TasksCubit, TasksState>(
        listener: (context, state) {
          if (state is TasksLoaded && state.notice != null) {
            ScaffoldMessenger.of(context)
                .showSnackBar(SnackBar(content: Text(state.notice!)));
          }
        },
        builder: (context, state) => switch (state) {
          TasksLoading() => const Center(child: CircularProgressIndicator()),
          TasksError(:final message) => ErrorView(
              message: message,
              onRetry: () => context.read<TasksCubit>().load(),
            ),
          TasksLoaded(:final tasks) when tasks.isEmpty =>
            const Center(child: Text('No tasks yet.')),
          TasksLoaded(:final tasks) => RefreshIndicator(
              onRefresh: () => context.read<TasksCubit>().load(),
              child: ListView(
                children: [
                  for (final task in tasks)
                    CheckboxListTile(
                      value: task.isCompleted,
                      title: Text(task.title),
                      onChanged: (v) =>
                          context.read<TasksCubit>().toggle(task, v ?? false),
                    ),
                ],
              ),
            ),
        },
      ),
    );
  }
}

class ErrorView extends StatelessWidget {
  const ErrorView({super.key, required this.message, required this.onRetry});
  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        spacing: 12,
        children: [
          const Icon(Icons.cloud_off, size: 48),
          Text(message),
          FilledButton.icon(
            onPressed: onRetry,
            icon: const Icon(Icons.refresh),
            label: const Text('Retry'),
          ),
        ],
      ),
    );
  }
}
