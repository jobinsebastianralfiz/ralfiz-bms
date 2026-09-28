# Lab 1.3 - Grade Book v3 (loops and patterns)

Version 3 grades a whole class. The rows look like data from a file or an API,
and some of them are broken. Your program must grade the good rows and skip the
bad ones without crashing and without a single "as" cast.

## How to run

Paste start/bin/main.dart into DartPad, or copy it to bin/main.dart in your
grade_book project and run "dart run bin/main.dart".

## Task

Complete TODO(1) to TODO(7). Use:

- a switch expression with relational patterns for letter grades,
- if-case with a map pattern to validate each row,
- for-in loops, continue, and a guard (when) for students who failed a subject.

## Expected output

    Asha: 85.3, grade B
    Ravi: 47.7, grade F (failed a subject)
    Meera: 94.7, grade A
    Anu: no marks yet
    Skipping bad row: {name: Joel}
    Skipping bad row: {name: Sam, marks: [70, absent, 65]}
    3 students graded
    Top student: Meera (94.7)

## Acceptance criteria

- The output matches the block above.
- The file contains no " as " casts and no ! operators.
- Removing the _ arm from letterGrade makes the analyzer report that the switch
  is not exhaustive. Put it back.
- Moving the >= 60 arm above >= 90 makes Meera's grade C. Put it back and
  explain why the order matters.

## Stretch

- Add a row {'name': 'Lena', 'marks': [100, 101, 99]} and reject marks above 100
  with a guard in the if-case: if (row case {...} when marks.every((m) => m <= 100)).
- Number each graded student (1. Asha ...) using a counter.