# Lesson 10.1 lab: a Drift database for TaskFlow

TaskFlow gets a real local database. Tasks and projects live in SQLite,
the list updates itself through watch() streams, and you perform your first
schema migration without losing data.

## Setup

1. Create the project (or use your TaskFlow project from module 9):

       flutter create taskflow
       cd taskflow
       flutter pub add drift drift_flutter dev:drift_dev dev:build_runner

2. Copy the files:
   - flutter/fl55/lib/main.dart            -> lib/main.dart (finished UI)
   - flutter/fl55/start/lib/data/app_database.dart -> lib/data/app_database.dart
3. Generate the code (creates lib/data/app_database.g.dart):

       dart run build_runner build -d

   Run it again after every change to tables or annotations. While you work
   you can leave "dart run build_runner watch -d" running instead.
4. Run on an Android or iOS emulator, or on desktop. (Drift also runs on
   the web, but that needs extra files in web/; see the Drift docs.)

## Your tasks (TODOs in app_database.dart)

1. watchTasks: a joined, ordered, filtered query that you watch().
2. watchOpenCount: a selectOnly count query that you watch.
3. addTask: insert with a companion.
4. toggleDone: update one row.
5. deleteDone: delete all done rows and return how many.
6. mergeProject: two statements in one transaction.
7. Migration to schema version 2. Do this LAST, after you have added a
   few tasks, so there is real data to keep:
   - add enum Priority and the priority column (see the comment),
   - set schemaVersion to 2,
   - add onUpgrade: if (from < 2) await m.addColumn(tasks, tasks.priority);
   - add the optional priority parameter to addTask,
   - run build_runner again, then stop and start the app (not hot reload).

## Test it (create test/app_database_test.dart)

    import 'package:drift/native.dart';
    import 'package:flutter_test/flutter_test.dart';
    import 'package:taskflow/data/app_database.dart';

    void main() {
      late AppDatabase db;
      setUp(() => db = AppDatabase(NativeDatabase.memory()));
      tearDown(() => db.close());

      test('a new task is open, normal priority and in the Inbox', () async {
        await db.taskDao.addTask('Write report', projectId: 1);
        final items = await db.taskDao.watchTasks().first;
        expect(items.single.task.done, isFalse);
        expect(items.single.task.priority, Priority.normal);
        expect(items.single.project?.name, 'Inbox');
      });

      test('mergeProject moves tasks and deletes the old project', () async {
        final work = await db.taskDao.addProject('Work');
        await db.taskDao.addTask('Plan sprint', projectId: work);
        await db.taskDao.mergeProject(fromId: work, intoId: 1);
        final items = await db.taskDao.watchTasks().first;
        expect(items.single.project?.name, 'Inbox');
      });
    }

Run it with: flutter test. The in-memory database needs the SQLite library
on your computer; if the test cannot load it, follow the testing page of
the Drift documentation. (Your package name must be taskflow for the import.)

## Acceptance criteria

- Adding three tasks shows them at once, newest first, with Inbox under each.
- Ticking a task moves it to the bottom with a line through it, and the
  title count goes down by one.
- Hide done removes ticked tasks; turning it off brings them back.
- The delete button removes all done tasks and the SnackBar shows how many.
- After the version 2 upgrade, tasks created before it are still there.
- flutter test reports All tests passed!