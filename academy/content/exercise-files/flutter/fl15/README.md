# Prime Counter (lesson 1.13)

A console app that proves heavy work blocks the event loop, and that
Isolate.run keeps the main isolate free. A heartbeat timer counts how many
times it managed to fire while the primes were counted.

Isolates need the Dart VM, so run this on your machine, not in DartPad.

## Setup

    dart create prime_counter
    cd prime_counter

Copy start/bin/main.dart to bin/main.dart and run:

    dart run bin/main.dart

If the first line prints in well under a second, raise limit (for example to
6000000). If it takes much longer than three seconds, lower it.

## Tasks

1. TODO(1) Run the same count with Isolate.run and print the heartbeats.
2. TODO(2) Show that an error inside the isolate is thrown again in main.
3. TODO(3) Call countInParallel(limit, 4) and print the time.
4. TODO(4) Make countRange use Isolate.run.
5. TODO(5) Split the range into parts, start them all, sum the results.

## Acceptance criteria

The output has this shape (numbers depend on your machine):

    Main isolate: <count> primes in <ms> ms, heartbeats: 0 or 1
    Isolate.run: <count> primes in <ms> ms, heartbeats: <about ms / 200>
    Caught FormatException in main
    4 isolates: <count> primes in <ms> ms

- All three counts are the same number.
- The main-isolate line has 0 or 1 heartbeats: the timer could not run.
- The Isolate.run line has roughly (time / 200) heartbeats.
- The 4-isolate run is faster than the single isolate on a multi-core machine.
  It is not exactly four times faster: starting isolates costs time, and the
  higher ranges hold bigger numbers that take longer to test.
