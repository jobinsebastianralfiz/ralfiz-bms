# Lab 1.5: Grade Book with collections

You continue the Grade Book console app. The data is a const Map<String, List<int>>
of student names and their three test scores. You turn it into a small report
using only collection tools: fold, where, map, sort, expand, reduce,
collection for/if and a Set.

## Files
- start/bin/main.dart: compiles and runs, but prints placeholder values. Fill TODO(1) to TODO(7).
- solution/bin/main.dart: one finished version. Compare only after you try.

## Run it

    dart run bin/main.dart

No packages are needed, so you can also paste the file into DartPad.

## Expected output

    Grade Book
    Asha: 83.3
    Ben: 65.7
    Chen: 91.7
    Divya: 52.0
    Passing (best first): [Chen, Asha, Ben]
    Scores recorded: 12
    Highest score: 95
    Class average: 73.2
    Honours: Chen
    Grades used: {B, A, C, D}

## Acceptance criteria
1. average uses fold<int> and returns a double.
2. averages is built with a map literal and a collection for, not with forEach plus []=.
3. The passing list is sorted with sort and a comparator. You never assign the result of sort (it returns void).
4. allScores comes from expand; the highest score comes from reduce.
5. honours uses a collection for with a collection if inside one list literal.
6. The set of letter grades keeps first-seen order and has no duplicates.

## Stretch
- Uncomment gradeBook['Eve'] = [70]; at the end of the solution and run it. A const map
  throws an UnsupportedError at runtime. Then make a modifiable copy with
  Map.of(gradeBook) and add Eve to the copy instead.
- Print each student with a rank using averages.keys.indexed (Dart 3), for example "1. Asha".