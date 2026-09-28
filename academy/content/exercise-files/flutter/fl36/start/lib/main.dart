import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import 'task_cubit.dart';

// Lab 6.3 starter: finish task_cubit.dart first, then TODO(5) to TODO(7) below.
// Setup: flutter create task_tracker, flutter pub add flutter_bloc bloc equatable,
// copy this file and task_cubit.dart into lib/.

// TODO(5): write an AppObserver extends BlocObserver that overrides onChange and
//          debugPrints the change, and set Bloc.observer = const AppObserver().

void main() {
  runApp(MaterialApp(
    theme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: Colors.green)),
    // TODO(5): wrap TaskPage in BlocProvider(create: (context) => TaskCubit(fakeLoad)..load()).
    home: const TaskPage(),
  ));
}

class TaskPage extends StatelessWidget {
  const TaskPage({super.key});

  @override
  Widget build(BuildContext context) {
    // TODO(7): wrap the Scaffold in a BlocListener<TaskCubit, TasksState> that shows
    //          a SnackBar 'Deleted <title>' with an Undo action when lastDeleted is set.
    return Scaffold(
      appBar: AppBar(title: const Text('Task Tracker')),
      // TODO(6): replace this with a BlocBuilder<TaskCubit, TasksState> whose builder
      //          switches on the state: loading spinner, error with Retry, or TaskList.
      body: const Center(child: Text('Connect the TaskCubit (TODO 5 and 6)')),
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
