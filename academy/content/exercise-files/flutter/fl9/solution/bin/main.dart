// Library Manager, lesson 1.7: inheritance, interfaces, mixins, extensions (SOLUTION).
// Run with: dart run bin/main.dart   (or paste into DartPad)

/// Base class for everything the library holds. abstract: no LibraryItem(...) objects.
abstract class LibraryItem {
  LibraryItem({required this.id, required this.title});

  final String id;
  final String title;

  /// Abstract getter: every concrete subclass must provide it.
  String get kind;

  @override
  String toString() => '$kind $id: $title';
}

/// An interface: a contract with no code. Classes "implements" it.
abstract class Borrowable {
  String get title;
  int get loanDays;
  String? get borrower;
  void borrow(String member);
  void giveBack();
}

/// Mixin: reusable loan logic. It can only be mixed into LibraryItem
/// subclasses (on LibraryItem), and it implements most of Borrowable.
mixin Lending on LibraryItem implements Borrowable {
  String? _borrower;

  @override
  String? get borrower => _borrower;

  @override
  void borrow(String member) {
    if (_borrower != null) throw StateError('$title is already on loan');
    _borrower = member;
  }

  @override
  void giveBack() => _borrower = null;
}

/// Mixin with its own state: star ratings.
mixin Rateable {
  final List<int> _ratings = [];

  void rate(int stars) {
    if (stars < 1 || stars > 5) throw RangeError.range(stars, 1, 5, 'stars');
    _ratings.add(stars);
  }

  double get averageRating =>
      _ratings.isEmpty ? 0.0 : _ratings.reduce((a, b) => a + b) / _ratings.length;
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

  @override
  String toString() => super.toString() + ' (reading room only)';
}

/// Value object: two Isbn objects with the same digits are equal.
class Isbn {
  Isbn(String raw) : digits = raw.replaceAll('-', '');

  final String digits;

  @override
  bool operator ==(Object other) => other is Isbn && other.digits == digits;

  @override
  int get hashCode => digits.hashCode;

  @override
  String toString() => 'ISBN $digits';
}

/// Extension methods: new abilities for DateTime without subclassing it.
extension LoanDates on DateTime {
  DateTime plusDays(int days) => add(Duration(days: days));

  String get ymd {
    final m = month.toString().padLeft(2, '0');
    final d = day.toString().padLeft(2, '0');
    return '$year-$m-$d';
  }
}

/// Works with ANY Borrowable: a Book, a Dvd, or something new later.
void lend(Borrowable item, String member, DateTime today) {
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
  lend(inception, 'Ben', today);
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