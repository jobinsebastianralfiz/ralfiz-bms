# Lesson 6.5 lab: Task Tracker, layered

## Goal
Refactor start/lib/main.dart (everything inside one StatefulWidget) into
presentation, domain and data layers, inject the repository, and prove the
logic with unit tests that use a fake repository.

## Target folder layout (feature-first)

    lib/
      main.dart                  composition root: builds real dependencies
      app.dart                   App widget, RepositoryProvider, theme
      features/
        tasks/
          domain/
            task.dart            Task model (Equatable)
            task_repository.dart abstract interface class TaskRepository
          data/
            in_memory_task_repository.dart
          presentation/
            tasks_cubit.dart     TasksState (sealed) + TasksCubit
            tasks_page.dart      UI only: BlocBuilder + switch
    test/
      tasks_cubit_test.dart      FakeTaskRepository + blocTests

You may keep everything in one file first (the solution does, so it can be
pasted in one go) and then split it using the section headers.

## Rules
- Widgets never create repositories or call Future.delayed themselves.
- TasksCubit only knows the TaskRepository interface, never a concrete class.
- The domain folder imports no Flutter and no package from the data layer.
- Only main.dart decides which implementation is used.

## Acceptance criteria
1. The app shows a spinner, then "Plan sprint" and "Review pull request".
2. Tapping + and adding "Ship it" shows three tasks.
3. flutter test passes: load success, load failure, add, blank title.
4. Temporarily adding  throw Exception('offline');  as the first line of
   InMemoryTaskRepository.fetchTasks shows "Could not load tasks." and a
   Retry button, with no change to the cubit or the page.
