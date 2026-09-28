# Lesson 9.5 lab: wiring TaskFlow with dependency injection

## Goal
The starter works, but TasksCubit creates its own Dio and repository with a
hard-coded URL. Refactor it so that:
- every class receives its dependencies through its constructor,
- one function, setupDependencies, builds the object graph with get_it,
- the API URL and environment come from --dart-define,
- a widget test swaps in a fake repository without touching the UI.

## Packages

    flutter pub add dio get_it flutter_bloc

## Object graph

    AppConfig        registerSingleton        (built in main from dart-defines)
    Dio              registerLazySingleton    (baseUrl from AppConfig)
    ApiClient        registerLazySingleton    (needs Dio)
    TaskRepository   registerLazySingleton    (RemoteTaskRepository, needs ApiClient)
    TasksCubit       registerFactory          (needs TaskRepository)

## Rules
- Only main.dart, setupDependencies and BlocProvider(create: ...) call getIt.
- TasksCubit and RemoteTaskRepository never call getIt or create Dio.
- Cubits are factories, never singletons.

## Run it

    flutter run
    flutter run --dart-define=ENV=staging
    flutter run --dart-define=ENV=prod

You can also put the values in config/staging.json:

    { "ENV": "staging", "API_BASE_URL": "https://dummyjson.com" }

and run: flutter run --dart-define-from-file=config/staging.json

These values end up inside the app. They are configuration, not secrets.

## Acceptance criteria
1. flutter run shows a DEV banner with https://dummyjson.com and a list of tasks.
2. flutter run --dart-define=ENV=staging shows a STAGING banner.
3. flutter run --dart-define=ENV=prod shows no banner.
4. flutter test passes: the page shows Fake task A from the fake repository.
