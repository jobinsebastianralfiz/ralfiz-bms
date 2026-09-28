# Lab 1.9: Typed Repository with Result<T>

You build one generic in-memory repository that stores books, members or any
other Entity, with full type safety. Every operation returns a Result<T>, a
sealed generic type that is either Success<T> or Failure<T>, instead of
throwing or returning null. This is the same shape you will use later for
repositories that call real APIs.

## Files
- start/bin/main.dart: compiles, but uses casts instead of a bound, and findById, when() and countBy are placeholders. Fill TODO(1) to TODO(4).
- solution/bin/main.dart: one finished version.

## Run it

    dart run bin/main.dart

## Expected output

    OK    Clean Code by Robert C. Martin
    OK    Refactoring by Martin Fowler
    OK    Clean Architecture by Robert C. Martin
    FAIL  Duplicate id b1
    OK    Asha
    OK    Refactoring by Martin Fowler
    FAIL  No item with id m9
    Since 2017: [Refactoring, Clean Architecture]
    By author: {Robert C. Martin: 2, Martin Fowler: 1}
    Items stored: 4

## Acceptance criteria
1. InMemoryRepository is declared as InMemoryRepository<T extends Entity> and contains no "as" casts.
2. InMemoryRepository<int>() is now a compile error (try it, then remove the line).
3. findById returns a Result<T> and never returns null or throws for a missing id.
4. when() is a switch expression over the sealed Result with no wildcard arm.
5. countBy is a generic function with two type parameters (T and K) and works for any key type.

## Stretch
- Add a generic method Result<R> map<R>(R Function(T value) transform) to the ResultX extension, then call report(books.findById('b1').map((b) => b.year)). It should print OK    2008.
- Count books by decade with countBy(books.all, (b) => b.year ~/ 10 * 10). K is now int, and you changed no code in countBy.