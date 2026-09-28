# Lab 1.1 - Grade Book v1

The Grade Book is the console app you grow through module 1.
Version 1 uses only variables, types and operators.

## How to run

- Quickest: paste start/bin/main.dart into https://dartpad.dev and press Run.
- Locally: run "dart create grade_book", copy the file to bin/main.dart, then
  run "dart run bin/main.dart" inside the grade_book folder.

## Task

Complete TODO(1) to TODO(6) in start/bin/main.dart.

Rules:

- Use final for values computed once and const for values fixed in the source.
- Use / for the average and ~/ for the whole-number average.
- Do not use a dollar sign followed by a curly bracket anywhere. Put the value
  in a local variable first and interpolate it with a plain dollar sign.

## Expected output

    Flutter Foundations - Grade Book v1
    Student: Asha Menon (roll 17)
    Math: 88 | Science: 76 | English: 92
    Total: 256 / 300
    Average: 85.3 (whole number: 85)
    Result: PASS
    With bonus: 261 / 300

## Acceptance criteria

- The output matches the block above line for line.
- Changing science to 35 prints "Result: FAIL" and "Total: 215 / 300".
- dart analyze reports no errors (unused-variable warnings from the starter are gone).
- No variable in your solution is declared with dynamic.

## Stretch

- Print the percentage with one decimal place: Percentage: 85.3%
- Add a fourth subject and change only the lines that must change.