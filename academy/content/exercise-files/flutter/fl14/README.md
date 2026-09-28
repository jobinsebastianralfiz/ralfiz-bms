# Weather Station (lesson 1.12)

A console app that reads a fake temperature sensor as a Stream, cleans and
converts the readings, and sends alerts to two listeners through a broadcast
StreamController.

## Setup

    dart create weather_station
    cd weather_station

Copy start/bin/main.dart to bin/main.dart and run:

    dart run bin/main.dart

## Tasks

1. TODO(1) Make sensor() an async* generator that yields each reading.
2. TODO(2) Drop glitch values (-999) and convert to Fahrenheit.
3. TODO(3) Build AlertCenter on a broadcast StreamController.
4. TODO(4) Add a second listener (the watch) and keep its subscription.
5. TODO(5) Read the first five clean readings with await for and raise alerts.
6. TODO(6) Cancel the watch, then use toList() for the daily maximum.
7. TODO(7) Listen to a periodic ticker, cancel it, then close the center.

## Acceptance criteria

The output is:

    Reading 1: 82.4 F
    Reading 2: 85.1 F
    Reading 3: 91.8 F
    Phone: Hot! 91.8 F
    Watch: Hot! 91.8 F
    Reading 4: 87.8 F
    Reading 5: 96.4 F
    Phone: Hot! 96.4 F
    Watch: Hot! 96.4 F
    Watch unpaired
    Max of 7 readings: 97.5 F
    Phone: Daily max 97.5 F
    Tick 1
    Tick 2
    Tick 3
    Tick 4
    Ticker cancelled
    Station closed

- The glitch reading never appears.
- After "Watch unpaired" only the phone receives alerts.
- No ticks are printed after "Ticker cancelled".
- The program exits by itself (every controller is closed, every
  subscription cancelled or done).
