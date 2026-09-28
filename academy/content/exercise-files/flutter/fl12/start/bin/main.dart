// Library Command Desk, lesson 1.10: errors and exceptions (STARTER).
// Run with: dart run --enable-asserts bin/main.dart   (or paste into DartPad)
// It compiles, but the first bad command crashes the program. Fill TODO(1) to TODO(5).

sealed class LibraryException implements Exception {
  const LibraryException(this.message);
  final String message;

  // TODO(1): Override toString to return message, so printing the exception
  // shows 'No book with id b9' instead of "Instance of 'BookNotFoundException'".
}

final class BookNotFoundException extends LibraryException {
  BookNotFoundException(String id) : super('No book with id $id');
}

// TODO(4a): Add AlreadyOnLoanException(String title, String borrower) with the
// message '<title> is already on loan to <borrower>', and
// LoanLimitException(String member, int limit) with the message
// '<member> has reached the limit of <limit> loans'.

class Book {
  Book(this.id, this.title);
  final String id;
  final String title;
  String? borrower;
}

class LibraryDesk {
  LibraryDesk({required this.loanLimit}) : assert(loanLimit > 0, 'loanLimit must be positive');

  final int loanLimit;
  final Map<String, Book> _books = {
    for (final b in [
      Book('b1', 'Clean Code'),
      Book('b2', 'Dune'),
      Book('b3', 'Refactoring'),
      Book('b4', 'The Pragmatic Programmer'),
    ])
      b.id: b,
  };

  int loansOf(String member) => _books.values.where((b) => b.borrower == member).length;

  String run(String line) {
    final parts = line.trim().split(RegExp(r'\s+'));
    return switch (parts) {
      ['borrow', final id, final member] => borrow(id, member),
      // TODO(3): Add an arm for ['borrow', ...] that throws
      // const FormatException('Usage: borrow <bookId> <member>').
      ['fine', final member, final amount] => payFine(member, parseAmount(amount)),
      [final command, ...] => throw FormatException('Unknown command: $command'),
      [] => throw const FormatException('Empty command'),
    };
  }

  String borrow(String id, String member) {
    final book = _books[id];
    if (book == null) throw BookNotFoundException(id);
    // TODO(4b): If the book already has a borrower, throw AlreadyOnLoanException.
    // If loansOf(member) >= loanLimit, throw LoanLimitException.
    book.borrower = member;
    final title = book.title;
    return '$member borrowed $title';
  }

  String payFine(String member, int amount) {
    assert(amount > 0); // parseAmount must guarantee this.
    return '$member paid a fine of $amount';
  }

  int parseAmount(String raw) {
    // TODO(5): Use int.tryParse. If the result is null or not positive, throw
    // FormatException('Fine must be a positive whole number: <raw>').
    return int.parse(raw);
  }
}

const commands = [
  'borrow b1 asha',
  'borrow b9 asha',
  'borrow b2',
  'borrow b2 ben',
  'borrow b3 asha',
  'borrow b4 asha',
  'borrow b1 ben',
  'fine asha -5',
  'fine asha 20',
  'dance',
];

void main() {
  final desk = LibraryDesk(loanLimit: 2);
  var ok = 0, failed = 0, processed = 0;

  for (final line in commands) {
    try {
      final result = desk.run(line);
      print('OK    $result');
      ok++;
    } on LibraryException catch (e) {
      print('DENY  $e');
      failed++;
    }
    // TODO(2): Add "on FormatException catch (e)" that prints 'BAD   ' plus
    // e.message and counts a failure. Then add a finally block that does
    // processed++ for every command, whatever happened.
    catch (e, stackTrace) {
      print('BUG   $e');
      print(stackTrace);
      rethrow;
    }
  }

  print('Processed $processed commands: $ok ok, $failed failed');
}