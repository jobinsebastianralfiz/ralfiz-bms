import 'package:equatable/equatable.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

void main() => runApp(const TaskApp());

class Task extends Equatable {
  const Task({required this.id, required this.title, this.done = false});
  final int id;
  final String title;
  final bool done;
  Task copyWith({bool? done}) => Task(id: id, title: title, done: done ?? this.done);
  @override
  List<Object?> get props => [id, title, done];
}

sealed class TaskEvent {
  const TaskEvent();
}
final class TaskAdded extends TaskEvent {
  const TaskAdded(this.title);
  final String title;
}
final class TaskToggled extends TaskEvent {
  const TaskToggled(this.id);
  final int id;
}
final class TaskDeleted extends TaskEvent {
  const TaskDeleted(this.id);
  final int id;
}

class TaskState extends Equatable {
  const TaskState({this.tasks = const [], this.lastDeleted});
  final List<Task> tasks;
  final Task? lastDeleted;
  @override
  List<Object?> get props => [tasks, lastDeleted];
}

class TaskBloc extends Bloc<TaskEvent, TaskState> {
  TaskBloc() : super(const TaskState()) {
    on<TaskAdded>(_onAdded);
    on<TaskToggled>(_onToggled);
    on<TaskDeleted>(_onDeleted);
  }

  int _nextId = 1;
  void _onAdded(TaskAdded event, Emitter<TaskState> emit) {
    final title = event.title.trim();
    if (title.isEmpty) return;
    final task = Task(id: _nextId++, title: title);
    emit(TaskState(tasks: [...state.tasks, task]));
  }

  void _onToggled(TaskToggled event, Emitter<TaskState> emit) {
    emit(TaskState(tasks: [
      for (final t in state.tasks)
        t.id == event.id ? t.copyWith(done: !t.done) : t,
    ]));
  }

  void _onDeleted(TaskDeleted event, Emitter<TaskState> emit) {
    final removed = state.tasks.where((t) => t.id == event.id).firstOrNull;
    if (removed == null) return;
    emit(TaskState(
      tasks: [for (final t in state.tasks) if (t.id != event.id) t],
      lastDeleted: removed,
    ));
  }
}

enum TaskFilter { all, active, done }

class FilterCubit extends Cubit<TaskFilter> {
  FilterCubit() : super(TaskFilter.all);
  void select(TaskFilter filter) => emit(filter);
}

class TaskApp extends StatelessWidget {
  const TaskApp({super.key});
  @override
  Widget build(BuildContext context) {
    return MultiBlocProvider(
      providers: [BlocProvider(create: (_) => TaskBloc()), BlocProvider(create: (_) => FilterCubit())],
      child: MaterialApp(
        title: 'Task Tracker',
        theme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: Colors.indigo)),
        home: const TaskPage(),
      ),
    );
  }
}

class TaskPage extends StatefulWidget {
  const TaskPage({super.key});
  @override
  State<TaskPage> createState() => _TaskPageState();
}

class _TaskPageState extends State<TaskPage> {
  final _controller = TextEditingController();
  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _add() {
    context.read<TaskBloc>().add(TaskAdded(_controller.text));
    _controller.clear();
  }

  @override
  Widget build(BuildContext context) {
    final filter = context.watch<FilterCubit>().state;
    return Scaffold(
      appBar: AppBar(title: const Text('Task Tracker')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(12),
            child: TextField(
              controller: _controller,
              decoration: InputDecoration(
                labelText: 'New task',
                suffixIcon: IconButton(icon: const Icon(Icons.add), onPressed: _add),
              ),
              onSubmitted: (_) => _add(),
            ),
          ),
          SegmentedButton<TaskFilter>(
            segments: const [
              ButtonSegment(value: TaskFilter.all, label: Text('All')),
              ButtonSegment(value: TaskFilter.active, label: Text('Active')),
              ButtonSegment(value: TaskFilter.done, label: Text('Done')),
            ],
            selected: {filter},
            onSelectionChanged: (s) => context.read<FilterCubit>().select(s.first),
          ),
          Expanded(
            child: BlocConsumer<TaskBloc, TaskState>(
              listenWhen: (prev, curr) =>
                  curr.lastDeleted != null && curr.lastDeleted != prev.lastDeleted,
              listener: (context, state) {
                final title = state.lastDeleted!.title;
                ScaffoldMessenger.of(context)
                  ..hideCurrentSnackBar()
                  ..showSnackBar(SnackBar(content: Text('Deleted "$title"')));
              },
              builder: (context, state) {
                final visible = switch (filter) {
                  TaskFilter.all => state.tasks,
                  TaskFilter.active => [for (final t in state.tasks) if (!t.done) t],
                  TaskFilter.done => [for (final t in state.tasks) if (t.done) t],
                };
                if (visible.isEmpty) return const Center(child: Text('No tasks here yet'));
                return ListView(children: [
                    for (final task in visible)
                      CheckboxListTile(
                        controlAffinity: ListTileControlAffinity.leading,
                        value: task.done,
                        title: Text(task.title),
                        onChanged: (_) => context.read<TaskBloc>().add(TaskToggled(task.id)),
                        secondary: IconButton(
                          icon: const Icon(Icons.delete_outline),
                          onPressed: () => context.read<TaskBloc>().add(TaskDeleted(task.id)),
                        ),
                      ),
                ]);
              },
            ),
          ),
        ],
      ),
    );
  }
}
