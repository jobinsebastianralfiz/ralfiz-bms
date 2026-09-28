import 'package:bloc_test/bloc_test.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:task_tracker/main.dart';

// SOLUTION tests - lesson 6.4. Run with: flutter test
void main() {
  group('TaskBloc', () {
    test('starts with no tasks', () {
      expect(TaskBloc().state, const TaskState());
    });

    blocTest<TaskBloc, TaskState>(
      'adds tasks with increasing ids',
      build: TaskBloc.new,
      act: (bloc) => bloc
        ..add(const TaskAdded('Buy milk'))
        ..add(const TaskAdded('Call Asha')),
      expect: () => const [
        TaskState(tasks: [Task(id: 1, title: 'Buy milk')]),
        TaskState(tasks: [
          Task(id: 1, title: 'Buy milk'),
          Task(id: 2, title: 'Call Asha'),
        ]),
      ],
    );

    blocTest<TaskBloc, TaskState>(
      'ignores blank titles',
      build: TaskBloc.new,
      act: (bloc) => bloc.add(const TaskAdded('   ')),
      expect: () => const <TaskState>[],
    );

    blocTest<TaskBloc, TaskState>(
      'toggles a task',
      build: TaskBloc.new,
      seed: () => const TaskState(tasks: [Task(id: 1, title: 'Buy milk')]),
      act: (bloc) => bloc.add(const TaskToggled(1)),
      expect: () => const [
        TaskState(tasks: [Task(id: 1, title: 'Buy milk', done: true)]),
      ],
    );

    blocTest<TaskBloc, TaskState>(
      'deletes a task and remembers it for the SnackBar',
      build: TaskBloc.new,
      seed: () => const TaskState(tasks: [Task(id: 1, title: 'Buy milk')]),
      act: (bloc) => bloc.add(const TaskDeleted(1)),
      expect: () => const [
        TaskState(tasks: [], lastDeleted: Task(id: 1, title: 'Buy milk')),
      ],
    );

    blocTest<TaskBloc, TaskState>(
      'does nothing when the id does not exist',
      build: TaskBloc.new,
      act: (bloc) => bloc.add(const TaskDeleted(42)),
      expect: () => const <TaskState>[],
    );
  });

  group('FilterCubit', () {
    blocTest<FilterCubit, TaskFilter>(
      'selects the done filter',
      build: FilterCubit.new,
      act: (cubit) => cubit.select(TaskFilter.done),
      expect: () => const [TaskFilter.done],
    );
  });
}
