// TaskFlow - lesson 9.3: the task list page (infinite scroll, pull-to-refresh).
// lib/tasks/task_list_page.dart. This file is complete and is the same in the solution.
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import 'task_data.dart';
import 'task_list_bloc.dart';

class TaskListPage extends StatefulWidget {
  const TaskListPage({super.key});
  @override
  State<TaskListPage> createState() => _TaskListPageState();
}

class _TaskListPageState extends State<TaskListPage> {
  final _scroll = ScrollController();

  @override
  void initState() {
    super.initState();
    _scroll.addListener(_onScroll);
  }

  void _onScroll() {
    final bloc = context.read<TaskListBloc>();
    final pos = _scroll.position;
    // Near the end, and no failed page waiting for a manual retry.
    if (pos.pixels >= pos.maxScrollExtent - 300 && bloc.state.failure == null) {
      bloc.add(const TaskListNextPageRequested());
    }
  }

  @override
  void dispose() {
    _scroll.dispose();
    super.dispose();
  }

  Future<void> _refresh() async {
    final bloc = context.read<TaskListBloc>()..add(const TaskListRefreshed());
    // RefreshIndicator keeps spinning until this Future completes.
    await bloc.stream.firstWhere((s) => !s.isRefreshing);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Tasks')),
      body: BlocConsumer<TaskListBloc, TaskListState>(
        // Only a failed refresh: the end of a refresh with a failure set.
        listenWhen: (prev, curr) =>
            prev.isRefreshing && !curr.isRefreshing && curr.failure != null,
        listener: (context, state) => ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(failureMessage(state.failure!)))),
        builder: (context, state) => switch (state.status) {
          LoadStatus.initial || LoadStatus.loading =>
            const Center(child: CircularProgressIndicator()),
          LoadStatus.failure => Center(
              child: Column(mainAxisSize: MainAxisSize.min, spacing: 12, children: [
                const Icon(Icons.cloud_off, size: 48),
                Text(failureMessage(state.failure!)),
                FilledButton(
                  onPressed: () => context.read<TaskListBloc>().add(const TaskListStarted()),
                  child: const Text('Retry'),
                ),
              ]),
            ),
          LoadStatus.success => RefreshIndicator(
              onRefresh: _refresh,
              child: ListView.builder(
                controller: _scroll,
                physics: const AlwaysScrollableScrollPhysics(),
                itemCount: state.tasks.length + 1,
                itemBuilder: (context, i) =>
                    i < state.tasks.length ? _TaskTile(state.tasks[i]) : _Footer(state),
              ),
            ),
        },
      ),
    );
  }
}

class _TaskTile extends StatelessWidget {
  const _TaskTile(this.task);
  final Task task;
  @override
  Widget build(BuildContext context) => ListTile(
        leading: Icon(task.completed ? Icons.check_circle : Icons.radio_button_unchecked),
        title: Text(task.title),
      );
}

class _Footer extends StatelessWidget {
  const _Footer(this.state);
  final TaskListState state;
  @override
  Widget build(BuildContext context) {
    final Widget child;
    if (state.hasReachedMax) {
      child = const Text('You are all caught up');
    } else if (state.failure != null && !state.isLoadingMore) {
      child = TextButton.icon(
        onPressed: () => context.read<TaskListBloc>().add(const TaskListNextPageRequested()),
        icon: const Icon(Icons.refresh),
        label: const Text('Could not load more. Retry'),
      );
    } else {
      child = const CircularProgressIndicator();
    }
    return Padding(padding: const EdgeInsets.all(16), child: Center(child: child));
  }
}
