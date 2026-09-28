// Grade Book v1 (lesson 1.1) - SOLUTION
// Run with: dart run bin/main.dart

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

  // TODO(1)
  final total = math + science + english;

  // TODO(2): / always gives a double, ~/ truncates to an int.
  final average = total / 3;
  final wholeAverage = total ~/ 3;

  // TODO(3)
  final maxTotal = maxPerSubject * 3;

  // TODO(4)
  final passed =
      math >= passMark && science >= passMark && english >= passMark;

  // TODO(5): int.parse throws on bad text; lesson 1.2 shows tryParse + ??.
  final bonus = int.parse(bonusInput);
  final withBonus = total + bonus;

  // TODO(6): compute display values first, then interpolate plain names.
  final avgText = average.toStringAsFixed(1);
  final result = passed ? 'PASS' : 'FAIL';

  print('$courseName - Grade Book v1');
  print('Student: $studentName (roll $rollNo)');
  print('Math: $math | Science: $science | English: $english');
  print('Total: $total / $maxTotal');
  print('Average: $avgText (whole number: $wholeAverage)');
  print('Result: $result');
  print('With bonus: $withBonus / $maxTotal');
}