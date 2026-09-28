// Library Manager, lesson 1.6: classes, objects and constructors (STARTER).
// Run with: dart run bin/main.dart   (or paste into DartPad)
// It compiles now. Fill TODO(1) to TODO(7), uncommenting lines in main as you go.

class Book {
  static int _nextId = 1;

  final int id;
  final String title;
  final String author;
  final int year;
  bool _onLoan = false;

  // TODO(1): Add assert(title.isNotEmpty, 'title must not be empty')
  // to the initializer list, before id = _nextId++.
  Book({required this.title, required this.author, required this.year})
      : id = _nextId++;

  // TODO(2): Add a redirecting constructor Book.unknownAuthor that takes
  // required title and year and redirects to Book(...) with author 'Unknown'.

  // TODO(3): Add factory Book.fromMap(Map<String, Object?> map).
  // Read title, author and year. If any is missing or has the wrong type,
  // throw FormatException('Invalid book data: $map'). Otherwise return a Book.

  // TODO(4): Return true when the book is not on loan.
  bool get isAvailable => true;

  // TODO(5): If the book is already on loan return false.
  // Otherwise mark it as on loan and return true.
  bool checkOut() => false;

  void giveBack() => _onLoan = false;

  // TODO(6): Override toString so a book prints like
  // #2 Dune by Frank Herbert (1965) - on loan
  // (status is 'available' or 'on loan'). Remove the line below when done.
  bool get debugOnLoan => _onLoan;
}

class Library {
  Library(this.name);

  final String name;
  final List<Book> _books = [];

  void add(Book book) => _books.add(book);

  int get total => _books.length;
  int get availableCount => _books.where((b) => b.isAvailable).length;

  // TODO(7): Return the book with this id, or null if there is none.
  Book? findById(int id) => null;

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
  // After TODO(3):
  // library.add(Book.fromMap({'title': 'Dune', 'author': 'Frank Herbert', 'year': 1965}));
  // After TODO(2):
  // library.add(Book.unknownAuthor(title: 'Beowulf', year: 1000));

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

  // After TODO(3):
  // try {
  //   Book.fromMap({'title': 'Broken'});
  // } on FormatException catch (e) {
  //   final message = e.message;
  //   print('Error: $message');
  // }
}