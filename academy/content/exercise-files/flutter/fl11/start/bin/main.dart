// Typed Repository, lesson 1.9: generics (STARTER).
// Run with: dart run bin/main.dart   (or paste into DartPad)
// It compiles now, but findById, when() and countBy are placeholders. Fill TODO(1) to TODO(4).

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
      // TODO(3): switch on this: call success(value) for Success and
      // failure(error) for Failure. No wildcard arm needed: Result is sealed.
      failure('when() is not implemented yet');
}

// TODO(1): Add the bound T extends Entity, then delete every (item as Entity)
// cast and use item.id directly. The casts are a runtime risk: try
// InMemoryRepository<int>() before and after the change.
class InMemoryRepository<T> {
  final Map<String, T> _items = {};

  int get count => _items.length;
  List<T> get all => _items.values.toList();

  Result<T> add(T item) {
    final id = (item as Entity).id;
    if (_items.containsKey(id)) {
      return Failure('Duplicate id $id');
    }
    _items[id] = item;
    return Success(item);
  }

  // TODO(2): Look the id up in _items. Return Success(item) when found,
  // otherwise Failure('No item with id <id>').
  Result<T> findById(String id) => Failure('findById is not implemented yet');

  List<T> where(bool Function(T item) test) => _items.values.where(test).toList();
}

/// Generic top-level function with two type parameters.
// TODO(4): Count how many items share each key, e.g. {Robert C. Martin: 2, ...}.
// Start from an empty <K, int>{} and add 1 per item (hint: counts[key] ?? 0).
Map<K, int> countBy<T, K>(Iterable<T> items, K Function(T item) keyOf) {
  return <K, int>{};
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