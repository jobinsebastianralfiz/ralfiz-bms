// Lesson 8.3 lab - write the tests marked TODO, then run: flutter test
// ignore: unused_import
import 'package:bloc_test/bloc_test.dart'; // used once you write TODO(2)-(4)
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:tasks_app/main.dart';

class MockTaskRepository extends Mock implements TaskRepository {}

void main() {
  group('summary', () {
    test('counts open tasks', () {
      // TODO(1): expect '2 tasks left' for [Task('a'), Task('b', done: true), Task('c')].
      // Then add a second test for '1 task left' and 'All done!'.
      expect(summary(const []), 'All done!');
    });
  });

  group('TasksCubit', () {
    late MockTaskRepository repo;
    setUp(() => repo = MockTaskRepository());

    test('starts in TasksInitial', () {
      expect(TasksCubit(repo).state, const TasksInitial());
    });

    // TODO(2): blocTest<TasksCubit, TasksState> - load success:
    //   setUp: stub fetchTasks with thenAnswer((_) async => const [Task('Test me')])
    //   expect: [TasksLoading(), TasksLoaded([Task('Test me')])]
    //   verify: fetchTasks called once

    // TODO(3): blocTest - load failure (thenThrow) emits
    //   [TasksLoading(), TasksError('Could not load tasks')]

    // TODO(4): blocTest - seed TasksLoaded([Task('a')]), act add('  b  '),
    //   expect [TasksLoaded([Task('a'), Task('b')])]
  });

  group('TasksPage', () {
    testWidgets('shows a spinner first', (tester) async {
      final repo = MockTaskRepository();
      when(() => repo.fetchTasks()).thenAnswer((_) async => const [Task('Buy milk')]);
      await tester.pumpWidget(TasksApp(repository: repo));
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
      await tester.pumpAndSettle();
      // TODO(5): expect 'Buy milk' and '1 task left'; enterText 'Walk dog' into
      // Key('newTask'), tap Key('addTask'), pump, expect '2 tasks left';
      // tap 'Buy milk', pump, expect '1 task left'.
    });

    // TODO(6): testWidgets - fetchTasks throws; after pumpAndSettle expect
    // 'Could not load tasks' and 'Retry'.
  });
}
