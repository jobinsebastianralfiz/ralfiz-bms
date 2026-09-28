// Library Command Desk, lesson 1.10: errors and exceptions (SOLUTION).
// Run with: dart run --enable-asserts bin/main.dart   (or paste into DartPad)

/// Base type for every expected library problem. Callers can catch them all
/// with one "on LibraryException" clause, or pick specific subtypes.
sealed class LibraryException implements Exception {
  const LibraryException(this.message);
  final String message;

  @override
  String toString() => message;
}

final class BookNotFoundException extends LibraryException {
  BookNotFoundException(String id) : super('No book with id $id');
}

final class AlreadyOnLoanException extends LibraryException {
  AlreadyOnLoanException(String title, String borrower)
      : super('$title is already on loan to $borrower');
}

final class LoanLimitException extends LibraryException {
  LoanLimitException(String member, int limit)
      : super('$member has reached the limit of $limit loans');
}

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

  /// Parses one command line and runs it. Throws FormatException for bad
  /// input and LibraryException subtypes for rule violations.
  String run(String line) {
    final parts = line.trim().split(RegExp(r'\s+'));
    return switch (parts) {
      ['borrow', final id, final member] => borrow(id, member),
      ['borrow', ...] => throw const FormatException('Usage: borrow <bookId> <member>'),
      ['fine', final member, final amount] => payFine(member, parseAmount(amount)),
      [final command, ...] => throw FormatException('Unknown command: $command'),
      [] => throw const FormatException('Empty command'),
    };
  }

  String borrow(String id, String member) {
    final book = _books[id];
    if (book == null) throw BookNotFoundException(id);
    final current = book.borrower;
    if (current != null) throw AlreadyOnLoanException(book.title, current);
    if (loansOf(member) >= loanLimit) throw LoanLimitException(member, loanLimit);
    book.borrower = member;
    final title = book.title;
    return '$member borrowed $title';
  }

  String payFine(String member, int amount) {
    assert(amount > 0); // parseAmount guarantees this; the assert documents it.
    return '$member paid a fine of $amount';
  }

  int parseAmount(String raw) {
    final amount = int.tryParse(raw);
    if (amount == null || amount <= 0) {
      throw FormatException('Fine must be a positive whole number: $raw');
    }
    return amount;
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
      // Expected business rule: tell the user, keep going.
      print('DENY  $e');
      failed++;
    } on FormatException catch (e) {
      // Bad input: show the message only.
      final message = e.message;
      print('BAD   $message');
      failed++;
    } catch (e, stackTrace) {
      // Anything else is a bug: log it with the stack trace, then rethrow.
      print('BUG   $e');
      print(stackTrace);
      rethrow;
    } finally {
      processed++;
    }
  }

  print('Processed $processed commands: $ok ok, $failed failed');
}