# Lab 1.4 - Grade Book v4 (functions and closures)

Version 4 refactors the Grade Book into small functions that each do one job.
You pass grading rules and validation rules around as values, and build a
"curve" function with a closure.

## How to run

Paste start/bin/main.dart into DartPad, or copy it to bin/main.dart in your
grade_book project and run "dart run bin/main.dart".

## Task

Complete TODO(1) to TODO(8). Practise:

- arrow functions and a switch expression (letterGrade, passFail),
- a typedef for a function type (Grader, MarkRule),
- required and default named parameters (formatRow, validate),
- a function that returns a closure (makeCurve),
- a local function that changes a captured variable (report).

Pass functions by name (grader: letterGrade), never by calling them
(grader: letterGrade(avg) is a type error here, which is the point).

## Expected output

    Asha: 85.3 (B)
    Asha: 85 (Pass)
      curved: Asha: 90.3 (A)
    Ravi: 47.7 (D)
    Ravi: 48 (Pass)
      curved: Ravi: 52.7 (D)
    Sam: invalid (mark 120 is above 100, negative mark -5)
    Reports printed: 7

## Acceptance criteria

- The output matches the block above.
- formatRow is called with both letterGrade and passFail without changing formatRow.
- makeCurve(5) and makeCurve(15) give two independent functions:
  makeCurve(15)(90) returns 100 (capped) while makeCurve(5)(90) returns 95.
- Removing required from grader makes the analyzer complain that the
  non-nullable parameter needs a default value.

## Stretch

- Add a third Grader that returns 'Distinction' for averages of 85 or more
  and 'Merit' otherwise, and print one more line per student with it.
- Replace applyCurve's loop with marks.map(curve).toList() after lesson 1.5.