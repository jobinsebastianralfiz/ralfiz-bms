// Library Manager, lesson 1.7: inheritance, interfaces, mixins, extensions (STARTER).
// Run with: dart run bin/main.dart   (or paste into DartPad)
// It compiles now, but several results are wrong. Fill TODO(1) to TODO(6).

abstract class LibraryItem {
  LibraryItem({required this.id, required this.title});

  final String id;
  final String title;

  String get kind;

  @override
  String toString() => '$kind $id: $title';
}

abstract class Borrowable {
  String get title;
  int get loanDays;
  String? get borrower;
  void borrow(String member);
  void giveBack();
}

mixin Lending on LibraryItem implements Borrowable {
  String? _borrower;

  @override
  String? get borrower => _borrower;

  @override
  void borrow(String member) {
    // TODO(1): If the item is already on loan, throw
    // StateError('$title is already on loan') instead of lending it twice.
    _borrower = member;
  }

  @override
  void giveBack() => _borrower = null;
}

mixin Rateable {
  final List<int> _ratings = [];

  void rate(int stars) {
    if (stars < 1 || stars > 5) throw RangeError.range(stars, 1, 5, 'stars');
    _ratings.add(stars);
  }

  // TODO(2): Return the average of _ratings, or 0.0 when there are none.
  double get averageRating => _ratings.isEmpty ? 0.0 : 0.0;
}

class Book extends LibraryItem with Lending, Rateable {
  Book({required super.id, required super.title, required this.isbn});

  final Isbn isbn;

  @override
  String get kind => 'Book';

  @override
  int get loanDays => 21;
}

class Dvd extends LibraryItem with Lending {
  Dvd({required super.id, required super.title});

  @override
  String get kind => 'DVD';

  @override
  int get loanDays => 7;
}

class Magazine extends LibraryItem {
  Magazine({required super.id, required super.title});

  @override
  String get kind => 'Magazine';

  // TODO(3): Override toString to reuse super.toString() and add
  // ' (reading room only)' at the end.
}

class Isbn {
  Isbn(String raw) : digits = raw.replaceAll('-', '');

  final String digits;

  // TODO(4): Override operator == and hashCode so two Isbn objects with the
  // same digits are equal (and a Set keeps only one of them).

  @override
  String toString() => 'ISBN $digits';
}

extension LoanDates on DateTime {
  DateTime plusDays(int days) => add(Duration(days: days));

  // TODO(5): Return the date as yyyy-mm-dd, e.g. 2026-09-08
  // (hint: month.toString().padLeft(2, '0')).
  String get ymd => toIso8601String();
}

// TODO(6): Change the parameter type from Book to Borrowable, so a Dvd can be
// lent too, then uncomment the Inception line in main.
void lend(Book item, String member, DateTime today) {
  item.borrow(member);
  final title = item.title;
  final due = today.plusDays(item.loanDays).ymd;
  print('$member borrows $title, due $due');
}

void main() {
  final today = DateTime.utc(2026, 9, 1);
  final cleanCode = Book(id: 'B1', title: 'Clean Code', isbn: Isbn('978-0132350884'));
  final inception = Dvd(id: 'D1', title: 'Inception');
  final wired = Magazine(id: 'M1', title: 'Wired');

  final List<LibraryItem> catalogue = [cleanCode, inception, wired];
  print('Catalogue');
  for (final item in catalogue) {
    print('  $item');
  }

  lend(cleanCode, 'Asha', today);
  // lend(inception, 'Ben', today);
  try {
    lend(cleanCode, 'Chen', today);
  } on StateError catch (e) {
    print('Error: $e');
  }

  cleanCode
    ..rate(5)
    ..rate(4);
  final rating = cleanCode.averageRating;
  print('Clean Code rating: $rating');

  final copy = Isbn('9780132350884');
  final same = cleanCode.isbn == copy;
  final unique = {cleanCode.isbn, copy}.length;
  print('Same ISBN: $same');
  print('Unique ISBNs: $unique');
}