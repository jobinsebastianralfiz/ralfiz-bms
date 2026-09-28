# Weather Fetcher (lesson 1.11)

A console app that pretends to call a weather service. Every city has a fake
delay, so you can practise async/await, errors, timeouts and Future.wait
without a real network.

## Setup

    dart create weather_fetcher
    cd weather_fetcher

Replace bin/weather_fetcher.dart with start/bin/main.dart (or copy it to
bin/main.dart) and run:

    dart run bin/main.dart

## Tasks

1. TODO(1) fetchWeather: wait for the city's delay, throw
   CityNotFoundException for unknown cities, return a Weather record.
2. TODO(2) describe: destructure the record and format one line.
3. TODO(3) fetch Kochi and print it.
4. TODO(4) fetch Dubai then Toronto one after the other and print the time.
5. TODO(5) fetch both with Future.wait and print the time.
6. TODO(6) handle an unknown city and a timeout.

## Acceptance criteria

The output looks like this (times vary a little):

    Kochi: 29.5 C, Humid
    Dubai: 38.0 C, Sunny
    Toronto: 12.0 C, Cloudy
    Sequential: 2205 ms
    Dubai: 38.0 C, Sunny
    Toronto: 12.0 C, Cloudy
    Parallel: 1203 ms
    Error: No weather data for Atlantis
    London timed out after 2 s
    Done

- Sequential is about 2,200 ms (1,200 + 1,000).
- Parallel is about 1,200 ms (the slowest of the two).
- The results of Future.wait are printed Dubai first, then Toronto, even
  though Toronto finishes first.
- The program ends about one second after "Done": .timeout stops you
  waiting, but the London timer still runs to the end.

Compare with solution/bin/main.dart when you are done.
