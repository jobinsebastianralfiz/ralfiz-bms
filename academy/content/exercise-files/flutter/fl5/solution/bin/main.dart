// Grade Book v3 - loops and patterns (lesson 1.3) - SOLUTION
// Run with: dart run bin/main.dart

const passMark = 40;

// TODO(1): arms are tried top to bottom; the first match wins.
String letterGrade(double avg) => switch (avg) {
      >= 90 => 'A',
      >= 75 => 'B',
      >= 60 => 'C',
      >= passMark => 'D',
      _ => 'F',
    };

void main() {
  final List<Map<String, Object>> rows = [
    {'name': 'Asha', 'marks': [88, 76, 92]},
    {'name': 'Ravi', 'marks': [45, 38, 60]},
    {'name': 'Meera', 'marks': [95, 91, 98]},
    {'name': 'Anu', 'marks': <int>[]},
    {'name': 'Joel'},
    {'name': 'Sam', 'marks': [70, 'absent', 65]},
  ];

  var graded = 0;
  var bestName = '';
  var bestAvg = -1.0;

  for (final row in rows) {
    // TODO(2): the pattern checks both keys AND the value types.
    if (row case {'name': String name, 'marks': List<int> marks}) {
      // TODO(3)
      if (marks.isEmpty) {
        print('$name: no marks yet');
        continue;
      }

      // TODO(4)
      var total = 0;
      var failedOne = false;
      for (final m in marks) {
        total += m;
        if (m < passMark) failedOne = true;
      }

      // TODO(5)
      final avg = total / marks.length;
      final grade = switch (avg) {
        _ when failedOne => 'F (failed a subject)',
        _ => letterGrade(avg),
      };

      // TODO(6)
      final avgText = avg.toStringAsFixed(1);
      print('$name: $avgText, grade $grade');
      graded++;
      if (avg > bestAvg) {
        bestAvg = avg;
        bestName = name;
      }
    } else {
      // Joel has no marks key; Sam's list holds a String, so it is
      // not a List<int>. Neither can crash the program.
      print('Skipping bad row: $row');
    }
  }

  // TODO(7)
  final summary = switch (graded) {
    0 => 'No students graded',
    1 => 'One student graded',
    _ => '$graded students graded',
  };
  print(summary);
  if (graded > 0) {
    final bestText = bestAvg.toStringAsFixed(1);
    print('Top student: $bestName ($bestText)');
  }
}