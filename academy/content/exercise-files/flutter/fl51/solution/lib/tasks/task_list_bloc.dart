// TaskFlow - lesson 9.3 (SOLUTION)
// lib/tasks/task_list_bloc.dart: events, state and the paginated TaskListBloc.
import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import 'task_data.dart';

// ------------------------------ events ------------------------------
sealed class TaskListEvent {
  const TaskListEvent();
}

final class TaskListStarted extends TaskListEvent {
  const TaskListStarted();
}

final class TaskListNextPageRequested extends TaskListEvent {
  const TaskListNextPageRequested();
}

final class TaskListRefreshed extends TaskListEvent {
  const TaskListRefreshed();
}

// ------------------------------ state ------------------------------
enum LoadStatus { initial, loading, success, failure }

class TaskListState extends Equatable {
  const TaskListState({
    this.status = LoadStatus.initial,
    this.tasks = const [],
    this.hasReachedMax = false,
    this.isLoadingMore = false,
    this.isRefreshing = false,
    this.failure,
  });

  final LoadStatus status;
  final List<Task> tasks;
  final bool hasReachedMax;
  final bool isLoadingMore;
  final bool isRefreshing;
  final Failure? failure; // the latest error, if any

  TaskListState copyWith({
    LoadStatus? status,
    List<Task>? tasks,
    bool? hasReachedMax,
    bool? isLoadingMore,
    bool? isRefreshing,
    Failure? Function()? failure, // a function, so we can set null
  }) =>
      TaskListState(
        status: status ?? this.status,
        tasks: tasks ?? this.tasks,
        hasReachedMax: hasReachedMax ?? this.hasReachedMax,
        isLoadingMore: isLoadingMore ?? this.isLoadingMore,
        isRefreshing: isRefreshing ?? this.isRefreshing,
        failure: failure != null ? failure() : this.failure,
      );

  @override
  List<Object?> get props =>
      [status, tasks, hasReachedMax, isLoadingMore, isRefreshing, failure];
}

// ------------------------------ bloc ------------------------------
class TaskListBloc extends Bloc<TaskListEvent, TaskListState> {
  TaskListBloc(this._repository, {this.pageSize = 20})
      : super(const TaskListState()) {
    on<TaskListStarted>(_onStarted);
    on<TaskListNextPageRequested>(_onNextPage);
    on<TaskListRefreshed>(_onRefreshed);
  }

  final TaskRepository _repository;
  final int pageSize;

  Future<void> _onStarted(TaskListStarted e, Emitter<TaskListState> emit) async {
    emit(state.copyWith(status: LoadStatus.loading, failure: () => null));
    await _loadFirstPage(emit, forceRefresh: false);
  }

  Future<void> _onRefreshed(
      TaskListRefreshed e, Emitter<TaskListState> emit) async {
    // Always emits true then false, so the page can wait for "false".
    emit(state.copyWith(isRefreshing: true, failure: () => null));
    await _loadFirstPage(emit, forceRefresh: true);
  }

  Future<void> _loadFirstPage(Emitter<TaskListState> emit,
      {required bool forceRefresh}) async {
    final result = await _repository.fetchTasks(
        skip: 0, limit: pageSize, forceRefresh: forceRefresh);
    switch (result) {
      case Ok(value: final page):
        emit(TaskListState(
            status: LoadStatus.success,
            tasks: page.tasks,
            hasReachedMax: !page.hasMore));
      case Err(:final failure):
        // Keep what we already show; only an empty list becomes an error page.
        emit(state.copyWith(
            status: state.tasks.isEmpty ? LoadStatus.failure : LoadStatus.success,
            isRefreshing: false,
            failure: () => failure));
    }
  }

  Future<void> _onNextPage(
      TaskListNextPageRequested e, Emitter<TaskListState> emit) async {
    // Guard: one page at a time, and nothing after the last page.
    if (state.status != LoadStatus.success ||
        state.isLoadingMore ||
        state.hasReachedMax) {
      return;
    }
    emit(state.copyWith(isLoadingMore: true, failure: () => null));
    final result = await _repository.fetchTasks(
        skip: state.tasks.length, limit: pageSize);
    switch (result) {
      case Ok(value: final page):
        emit(state.copyWith(
            tasks: [...state.tasks, ...page.tasks],
            hasReachedMax: !page.hasMore,
            isLoadingMore: false));
      case Err(:final failure):
        emit(state.copyWith(isLoadingMore: false, failure: () => failure));
    }
  }
}
