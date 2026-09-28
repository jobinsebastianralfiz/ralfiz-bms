// test/grades_test.dart - SOLUTION (lesson 1.14)
// Run with: dart test
import 'package:grade_book/grade_book.dart';
import 'package:test/test.dart';

void main() {
  group('average', () {
    test('returns the mean of the scores', () {
      expect(average([80, 90, 100]), 90);
    });

    test('handles decimals', () {
      expect(average([1, 2]), closeTo(1.5, 0.0001));
    });

    test('throws ArgumentError on an empty list', () {
      expect(() => average([]), throwsArgumentError);
    });
  });

  group('letterFor', () {
    test('gives A from 90 upwards', () {
      expect(letterFor(90), 'A');
      expect(letterFor(100), 'A');
    });

    test('checks every boundary', () {
      expect(letterFor(89.9), 'B');
      expect(letterFor(80), 'B');
      expect(letterFor(70), 'C');
      expect(letterFor(60), 'D');
      expect(letterFor(59.9), 'F');
      expect(letterFor(0), 'F');
    });

    test('rejects scores outside 0 to 100', () {
      expect(() => letterFor(101), throwsA(isA<ArgumentError>()));
      expect(() => letterFor(-1), throwsArgumentError);
    });
  });

  group('letterCounts', () {
    test('counts each letter and leaves out missing ones', () {
      expect(letterCounts([95, 91, 72]), {'A': 2, 'C': 1});
    });

    test('returns an empty map for no scores', () {
      expect(letterCounts([]), isEmpty);
    });
  });

  group('reportLine', () {
    late List<num> scores;

    setUp(() {
      scores = [88, 95];
    });

    test('shows the average with one decimal and the letter', () {
      expect(reportLine('Asha', scores), 'Asha: 91.5 (A)');
    });

    test('contains the name', () {
      expect(reportLine('Ravi', scores), contains('Ravi'));
    });
  });
}
