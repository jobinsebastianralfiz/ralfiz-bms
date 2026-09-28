// test/grades_test.dart - STARTER (lesson 1.14)
// Run with: dart test
// Two tests are done for you. Add the rest at TODO(1) to TODO(6).
import 'package:grade_book/grade_book.dart';
import 'package:test/test.dart';

void main() {
  group('average', () {
    test('returns the mean of the scores', () {
      expect(average([80, 90, 100]), 90);
    });

    // TODO(1): Test that average([1, 2]) is 1.5. Use closeTo(1.5, 0.0001).

    // TODO(2): Test that average([]) throws. Remember the () => wrapper
    //   and the throwsArgumentError matcher.
  });

  group('letterFor', () {
    test('gives A from 90 upwards', () {
      expect(letterFor(90), 'A');
      expect(letterFor(100), 'A');
    });

    // TODO(3): Test every boundary: 89.9 is B, 80 is B, 70 is C, 60 is D,
    //   59.9 is F and 0 is F.

    // TODO(4): Test that 101 and -1 throw. Try throwsA(isA<ArgumentError>())
    //   for one of them.
  });

  // TODO(5): Add a group for letterCounts: [95, 91, 72] gives
  //   {'A': 2, 'C': 1}, and an empty list gives an empty map (isEmpty).

  // TODO(6): Add a group for reportLine with a setUp that creates
  //   scores = [88, 95]. Check the line is 'Asha: 91.5 (A)'.
}
