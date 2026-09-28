// Grade Book v2 - null safety (lesson 1.2) - SOLUTION
// Run with: dart run bin/main.dart
// Not a single ! operator: every null is handled on purpose.

String? nicknameFor(String name) {
  const nicknames = {'Asha Menon': 'Ash', 'Joel Thomas': 'JT'};
  return nicknames[name];
}

// TODO(1): required named parameter plus an optional nullable one.
String formatLine({required String subject, int? mark}) {
  if (mark == null) return '$subject: absent';
  return '$subject: $mark'; // mark is promoted to int here
}

// TODO(2): assigned exactly once, later than its declaration.
late final String reportTitle;

void main() {
  const studentName = 'Asha Menon';
  final Map<String, int?> marks = {'Math': 88, 'Science': null, 'English': 92};

  // TODO(3)
  reportTitle = 'Term 1 report';
  print(reportTitle);

  // TODO(4)
  final display = nicknameFor(studentName) ?? studentName;
  print('Student: $display');

  var total = 0;
  var attempted = 0;
  for (final subject in marks.keys) {
    final mark = marks[subject]; // int?
    // TODO(5)
    if (mark != null) {
      total += mark; // promoted to int inside this block
      attempted++;
    }
    print(formatLine(subject: subject, mark: mark));
  }

  // TODO(6)
  final double? average = attempted == 0 ? null : total / attempted;
  final avgText = average?.toStringAsFixed(1) ?? 'n/a';
  final subjectCount = marks.length;
  print('Attempted: $attempted of $subjectCount');
  print('Total: $total');
  print('Average: $avgText');

  // TODO(7)
  final history = marks['History'];
  final historyText = history?.toString() ?? 'not taken';
  print('History: $historyText');

  // TODO(8)
  final raviNickname = nicknameFor('Ravi Kumar');
  final raviLength = raviNickname?.length;
  print('Ravi nickname length: $raviLength');
}