# Lab 1.10: Library Command Desk (errors and exceptions)

The desk reads text commands such as "borrow b1 asha" and "fine asha 20".
Some commands are badly typed (FormatException), some break library rules
(your own LibraryException types), and anything else is a bug that should be
logged with its stack trace and rethrown. One bad command must never stop the
whole batch.

## Files
- start/bin/main.dart: compiles, but crashes on the third command and lets rules be broken. Fill TODO(1) to TODO(5) (TODO 4 has parts a and b).
- solution/bin/main.dart: one finished version.

## Run it
Run with asserts on, so assert() checks are active (Flutter debug builds do this for you):

    dart run --enable-asserts bin/main.dart

## Expected output

    OK    asha borrowed Clean Code
    DENY  No book with id b9
    BAD   Usage: borrow <bookId> <member>
    OK    ben borrowed Dune
    OK    asha borrowed Refactoring
    DENY  asha has reached the limit of 2 loans
    DENY  Clean Code is already on loan to asha
    BAD   Fine must be a positive whole number: -5
    OK    asha paid a fine of 20
    BAD   Unknown command: dance
    Processed 10 commands: 4 ok, 6 failed

## What you will see on the way
- Before TODO(2), "borrow b2" reaches the catch-all clause: it prints BUG, the stack trace, and rethrow stops the program. That is the right behaviour for a real bug, but a typing mistake is not a bug.
- Before TODO(5), "fine asha -5" breaks the assert in payFine when asserts are on. Without --enable-asserts it silently accepts a negative fine. That is why asserts are not input validation.

## Acceptance criteria
1. All custom exceptions extend the sealed LibraryException, which implements Exception and overrides toString.
2. main catches LibraryException and FormatException with separate on clauses, and never catches Error types on purpose.
3. The catch-all clause logs the error and stack trace, then uses rethrow.
4. processed is incremented in a finally block and ends at 10.
5. parseAmount uses int.tryParse and throws a FormatException that includes the bad text.

## Stretch
- Add a "return b1" command that throws a new NotOnLoanException when the book is on the shelf.
- Temporarily add throw StateError('test'); as the first line of payFine and run again. The catch-all clause logs BUG with a stack trace and rethrow stops the batch. Remove the line afterwards.