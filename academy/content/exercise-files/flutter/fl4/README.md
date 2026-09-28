# Lab 1.2 - Grade Book v2 (null safety)

Real data has holes. In this version a student can be absent for an exam
(the mark is null), may or may not have a nickname, and a subject may be
missing from the map entirely.

## How to run

Paste start/bin/main.dart into DartPad, or copy it to bin/main.dart in your
grade_book project and run "dart run bin/main.dart".

## Task

Complete TODO(1) to TODO(8). The one rule: **no ! operator anywhere**.
Use ??, ??=, ?., a null check that promotes, late and required instead.

## Expected output

    Term 1 report
    Student: Ash
    Math: 88
    Science: absent
    English: 92
    Attempted: 2 of 3
    Total: 180
    Average: 90.0
    History: not taken
    Ravi nickname length: null

(Remove the starter's "Attempted so far" line when you are done.)

## Acceptance criteria

- The output matches the block above.
- Searching your file for "!" finds only != comparisons, never a null assertion.
- Setting all three marks to null prints "Attempted: 0 of 3" and "Average: n/a"
  and does not crash.
- Calling formatLine(mark: 50) without a subject is a compile error.
- Moving print(reportTitle) above the assignment compiles but throws
  LateInitializationError when run. Try it, then put it back.

## Stretch

- Change studentName to 'Ravi Kumar' and check the Student line falls back to his full name.
- Add 'Joel Thomas' with no marks map at all (use Map<String, int?>? and ?? const {}).