// Library Manager, lesson 1.6: classes, objects and constructors (SOLUTION).
// Run with: dart run bin/main.dart   (or paste into DartPad)

class Book {
  /// Shared by every Book: the next id to hand out.
  static int _nextId = 1;

  final int id;
  final String title;
  final String author;
  final int year;

  /// Private field: only code in this file (library) can touch it.
  bool _onLoan = false;

  /// Generative constructor with named, required parameters,
  /// an assert and an initializer list that sets id.
  Book({required this.title, required this.author, required this.year})
      : assert(title.isNotEmpty, 'title must not be empty'),
        id = _nextId++;

  /// Redirecting constructor: fills in the author, then calls Book(...).
  Book.unknownAuthor({required String title, required int year})
      : this(title: title, author: 'Unknown', year: year);

  /// Factory constructor: validates raw data before creating a Book.
  factory Book.fromMap(Map<String, Object?> map) {
    final title = map['title'];
    final author = map['author'];
    final year = map['year'];
    if (title is! String || author is! String || year is! int) {
      throw FormatException('Invalid book data: $map');
    }
    return Book(title: title, author: author, year: year);
  }

  /// Getter: computed from private state, read like a field.
  bool get isAvailable => !_onLoan;

  bool checkOut() {
    if (_onLoan) return false;
    _onLoan = true;
    return true;
  }

  void giveBack() => _onLoan = false;

  @override
  String toString() {
    final status = _onLoan ? 'on loan' : 'available';
    return '#$id $title by $author ($year) - $status';
  }
}

class Library {
  Library(this.name);

  final String name;
  final List<Book> _books = [];

  void add(Book book) => _books.add(book);

  int get total => _books.length;
  int get availableCount => _books.where((b) => b.isAvailable).length;

  Book? findById(int id) {
    for (final book in _books) {
      if (book.id == id) return book;
    }
    return null;
  }

  bool checkOut(int id) => findById(id)?.checkOut() ?? false;

  void printCatalogue() {
    for (final book in _books) {
      print('  $book');
    }
  }
}

void main() {
  final library = Library('Ralfiz Community Library');
  library.add(Book(title: 'Clean Code', author: 'Robert C. Martin', year: 2008));
  library.add(Book.fromMap({'title': 'Dune', 'author': 'Frank Herbert', 'year': 1965}));
  library.add(Book.unknownAuthor(title: 'Beowulf', year: 1000));

  print(library.name);
  library.printCatalogue();

  final first = library.checkOut(2);
  final second = library.checkOut(2);
  final missing = library.checkOut(99);
  print('Check out #2: $first');
  print('Check out #2 again: $second');
  print('Check out #99: $missing');

  final available = library.availableCount;
  final total = library.total;
  print('Available: $available of $total');
  library.printCatalogue();

  try {
    Book.fromMap({'title': 'Broken'});
  } on FormatException catch (e) {
    final message = e.message;
    print('Error: $message');
  }
}