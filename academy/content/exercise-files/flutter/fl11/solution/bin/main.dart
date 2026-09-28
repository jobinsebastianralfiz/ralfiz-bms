// Typed Repository, lesson 1.9: generics (SOLUTION).
// Run with: dart run bin/main.dart   (or paste into DartPad)

/// Anything stored in a repository must have an id.
abstract interface class Entity {
  String get id;
}

class Book implements Entity {
  const Book({required this.id, required this.title, required this.author, required this.year});

  @override
  final String id;
  final String title;
  final String author;
  final int year;

  @override
  String toString() => '$title by $author';
}

class Member implements Entity {
  const Member({required this.id, required this.name});

  @override
  final String id;
  final String name;

  @override
  String toString() => name;
}

/// Result<T>: either a value of type T or an error message. Never both.
sealed class Result<T> {
  const Result();
}

final class Success<T> extends Result<T> {
  const Success(this.value);
  final T value;
}

final class Failure<T> extends Result<T> {
  const Failure(this.error);
  final String error;
}

/// A generic method on every Result: turn it into one value of type R.
extension ResultX<T> on Result<T> {
  R when<R>({
    required R Function(T value) success,
    required R Function(String error) failure,
  }) =>
      switch (this) {
        Success(:final value) => success(value),
        Failure(:final error) => failure(error),
      };
}

/// One class, many types: InMemoryRepository<Book>, InMemoryRepository<Member>...
/// The bound (T extends Entity) guarantees every item has an id.
class InMemoryRepository<T extends Entity> {
  final Map<String, T> _items = {};

  int get count => _items.length;
  List<T> get all => _items.values.toList();

  Result<T> add(T item) {
    if (_items.containsKey(item.id)) {
      final id = item.id;
      return Failure('Duplicate id $id');
    }
    _items[item.id] = item;
    return Success(item);
  }

  Result<T> findById(String id) {
    final item = _items[id];
    return item == null ? Failure('No item with id $id') : Success(item);
  }

  List<T> where(bool Function(T item) test) => _items.values.where(test).toList();
}

/// Generic top-level function with two type parameters.
Map<K, int> countBy<T, K>(Iterable<T> items, K Function(T item) keyOf) {
  final counts = <K, int>{};
  for (final item in items) {
    final key = keyOf(item);
    counts[key] = (counts[key] ?? 0) + 1;
  }
  return counts;
}

void report<T>(Result<T> result) {
  final line = result.when(
    success: (value) => 'OK    $value',
    failure: (error) => 'FAIL  $error',
  );
  print(line);
}

void main() {
  final books = InMemoryRepository<Book>();
  final members = InMemoryRepository<Member>();

  report(books.add(const Book(id: 'b1', title: 'Clean Code', author: 'Robert C. Martin', year: 2008)));
  report(books.add(const Book(id: 'b2', title: 'Refactoring', author: 'Martin Fowler', year: 2018)));
  report(books.add(const Book(id: 'b3', title: 'Clean Architecture', author: 'Robert C. Martin', year: 2017)));
  report(books.add(const Book(id: 'b1', title: 'Dune', author: 'Frank Herbert', year: 1965)));
  report(members.add(const Member(id: 'm1', name: 'Asha')));

  report(books.findById('b2'));
  report(members.findById('m9'));

  // where() returns a List<Book>, so b.year and b.title compile without casts.
  final recent = books.where((b) => b.year >= 2017).map((b) => b.title).toList();
  print('Since 2017: $recent');

  final byAuthor = countBy(books.all, (b) => b.author);
  print('By author: $byAuthor');

  final total = books.count + members.count;
  print('Items stored: $total');
}