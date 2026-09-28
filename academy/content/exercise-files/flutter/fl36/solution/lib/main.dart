import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import 'task_cubit.dart';

/// Logs every state change of every Cubit or Bloc in the app.
class AppObserver extends BlocObserver {
  const AppObserver();
  @override
  void onChange(BlocBase<dynamic> bloc, Change<dynamic> change) {
    super.onChange(bloc, change);
    final name = bloc.runtimeType;
    debugPrint('$name $change');
  }
}

void main() {
  Bloc.observer = const AppObserver();
  runApp(MaterialApp(
    theme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: Colors.green)),
    home: BlocProvider(
      create: (context) => TaskCubit(fakeLoad)..load(),
      child: const TaskPage(),
    ),
  ));
}

class TaskPage extends StatelessWidget {
  const TaskPage({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocListener<TaskCubit, TasksState>(
      // Side effects (snack bars, navigation) belong in a listener, not a builder.
      listenWhen: (previous, current) => current is TasksLoaded && current.lastDeleted != null,
      listener: (context, state) {
        if (state case TasksLoaded(lastDeleted: final Task deleted)) {
          final title = deleted.title;
          ScaffoldMessenger.of(context)
            ..hideCurrentSnackBar()
            ..showSnackBar(SnackBar(
              content: Text('Deleted $title'),
              action: SnackBarAction(
                  label: 'Undo', onPressed: () => context.read<TaskCubit>().undoDelete()),
            ));
        }
      },
      child: Scaffold(
        appBar: AppBar(title: const Text('Task Tracker')),
        body: BlocBuilder<TaskCubit, TasksState>(
          builder: (context, state) => switch (state) {
            TasksLoading() => const Center(child: CircularProgressIndicator()),
            TasksLoadFailure(:final message) => Center(
                child: Column(mainAxisSize: MainAxisSize.min, spacing: 12, children: [
                  Text(message),
                  FilledButton(
                      onPressed: () => context.read<TaskCubit>().load(),
                      child: const Text('Retry')),
                ]),
              ),
            TasksLoaded loaded => TaskList(state: loaded),
          },
        ),
      ),
    );
  }
}

class TaskList extends StatelessWidget {
  const TaskList({super.key, required this.state});
  final TasksLoaded state;

  @override
  Widget build(BuildContext context) {
    final cubit = context.read<TaskCubit>();
    final visible = state.visible;
    final left = state.remaining;
    final noun = left == 1 ? 'task' : 'tasks';
    return Column(children: [
      const Padding(padding: EdgeInsets.fromLTRB(16, 16, 16, 8), child: NewTaskField()),
      SegmentedButton<TaskFilter>(
        segments: const [
          ButtonSegment(value: TaskFilter.all, label: Text('All')),
          ButtonSegment(value: TaskFilter.active, label: Text('Active')),
          ButtonSegment(value: TaskFilter.done, label: Text('Done')),
        ],
        selected: {state.filter},
        onSelectionChanged: (selection) => cubit.setFilter(selection.first),
      ),
      Expanded(
        child: visible.isEmpty
            ? const Center(child: Text('No tasks here'))
            : ListView(children: [
                for (final t in visible)
                  ListTile(
                    leading: Checkbox(value: t.done, onChanged: (_) => cubit.toggle(t.id)),
                    title: Text(t.title),
                    trailing: IconButton(
                        icon: const Icon(Icons.delete_outline),
                        onPressed: () => cubit.delete(t.id)),
                  ),
              ]),
      ),
      Padding(padding: const EdgeInsets.all(16), child: Text('$left $noun left')),
    ]);
  }
}

class NewTaskField extends StatefulWidget {
  const NewTaskField({super.key});
  @override
  State<NewTaskField> createState() => _NewTaskFieldState();
}

class _NewTaskFieldState extends State<NewTaskField> {
  final _controller = TextEditingController(); // UI state stays in the widget

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _submit() {
    context.read<TaskCubit>().add(_controller.text);
    _controller.clear();
  }

  @override
  Widget build(BuildContext context) {
    return Row(spacing: 8, children: [
      Expanded(
        child: TextField(
          controller: _controller,
          decoration: const InputDecoration(hintText: 'New task', border: OutlineInputBorder()),
          textInputAction: TextInputAction.done,
          onSubmitted: (_) => _submit(),
        ),
      ),
      IconButton.filled(icon: const Icon(Icons.add), onPressed: _submit),
    ]);
  }
}
