// Grade Book v3 - loops and patterns (lesson 1.3) - STARTER
// Run with: dart run bin/main.dart  (or paste into DartPad)
// It compiles as it is. Complete TODO(1) to TODO(7).

const passMark = 40;

// TODO(1): Write String letterGrade(double avg) as a switch expression:
//          >= 90 'A', >= 75 'B', >= 60 'C', >= passMark 'D', otherwise 'F'.

void main() {
  // Rows as they might arrive from a file or an API: some are broken.
  final List<Map<String, Object>> rows = [
    {'name': 'Asha', 'marks': [88, 76, 92]},
    {'name': 'Ravi', 'marks': [45, 38, 60]},
    {'name': 'Meera', 'marks': [95, 91, 98]},
    {'name': 'Anu', 'marks': <int>[]},
    {'name': 'Joel'},
    {'name': 'Sam', 'marks': [70, 'absent', 65]},
  ];

  var graded = 0;

  for (final row in rows) {
    // TODO(2): Use if-case with a map pattern to bind String name and
    //          List<int> marks. In the else branch print
    //          'Skipping bad row: $row'.
    // TODO(3): If marks is empty, print '<name>: no marks yet' and continue.
    // TODO(4): Loop over marks with for-in to compute total and a bool
    //          failedOne (true if any mark is below passMark).
    // TODO(5): Compute avg = total / marks.length and grade with a switch
    //          expression whose first arm is a guard:
    //          _ when failedOne => 'F (failed a subject)', then
    //          _ => letterGrade(avg).
    // TODO(6): Print '<name>: <avg with 1 decimal>, grade <grade>',
    //          add 1 to graded and remember the top student and average.
    print(row);
  }

  // TODO(7): Print a summary with a switch expression on graded:
  //          0 => 'No students graded', 1 => 'One student graded',
  //          otherwise '<n> students graded'. Then print the top student.
  print('Graded: $graded');
}