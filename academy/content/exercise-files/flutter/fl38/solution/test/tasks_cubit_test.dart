import 'package:bloc_test/bloc_test.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:task_tracker/main.dart';

// A fake is a tiny hand-written implementation of the interface.
class FakeTaskRepository implements TaskRepository {
  FakeTaskRepository({this.fail = false});
  final bool fail;
  final List<Task> tasks = [const Task(id: 1, title: 'Write tests')];

  @override
  Future<List<Task>> fetchTasks() async {
    if (fail) throw Exception('offline');
    return List.of(tasks);
  }

  @override
  Future<Task> addTask(String title) async {
    final task = Task(id: tasks.length + 1, title: title);
    tasks.add(task);
    return task;
  }
}

void main() {
  group('TasksCubit', () {
    test('starts in TasksInitial', () {
      expect(TasksCubit(FakeTaskRepository()).state, const TasksInitial());
    });

    blocTest<TasksCubit, TasksState>(
      'load emits loading, then the tasks from the repository',
      build: () => TasksCubit(FakeTaskRepository()),
      act: (cubit) => cubit.load(),
      expect: () => const [
        TasksLoading(),
        TasksLoaded([Task(id: 1, title: 'Write tests')]),
      ],
    );

    blocTest<TasksCubit, TasksState>(
      'load emits a failure when the repository throws',
      build: () => TasksCubit(FakeTaskRepository(fail: true)),
      act: (cubit) => cubit.load(),
      expect: () => const [
        TasksLoading(),
        TasksFailure('Could not load tasks.'),
      ],
    );

    blocTest<TasksCubit, TasksState>(
      'add saves the task and emits the new list',
      build: () => TasksCubit(FakeTaskRepository()),
      act: (cubit) => cubit.add('  Ship it  '),
      expect: () => const [
        TasksLoaded([
          Task(id: 1, title: 'Write tests'),
          Task(id: 2, title: 'Ship it'),
        ]),
      ],
    );

    blocTest<TasksCubit, TasksState>(
      'add ignores a blank title',
      build: () => TasksCubit(FakeTaskRepository()),
      act: (cubit) => cubit.add('   '),
      expect: () => const <TasksState>[],
    );
  });
}
