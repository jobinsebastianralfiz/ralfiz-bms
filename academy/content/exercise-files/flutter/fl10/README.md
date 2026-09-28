# Lab 1.8: Loan Desk (records, sealed classes, enums)

The Library Manager gets a loan desk. Each title has a loan status that is
exactly one of Available, OnLoan or Overdue: a sealed family. Membership levels
are an enhanced enum that carries loan limits and fines. Members are records,
and the summary function returns three counts as one record.

## Files
- start/bin/main.dart: compiles, but describe() says "unknown", fines are 0 and counts are 0. Fill TODO(1) to TODO(6).
- solution/bin/main.dart: one finished version.

## Run it

    dart run bin/main.dart

## Expected output

    Clean Code: on the shelf
    Dune: with Asha, 5 days left
    Refactoring: due today from Ben
    Inception: 3 days late (Asha)
    Shelf 1, out 2, overdue 1
    Fine for Asha (Basic): Rs 30
    Basic: up to 2 loans, Rs 10 per late day
    Premium: up to 5 loans, Rs 5 per late day

## Acceptance criteria
1. describe() and fineFor() are switch expressions with no wildcard (_) arm. They still compile because LoanStatus is sealed.
2. The "due today" case uses a constant sub-pattern (daysLeft: 0) placed before the general OnLoan arm.
3. summarise() returns a record and main destructures it into three variables.
4. main destructures the named record asha with (:name, :tier).
5. The catalogue loop uses a MapEntry pattern in the for-in.

## Stretch
- Add a fourth status, Lost (member, replacementCost). Watch the compiler list every switch that is no longer exhaustive, then fix them.
- Add a student level to Membership with maxLoans 1 and finePerDay 2. Nothing else should need to change.