// Loan Desk, lesson 1.8: records, sealed classes and enums (SOLUTION).
// Run with: dart run bin/main.dart   (or paste into DartPad)

/// Enhanced enum: each value carries data and the enum has members.
enum Membership {
  basic(maxLoans: 2, finePerDay: 10),
  premium(maxLoans: 5, finePerDay: 5);

  const Membership({required this.maxLoans, required this.finePerDay});

  final int maxLoans;
  final int finePerDay; // rupees per late day

  String get label => name[0].toUpperCase() + name.substring(1);
}

/// Sealed family: the compiler knows every subtype, so switches are exhaustive.
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

/// A named record type, given a readable alias.
typedef Member = ({String name, Membership tier});

/// Switch expression with object patterns, a constant sub-pattern and no default.
String describe(LoanStatus status) => switch (status) {
      Available() => 'on the shelf',
      OnLoan(:final member, daysLeft: 0) => 'due today from $member',
      OnLoan(:final member, :final daysLeft) => 'with $member, $daysLeft days left',
      Overdue(:final member, :final daysLate) => '$daysLate days late ($member)',
    };

int fineFor(LoanStatus status, Membership tier) => switch (status) {
      Overdue(:final daysLate) => daysLate * tier.finePerDay,
      Available() || OnLoan() => 0,
    };

/// Returns three values at once as a positional record.
(int, int, int) summarise(Iterable<LoanStatus> all) {
  var shelf = 0, out = 0, overdue = 0;
  for (final status in all) {
    switch (status) {
      case Available():
        shelf++;
      case OnLoan():
        out++;
      case Overdue():
        overdue++;
    }
  }
  return (shelf, out, overdue);
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

  // Destructure each MapEntry with an object pattern.
  for (final MapEntry(key: title, value: status) in catalogue.entries) {
    final text = describe(status);
    print('$title: $text');
  }

  // Destructure the record returned by summarise.
  final (shelf, out, overdue) = summarise(catalogue.values);
  print('Shelf $shelf, out $out, overdue $overdue');

  // Destructure a named record with :name shorthand.
  final (:name, :tier) = asha;
  final fine = fineFor(catalogue['Inception']!, tier);
  final label = tier.label;
  print('Fine for $name ($label): Rs $fine');

  // Enum values are a List, so you can loop over them.
  for (final level in Membership.values) {
    final levelName = level.label;
    final max = level.maxLoans;
    final perDay = level.finePerDay;
    print('$levelName: up to $max loans, Rs $perDay per late day');
  }
}