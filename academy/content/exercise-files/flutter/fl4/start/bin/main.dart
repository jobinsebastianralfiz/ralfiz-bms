// Grade Book v2 - null safety (lesson 1.2) - STARTER
// Run with: dart run bin/main.dart  (or paste into DartPad)
// It compiles as it is. Complete TODO(1) to TODO(8).
// Rule for this lab: do not use the ! operator anywhere.

String? nicknameFor(String name) {
  const nicknames = {'Asha Menon': 'Ash', 'Joel Thomas': 'JT'};
  return nicknames[name]; // a map lookup is nullable: the key may be missing
}

// TODO(1): Write String formatLine({required String subject, int? mark})
//          that returns 'Math: 88', or 'Science: absent' when mark is null.

// TODO(2): Declare a top-level late final String reportTitle;

void main() {
  const studentName = 'Asha Menon';
  // null means the student was absent for that exam
  final Map<String, int?> marks = {'Math': 88, 'Science': null, 'English': 92};

  // TODO(3): Assign reportTitle = 'Term 1 report' and print it.

  // TODO(4): Build display from nicknameFor(studentName) with ?? so it falls
  //          back to the full name, and print 'Student: <display>'.

  var total = 0;
  var attempted = 0;
  for (final subject in marks.keys) {
    final mark = marks[subject]; // int?
    // TODO(5): If mark is not null, add it to total and add 1 to attempted.
    //          The null check promotes mark to int, so no ! is needed.
    //          Then print formatLine(subject: subject, mark: mark).
    print('$subject: $mark');
  }

  // TODO(6): Declare final double? average: null when attempted is 0,
  //          otherwise total / attempted. Print it with one decimal place
  //          using ?. and ?? so it shows 'n/a' when there is no average.
  //          Also print 'Attempted: 2 of 3' and 'Total: 180'.

  // TODO(7): Read marks['History'] and print 'History: not taken'
  //          using ?.toString() and ??.

  // TODO(8): Print the length of Ravi Kumar's nickname with ?.length.
  //          He has none, so it should print 'Ravi nickname length: null'.

  print('Attempted so far: $attempted, total so far: $total');
}