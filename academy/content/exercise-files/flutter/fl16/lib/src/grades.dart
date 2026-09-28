// lib/src/grades.dart - Grade Book helpers (lesson 1.14).
// Export this file from lib/grade_book.dart:  export 'src/grades.dart';

/// Returns the mean of [scores]. Throws [ArgumentError] for an empty list.
double average(List<num> scores) {
  if (scores.isEmpty) {
    throw ArgumentError('scores must not be empty');
  }
  final total = scores.fold<num>(0, (sum, s) => sum + s);
  return total / scores.length;
}

/// Returns the letter grade for a score from 0 to 100.
String letterFor(num score) {
  if (score < 0 || score > 100) {
    throw ArgumentError.value(score, 'score', 'must be 0 to 100');
  }
  return switch (score) {
    >= 90 => 'A',
    >= 80 => 'B',
    >= 70 => 'C',
    >= 60 => 'D',
    _ => 'F',
  };
}

/// Counts how many scores got each letter, e.g. {A: 2, C: 1}.
/// Letters with no scores are left out.
Map<String, int> letterCounts(List<num> scores) {
  final counts = <String, int>{};
  for (final s in scores) {
    final letter = letterFor(s);
    counts[letter] = (counts[letter] ?? 0) + 1;
  }
  return counts;
}

/// Formats one report line, e.g. "Asha: 91.5 (A)".
String reportLine(String name, List<num> scores) {
  final avg = average(scores);
  final shown = avg.toStringAsFixed(1);
  final letter = letterFor(avg);
  return '$name: $shown ($letter)';
}
