# Lesson 9.4 lab: TaskFlow models with freezed and json_serializable

## Goal
Replace the hand-written Task and TodosPage models with generated ones,
add a priority enum that tolerates unknown values, and a sealed TasksState
union. Prove it with unit tests.

## Setup

    flutter create taskflow
    cd taskflow
    flutter pub add freezed_annotation json_annotation
    flutter pub add dev:build_runner dev:freezed dev:json_serializable

Create build.yaml in the project root so nested models become maps in toJson:

    targets:
      $default:
        builders:
          json_serializable:
            options:
              explicit_to_json: true

Add this to analysis_options.yaml (keep the existing include line):

    analyzer:
      exclude:
        - "**/*.g.dart"
        - "**/*.freezed.dart"
      errors:
        invalid_annotation_target: ignore

## Sample data (from https://dummyjson.com/todos?limit=3)

    {"todos":[
      {"id":1,"todo":"Do something nice for someone you care about","completed":false,"userId":152},
      {"id":2,"todo":"Memorize a poem","completed":true,"userId":13},
      {"id":3,"todo":"Watch a classic movie","completed":false,"userId":68}],
     "total":254,"skip":0,"limit":3}

DummyJSON sends no priority or dueDate. TaskFlow's own backend will, later.
The test file also sends "high" and an unknown "urgent" priority.

## Steps
1. Copy start/lib/models/task.dart to lib/models/task.dart. It compiles.
2. Work through TODO(1) to TODO(6).
3. Run: dart run build_runner build -d
   (recent build_runner versions delete conflicting outputs by default; -d is harmless)
4. Copy solution/test/task_model_test.dart to test/ and run flutter test.

## Acceptance criteria
- lib/models/task.dart has no hand-written ==, hashCode, copyWith or toJson.
- Task.fromJson reads "todo" into title; missing priority gives normal;
  "urgent" gives normal; "high" gives high.
- task.copyWith(dueDate: null) clears the due date.
- TodosPage.fromJson(jsonDecode(jsonEncode(page.toJson()))) == page.
- flutter test reports All tests passed!

## Decide and document
Will generated files be committed in this project? Write one sentence in
your README with the choice and the reason.
