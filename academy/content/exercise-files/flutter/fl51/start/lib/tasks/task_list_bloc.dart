// TaskFlow - lesson 9.3 (STARTER)
// It compiles as it is. Complete TODO(1) to TODO(4).
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
    // TODO(4): emit isRefreshing: true (and clear the failure) BEFORE
    // loading, so the page can wait for a state with isRefreshing == false.
    await _loadFirstPage(emit, forceRefresh: true);
  }

  Future<void> _loadFirstPage(Emitter<TaskListState> emit,
      {required bool forceRefresh}) async {
    final result = await _repository.fetchTasks(
        skip: 0, limit: pageSize, forceRefresh: forceRefresh);
    // TODO(1): switch on result.
    //   Ok(value: final page) -> emit a NEW TaskListState with status success,
    //     tasks: page.tasks and hasReachedMax: !page.hasMore.
    //   Err(:final failure) -> keep the current tasks; status becomes failure
    //     only when the list is empty; set isRefreshing: false and failure.
    if (result case Ok(value: final page)) {
      emit(TaskListState(status: LoadStatus.success, tasks: page.tasks));
    }
  }

  Future<void> _onNextPage(
      TaskListNextPageRequested e, Emitter<TaskListState> emit) async {
    // TODO(2): return early unless status is success, no page is loading
    // and hasReachedMax is false. Without this guard, every scroll tick near
    // the bottom starts another request.

    // TODO(3): emit isLoadingMore: true (clear the failure), fetch with
    // skip: state.tasks.length and limit: pageSize, then either append
    // page.tasks and update hasReachedMax, or keep the list and store the
    // failure. Always set isLoadingMore back to false.
    final result = await _repository.fetchTasks(
        skip: state.tasks.length, limit: pageSize);
    if (result case Ok(value: final page)) {
      emit(state.copyWith(tasks: [...state.tasks, ...page.tasks]));
    }
  }
}
