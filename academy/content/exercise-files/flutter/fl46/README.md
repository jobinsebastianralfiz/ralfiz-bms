# Lesson 8.3 lab: test the Tasks app

The app (lib/main.dart) is finished. Your job is to write its tests.

## Setup

    flutter create tasks_app
    cd tasks_app
    flutter pub add flutter_bloc equatable
    flutter pub add dev:bloc_test dev:mocktail

Copy lib/main.dart from this folder over lib/main.dart, delete the default
test/widget_test.dart, and copy start/test/tasks_test.dart into test/.
The package name must be tasks_app (the tests import package:tasks_app/main.dart).

## Tasks (TODOs in test/tasks_test.dart)

- TODO(1) Unit tests for summary(): "2 tasks left", "1 task left", "All done!".
- TODO(2) blocTest: load() emits [TasksLoading(), TasksLoaded([...])] and
  calls fetchTasks exactly once.
- TODO(3) blocTest: load() emits [TasksLoading(), TasksError('Could not load tasks')]
  when fetchTasks throws.
- TODO(4) blocTest: with seed TasksLoaded([Task('a')]), add('  b  ') emits
  TasksLoaded([Task('a'), Task('b')]).
- TODO(5) Widget test: spinner first, then "Buy milk" and "1 task left";
  add "Walk dog" -> "2 tasks left"; tap "Buy milk" -> "1 task left".
- TODO(6) Widget test: when fetchTasks throws, the screen shows
  "Could not load tasks" and a "Retry" button.

Run: flutter test

## Optional: integration test

1. In pubspec.yaml under dev_dependencies add:

       integration_test:
         sdk: flutter

2. Create integration_test/app_test.dart:

       import 'package:flutter/material.dart';
       import 'package:flutter_test/flutter_test.dart';
       import 'package:integration_test/integration_test.dart';
       import 'package:tasks_app/main.dart';

       void main() {
         IntegrationTestWidgetsFlutterBinding.ensureInitialized();

         testWidgets('add a task end to end', (tester) async {
           await tester.pumpWidget(TasksApp(repository: InMemoryTaskRepository()));
           await tester.pumpAndSettle();
           await tester.enterText(find.byKey(const Key('newTask')), 'Ship it');
           await tester.tap(find.byKey(const Key('addTask')));
           await tester.pumpAndSettle();
           expect(find.text('Ship it'), findsOneWidget);
         });
       }

3. Start an emulator and run: flutter test integration_test

## Acceptance criteria

- flutter test reports All tests passed! with 7 tests.
- Changing '1 task left' to '1 tasks left' in lib/main.dart makes exactly
  the summary test and the page test fail. Change it back afterwards.
- The optional integration test passes on an emulator.
