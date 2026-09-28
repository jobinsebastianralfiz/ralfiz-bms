# Lab 1.6: Library Manager, part 1 (classes and constructors)

You start the Library Manager console app. A Book knows its id, title, author,
year and whether it is on loan. A Library holds a private list of books and
lends them out. You practise every constructor kind from the lesson.

## Files
- start/bin/main.dart: compiles now. Fill TODO(1) to TODO(7) and uncomment the lines in main marked "After TODO(n)".
- solution/bin/main.dart: one finished version.

## Run it

    dart run bin/main.dart

To see asserts fire, run with asserts on:

    dart run --enable-asserts bin/main.dart

## Expected output

    Ralfiz Community Library
      #1 Clean Code by Robert C. Martin (2008) - available
      #2 Dune by Frank Herbert (1965) - available
      #3 Beowulf by Unknown (1000) - available
    Check out #2: true
    Check out #2 again: false
    Check out #99: false
    Available: 2 of 3
      #1 Clean Code by Robert C. Martin (2008) - available
      #2 Dune by Frank Herbert (1965) - on loan
      #3 Beowulf by Unknown (1000) - available
    Error: Invalid book data: {title: Broken}

## Acceptance criteria
1. Ids come from a static counter in an initializer list, so the first three books get #1, #2 and #3.
2. Book.unknownAuthor is a redirecting constructor (": this(...)" with no body).
3. Book.fromMap is a factory constructor that throws a FormatException for bad data and never creates a half-built Book.
4. The on-loan flag is private (_onLoan) and only changes through checkOut and giveBack.
5. toString is overridden, so printing a book never shows "Instance of 'Book'".

## Stretch
- Add Book(title: '', author: 'X', year: 2000) to main and run with --enable-asserts. Read the assert message.
- Add a const constructor to a small Genre class (final String name) and prove with identical() that two const Genre('Fiction') objects are the same instance.