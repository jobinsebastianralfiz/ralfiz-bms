// Grade Book, lesson 1.5: collections in depth (SOLUTION).
// Run with: dart run bin/main.dart   (or paste into DartPad)

/// Scores per student. A const map is deeply immutable:
/// neither the map nor the lists inside it can change.
const Map<String, List<int>> gradeBook = {
  'Asha': [82, 91, 77],
  'Ben': [67, 58, 72],
  'Chen': [95, 88, 92],
  'Divya': [45, 61, 50],
};

const int passMark = 60;
const int honoursMark = 90;

/// Average of a list of scores.
/// fold<int> makes the running total an int, then / gives a double.
double average(List<int> scores) =>
    scores.fold<int>(0, (sum, s) => sum + s) / scores.length;

void main() {
  // 1. Map literal with collection for: name -> average.
  final averages = <String, double>{
    for (final entry in gradeBook.entries) entry.key: average(entry.value),
  };

  print('Grade Book');
  averages.forEach((name, avg) {
    final text = avg.toStringAsFixed(1);
    print('$name: $text');
  });

  // 2. where + toList + cascade sort (sort works in place and returns void).
  final passing = averages.entries.where((e) => e.value >= passMark).toList()
    ..sort((a, b) => b.value.compareTo(a.value));
  final passingNames = passing.map((e) => e.key).toList();
  print('Passing (best first): $passingNames');

  // 3. expand flattens the lists of scores into one list.
  final allScores = gradeBook.values.expand((scores) => scores).toList();
  final count = allScores.length;
  print('Scores recorded: $count');

  // 4. reduce finds the highest score (the list is not empty).
  final highest = allScores.reduce((a, b) => a > b ? a : b);
  print('Highest score: $highest');

  final classAverage = average(allScores).toStringAsFixed(1);
  print('Class average: $classAverage');

  // 5. List literal with collection for + collection if.
  final honours = [
    for (final e in averages.entries)
      if (e.value >= honoursMark) e.key,
  ];
  final honourList = honours.join(', ');
  print('Honours: $honourList');

  // 6. A Set removes duplicates: which grades (A-D) appear at all?
  final letterGrades = {for (final s in allScores) letter(s)};
  print('Grades used: $letterGrades');

  // 7. Immutability check (uncomment to see the UnsupportedError at runtime):
  // gradeBook['Eve'] = [70];
}

/// A switch expression with relational patterns maps a score to a letter.
String letter(int score) => switch (score) {
      >= 90 => 'A',
      >= 75 => 'B',
      >= 60 => 'C',
      _ => 'D',
    };