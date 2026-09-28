// Prime Counter - SOLUTION (lesson 1.13)
// Run with: dart run bin/main.dart   (isolates do not run in DartPad)
import 'dart:async';
import 'dart:isolate';

/// Raise or lower this so each count takes one to three seconds on your machine.
const limit = 3000000;

/// True when n is a prime number.
bool isPrime(int n) {
  if (n < 2) return false;
  for (var d = 2; d * d <= n; d++) {
    if (n % d == 0) return false;
  }
  return true;
}

/// Heavy, CPU-only work: counts primes p with from <= p < to.
/// Top-level, so it is safe to run in another isolate.
int countPrimesBetween(int from, int to) {
  var count = 0;
  for (var n = from; n < to; n++) {
    if (isPrime(n)) count++;
  }
  return count;
}

int countPrimes(int max) => countPrimesBetween(2, max);

/// Runs one range in a new isolate. The closure captures only from and to.
Future<int> countRange(int from, int to) =>
    Isolate.run(() => countPrimesBetween(from, to));

/// Stretch: splits the range into parts, one isolate per part.
Future<int> countInParallel(int max, int parts) async {
  final size = max ~/ parts;
  final jobs = [
    for (var i = 0; i < parts; i++)
      countRange(i * size, i == parts - 1 ? max : (i + 1) * size),
  ];
  final counts = await Future.wait(jobs);
  return counts.fold<int>(0, (sum, c) => sum + c);
}

Future<void> main() async {
  var beats = 0;
  final heartbeat = Timer.periodic(
    const Duration(milliseconds: 200),
    (_) => beats++,
  );
  final watch = Stopwatch()..start();

  // 1. Heavy work on the main isolate: the heartbeat cannot run.
  final a = countPrimes(limit);
  await Future.delayed(Duration.zero); // let pending timer events run
  final t1 = watch.elapsedMilliseconds;
  print('Main isolate: $a primes in $t1 ms, heartbeats: $beats');

  // 2. The same work in Isolate.run: the main isolate stays free.
  beats = 0;
  watch.reset();
  final b = await Isolate.run(() => countPrimes(limit));
  final t2 = watch.elapsedMilliseconds;
  print('Isolate.run: $b primes in $t2 ms, heartbeats: $beats');

  // 3. Errors come back as the same error type.
  try {
    await Isolate.run(() => countPrimes(int.parse('three million')));
  } on FormatException {
    print('Caught FormatException in main');
  }

  // 4. Stretch: split the work across 4 isolates.
  watch.reset();
  final c = await countInParallel(limit, 4);
  final t3 = watch.elapsedMilliseconds;
  print('4 isolates: $c primes in $t3 ms');

  heartbeat.cancel();
}
