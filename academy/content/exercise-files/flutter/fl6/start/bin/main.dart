// Grade Book v4 - functions and closures (lesson 1.4) - STARTER
// Run with: dart run bin/main.dart  (or paste into DartPad)
// It compiles as it is, but the stubs return placeholder values.
// Complete TODO(1) to TODO(8).

const passMark = 40;

/// A grading rule: turns an average into a label such as 'B' or 'Pass'.
typedef Grader = String Function(double average);

// TODO(1): Complete average. Return 0 for an empty list,
//          otherwise the total divided by the number of marks.
double average(List<int> marks) {
  return 0;
}

// TODO(2): Complete letterGrade with an arrow function and a switch
//          expression: >= 90 'A', >= 75 'B', >= 60 'C', >= passMark 'D', else 'F'.
String letterGrade(double avg) {
  return '?';
}

// TODO(3): Write String passFail(double avg) as an arrow function that
//          returns 'Pass' when avg >= passMark, otherwise 'Fail'.

// TODO(4): Declare typedef MarkRule = String? Function(int mark);
//          Write notNegative (returns 'negative mark <m>' for m < 0) and
//          atMost100 (returns 'mark <m> is above 100' for m > 100); both
//          return null when the mark is fine.
//          Then write List<String> validate(List<int> marks,
//          {required List<MarkRule> rules}) that collects every error.

// TODO(5): Write int Function(int) makeCurve(int bonus) that returns a
//          closure adding bonus to a mark, capped at 100.

// TODO(6): Write List<int> applyCurve(List<int> marks, int Function(int) curve)
//          that returns a new list with the curve applied to each mark.

// TODO(7): Write String formatRow(String name, List<int> marks,
//          {required Grader grader, int decimals = 1}) that returns
//          '<name>: <average with decimals> (<grade>)'.

void main() {
  final students = {
    'Asha': [88, 76, 92],
    'Ravi': [45, 38, 60],
    'Sam': [70, 120, -5],
  };

  // TODO(8): Create var reportsPrinted = 0 and a local function
  //          void report(String line) that prints the line and adds 1 to
  //          reportsPrinted (a closure over a local variable).
  //          For each student: validate first; if there are errors, report
  //          '<name>: invalid (<errors joined with comma and space>)' and
  //          continue. Otherwise report three lines: formatRow with
  //          letterGrade, formatRow with passFail and decimals: 0, and
  //          '  curved: ' + formatRow(...) using makeCurve(5).
  //          Finish with 'Reports printed: <count>'.
  for (final entry in students.entries) {
    final name = entry.key;
    final marks = entry.value;
    final avg = average(marks);
    final grade = letterGrade(avg);
    print('$name $avg $grade');
  }
}