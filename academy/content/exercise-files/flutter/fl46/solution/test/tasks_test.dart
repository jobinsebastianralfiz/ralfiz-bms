import 'package:bloc_test/bloc_test.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:tasks_app/main.dart';

class MockTaskRepository extends Mock implements TaskRepository {}

void main() {
  group('summary', () {
    test('counts open tasks', () {
      expect(summary(const [Task('a'), Task('b', done: true), Task('c')]), '2 tasks left');
    });

    test('uses singular and celebrates zero', () {
      expect(summary(const [Task('a')]), '1 task left');
      expect(summary(const [Task('a', done: true)]), 'All done!');
    });
  });

  group('TasksCubit', () {
    late MockTaskRepository repo;
    setUp(() => repo = MockTaskRepository());

    blocTest<TasksCubit, TasksState>(
      'load emits [loading, loaded] on success',
      setUp: () => when(() => repo.fetchTasks()).thenAnswer((_) async => const [Task('Test me')]),
      build: () => TasksCubit(repo),
      act: (cubit) => cubit.load(),
      expect: () => const [TasksLoading(), TasksLoaded([Task('Test me')])],
      verify: (_) => verify(() => repo.fetchTasks()).called(1),
    );

    blocTest<TasksCubit, TasksState>(
      'load emits [loading, error] when the repository throws',
      setUp: () => when(() => repo.fetchTasks()).thenThrow(Exception('offline')),
      build: () => TasksCubit(repo),
      act: (cubit) => cubit.load(),
      expect: () => const [TasksLoading(), TasksError('Could not load tasks')],
    );

    blocTest<TasksCubit, TasksState>(
      'add appends a trimmed task',
      build: () => TasksCubit(repo),
      seed: () => const TasksLoaded([Task('a')]),
      act: (cubit) => cubit.add('  b  '),
      expect: () => const [TasksLoaded([Task('a'), Task('b')])],
    );
  });

  group('TasksPage', () {
    testWidgets('shows tasks, adds one and toggles it', (tester) async {
      final repo = MockTaskRepository();
      when(() => repo.fetchTasks()).thenAnswer((_) async => const [Task('Buy milk')]);

      await tester.pumpWidget(TasksApp(repository: repo));
      expect(find.byType(CircularProgressIndicator), findsOneWidget);

      await tester.pumpAndSettle();
      expect(find.text('Buy milk'), findsOneWidget);
      expect(find.text('1 task left'), findsOneWidget);

      await tester.enterText(find.byKey(const Key('newTask')), 'Walk dog');
      await tester.tap(find.byKey(const Key('addTask')));
      await tester.pump();
      expect(find.text('Walk dog'), findsOneWidget);
      expect(find.text('2 tasks left'), findsOneWidget);

      await tester.tap(find.text('Buy milk'));
      await tester.pump();
      expect(find.text('1 task left'), findsOneWidget);
    });

    testWidgets('shows Retry when loading fails', (tester) async {
      final repo = MockTaskRepository();
      when(() => repo.fetchTasks()).thenThrow(Exception('offline'));

      await tester.pumpWidget(TasksApp(repository: repo));
      await tester.pumpAndSettle();

      expect(find.text('Could not load tasks'), findsOneWidget);
      expect(find.widgetWithText(TextButton, 'Retry'), findsOneWidget);
    });
  });
}
