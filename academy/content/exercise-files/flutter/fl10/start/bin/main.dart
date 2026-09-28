// Loan Desk, lesson 1.8: records, sealed classes and enums (STARTER).
// Run with: dart run bin/main.dart   (or paste into DartPad)
// It compiles now, but prints placeholder values. Fill TODO(1) to TODO(6).

enum Membership {
  basic(maxLoans: 2, finePerDay: 10),
  premium(maxLoans: 5, finePerDay: 5);

  const Membership({required this.maxLoans, required this.finePerDay});

  final int maxLoans;
  final int finePerDay; // rupees per late day

  // TODO(1): Return the name with a capital first letter: basic -> Basic.
  String get label => name;
}

sealed class LoanStatus {
  const LoanStatus();
}

final class Available extends LoanStatus {
  const Available();
}

final class OnLoan extends LoanStatus {
  const OnLoan({required this.member, required this.daysLeft});
  final String member;
  final int daysLeft;
}

final class Overdue extends LoanStatus {
  const Overdue({required this.member, required this.daysLate});
  final String member;
  final int daysLate;
}

typedef Member = ({String name, Membership tier});

// TODO(2): Remove the wildcard arm and write one arm per case:
//   Available()                          -> 'on the shelf'
//   OnLoan with daysLeft: 0              -> 'due today from <member>'
//   any other OnLoan                     -> 'with <member>, <daysLeft> days left'
//   Overdue                              -> '<daysLate> days late (<member>)'
// Use :final member style patterns to pull out the fields.
String describe(LoanStatus status) => switch (status) {
      Available() => 'on the shelf',
      _ => 'unknown',
    };

// TODO(3): Return daysLate * tier.finePerDay for Overdue, 0 otherwise.
// Use a switch expression with no wildcard (hint: Available() || OnLoan()).
int fineFor(LoanStatus status, Membership tier) => 0;

// TODO(4): Count how many statuses are Available, OnLoan and Overdue with a
// switch statement, and return the three counts as a record.
(int, int, int) summarise(Iterable<LoanStatus> all) {
  return (0, 0, 0);
}

void main() {
  const Member asha = (name: 'Asha', tier: Membership.basic);
  const Member ben = (name: 'Ben', tier: Membership.premium);

  final catalogue = <String, LoanStatus>{
    'Clean Code': const Available(),
    'Dune': OnLoan(member: asha.name, daysLeft: 5),
    'Refactoring': OnLoan(member: ben.name, daysLeft: 0),
    'Inception': Overdue(member: asha.name, daysLate: 3),
  };

  // TODO(5): Replace entry.key / entry.value with a MapEntry pattern:
  // for (final MapEntry(key: title, value: status) in catalogue.entries)
  for (final entry in catalogue.entries) {
    final title = entry.key;
    final text = describe(entry.value);
    print('$title: $text');
  }

  final (shelf, out, overdue) = summarise(catalogue.values);
  print('Shelf $shelf, out $out, overdue $overdue');

  // TODO(6): Replace these two lines with one named-record destructuring:
  // final (:name, :tier) = asha;
  final name = asha.name;
  final tier = asha.tier;
  final fine = fineFor(catalogue['Inception']!, tier);
  final label = tier.label;
  print('Fine for $name ($label): Rs $fine');

  for (final level in Membership.values) {
    final levelName = level.label;
    final max = level.maxLoans;
    final perDay = level.finePerDay;
    print('$levelName: up to $max loans, Rs $perDay per late day');
  }
}