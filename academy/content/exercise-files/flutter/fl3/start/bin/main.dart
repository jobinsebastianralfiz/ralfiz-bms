// Grade Book v1 (lesson 1.1) - STARTER
// Run in DartPad, or in a project made with "dart create grade_book":
// put this file at bin/main.dart and run "dart run bin/main.dart".
// It compiles as it is. Complete TODO(1) to TODO(6).

void main() {
  const courseName = 'Flutter Foundations';
  const passMark = 40;
  const maxPerSubject = 100;

  final studentName = 'Asha Menon';
  final rollNo = 17;
  final math = 88;
  final science = 76;
  final english = 92;
  const bonusInput = '5'; // text typed in by the teacher

  // TODO(1): Declare final total as the sum of the three marks.

  // TODO(2): Declare final average using / (a double) and
  //          final wholeAverage using ~/ (an int).

  // TODO(3): Declare final maxTotal = maxPerSubject * 3.

  // TODO(4): Declare final passed. It is true only if EVERY subject
  //          is at least passMark (combine three comparisons with &&).

  // TODO(5): Turn bonusInput into an int with int.parse and
  //          compute final withBonus = total + bonus.

  // TODO(6): Print the report card exactly as shown in README.md.
  //          Use a local avgText = average.toStringAsFixed(1) and a
  //          conditional (passed ? 'PASS' : 'FAIL') for the result.
  //          Never write a dollar sign followed by a curly bracket:
  //          make a local variable and use plain $name interpolation.

  print('$courseName - Grade Book v1');
  print('Student: $studentName (roll $rollNo)');
}