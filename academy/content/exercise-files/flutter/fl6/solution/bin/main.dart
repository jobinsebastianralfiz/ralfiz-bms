// Grade Book v4 - functions and closures (lesson 1.4) - SOLUTION
// Run with: dart run bin/main.dart

const passMark = 40;

/// A grading rule: turns an average into a label such as 'B' or 'Pass'.
typedef Grader = String Function(double average);

/// A validation rule: returns an error message, or null when the mark is fine.
typedef MarkRule = String? Function(int mark);

// TODO(1)
double average(List<int> marks) {
  if (marks.isEmpty) return 0;
  var total = 0;
  for (final m in marks) {
    total += m;
  }
  return total / marks.length;
}

// TODO(2)
String letterGrade(double avg) => switch (avg) {
      >= 90 => 'A',
      >= 75 => 'B',
      >= 60 => 'C',
      >= passMark => 'D',
      _ => 'F',
    };

// TODO(3)
String passFail(double avg) => avg >= passMark ? 'Pass' : 'Fail';

// TODO(4)
String? notNegative(int m) => m < 0 ? 'negative mark $m' : null;
String? atMost100(int m) => m > 100 ? 'mark $m is above 100' : null;

List<String> validate(List<int> marks, {required List<MarkRule> rules}) {
  final errors = <String>[];
  for (final m in marks) {
    for (final rule in rules) {
      final error = rule(m);
      if (error != null) errors.add(error);
    }
  }
  return errors;
}

// TODO(5): the returned function captures bonus.
int Function(int) makeCurve(int bonus) {
  return (int mark) {
    final curved = mark + bonus;
    return curved > 100 ? 100 : curved;
  };
}

// TODO(6): curve is just a value we call.
List<int> applyCurve(List<int> marks, int Function(int) curve) {
  final result = <int>[];
  for (final m in marks) {
    result.add(curve(m));
  }
  return result;
}

// TODO(7): the grading rule is a parameter (strategy pattern).
String formatRow(
  String name,
  List<int> marks, {
  required Grader grader,
  int decimals = 1,
}) {
  final avg = average(marks);
  final avgText = avg.toStringAsFixed(decimals);
  final grade = grader(avg);
  return '$name: $avgText ($grade)';
}

void main() {
  final students = {
    'Asha': [88, 76, 92],
    'Ravi': [45, 38, 60],
    'Sam': [70, 120, -5],
  };
  final List<MarkRule> rules = [notNegative, atMost100];
  final curve = makeCurve(5);

  // TODO(8): report is a closure over reportsPrinted.
  var reportsPrinted = 0;
  void report(String line) {
    reportsPrinted++;
    print(line);
  }

  for (final entry in students.entries) {
    final name = entry.key;
    final marks = entry.value;

    final errors = validate(marks, rules: rules);
    if (errors.isNotEmpty) {
      final errorText = errors.join(', ');
      report('$name: invalid ($errorText)');
      continue;
    }

    report(formatRow(name, marks, grader: letterGrade));
    report(formatRow(name, marks, grader: passFail, decimals: 0));
    report('  curved: ' + formatRow(name, applyCurve(marks, curve), grader: letterGrade));
  }

  print('Reports printed: $reportsPrinted');
}