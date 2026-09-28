import 'package:bloc_test/bloc_test.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:task_tracker/main.dart';

// STARTER tests - lesson 6.4. Run with: flutter test
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

    // TODO(6): write a blocTest that seeds one task, adds TaskToggled(1)
    // and expects the same task with done: true.

    // TODO(7): write a blocTest that seeds one task, adds TaskDeleted(1)
    // and expects an empty list with lastDeleted set to that task.
  });
}
