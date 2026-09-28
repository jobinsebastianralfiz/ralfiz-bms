// Grade Book, lesson 1.5: collections in depth (STARTER).
// Run with: dart run bin/main.dart   (or paste into DartPad)
// It compiles and runs now, but prints placeholder values. Fill the TODOs.

const Map<String, List<int>> gradeBook = {
  'Asha': [82, 91, 77],
  'Ben': [67, 58, 72],
  'Chen': [95, 88, 92],
  'Divya': [45, 61, 50],
};

const int passMark = 60;
const int honoursMark = 90;

double average(List<int> scores) {
  // TODO(1): Return the average of scores.
  // Use scores.fold<int>(0, ...) for the total, then divide by scores.length.
  return 0;
}

void main() {
  // TODO(2): Build a Map<String, double> of name -> average
  // with a collection for over gradeBook.entries.
  final averages = <String, double>{};

  print('Grade Book');
  averages.forEach((name, avg) {
    final text = avg.toStringAsFixed(1);
    print('$name: $text');
  });

  // TODO(3): Keep the entries with an average >= passMark, sort them
  // best first (hint: toList() then ..sort), and keep only the names.
  final List<String> passingNames = [];
  print('Passing (best first): $passingNames');

  // TODO(4): Flatten every score into one List<int> with expand.
  final List<int> allScores = [];
  final count = allScores.length;
  print('Scores recorded: $count');

  // TODO(5): Find the highest score with reduce (guard against an empty list
  // while allScores is still the placeholder).
  final highest = allScores.isEmpty ? 0 : allScores.first;
  print('Highest score: $highest');

  final classAverage =
      allScores.isEmpty ? '0.0' : average(allScores).toStringAsFixed(1);
  print('Class average: $classAverage');

  // TODO(6): Build the honours list with a collection for plus a
  // collection if (average >= honoursMark).
  final List<String> honours = [];
  final honourList = honours.join(', ');
  print('Honours: $honourList');

  // TODO(7): Build a Set of letter grades used, e.g. {B, A, C, D},
  // with a set literal and a collection for that calls letter(score).
  final Set<String> letterGrades = {};
  print('Grades used: $letterGrades');
}

String letter(int score) => switch (score) {
      >= 90 => 'A',
      >= 75 => 'B',
      >= 60 => 'C',
      _ => 'D',
    };