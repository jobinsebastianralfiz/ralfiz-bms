// Prime Counter - STARTER (lesson 1.13)
// Run with: dart run bin/main.dart   (isolates do not run in DartPad)
// This file compiles as it is. Fill in TODO(1) to TODO(5).
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
int countPrimesBetween(int from, int to) {
  var count = 0;
  for (var n = from; n < to; n++) {
    if (isPrime(n)) count++;
  }
  return count;
}

int countPrimes(int max) => countPrimesBetween(2, max);

/// Runs one range in a new isolate.
Future<int> countRange(int from, int to) async {
  // TODO(4): Return Isolate.run(() => countPrimesBetween(from, to)).
  return countPrimesBetween(from, to);
}

/// Stretch: splits 2..max into parts, one isolate per part.
Future<int> countInParallel(int max, int parts) async {
  // TODO(5): Build a list of countRange futures (the last part ends at max),
  //   await them with Future.wait and return the sum.
  return 0;
}

Future<void> main() async {
  var beats = 0;
  final heartbeat = Timer.periodic(
    const Duration(milliseconds: 200),
    (_) => beats++,
  );
  final watch = Stopwatch()..start();

  // 1. Heavy work on the main isolate.
  final a = countPrimes(limit);
  await Future.delayed(Duration.zero); // let pending timer events run
  final t1 = watch.elapsedMilliseconds;
  print('Main isolate: $a primes in $t1 ms, heartbeats: $beats');

  // TODO(1): Reset beats and the stopwatch. Run countPrimes(limit) with
  //   Isolate.run and print "Isolate.run: <count> primes in <ms> ms,
  //   heartbeats: <beats>".

  // TODO(2): Call Isolate.run(() => countPrimes(int.parse('three million')))
  //   inside try, and print "Caught FormatException in main" in an
  //   on FormatException block.

  // TODO(3): Reset the stopwatch, call countInParallel(limit, 4) and print
  //   "4 isolates: <count> primes in <ms> ms".

  heartbeat.cancel();
}
