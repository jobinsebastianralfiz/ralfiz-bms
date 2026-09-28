# Lab 1.7: Library Manager, part 2 (inheritance, mixins, extensions)

The library now holds books, DVDs and magazines. They share a base class
(LibraryItem), borrowable items follow a contract (Borrowable), loan logic and
ratings are reused through mixins (Lending, Rateable), ISBNs compare by value,
and an extension adds date helpers to DateTime.

## Files
- start/bin/main.dart: compiles, but lends twice, rates 0.0, compares ISBNs by identity and prints ISO dates. Fill TODO(1) to TODO(6).
- solution/bin/main.dart: one finished version.

## Run it

    dart run bin/main.dart

## Expected output

    Catalogue
      Book B1: Clean Code
      DVD D1: Inception
      Magazine M1: Wired (reading room only)
    Asha borrows Clean Code, due 2026-09-22
    Ben borrows Inception, due 2026-09-08
    Error: Bad state: Clean Code is already on loan
    Clean Code rating: 4.5
    Same ISBN: true
    Unique ISBNs: 1

## Acceptance criteria
1. LibraryItem is abstract and declares the abstract getter kind; each subclass overrides it with @override.
2. lend() takes a Borrowable, not a Book, so it works for every borrowable type.
3. Lending throws a StateError when an item is already on loan.
4. Magazine.toString calls super.toString().
5. Isbn overrides both == and hashCode, using the digits only.
6. The due date comes from the ymd getter in the LoanDates extension.

## Stretch
- Add an AudioBook class (loanDays 14) that extends LibraryItem with Lending and Rateable. You should not need to touch lend().
- Add operator + to a small Money class (final int paise) and total two fines with +.